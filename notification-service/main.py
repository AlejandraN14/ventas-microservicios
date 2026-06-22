import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client as TwilioClient

app = FastAPI(title="Notification Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuración SMTP ───────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL", SMTP_USER)

# ── Configuración Twilio ─────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


class ItemCompra(BaseModel):
    nombre: str
    cantidad: int
    subtotal: float


class NotificacionCompra(BaseModel):
    email_destino: str
    nombre_cliente: str
    numero_operacion: str
    monto_total: float
    metodo_pago: str
    items: list[ItemCompra]
    whatsapp_destino: Optional[str] = None


def _enviar_smtp(destinatario: str, asunto: str, html: str, texto: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = SMTP_SENDER_EMAIL
    msg["To"] = destinatario
    msg.attach(MIMEText(texto, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.ehlo()
        servidor.starttls()
        servidor.login(SMTP_USER, SMTP_PASSWORD)
        servidor.sendmail(SMTP_SENDER_EMAIL, destinatario, msg.as_string())


def _construir_email(data: NotificacionCompra) -> tuple[str, str]:
    items_html = "".join(
        f"<tr><td style='padding:6px 12px'>{item.nombre}</td>"
        f"<td style='padding:6px 12px;text-align:center'>{item.cantidad}</td>"
        f"<td style='padding:6px 12px;text-align:right'>${item.subtotal:,.0f}</td></tr>"
        for item in data.items
    )

    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;background:#0F172A;color:#E2E8F0;border-radius:12px;overflow:hidden">
      <div style="background:linear-gradient(135deg,#3B82F6,#8B5CF6);padding:32px;text-align:center">
        <div style="font-size:48px">✅</div>
        <h1 style="color:#fff;margin:12px 0 4px;font-size:24px">¡Pago Exitoso!</h1>
        <p style="color:rgba(255,255,255,0.8);margin:0">Tu compra ha sido procesada correctamente</p>
      </div>
      <div style="padding:32px">
        <p style="margin:0 0 24px">Hola <strong>{data.nombre_cliente}</strong>, gracias por tu compra en <strong>TiendaOnline</strong>.</p>

        <div style="background:#1E293B;border-radius:8px;padding:20px;margin-bottom:24px">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="color:#94A3B8">N° Operación</span>
            <strong>#{data.numero_operacion}</strong>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="color:#94A3B8">Método de pago</span>
            <strong>{data.metodo_pago.capitalize()}</strong>
          </div>
          <div style="border-top:1px solid #334155;margin-top:12px;padding-top:12px;display:flex;justify-content:space-between">
            <span style="color:#94A3B8">Total pagado</span>
            <strong style="color:#3B82F6;font-size:18px">${data.monto_total:,.0f}</strong>
          </div>
        </div>

        <h3 style="margin:0 0 12px;color:#E2E8F0">Productos comprados</h3>
        <table style="width:100%;border-collapse:collapse;background:#1E293B;border-radius:8px;overflow:hidden">
          <thead>
            <tr style="background:#334155">
              <th style="padding:10px 12px;text-align:left;color:#94A3B8;font-weight:500">Producto</th>
              <th style="padding:10px 12px;text-align:center;color:#94A3B8;font-weight:500">Cant.</th>
              <th style="padding:10px 12px;text-align:right;color:#94A3B8;font-weight:500">Subtotal</th>
            </tr>
          </thead>
          <tbody>{items_html}</tbody>
        </table>

        <p style="margin-top:32px;color:#64748B;font-size:13px;text-align:center">
          Este es un correo automático generado por TiendaOnline · No responder
        </p>
      </div>
    </div>
    """

    items_texto = "\n".join(
        f"  - {item.nombre} x{item.cantidad}: ${item.subtotal:,.0f}"
        for item in data.items
    )
    texto = (
        f"¡Pago Exitoso!\n\n"
        f"Hola {data.nombre_cliente}, tu compra fue procesada correctamente.\n\n"
        f"N° Operación: #{data.numero_operacion}\n"
        f"Método de pago: {data.metodo_pago}\n"
        f"Total: ${data.monto_total:,.0f}\n\n"
        f"Productos:\n{items_texto}"
    )
    return html, texto


def _construir_whatsapp(data: NotificacionCompra) -> str:
    items_texto = "\n".join(
        f"  • {item.nombre} ×{item.cantidad} → ${item.subtotal:,.0f}"
        for item in data.items
    )
    return (
        f"✅ *¡Pago Exitoso!* - TiendaOnline\n\n"
        f"Hola *{data.nombre_cliente}*, tu compra fue procesada.\n\n"
        f"📋 *N° Operación:* #{data.numero_operacion}\n"
        f"💳 *Método:* {data.metodo_pago.capitalize()}\n\n"
        f"🛒 *Productos:*\n{items_texto}\n\n"
        f"💰 *Total pagado:* ${data.monto_total:,.0f}\n\n"
        f"¡Gracias por comprar con nosotros! 🎉"
    )


@app.post("/notificar-compra")
def notificar_compra(data: NotificacionCompra):
    resultados = {"email": None, "whatsapp": None}
    errores = []

    # ── Enviar email por SMTP ────────────────────────────────────
    if not SMTP_USER or not SMTP_PASSWORD:
        errores.append("Credenciales SMTP no configuradas")
    else:
        try:
            html_body, texto_body = _construir_email(data)
            _enviar_smtp(
                destinatario=data.email_destino,
                asunto=f"✅ Comprobante de pago #{data.numero_operacion} - TiendaOnline",
                html=html_body,
                texto=texto_body,
            )
            resultados["email"] = "enviado"
        except Exception as e:
            errores.append(f"SMTP error: {str(e)}")
            resultados["email"] = "error"

    # ── Enviar WhatsApp por Twilio ───────────────────────────────
    if data.whatsapp_destino:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            errores.append("Credenciales Twilio no configuradas")
        else:
            try:
                cliente_twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                destino = data.whatsapp_destino
                if not destino.startswith("whatsapp:"):
                    destino = f"whatsapp:{destino}"
                mensaje = _construir_whatsapp(data)
                cliente_twilio.messages.create(
                    from_=TWILIO_WHATSAPP_FROM,
                    to=destino,
                    body=mensaje,
                )
                resultados["whatsapp"] = "enviado"
            except Exception as e:
                errores.append(f"Twilio error: {str(e)}")
                resultados["whatsapp"] = "error"

    return {
        "ok": len(errores) == 0,
        "resultados": resultados,
        "errores": errores,
    }


class NotificacionArchivo(BaseModel):
    whatsapp_destino: str
    nombre_archivo: str
    fecha_carga: str
    espacio_usado_mb: float
    espacio_disponible_mb: float


@app.post("/notificar-archivo")
def notificar_archivo(data: NotificacionArchivo):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise HTTPException(status_code=500, detail="Credenciales Twilio no configuradas")
    try:
        destino = data.whatsapp_destino if data.whatsapp_destino.startswith("whatsapp:") else f"whatsapp:{data.whatsapp_destino}"
        mensaje = (
            f"📁 *Archivo subido exitosamente*\n\n"
            f"📄 *Archivo:* {data.nombre_archivo}\n"
            f"📅 *Fecha:* {data.fecha_carga[:19].replace('T', ' ')}\n"
            f"💾 *Espacio usado:* {data.espacio_usado_mb} MB\n"
            f"✅ *Espacio disponible:* {data.espacio_disponible_mb} MB"
        )
        cliente = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        cliente.messages.create(from_=TWILIO_WHATSAPP_FROM, to=destino, body=mensaje)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CodigoVerificacionRequest(BaseModel):
    email: str
    nombre: str
    codigo: str


@app.post("/enviar-codigo-verificacion")
def enviar_codigo_verificacion(data: CodigoVerificacionRequest):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise HTTPException(status_code=500, detail="Credenciales SMTP no configuradas")
    try:
        html = f"""
        <div style="font-family:Inter,Arial,sans-serif;max-width:500px;margin:0 auto;background:#0F172A;color:#E2E8F0;border-radius:12px;overflow:hidden">
          <div style="background:linear-gradient(135deg,#3B82F6,#8B5CF6);padding:32px;text-align:center">
            <div style="font-size:48px">✉️</div>
            <h1 style="color:#fff;margin:12px 0 4px;font-size:22px">Verifica tu cuenta</h1>
            <p style="color:rgba(255,255,255,0.8);margin:0">TiendaOnline</p>
          </div>
          <div style="padding:32px;text-align:center">
            <p>Hola <strong>{data.nombre}</strong>, usa este código para activar tu cuenta:</p>
            <div style="background:#1E293B;border-radius:12px;padding:24px;margin:24px 0;letter-spacing:8px;font-size:36px;font-weight:bold;color:#3B82F6">{data.codigo}</div>
            <p style="color:#64748B;font-size:13px">Este código es de un solo uso. Si no solicitaste esto, ignora este mensaje.</p>
          </div>
        </div>
        """
        _enviar_smtp(
            destinatario=data.email,
            asunto="🔐 Código de verificación - TiendaOnline",
            html=html,
            texto=f"Tu código de verificación es: {data.codigo}",
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "notification-service"}