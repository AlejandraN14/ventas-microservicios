from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Numeric
from sqlalchemy.sql import func
from app.database import Base

class Pago(Base):
    __tablename__ = "pago"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False, index=True)
    id_suscripcion = Column(Integer)
    id_metodo_pago = Column(Integer, nullable=False)
    fecha_pago = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    periodo_anio = Column(Integer, nullable=False)
    periodo_mes = Column(Integer, nullable=False)
    monto_total = Column(Numeric(12, 2), nullable=False)
    estado_pago = Column(String(20), nullable=False, default='PENDIENTE')
    codigo_transaccion = Column(String(100))
    observacion = Column(Text)
