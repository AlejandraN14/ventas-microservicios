from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

origins = [
    "http://localhost:4200",
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
        "numero_tarjeta": "4111111111111111",
        "mes_vencimiento": 12,
        "anio_vencimiento": 2030,
        "cvv": "123",
        "nombre_titular": "ALEJANDRA",
        "email": "test@test.com",
        "descripcion": "Compra tienda online",
        "monto": data["monto"]
    }

    response = requests.post(
        "http://127.0.0.1:8002/pagos/directo/procesar",

        json=payload
    )

    return response.json()