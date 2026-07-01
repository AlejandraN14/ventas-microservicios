import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ventasdb")
AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://54.204.22.116:8005")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class EventoAuditoria(Base):
    __tablename__ = "auditoria"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    servicio = Column(String(50), nullable=False)
    tipo_evento = Column(String(50), nullable=False)
    usuario_id = Column(Integer, nullable=True)
    detalle = Column(Text, nullable=True)


app = FastAPI(title="Audit Service")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EventoIn(BaseModel):
    servicio: str
    tipo_evento: str
    usuario_id: Optional[int] = None
    detalle: Optional[dict] = None


@app.post("/eventos")
def registrar_evento(ev: EventoIn):
    db = SessionLocal()
    try:
        evento = EventoAuditoria(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            servicio=ev.servicio,
            tipo_evento=ev.tipo_evento,
            usuario_id=ev.usuario_id,
            detalle=json.dumps(ev.detalle) if ev.detalle else None,
        )
        db.add(evento)
        db.commit()
        return {"ok": True, "id": evento.id}
    finally:
        db.close()


@app.get("/eventos")
def listar_eventos(
    servicio: Optional[str] = Query(None),
    tipo_evento: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
):
    db = SessionLocal()
    try:
        q = db.query(EventoAuditoria)
        if servicio:
            q = q.filter(EventoAuditoria.servicio == servicio)
        if tipo_evento:
            q = q.filter(EventoAuditoria.tipo_evento == tipo_evento)
        if usuario_id is not None:
            q = q.filter(EventoAuditoria.usuario_id == usuario_id)
        eventos = q.order_by(EventoAuditoria.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "servicio": e.servicio,
                "tipo_evento": e.tipo_evento,
                "usuario_id": e.usuario_id,
                "detalle": json.loads(e.detalle) if e.detalle else None,
            }
            for e in eventos
        ]
    finally:
        db.close()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard de Auditoría</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; background: #f0f2f5; color: #333; }
    header { background: #1a73e8; color: white; padding: 16px 24px; }
    header h1 { font-size: 1.4rem; }
    header p { font-size: 0.85rem; opacity: 0.85; margin-top: 2px; }
    .container { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
    .filters { background: white; border-radius: 8px; padding: 16px; margin-bottom: 20px;
               display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end;
               box-shadow: 0 1px 4px rgba(0,0,0,.1); }
    .filters label { display: flex; flex-direction: column; gap: 4px; font-size: 0.82rem; font-weight: 600; }
    .filters select, .filters input {
      padding: 7px 10px; border: 1px solid #ccc; border-radius: 5px;
      font-size: 0.9rem; min-width: 140px;
    }
    .filters button {
      padding: 8px 20px; background: #1a73e8; color: white; border: none;
      border-radius: 5px; cursor: pointer; font-size: 0.9rem; height: 36px;
    }
    .filters button:hover { background: #1558b0; }
    .filters button.reset { background: #666; }
    .filters button.reset:hover { background: #444; }
    .stats { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
    .stat-card { background: white; border-radius: 8px; padding: 14px 20px; flex: 1; min-width: 150px;
                 box-shadow: 0 1px 4px rgba(0,0,0,.1); text-align: center; }
    .stat-card .num { font-size: 2rem; font-weight: 700; color: #1a73e8; }
    .stat-card .lbl { font-size: 0.78rem; color: #888; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; background: white;
            border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
    thead { background: #1a73e8; color: white; }
    th, td { padding: 10px 14px; text-align: left; font-size: 0.87rem; }
    tbody tr:nth-child(even) { background: #f8f9fa; }
    tbody tr:hover { background: #e8f0fe; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 12px;
             font-size: 0.78rem; font-weight: 600; }
    .badge-backend { background: #d1e8ff; color: #0052cc; }
    .badge-app-pagos { background: #d4edda; color: #155724; }
    .badge-file-service { background: #fff3cd; color: #856404; }
    .badge-audit-service { background: #e2d9f3; color: #4a235a; }
    .detalle { max-width: 280px; font-size: 0.78rem; color: #555;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    #status { text-align: center; padding: 20px; color: #888; font-size: 0.9rem; }
  </style>
</head>
<body>
  <header>
    <h1>Dashboard de Auditoría — Ventas Microservicios</h1>
    <p>Registro de eventos del sistema en tiempo real</p>
  </header>
  <div class="container">
    <div class="filters">
      <label>Servicio
        <select id="f-servicio">
          <option value="">Todos</option>
          <option value="backend">backend</option>
          <option value="app-pagos">app-pagos</option>
          <option value="file-service">file-service</option>
        </select>
      </label>
      <label>Tipo de evento
        <select id="f-tipo">
          <option value="">Todos</option>
          <option value="login">login</option>
          <option value="logout">logout</option>
          <option value="compra">compra</option>
          <option value="pago_exitoso">pago_exitoso</option>
          <option value="pago_fallido">pago_fallido</option>
          <option value="subida_archivo">subida_archivo</option>
          <option value="eliminacion_archivo">eliminacion_archivo</option>
          <option value="crear_producto">crear_producto</option>
          <option value="eliminar_producto">eliminar_producto</option>
        </select>
      </label>
      <label>Usuario ID
        <input type="number" id="f-usuario" placeholder="Ej: 16" min="1">
      </label>
      <label>Límite
        <select id="f-limit">
          <option value="50">50</option>
          <option value="100" selected>100</option>
          <option value="200">200</option>
          <option value="500">500</option>
        </select>
      </label>
      <button onclick="cargar()">Filtrar</button>
      <button class="reset" onclick="resetFiltros()">Limpiar</button>
    </div>

    <div class="stats">
      <div class="stat-card"><div class="num" id="s-total">—</div><div class="lbl">Eventos mostrados</div></div>
      <div class="stat-card"><div class="num" id="s-logins">—</div><div class="lbl">Logins</div></div>
      <div class="stat-card"><div class="num" id="s-compras">—</div><div class="lbl">Compras</div></div>
      <div class="stat-card"><div class="num" id="s-archivos">—</div><div class="lbl">Archivos subidos</div></div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Servicio</th>
          <th>Tipo evento</th>
          <th>Usuario</th>
          <th>Detalle</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div id="status">Cargando eventos...</div>
  </div>

  <script>
    const API = window.location.origin;

    function badgeServicio(s) {
      const cls = { backend: 'badge-backend', 'app-pagos': 'badge-app-pagos',
                    'file-service': 'badge-file-service', 'audit-service': 'badge-audit-service' };
      return `<span class="badge ${cls[s] || ''}">${s}</span>`;
    }

    function formatTs(ts) {
      if (!ts) return '—';
      const d = new Date(ts + 'Z');
      return d.toLocaleString('es-CL', { timeZone: 'America/Santiago' });
    }

    function formatDetalle(d) {
      if (!d) return '—';
      return JSON.stringify(d);
    }

    async function cargar() {
      const servicio = document.getElementById('f-servicio').value;
      const tipo = document.getElementById('f-tipo').value;
      const usuario = document.getElementById('f-usuario').value;
      const limit = document.getElementById('f-limit').value;

      let url = `${API}/eventos?limit=${limit}`;
      if (servicio) url += `&servicio=${encodeURIComponent(servicio)}`;
      if (tipo) url += `&tipo_evento=${encodeURIComponent(tipo)}`;
      if (usuario) url += `&usuario_id=${encodeURIComponent(usuario)}`;

      document.getElementById('status').textContent = 'Cargando...';
      document.getElementById('tbody').innerHTML = '';

      try {
        const res = await fetch(url);
        const data = await res.json();

        const tbody = document.getElementById('tbody');
        if (data.length === 0) {
          document.getElementById('status').textContent = 'No hay eventos con esos filtros.';
        } else {
          document.getElementById('status').textContent = '';
          data.forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${formatTs(e.timestamp)}</td>
              <td>${badgeServicio(e.servicio)}</td>
              <td>${e.tipo_evento}</td>
              <td>${e.usuario_id ?? '—'}</td>
              <td class="detalle" title="${formatDetalle(e.detalle).replace(/"/g,'&quot;')}">${formatDetalle(e.detalle)}</td>
            `;
            tbody.appendChild(tr);
          });
        }

        document.getElementById('s-total').textContent = data.length;
        document.getElementById('s-logins').textContent = data.filter(e => e.tipo_evento === 'login').length;
        document.getElementById('s-compras').textContent = data.filter(e => e.tipo_evento === 'compra').length;
        document.getElementById('s-archivos').textContent = data.filter(e => e.tipo_evento === 'subida_archivo').length;
      } catch (err) {
        document.getElementById('status').textContent = 'Error al cargar eventos: ' + err.message;
      }
    }

    function resetFiltros() {
      document.getElementById('f-servicio').value = '';
      document.getElementById('f-tipo').value = '';
      document.getElementById('f-usuario').value = '';
      document.getElementById('f-limit').value = '100';
      cargar();
    }

    cargar();
    setInterval(cargar, 30000);
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "audit-service"}
