import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import count
from threading import Lock
from typing import Dict, List

import mercadopago
import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.crud import pago as crud_pago
from app.database import get_db
from app.schemas.pago import (
    PagoCancelarResponse,
    PagoCreate,
    PagoCreateCheckoutRequest,
    PagoCreateCheckoutResponse,
    PagoDirectoRequest,
    PagoDirectoResponse,
    PagoEstadoResponse,
    PagoEstadoUpdate,
    PagoResponse,
    PagoUpdate,
    WebhookAckResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pagos", tags=["pagos"])

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_SUCCESS_URL = os.getenv("MP_SUCCESS_URL", "https://www.mercadopago.cl")
MP_FAILURE_URL = os.getenv("MP_FAILURE_URL", "https://www.mercadopago.cl")
MP_PENDING_URL = os.getenv("MP_PENDING_URL", "https://www.mercadopago.cl")
MP_WEBHOOK_URL = os.getenv("MP_WEBHOOK_URL")
TIMEOUT_PAGO_SEGUNDOS = 120

OPERACIONES_PAGO: Dict[int, dict] = {}
OPERACIONES_LOCK = Lock()
OPERACIONES_SEQ = count(start=1_000_000)


ESTADOS_FINALES = {"PAGADO", "RECHAZADO", "CANCELADO", "EXPIRADO", "ANULADO"}


def _registrar_operacion(payload: PagoDirectoRequest, external_reference: str, mp_payment_id: int | None, estado: str) -> int:
    id_operacion = next(OPERACIONES_SEQ)
    with OPERACIONES_LOCK:
        OPERACIONES_PAGO[id_operacion] = {
            "id_operacion": id_operacion,
            "id_usuario": payload.id_usuario,
            "descripcion": payload.descripcion,
            "monto": float(payload.monto),
            "external_reference": external_reference,
            "mp_payment_id": mp_payment_id,
            "estado": estado,
            "creado_en": datetime.utcnow(),
            "id_pago_persistido": None,
        }
    return id_operacion


def _actualizar_operacion(id_operacion: int, estado: str) -> None:
    with OPERACIONES_LOCK:
        operacion = OPERACIONES_PAGO.get(id_operacion)
        if operacion:
            operacion["estado"] = estado


def _buscar_operacion_por_external_reference(external_reference: str) -> tuple[int, dict] | tuple[None, None]:
    with OPERACIONES_LOCK:
        for operacion_id, operacion in OPERACIONES_PAGO.items():
            if operacion.get("external_reference") == external_reference:
                return operacion_id, operacion
    return None, None


def _expirar_si_corresponde(id_operacion: int) -> dict | None:
    with OPERACIONES_LOCK:
        operacion = OPERACIONES_PAGO.get(id_operacion)
        if not operacion:
            return None

        if operacion["estado"] in ESTADOS_FINALES:
            return operacion

        if datetime.utcnow() - operacion["creado_en"] >= timedelta(seconds=TIMEOUT_PAGO_SEGUNDOS):
            operacion["estado"] = "EXPIRADO"
        return operacion


def _guardar_pago_si_aprobado(db: Session, operacion: dict) -> int:
    if operacion.get("id_pago_persistido"):
        return operacion["id_pago_persistido"]

    now = datetime.utcnow()
    pago_db = crud_pago.create_pago(
        db=db,
        pago=PagoCreate(
            id_usuario=operacion["id_usuario"],
            id_suscripcion=None,
            id_metodo_pago=1,
            periodo_anio=now.year,
            periodo_mes=now.month,
            monto_total=Decimal(str(operacion["monto"])),
            estado_pago="PAGADO",
            codigo_transaccion=str(operacion.get("mp_payment_id")) if operacion.get("mp_payment_id") else None,
            observacion=operacion["external_reference"],
        ),
    )
    operacion["id_pago_persistido"] = pago_db.id_pago
    return pago_db.id_pago


@router.post("/crear", response_model=PagoCreateCheckoutResponse, status_code=status.HTTP_201_CREATED)
def crear_pago_checkout(payload: PagoCreateCheckoutRequest, db: Session = Depends(get_db)):
    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="MP_ACCESS_TOKEN no configurado")

    logger.info("[pagos] Creación de pago iniciada id_usuario=%s monto=%s", payload.id_usuario, payload.monto)

    external_reference = crud_pago.generate_external_reference(payload.id_usuario)
    sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
    preference_data = {
        "items": [{"title": payload.descripcion, "quantity": 1, "currency_id": "CLP", "unit_price": float(payload.monto)}],
        "payer": {"email": payload.email_pagador},
        "external_reference": external_reference,
        "back_urls": {"success": MP_SUCCESS_URL, "failure": MP_FAILURE_URL, "pending": MP_PENDING_URL},
        "auto_return": "approved",
        "notification_url": MP_WEBHOOK_URL,
    }

    preference_response = sdk.preference().create(preference_data)
    body = preference_response.get("response", {})
    init_point = body.get("init_point")
    preference_id = body.get("id")
    if preference_response.get("status") not in (200, 201) or not init_point:
        raise HTTPException(status_code=502, detail="No fue posible crear preferencia en Mercado Pago")

    # Solo se crea operación temporal para checkout externo. Persistencia real ocurre al aprobarse.
    operacion_id = _registrar_operacion(
        payload=PagoDirectoRequest(
            id_usuario=payload.id_usuario,
            numero_tarjeta="4111111111111111",
            mes_vencimiento=11,
            anio_vencimiento=2030,
            cvv="123",
            nombre_titular="CHECKOUT",
            email=str(payload.email_pagador),
            descripcion=payload.descripcion,
            monto=payload.monto,
        ),
        external_reference=external_reference,
        mp_payment_id=None,
        estado="PENDIENTE",
    )
    _actualizar_operacion(operacion_id, "PENDIENTE")

    return PagoCreateCheckoutResponse(
        success=True,
        message="Pago creado correctamente",
        data={"id_pago": operacion_id, "url_pago": init_point, "external_reference": external_reference, "preference_id": preference_id},
    )


