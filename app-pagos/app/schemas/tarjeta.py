from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class TarjetaTokenRequest(BaseModel):
    token: str
    email: str
    
    @field_validator("token")
    @classmethod
    def validate_token(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("El token es requerido")
        return v.strip()


class TarjetaGuardarRequest(BaseModel):
    id_usuario: int
    token: str
    email: str
    
    @field_validator("token")
    @classmethod
    def validate_token(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("El token es requerido")
        return v.strip()


class TarjetaResponse(BaseModel):
    id: int
    id_usuario: int
    mp_customer_id: str
    mp_card_id: str
    payment_method_id: str
    brand: Optional[str] = None
    last_four_digits: str
    expiration_month: int
    expiration_year: int
    holder_name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TarjetaGuardarResponse(BaseModel):
    success: bool
    message: str
    data: Optional[TarjetaResponse] = None


class TarjetasListResponse(BaseModel):
    success: bool
    message: str
    data: list[TarjetaResponse]


class TarjetaSetDefaultRequest(BaseModel):
    is_default: bool


class TarjetaDeleteResponse(BaseModel):
    success: bool
    message: str


class PagoConTarjetaGuardadaRequest(BaseModel):
    id_usuario: int
    id_tarjeta: int
    descripcion: str
    monto: float
    
    @field_validator("monto")
    @classmethod
    def validate_monto(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v
    
    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, v):
        value = v.strip()
        if len(value) < 3:
            raise ValueError("La descripción debe tener al menos 3 caracteres")
        return value


class PagoConTarjetaGuardadaResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
