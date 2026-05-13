import logging
import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pagos_router

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Microservicio de Pagos",
    description="API especializada en procesamiento de pagos con tarjeta",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Verifica que el servicio esté saludable"""
    mp_token = os.getenv("MP_ACCESS_TOKEN", "")
    mp_public_key = os.getenv("MP_PUBLIC_KEY", "")
    mp_status = "ok" if mp_token and mp_public_key else "missing credentials"
    
    return {
        "status": "healthy" if mp_status == "ok" else "degraded",
        "service": "app-pagos",
        "mercadopago_status": mp_status,
    }

app.include_router(pagos_router)
