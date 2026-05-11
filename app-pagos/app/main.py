import logging
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.routers import pagos_router
from app.database import get_db

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Microservicio de Pagos",
    description="API especializada en gestión de pagos y transacciones",
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
def health_check(db: Session = Depends(get_db)):
    """Verifica que el servicio esté saludable"""
    try:
        # Verificar conexión a base de datos
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"[health] Error en conexión a base de datos: {e}")
        db_status = f"error: {str(e)}"
    
    # Verificar configuración de Mercado Pago
    mp_token = os.getenv("MP_ACCESS_TOKEN", "")
    mp_status = "ok" if mp_token else "missing MP_ACCESS_TOKEN"
    
    return {
        "status": "healthy" if db_status == "ok" and mp_status == "ok" else "degraded",
        "service": "app-pagos",
        "database": db_status,
        "mercadopago_token": mp_status,
    }

app.include_router(pagos_router)