@router.get("/{id_pago}/estado", response_model=PagoEstadoResponse)
def consultar_estado_pago(id_pago: int, db: Session = Depends(get_db)):
    operacion = _expirar_si_corresponde(id_pago)
    if operacion:
        return PagoEstadoResponse(id_pago=id_pago, estado=operacion["estado"])

    db_pago = crud_pago.get_pago(db, pago_id=id_pago)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return PagoEstadoResponse(id_pago=id_pago, estado=db_pago.estado_pago)


@router.post("/{id_pago}/cancelar", response_model=PagoCancelarResponse)
def cancelar_pago(id_pago: int, db: Session = Depends(get_db)):
    operacion = _expirar_si_corresponde(id_pago)
    if operacion:
        estado_actual = operacion["estado"]
        if estado_actual in {"PAGADO", "RECHAZADO", "EXPIRADO", "CANCELADO"}:
            return PagoCancelarResponse(success=True, message="El pago ya tiene un estado final", data=PagoEstadoResponse(id_pago=id_pago, estado=estado_actual))

        mp_payment_id = operacion.get("mp_payment_id")
        if mp_payment_id and MP_ACCESS_TOKEN:
            try:
                requests.put(
                    f"https://api.mercadopago.com/v1/payments/{mp_payment_id}",
                    headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                    json={"status": "cancelled"},
                    timeout=10,
                )
            except Exception as error:  # noqa: BLE001
                logger.warning("[pagos] No fue posible cancelar en MP id_pago=%s error=%s", id_pago, error)

        _actualizar_operacion(id_pago, "CANCELADO")
        return PagoCancelarResponse(success=True, message="Pago cancelado", data=PagoEstadoResponse(id_pago=id_pago, estado="CANCELADO"))

    db_pago = crud_pago.get_pago(db, pago_id=id_pago)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    db_pago = crud_pago.update_estado_pago(db, pago_id=id_pago, estado="CANCELADO")
    return PagoCancelarResponse(success=True, message="Pago cancelado", data=PagoEstadoResponse(id_pago=id_pago, estado=db_pago.estado_pago))


