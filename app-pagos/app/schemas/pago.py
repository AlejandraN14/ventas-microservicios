from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class PagoCreate(BaseModel):
    id_usuario: int
    id_suscripcion: Optional[int] = None
    id_metodo_pago: int
    periodo_anio: int
    periodo_mes: int
    monto_total: Decimal
    estado_pago: str = "PENDIENTE"
    codigo_transaccion: Optional[str] = None
    observacion: Optional[str] = None

    @field_validator("periodo_mes")
    @classmethod
    def validate_mes(cls, v):
        if not 1 <= v <= 12:
            raise ValueError("El mes debe estar entre 1 y 12")
        return v

    @field_validator("periodo_anio")
    @classmethod
    def validate_anio(cls, v):
        if v < 2020:
            raise ValueError("El año debe ser mayor o igual a 2020")
        return v

    @field_validator("monto_total")
    @classmethod
    def validate_monto(cls, v):
        if v < 0:
            raise ValueError("El monto debe ser mayor o igual a 0")
        return v

    @field_validator("estado_pago")
    @classmethod
    def validate_estado(cls, v):
        estados_validos = ["PENDIENTE", "PAGADO", "RECHAZADO", "ANULADO", "CANCELADO", "EXPIRADO"]
        if v not in estados_validos:
            raise ValueError(f'El estado debe ser uno de: {", ".join(estados_validos)}')
        return v


class PagoCreateCheckoutRequest(BaseModel):
    id_usuario: int
    descripcion: str
    monto: Decimal
    email_pagador: EmailStr = "usuario@email.cl"

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, v):
        value = v.strip()
        if len(value) < 3:
            raise ValueError("La descripción debe tener al menos 3 caracteres")
        return value

    @field_validator("monto")
    @classmethod
    def validate_monto(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v


class PagoCreateCheckoutResponse(BaseModel):
    success: bool
    message: str
    data: dict


class PagoEstadoResponse(BaseModel):
    id_pago: int
    estado: str


class PagoCancelarResponse(BaseModel):
    success: bool
    message: str
    data: PagoEstadoResponse | None = None


class WebhookAckResponse(BaseModel):
    success: bool
    message: str


class PagoUpdate(BaseModel):
    id_suscripcion: Optional[int] = None
    id_metodo_pago: Optional[int] = None
    periodo_anio: Optional[int] = None
    periodo_mes: Optional[int] = None
    monto_total: Optional[Decimal] = None
    estado_pago: Optional[str] = None
    codigo_transaccion: Optional[str] = None
    observacion: Optional[str] = None


class PagoEstadoUpdate(BaseModel):
    estado_pago: str

    @field_validator("estado_pago")
    @classmethod
    def validate_estado(cls, v):
        estados_validos = ["PENDIENTE", "PAGADO", "RECHAZADO", "ANULADO", "CANCELADO", "EXPIRADO"]
        if v not in estados_validos:
            raise ValueError(f'El estado debe ser uno de: {", ".join(estados_validos)}')
        return v


class PagoDirectoRequest(BaseModel):
    """Pago directo con tarjeta sin guardarla"""
    id_usuario: int
    numero_tarjeta: str
    mes_vencimiento: int
    anio_vencimiento: int
    cvv: str
    nombre_titular: str
    email: EmailStr
    descripcion: str
    monto: Decimal

    @field_validator("numero_tarjeta")
    @classmethod
    def validate_numero(cls, v):
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.isdigit() or len(cleaned) < 13:
            raise ValueError("Número de tarjeta inválido")
        return cleaned

    @field_validator("mes_vencimiento")
    @classmethod
    def validate_mes(cls, v):
        if not 1 <= v <= 12:
            raise ValueError("Mes de vencimiento inválido (1-12)")
        return v

    @field_validator("anio_vencimiento")
    @classmethod
    def validate_anio(cls, v):
        from datetime import datetime
        if v < datetime.now().year:
            raise ValueError("Año de vencimiento no válido")
        return v

    @field_validator("cvv")
    @classmethod
    def validate_cvv(cls, v):
        if not v.isdigit() or len(v) < 3 or len(v) > 4:
            raise ValueError("CVV inválido (3-4 dígitos)")
        return v

    @field_validator("nombre_titular")
    @classmethod
    def validate_nombre(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Nombre del titular muy corto")
        return v.upper()

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, v):
        value = v.strip()
        if len(value) < 3:
            raise ValueError("Descripción muy corta")
        return value

    @field_validator("monto")
    @classmethod
    def validate_monto(cls, v):
        if v <= 0:
            raise ValueError("Monto debe ser mayor a 0")
        return v


class PagoDirectoResponse(BaseModel):
    """Respuesta de pago directo"""
    success: bool
    message: str
    data: Optional[dict] = None


class PagoResponse(BaseModel):
    id_pago: int
    id_usuario: int
    id_suscripcion: Optional[int] = None
    id_metodo_pago: int
    fecha_pago: datetime
    periodo_anio: int
    periodo_mes: int
    monto_total: Decimal
    estado_pago: str
    codigo_transaccion: Optional[str] = None
    observacion: Optional[str] = None

    class Config:
        from_attributes = True
