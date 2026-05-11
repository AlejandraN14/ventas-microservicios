import random
import string
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.pago import Pago
from app.schemas.pago import PagoCreate, PagoUpdate


def get_pagos(db: Session, skip: int = 0, limit: int = 100) -> List[Pago]:
    return db.query(Pago).offset(skip).limit(limit).all()


def get_pago(db: Session, pago_id: int) -> Optional[Pago]:
    return db.query(Pago).filter(Pago.id_pago == pago_id).first()


def get_pago_by_external_reference(db: Session, external_reference: str) -> Optional[Pago]:
    return db.query(Pago).filter(Pago.observacion == external_reference).first()


def get_pagos_by_usuario(db: Session, usuario_id: int) -> List[Pago]:
    return db.query(Pago).filter(Pago.id_usuario == usuario_id).all()


def get_pagos_by_periodo(db: Session, anio: int, mes: int) -> List[Pago]:
    return db.query(Pago).filter(Pago.periodo_anio == anio, Pago.periodo_mes == mes).all()


def get_pagos_by_suscripcion(db: Session, suscripcion_id: int) -> List[Pago]:
    return db.query(Pago).filter(Pago.id_suscripcion == suscripcion_id).all()


def get_pagos_by_estado(db: Session, estado: str) -> List[Pago]:
    return db.query(Pago).filter(Pago.estado_pago == estado).all()


def create_pago(db: Session, pago: PagoCreate) -> Pago:
    db_pago = Pago(**pago.model_dump())
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    return db_pago


def update_pago(db: Session, pago_id: int, pago: PagoUpdate) -> Optional[Pago]:
    db_pago = get_pago(db, pago_id)
    if db_pago:
        update_data = pago.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_pago, key, value)
        db.commit()
        db.refresh(db_pago)
    return db_pago


def update_estado_pago(db: Session, pago_id: int, estado: str) -> Optional[Pago]:
    db_pago = get_pago(db, pago_id)
    if db_pago:
        db_pago.estado_pago = estado
        db.commit()
        db.refresh(db_pago)
    return db_pago


def update_codigo_transaccion(db: Session, pago_id: int, codigo: str | None) -> Optional[Pago]:
    db_pago = get_pago(db, pago_id)
    if db_pago:
        db_pago.codigo_transaccion = codigo
        db.commit()
        db.refresh(db_pago)
    return db_pago


def anular_pago(db: Session, pago_id: int) -> Optional[Pago]:
    return update_estado_pago(db, pago_id, "ANULADO")


def delete_pago(db: Session, pago_id: int) -> bool:
    db_pago = get_pago(db, pago_id)
    if db_pago:
        db.delete(db_pago)
        db.commit()
        return True
    return False


def map_mp_status(mp_status: str) -> str:
    mapping = {
        "approved": "PAGADO",
        "authorized": "PENDIENTE",
        "in_process": "PENDIENTE",
        "pending": "PENDIENTE",
        "rejected": "RECHAZADO",
        "cancelled": "CANCELADO",
        "expired": "EXPIRADO",
        "refunded": "ANULADO",
        "charged_back": "ANULADO",
    }
    return mapping.get((mp_status or "").lower(), "PENDIENTE")


def generate_external_reference(id_usuario: int) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"PAGO_{id_usuario}_{suffix}"
