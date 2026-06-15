import logging
import os
import uuid
from datetime import datetime, timedelta
from itertools import count
from threading import Lock
from typing import Dict

import mercadopago
import requests
from fastapi import APIRouter, HTTPException, Query, Request, status

from app.schemas.pago import (
    PagoCancelarResponse,
    PagoConTokenRequest,
    PagoCreateCheckoutRequest,
    PagoCreateCheckoutResponse,
    PagoDirectoRequest,
    PagoDirectoResponse,
    PagoEstadoResponse,
    WebhookAckResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pagos", tags=["pagos"])

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_PUBLIC_KEY = os.getenv("MP_PUBLIC_KEY", "")
MP_SUCCESS_URL = os.getenv("MP_SUCCESS_URL", "https://www.mercadopago.cl")
MP_FAILURE_URL = os.getenv("MP_FAILURE_URL", "https://www.mercadopago.cl")
MP_PENDING_URL = os.getenv("MP_PENDING_URL", "https://www.mercadopago.cl")
MP_WEBHOOK_URL = os.getenv("MP_WEBHOOK_URL")
TIMEOUT_PAGO_SEGUNDOS = 120

OPERACIONES_PAGO: Dict[int, dict] = {}
OPERACIONES_LOCK = Lock()
OPERACIONES_SEQ = count(start=1_000_000)

ESTADOS_FINALES = {"PAGADO", "RECHAZADO", "CANCELADO", "EXPIRADO", "ANULADO"}


def _generate_external_reference(id_usuario: int) -> str:
    """Genera una referencia externa única"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"USR{id_usuario}-{timestamp}-{uuid.uuid4().hex[:8]}"


def _map_mp_status(mp_status: str) -> str:
    """Mapea estados de MercadoPago a estados internos"""
    mapping = {
        "approved": "PAGADO",
        "pending": "PENDIENTE",
        "in_process": "PENDIENTE",
        "rejected": "RECHAZADO",
        "cancelled": "CANCELADO",
        "refunded": "ANULADO",
        "charged_back": "ANULADO",
    }
    return mapping.get(mp_status, "PENDIENTE")


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


@router.post("/crear", response_model=PagoCreateCheckoutResponse, status_code=status.HTTP_201_CREATED)
def crear_pago_checkout(payload: PagoCreateCheckoutRequest):
    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="MP_ACCESS_TOKEN no configurado")

    logger.info("[pagos] Creación de pago iniciada id_usuario=%s monto=%s", payload.id_usuario, payload.monto)

    external_reference = _generate_external_reference(payload.id_usuario)
    sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
    preference_data = {
        "items": [{"title": payload.descripcion, "quantity": 1, "currency_id": "CLP", "unit_price": int(float(payload.monto))}],
        "payer": {"email": str(payload.email_pagador)},
        "external_reference": external_reference,
        "back_urls": {"success": MP_SUCCESS_URL, "failure": MP_FAILURE_URL, "pending": MP_PENDING_URL},
    }
    if MP_WEBHOOK_URL:
        preference_data["notification_url"] = MP_WEBHOOK_URL

    preference_response = sdk.preference().create(preference_data)
    body = preference_response.get("response", {})
    init_point = body.get("init_point")
    preference_id = body.get("id")
    if preference_response.get("status") not in (200, 201) or not init_point:
        raise HTTPException(status_code=502, detail="No fue posible crear preferencia en Mercado Pago")

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

    return PagoCreateCheckoutResponse(
        success=True,
        message="Pago creado correctamente",
        data={"id_pago": operacion_id, "url_pago": init_point, "external_reference": external_reference, "preference_id": preference_id},
    )


@router.get("/{id_pago}/estado", response_model=PagoEstadoResponse)
def consultar_estado_pago(id_pago: int):
    operacion = _expirar_si_corresponde(id_pago)
    if not operacion:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return PagoEstadoResponse(id_pago=id_pago, estado=operacion["estado"])


@router.post("/{id_pago}/cancelar", response_model=PagoCancelarResponse)
def cancelar_pago(id_pago: int):
    operacion = _expirar_si_corresponde(id_pago)
    if not operacion:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    estado_actual = operacion["estado"]
    if estado_actual in ESTADOS_FINALES:
        return PagoCancelarResponse(
            success=True, 
            message="El pago ya tiene un estado final", 
            data=PagoEstadoResponse(id_pago=id_pago, estado=estado_actual)
        )

    mp_payment_id = operacion.get("mp_payment_id")
    if mp_payment_id and MP_ACCESS_TOKEN:
        try:
            requests.put(
                f"https://api.mercadopago.com/v1/payments/{mp_payment_id}",
                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                json={"status": "cancelled"},
                timeout=10,
            )
        except Exception as error:
            logger.warning("[pagos] No fue posible cancelar en MP id_pago=%s error=%s", id_pago, error)

    _actualizar_operacion(id_pago, "CANCELADO")
    return PagoCancelarResponse(
        success=True, 
        message="Pago cancelado", 
        data=PagoEstadoResponse(id_pago=id_pago, estado="CANCELADO")
    )


@router.post("/directo/procesar", response_model=PagoDirectoResponse, status_code=status.HTTP_201_CREATED)
def procesar_pago_directo(payload: PagoDirectoRequest):
    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="MP_ACCESS_TOKEN no configurado")
    if not MP_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="MP_PUBLIC_KEY no configurado")

    logger.info("[pagos] INICIO PAGO DIRECTO id_usuario=%s monto=%s", payload.id_usuario, payload.monto)
    try:
        auth_header = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}", "Content-Type": "application/json"}

        is_test = MP_ACCESS_TOKEN.startswith("TEST-")
        cardholder_name = "APRO" if is_test else payload.nombre_titular
        token_payload = {
            "card_number": payload.numero_tarjeta,
            "expiration_month": payload.mes_vencimiento,
            "expiration_year": payload.anio_vencimiento,
            "security_code": payload.cvv,
            "cardholder": {
                "name": cardholder_name,
                "identification": {"type": "RUT", "number": "12345678-5"},
            },
        }
        token_response = requests.post(
            f"https://api.mercadopago.com/v1/card_tokens?public_key={MP_PUBLIC_KEY}",
            json=token_payload,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        logger.info("[pagos] Token response status=%s body=%s", token_response.status_code, token_response.text)
        if token_response.status_code != 201:
            logger.error("[pagos] Error tokenizando tarjeta: %s", token_response.text)
            raise HTTPException(status_code=502, detail="No fue posible tokenizar la tarjeta")

        card_token = token_response.json().get("id")
        if not card_token:
            raise HTTPException(status_code=502, detail="No fue posible tokenizar la tarjeta")

        first_digit = payload.numero_tarjeta[0]
        if first_digit == "4":
            payment_method_id = "visa"
        elif first_digit == "5":
            payment_method_id = "master"
        elif first_digit == "3":
            payment_method_id = "amex"
        else:
            payment_method_id = "visa"

        external_reference = _generate_external_reference(payload.id_usuario)
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        payer_email = "test_buyer_123456@testuser.com" if is_test else payload.email
        payment_payload = {
            "token": card_token,
            "transaction_amount": int(float(payload.monto)),
            "description": payload.descripcion,
            "installments": 1,
            "payment_method_id": payment_method_id,
            "external_reference": external_reference,
            "payer": {"email": payer_email, "identification": {"type": "RUT", "number": "12345678-5"}},
        }
        logger.info("[pagos] Payment payload=%s", payment_payload)
        payment_response = sdk.payment().create(payment_payload)
        payment_data = payment_response.get("response", {})
        if payment_response.get("status") not in (200, 201):
            logger.error("[pagos] Error MP status=%s body=%s", payment_response.get("status"), payment_data)
            raise HTTPException(status_code=502, detail=payment_data.get("message", "Error procesando pago"))

        mp_payment_id = payment_data.get("id")
        estado = _map_mp_status(payment_data.get("status"))
        id_operacion = _registrar_operacion(payload, external_reference, mp_payment_id, estado)

        logger.info("[pagos] Pago directo creado id_operacion=%s mp_payment_id=%s estado=%s", id_operacion, mp_payment_id, estado)
        return PagoDirectoResponse(
            success=True,
            message="Pago procesado correctamente",
            data={"id_pago": id_operacion, "estado": estado, "mp_payment_id": mp_payment_id, "external_reference": external_reference},
        )
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("[pagos] Error inesperado en pago directo")
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/con-token", response_model=PagoDirectoResponse, status_code=status.HTTP_201_CREATED)
def pago_con_token(payload: PagoConTokenRequest):
    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="MP_ACCESS_TOKEN no configurado")

    logger.info("[pagos] Pago con token id_usuario=%s monto=%s metodo=%s", payload.id_usuario, payload.transaction_amount, payload.payment_method_id)

    try:
        is_test = MP_ACCESS_TOKEN.startswith("TEST-")
        payer_email = "test_buyer_123456@testuser.com" if is_test else payload.email

        external_reference = _generate_external_reference(payload.id_usuario)
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        payment_payload = {
            "token": payload.token,
            "transaction_amount": int(float(payload.transaction_amount)),
            "description": payload.descripcion,
            "installments": payload.installments,
            "payment_method_id": payload.payment_method_id,
            "external_reference": external_reference,
            "payer": {
                "email": payer_email,
                "identification": {"type": "RUT", "number": "12345678-5"},
            },
        }
        if payload.issuer_id:
            payment_payload["issuer_id"] = payload.issuer_id

        logger.info("[pagos] Payment payload con-token=%s", payment_payload)
        payment_response = sdk.payment().create(payment_payload)
        payment_data = payment_response.get("response", {})

        if payment_response.get("status") not in (200, 201):
            logger.error("[pagos] Error MP con-token status=%s body=%s", payment_response.get("status"), payment_data)
            raise HTTPException(status_code=502, detail=payment_data.get("message", "Error procesando pago"))

        mp_payment_id = payment_data.get("id")
        estado = _map_mp_status(payment_data.get("status", ""))

        fake_req = PagoDirectoRequest(
            id_usuario=payload.id_usuario,
            numero_tarjeta="4111111111111111",
            mes_vencimiento=12,
            anio_vencimiento=2030,
            cvv="123",
            nombre_titular="BRICK",
            email=payload.email,
            descripcion=payload.descripcion,
            monto=payload.transaction_amount,
        )
        id_operacion = _registrar_operacion(fake_req, external_reference, mp_payment_id, estado)

        logger.info("[pagos] Pago con-token id_operacion=%s mp_payment_id=%s estado=%s", id_operacion, mp_payment_id, estado)
        return PagoDirectoResponse(
            success=True,
            message="Pago procesado correctamente",
            data={"id_pago": id_operacion, "estado": estado, "mp_payment_id": mp_payment_id, "external_reference": external_reference},
        )
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("[pagos] Error inesperado en pago con-token")
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/webhook", response_model=WebhookAckResponse)
async def recibir_webhook(
    request: Request,
    type: str | None = Query(default=None),
    data_id: str | None = Query(default=None, alias="data.id"),
):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    event_type = type or payload.get("type")
    event_data_id = data_id or payload.get("data", {}).get("id")

    if event_type != "payment" or not event_data_id:
        return WebhookAckResponse(success=True, message="Evento ignorado")

    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="MP_ACCESS_TOKEN no configurado")

    sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
    payment_resp = sdk.payment().get(event_data_id)
    payment = payment_resp.get("response", {})
    external_reference = payment.get("external_reference")
    nuevo_estado = _map_mp_status(payment.get("status", ""))

    if external_reference:
        operacion_id, operacion = _buscar_operacion_por_external_reference(external_reference)
        if operacion:
            _actualizar_operacion(operacion_id, nuevo_estado)
            with OPERACIONES_LOCK:
                if nuevo_estado == "PAGADO":
                    operacion["mp_payment_id"] = payment.get("id")
            logger.info("[pagos] Webhook procesado external_ref=%s nuevo_estado=%s", external_reference, nuevo_estado)

    return WebhookAckResponse(success=True, message="Webhook procesado")
