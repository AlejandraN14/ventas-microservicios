from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.database import Base

class TarjetaGuardada(Base):
    __tablename__ = "tarjeta_guardada"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False, index=True)
    mp_customer_id = Column(String(100), nullable=False, index=True)
    mp_card_id = Column(String(100), nullable=False, unique=True, index=True)
    payment_method_id = Column(String(50), nullable=False)
    brand = Column(String(50))
    last_four_digits = Column(String(4), nullable=False)
    expiration_month = Column(Integer, nullable=False)
    expiration_year = Column(Integer, nullable=False)
    holder_name = Column(String(200), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
