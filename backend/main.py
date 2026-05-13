from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/productos")
def obtener_productos():
    return [
        {
            "id": 1,
            "nombre": "Notebook Gamer",
            "precio": 850000
        },
        {
            "id": 2,
            "nombre": "Mouse RGB",
            "precio": 25000
        }
    ]

@app.post("/procesar-pagos")
def procesar_pagos(data: dict):
    payload = { 
    "id_usuario": 1,
    "numero_tarjeta": data["numero_tarjeta"],
    "mes_vencimiento": data["mes_vencimiento"],
    "anio_vencimiento": data["anio_vencimiento"],
    "cvv": data["cvv"],
    "nombre_titular": data["nombre_titular"],
    "email": data["email"],
    "descripcion": f"Compra tienda online - Pago con tarjeta de {data.get('metodo_pago', 'debito')}",
    "monto": data["monto"]
}

    try:
        response = requests.post(
            "http://app-pagos:8002/pagos/directo/procesar",
            json=payload,
            timeout=10
        )

        return response.json()

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=500,
            detail="No se pudo conectar con el microservicio app-pagos. Revisa que esté corriendo en el puerto 8002."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando el pago: {str(e)}"
        )