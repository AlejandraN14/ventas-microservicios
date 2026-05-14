from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from database import Base

class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    monto = Column(Float)
    metodo_pago = Column(String)
    estado = Column(String)
    mp_payment_id = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)