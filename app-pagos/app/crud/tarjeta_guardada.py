from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.tarjeta_guardada import TarjetaGuardada


def get_tarjetas_by_usuario(db: Session, id_usuario: int) -> List[TarjetaGuardada]:
    return db.query(TarjetaGuardada).filter(TarjetaGuardada.id_usuario == id_usuario).order_by(TarjetaGuardada.is_default.desc(), TarjetaGuardada.created_at.desc()).all()


def get_tarjeta_by_id(db: Session, tarjeta_id: int) -> Optional[TarjetaGuardada]:
    return db.query(TarjetaGuardada).filter(TarjetaGuardada.id == tarjeta_id).first()


def get_tarjeta_by_mp_card_id(db: Session, mp_card_id: str) -> Optional[TarjetaGuardada]:
    return db.query(TarjetaGuardada).filter(TarjetaGuardada.mp_card_id == mp_card_id).first()


def get_default_tarjeta(db: Session, id_usuario: int) -> Optional[TarjetaGuardada]:
    return db.query(TarjetaGuardada).filter(
        TarjetaGuardada.id_usuario == id_usuario,
        TarjetaGuardada.is_default == True
    ).first()


def create_tarjeta(
    db: Session,
    id_usuario: int,
    mp_customer_id: str,
    mp_card_id: str,
    payment_method_id: str,
    brand: str,
    last_four_digits: str,
    expiration_month: int,
    expiration_year: int,
    holder_name: str,
    is_default: bool = False,
) -> TarjetaGuardada:
    if is_default:
        db.query(TarjetaGuardada).filter(TarjetaGuardada.id_usuario == id_usuario).update({"is_default": False})
        db.commit()

    db_tarjeta = TarjetaGuardada(
        id_usuario=id_usuario,
        mp_customer_id=mp_customer_id,
        mp_card_id=mp_card_id,
        payment_method_id=payment_method_id,
        brand=brand,
        last_four_digits=last_four_digits,
        expiration_month=expiration_month,
        expiration_year=expiration_year,
        holder_name=holder_name,
        is_default=is_default,
    )
    db.add(db_tarjeta)
    db.commit()
    db.refresh(db_tarjeta)
    return db_tarjeta


def set_default_tarjeta(db: Session, tarjeta_id: int, id_usuario: int) -> Optional[TarjetaGuardada]:
    db_tarjeta = get_tarjeta_by_id(db, tarjeta_id)
    if not db_tarjeta or db_tarjeta.id_usuario != id_usuario:
        return None

    db.query(TarjetaGuardada).filter(TarjetaGuardada.id_usuario == id_usuario).update({"is_default": False})
    db_tarjeta.is_default = True
    db.commit()
    db.refresh(db_tarjeta)
    return db_tarjeta


def delete_tarjeta(db: Session, tarjeta_id: int, id_usuario: int) -> bool:
    db_tarjeta = get_tarjeta_by_id(db, tarjeta_id)
    if db_tarjeta and db_tarjeta.id_usuario == id_usuario:
        db.delete(db_tarjeta)
        db.commit()
        return True
    return False
