import hashlib
import os
import secrets

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

from database import engine, SessionLocal, Base
from models.carrito import CarritoItem
from models.producto import Producto
from models.usuario import Usuario
from models.venta import Venta

app = FastAPI()

Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://3.144.69.118",
]

PAGOS_SERVICE_URL = os.getenv("PAGOS_SERVICE_URL", "http://app-pagos:8002")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, password_hash = stored_hash.split(":", 1)
    except ValueError:
        return False
    candidate = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(candidate, password_hash)


def serializar_producto(producto: Producto) -> dict:
    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "descripcion": producto.descripcion,
    }


def seed_productos():
    db = SessionLocal()
    try:
        if db.query(Producto).count() == 0:
            db.add_all([
                Producto(nombre="Notebook Gamer", precio=850000, descripcion="Notebook para juegos y productividad"),
                Producto(nombre="Mouse RGB", precio=25000, descripcion="Mouse ergonomico con iluminacion RGB"),
                Producto(nombre="Teclado Mecanico", precio=55000, descripcion="Teclado compacto para escritorio"),
            ])
            db.commit()
    finally:
        db.close()


seed_productos()


@app.post("/usuarios/registro")
def registrar_usuario(data: dict):
    nombre = str(data.get("nombre", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if len(nombre) < 2:
        raise HTTPException(status_code=400, detail="El nombre debe tener al menos 2 caracteres")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Correo electronico invalido")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="La contrasena debe tener al menos 6 caracteres")

    db = SessionLocal()
    try:
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            raise HTTPException(status_code=409, detail="El correo ya esta registrado")

        usuario = Usuario(nombre=nombre, email=email, password_hash=hash_password(password))
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return {"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email}
    finally:
        db.close()


@app.post("/usuarios/login")
def iniciar_sesion(data: dict):
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if not usuario or not verify_password(password, usuario.password_hash):
            raise HTTPException(status_code=401, detail="Credenciales invalidas")

        return {"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email}
    finally:
        db.close()


@app.get("/productos")
def obtener_productos():
    db = SessionLocal()
    try:
        productos = db.query(Producto).order_by(Producto.id).all()
        return [serializar_producto(producto) for producto in productos]
    finally:
        db.close()


@app.post("/productos")
def crear_producto(data: dict):
    nombre = str(data.get("nombre", "")).strip()
    descripcion = str(data.get("descripcion", "")).strip()

    try:
        precio = float(data.get("precio", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="El precio debe ser numerico")

    if len(nombre) < 2:
        raise HTTPException(status_code=400, detail="El nombre debe tener al menos 2 caracteres")
    if precio <= 0:
        raise HTTPException(status_code=400, detail="El precio debe ser mayor a 0")

    db = SessionLocal()
    try:
        producto = Producto(nombre=nombre, precio=precio, descripcion=descripcion)
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return serializar_producto(producto)
    finally:
        db.close()


@app.get("/usuarios/{usuario_id}/carrito")
def obtener_carrito(usuario_id: int):
    db = SessionLocal()
    try:
        items = db.query(CarritoItem, Producto).join(Producto, Producto.id == CarritoItem.producto_id).filter(
            CarritoItem.usuario_id == usuario_id
        ).all()
        return [
            {
                "id": item.id,
                "producto": serializar_producto(producto),
                "cantidad": item.cantidad,
                "subtotal": producto.precio * item.cantidad,
            }
            for item, producto in items
        ]
    finally:
        db.close()


@app.post("/usuarios/{usuario_id}/carrito")
def agregar_producto_carrito(usuario_id: int, data: dict):
    producto_id = int(data.get("producto_id", 0))
    cantidad = int(data.get("cantidad", 1))
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")

    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        producto = db.query(Producto).filter(Producto.id == producto_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        item = db.query(CarritoItem).filter(
            CarritoItem.usuario_id == usuario_id,
            CarritoItem.producto_id == producto_id,
        ).first()
        if item:
            item.cantidad += cantidad
        else:
            item = CarritoItem(usuario_id=usuario_id, producto_id=producto_id, cantidad=cantidad)
            db.add(item)

        db.commit()
        return obtener_carrito(usuario_id)
    finally:
        db.close()


@app.delete("/usuarios/{usuario_id}/carrito/{item_id}")
def eliminar_item_carrito(usuario_id: int, item_id: int):
    db = SessionLocal()
    try:
        item = db.query(CarritoItem).filter(
            CarritoItem.id == item_id,
            CarritoItem.usuario_id == usuario_id,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item de carrito no encontrado")
        db.delete(item)
        db.commit()
        return obtener_carrito(usuario_id)
    finally:
        db.close()


@app.delete("/usuarios/{usuario_id}/carrito")
def vaciar_carrito(usuario_id: int):
    db = SessionLocal()
    try:
        db.query(CarritoItem).filter(CarritoItem.usuario_id == usuario_id).delete()
        db.commit()
        return {"message": "Carrito vaciado"}
    finally:
        db.close()

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
            f"{PAGOS_SERVICE_URL}/pagos/directo/procesar",
            json=payload,
            timeout=10
        )


        resultado = response.json()

        print("RESPUESTA APP-PAGOS:", resultado)

        db = SessionLocal()

        nueva_venta = Venta(
            monto=data["monto"],
            metodo_pago=data.get("metodo_pago", "desconocido"),
            estado=resultado.get("data", {}).get("estado", "desconocido"),
            mp_payment_id=str(resultado.get("data", {}).get("mp_payment_id"))
        )

        db.add(nueva_venta)
        db.commit()
        db.refresh(nueva_venta)

        usuario_id = data.get("usuario_id")
        if usuario_id:
            db.query(CarritoItem).filter(CarritoItem.usuario_id == usuario_id).delete()
            db.commit()

        return resultado

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
    

@app.get("/ventas")
def obtener_ventas():
    db = SessionLocal()
    ventas = db.query(Venta).all()
    db.close()
    return ventas    
