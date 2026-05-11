from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base

class MpCustomer(Base):
    __tablename__ = "mp_customer"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False, unique=True, index=True)
    mp_customer_id = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
