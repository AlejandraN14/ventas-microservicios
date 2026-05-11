#!/usr/bin/env python3
"""Script para inicializar la base de datos"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models.tarjeta_guardada import TarjetaGuardada
from app.models.mp_customer import MpCustomer
from app.models.pago import Pago

def init_db():
    """Crea todas las tablas en la base de datos"""
    print("🔧 Inicializando base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")
    print("\n📊 Tablas creadas:")
    print("  - mp_customer")
    print("  - tarjeta_guardada")
    print("  - pago")

if __name__ == "__main__":
    init_db()