@router.post("/directo/procesar", response_model=PagoDirectoResponse, status_code=status.HTTP_201_CREATED)
def procesar_pago_directo(payload: PagoDirectoRequest, db: Session = Depends(get_db)):
    if not MP_ACCESS_TOKEN:
        return{
            "success": True,
            "message": "Pago Simulado Correctamente",
            "data":{
                "estado": "PAGADO",
                "monto": float(payload.monto)
            }
        }

    logger.info("[pagos] INICIO PAGO DIRECTO id_usuario=%s monto=%s", payload.id_usuario, payload.monto)
    try:
        import uuid
        auth_header = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}", "Content-Type": "application/json"}

        # Tokenizar tarjeta usando el access token como Bearer (server-side tokenization)
        token_payload = {
            "card_number": payload.numero_tarjeta,
            "expiration_month": payload.mes_vencimiento,
            "expiration_year": payload.anio_vencimiento,
            "security_code": payload.cvv,
            "cardholder": {
                "name": payload.nombre_titular,
                "identification": {"type": "RUT", "number": "14357293-K"},
            },
        }
        token_response = requests.post(
            "https://api.mercadopago.com/v1/card_tokens",
            json=token_payload,
            headers=auth_header,
            timeout=20,
        )
        if token_response.status_code != 201:
            logger.error("[pagos] Error tokenizando tarjeta: %s", token_response.text)
            raise HTTPException(status_code=502, detail="No fue posible tokenizar la tarjeta")

        card_token = token_response.json().get("id")
        if not card_token:
            raise HTTPException(status_code=502, detail="No fue posible tokenizar la tarjeta")

        external_reference = crud_pago.generate_external_reference(payload.id_usuario)
        # Nota: no incluir currency_id (rechazado por MP para CLP) ni payment_method_id
        # (MP lo infiere automáticamente del token de tarjeta)
        payment_payload = {
            "token": card_token,
            "transaction_amount": float(payload.monto),
            "description": payload.descripcion,
            "installments": 1,
            "external_reference": external_reference,
            "payer": {"email": payload.email},
        }
        idempotency_key = str(uuid.uuid4())
        payment_response = requests.post(
            "https://api.mercadopago.com/v1/payments",
            json=payment_payload,
            headers={**auth_header, "X-Idempotency-Key": idempotency_key},
            timeout=20,
        )
        payment_data = payment_response.json()
        if payment_response.status_code not in (200, 201):
            logger.error("[pagos] Error MP pago directo response=%s", payment_data)
            raise HTTPException(status_code=502, detail=payment_data.get("message", "Error procesando pago"))

        mp_payment_id = payment_data.get("id")
        estado = crud_pago.map_mp_status(payment_data.get("status"))
        id_operacion = _registrar_operacion(payload, external_reference, mp_payment_id, estado)

        if estado == "PAGADO":
            with OPERACIONES_LOCK:
                operacion = OPERACIONES_PAGO[id_operacion]
                _guardar_pago_si_aprobado(db, operacion)

        logger.info("[pagos] Pago directo creado id_operacion=%s mp_payment_id=%s estado=%s", id_operacion, mp_payment_id, estado)
        return PagoDirectoResponse(
            success=True,
            message="Pago iniciado correctamente",
            data={"id_pago": id_operacion, "estado": estado, "mp_payment_id": mp_payment_id, "external_reference": external_reference},
        )
    except HTTPException:
        raise
    except Exception as error:  # noqa: BLE001
        logger.exception("[pagos] Error inesperado en pago directo")
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/webhook", response_model=WebhookAckResponse)
async def recibir_webhook(
    request: Request,
    type: str | None = Query(default=None),
    data_id: str | None = Query(default=None, alias="data.id"),
    db: Session = Depends(get_db),
):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    event_type = type or payload.get("type")
    event_data_id = data_id or payload.get("data", {}).get("id")

    if event_type != "payment" or not event_data_id:
        return WebhookAckResponse(success=True, message="Evento ignorado")

    if not MP_ACCESS_TOKEN:
        return {
            "success": True,
            "messange":"Pago simulado correctamente",
            "data": {
                "estado": "PAGADO",
                "monto": float(payload.monto)
            }
        }

    sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
    payment_resp = sdk.payment().get(event_data_id)
    payment = payment_resp.get("response", {})
    external_reference = payment.get("external_reference")
    nuevo_estado = crud_pago.map_mp_status(payment.get("status", ""))

    if external_reference:
        operacion_id, operacion = _buscar_operacion_por_external_reference(external_reference)
        if operacion:
            _actualizar_operacion(operacion_id, nuevo_estado)
            with OPERACIONES_LOCK:
                if nuevo_estado == "PAGADO":
                    operacion = OPERACIONES_PAGO[operacion_id]
                    operacion["mp_payment_id"] = payment.get("id")
                    _guardar_pago_si_aprobado(db, operacion)
            return WebhookAckResponse(success=True, message="Webhook procesado")

        db_pago = crud_pago.get_pago_by_external_reference(db, external_reference)
        if db_pago and db_pago.estado_pago != nuevo_estado:
            crud_pago.update_estado_pago(db, pago_id=db_pago.id_pago, estado=nuevo_estado)
            crud_pago.update_codigo_transaccion(db, pago_id=db_pago.id_pago, codigo=str(payment.get("id")))

    return WebhookAckResponse(success=True, message="Webhook procesado")


