from typing import Optional
from sqlalchemy.orm import Session
from app.models.mp_customer import MpCustomer


def get_customer_by_usuario(db: Session, id_usuario: int) -> Optional[MpCustomer]:
    return db.query(MpCustomer).filter(MpCustomer.id_usuario == id_usuario).first()


def get_customer_by_mp_id(db: Session, mp_customer_id: str) -> Optional[MpCustomer]:
    return db.query(MpCustomer).filter(MpCustomer.mp_customer_id == mp_customer_id).first()


def create_customer(db: Session, id_usuario: int, mp_customer_id: str) -> MpCustomer:
    db_customer = MpCustomer(
        id_usuario=id_usuario,
        mp_customer_id=mp_customer_id,
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def delete_customer(db: Session, id_usuario: int) -> bool:
    db_customer = get_customer_by_usuario(db, id_usuario)
    if db_customer:
        db.delete(db_customer)
        db.commit()
        return True
    return False
