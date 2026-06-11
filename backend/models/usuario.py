from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    verificado = Column(Boolean, default=False, nullable=False)


class CodigoVerificacion(Base):
    __tablename__ = "codigos_verificacion"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    codigo = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
