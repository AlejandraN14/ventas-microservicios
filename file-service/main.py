import os
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="File Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "")
LIMITE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB por usuario


def _s3():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def _prefijo(usuario_id: int) -> str:
    return f"usuario_{usuario_id}/"


def _espacio_usado(usuario_id: int) -> int:
    s3 = _s3()
    prefijo = _prefijo(usuario_id)
    total = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefijo):
        for obj in page.get("Contents", []):
            total += obj["Size"]
    return total


@app.post("/archivos/{usuario_id}/subir")
async def subir_archivo(
    usuario_id: int,
    archivo: UploadFile = File(...),
    whatsapp: Optional[str] = Form(None),
):
    contenido = await archivo.read()
    tamano = len(contenido)

    usado = _espacio_usado(usuario_id)
    if usado + tamano > LIMITE_BYTES:
        raise HTTPException(status_code=400, detail="Has superado el límite de 2 GB")

    clave = f"{_prefijo(usuario_id)}{archivo.filename}"
    try:
        _s3().put_object(
            Bucket=S3_BUCKET,
            Key=clave,
            Body=contenido,
            ContentType=archivo.content_type or "application/octet-stream",
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

    nuevo_usado = usado + tamano
    disponible = LIMITE_BYTES - nuevo_usado

    if whatsapp and NOTIFICATION_SERVICE_URL:
        try:
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notificar-archivo",
                json={
                    "whatsapp_destino": whatsapp,
                    "nombre_archivo": archivo.filename,
                    "fecha_carga": datetime.utcnow().isoformat(),
                    "espacio_usado_mb": round(nuevo_usado / (1024 * 1024), 2),
                    "espacio_disponible_mb": round(disponible / (1024 * 1024), 2),
                },
                timeout=8,
            )
        except Exception:
            pass

    return {
        "ok": True,
        "archivo": archivo.filename,
        "tamano_bytes": tamano,
        "espacio_usado_mb": round(nuevo_usado / (1024 * 1024), 2),
        "espacio_disponible_mb": round(disponible / (1024 * 1024), 2),
    }


@app.get("/archivos/{usuario_id}")
def listar_archivos(usuario_id: int):
    s3 = _s3()
    prefijo = _prefijo(usuario_id)
    try:
        paginator = s3.get_paginator("list_objects_v2")
        archivos = []
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefijo):
            for obj in page.get("Contents", []):
                nombre = obj["Key"].replace(prefijo, "")
                if nombre:
                    archivos.append({
                        "nombre": nombre,
                        "tamano_bytes": obj["Size"],
                        "tamano_kb": round(obj["Size"] / 1024, 2),
                        "fecha_modificacion": obj["LastModified"].isoformat(),
                    })
        return archivos
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/archivos/{usuario_id}/espacio")
def consultar_espacio(usuario_id: int):
    usado = _espacio_usado(usuario_id)
    disponible = LIMITE_BYTES - usado
    return {
        "limite_mb": round(LIMITE_BYTES / (1024 * 1024), 2),
        "usado_mb": round(usado / (1024 * 1024), 2),
        "disponible_mb": round(disponible / (1024 * 1024), 2),
        "porcentaje_usado": round((usado / LIMITE_BYTES) * 100, 1),
    }


@app.delete("/archivos/{usuario_id}/{nombre_archivo}")
def eliminar_archivo(usuario_id: int, nombre_archivo: str):
    clave = f"{_prefijo(usuario_id)}{nombre_archivo}"
    try:
        _s3().delete_object(Bucket=S3_BUCKET, Key=clave)
        return {"ok": True, "eliminado": nombre_archivo}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "file-service"}