@router.get("/", response_model=List[PagoResponse])
def read_pagos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_pago.get_pagos(db, skip=skip, limit=limit)


@router.get("/usuario/{id_usuario}", response_model=List[PagoResponse])
def read_pagos_by_usuario(id_usuario: int, db: Session = Depends(get_db)):
    return crud_pago.get_pagos_by_usuario(db, usuario_id=id_usuario)


@router.get("/periodo/{anio}/{mes}", response_model=List[PagoResponse])
def read_pagos_by_periodo(anio: int, mes: int, db: Session = Depends(get_db)):
    if not 1 <= mes <= 12:
        raise HTTPException(status_code=400, detail="El mes debe estar entre 1 y 12")
    if anio < 2020:
        raise HTTPException(status_code=400, detail="El año debe ser mayor o igual a 2020")
    return crud_pago.get_pagos_by_periodo(db, anio=anio, mes=mes)


@router.get("/suscripcion/{id_suscripcion}", response_model=List[PagoResponse])
def read_pagos_by_suscripcion(id_suscripcion: int, db: Session = Depends(get_db)):
    return crud_pago.get_pagos_by_suscripcion(db, suscripcion_id=id_suscripcion)


@router.get("/{id}", response_model=PagoResponse)
def read_pago(id: int, db: Session = Depends(get_db)):
    db_pago = crud_pago.get_pago(db, pago_id=id)
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago


@router.put("/{id}", response_model=PagoResponse)
def update_pago(id: int, pago: PagoUpdate, db: Session = Depends(get_db)):
    db_pago = crud_pago.update_pago(db, pago_id=id, pago=pago)
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago


@router.patch("/{id}/estado", response_model=PagoResponse)
def update_estado_pago(id: int, estado_update: PagoEstadoUpdate, db: Session = Depends(get_db)):
    db_pago = crud_pago.update_estado_pago(db, pago_id=id, estado=estado_update.estado_pago)
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago


@router.post("/{id}/anular", response_model=PagoResponse)
def anular_pago(id: int, db: Session = Depends(get_db)):
    db_pago = crud_pago.anular_pago(db, pago_id=id)
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pago(id: int, db: Session = Depends(get_db)):
    success = crud_pago.delete_pago(db, pago_id=id)
    if not success:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return None
