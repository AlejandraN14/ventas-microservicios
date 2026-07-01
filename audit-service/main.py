import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text
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
    ip_origen = Column(String(45), nullable=True)


app = FastAPI(title="Audit Service")

Base.metadata.create_all(bind=engine)

with engine.connect() as _conn:
    _conn.execute(text("ALTER TABLE auditoria ADD COLUMN IF NOT EXISTS ip_origen VARCHAR(45)"))
    _conn.commit()

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
    ip_origen: Optional[str] = None


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
            ip_origen=ev.ip_origen,
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
                "ip_origen": e.ip_origen,
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
  <title>Dashboard TiendaOnline</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:        #0F172A;
      --bg-2:      #111827;
      --bg-card:   #1E293B;
      --bg-card-2: #162032;
      --blue:      #3B82F6;
      --blue-dark: #2563EB;
      --violet:    #8B5CF6;
      --success:   #22C55E;
      --text:      #F8FAFC;
      --text-2:    #94A3B8;
      --text-3:    #64748B;
      --border:    rgba(255,255,255,0.08);
      --border-2:  rgba(255,255,255,0.14);
      --r-xl: 24px; --r-lg: 16px; --r-md: 12px;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      background: var(--bg); color: var(--text);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      -webkit-font-smoothing: antialiased; min-height: 100vh;
    }

    /* NAVBAR */
    nav {
      background: rgba(15,23,42,0.85);
      backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      border-bottom: 1px solid var(--border);
      padding: 0.85rem 0; position: sticky; top: 0; z-index: 100;
    }
    .nav-inner {
      max-width: 1200px; margin: 0 auto; padding: 0 1.25rem;
      display: flex; align-items: center; justify-content: space-between;
    }
    .nav-brand { display: flex; align-items: center; gap: 0.6rem; text-decoration: none; color: var(--text); font-weight: 700; font-size: 1.05rem; letter-spacing: -0.3px; }
    .brand-icon {
      width: 34px; height: 34px; border-radius: 10px;
      background: linear-gradient(135deg, var(--blue) 0%, var(--violet) 100%);
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; font-size: 0.9rem; color: #fff; flex-shrink: 0;
    }
    .nav-badge {
      background: rgba(59,130,246,0.12); color: #93C5FD;
      border: 1px solid rgba(59,130,246,0.25); border-radius: 999px;
      padding: 0.28rem 0.75rem; font-size: 0.72rem; font-weight: 600;
      display: flex; align-items: center; gap: 0.4rem;
    }
    .nav-badge-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); box-shadow: 0 0 5px var(--success); }

    /* CONTAINER */
    .container { max-width: 1200px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

    /* PAGE HEADING */
    .page-heading { margin-bottom: 1.75rem; }
    .page-heading h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px; color: var(--text); margin-bottom: 0.25rem; }
    .page-heading p { color: var(--text-2); font-size: 0.88rem; }

    /* FILTERS CARD */
    .filters-card {
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: var(--r-lg); padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;
      display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end;
    }
    .filters-card label { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.72rem; font-weight: 700; color: #CBD5E1; text-transform: uppercase; letter-spacing: 0.07em; }
    .filters-card select, .filters-card input {
      background: rgba(10,18,36,0.7); border: 1px solid var(--border-2); color: var(--text);
      border-radius: var(--r-md); padding: 0.55rem 0.85rem; font-size: 0.88rem;
      font-family: inherit; min-width: 140px; outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .filters-card select:focus, .filters-card input:focus {
      border-color: var(--blue); box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
    }
    .filters-card select option { background: #1E293B; }
    .filters-card input::placeholder { color: var(--text-3); }
    .btn-filter {
      background: var(--blue); color: #fff; border: none; border-radius: var(--r-md);
      padding: 0.58rem 1.25rem; font-size: 0.86rem; font-weight: 700;
      cursor: pointer; font-family: inherit; transition: background 0.15s, transform 0.12s;
      box-shadow: 0 4px 14px rgba(59,130,246,0.3);
    }
    .btn-filter:hover { background: var(--blue-dark); transform: translateY(-1px); }
    .btn-reset {
      background: transparent; color: var(--text-2); border: 1px solid var(--border-2);
      border-radius: var(--r-md); padding: 0.58rem 1.1rem; font-size: 0.86rem;
      font-weight: 600; cursor: pointer; font-family: inherit; transition: color 0.15s, border-color 0.15s;
    }
    .btn-reset:hover { color: var(--text); border-color: rgba(255,255,255,0.28); }

    /* STATS */
    .stats { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .stat-card {
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: var(--r-lg); padding: 1.1rem 1.5rem; flex: 1; min-width: 140px; text-align: center;
    }
    .stat-num { font-size: 2rem; font-weight: 900; color: var(--blue); letter-spacing: -1px; line-height: 1; }
    .stat-lbl { font-size: 0.75rem; color: var(--text-3); margin-top: 0.35rem; font-weight: 500; }

    /* TABLE */
    .table-wrap {
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: var(--r-lg); overflow: hidden;
    }
    table { width: 100%; border-collapse: collapse; }
    thead { background: linear-gradient(90deg, rgba(59,130,246,0.12) 0%, rgba(139,92,246,0.08) 100%); border-bottom: 1px solid var(--border-2); }
    th { padding: 0.75rem 1rem; text-align: left; font-size: 0.7rem; font-weight: 700; color: var(--text-2); text-transform: uppercase; letter-spacing: 0.08em; }
    td { padding: 0.75rem 1rem; font-size: 0.86rem; border-bottom: 1px solid var(--border); color: var(--text); }
    tbody tr:last-child td { border-bottom: none; }
    tbody tr:hover td { background: rgba(59,130,246,0.04); }

    /* BADGES */
    .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.74rem; font-weight: 700; }
    .badge-backend       { background: rgba(59,130,246,0.15);  color: #93C5FD; border: 1px solid rgba(59,130,246,0.25); }
    .badge-app-pagos     { background: rgba(34,197,94,0.12);   color: #4ADE80; border: 1px solid rgba(34,197,94,0.22); }
    .badge-file-service  { background: rgba(251,191,36,0.12);  color: #FCD34D; border: 1px solid rgba(251,191,36,0.22); }
    .badge-audit-service { background: rgba(139,92,246,0.12);  color: #C4B5FD; border: 1px solid rgba(139,92,246,0.22); }

    .detalle { max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-3); font-size: 0.8rem; font-family: monospace; }
    #status { text-align: center; padding: 2rem; color: var(--text-3); font-size: 0.9rem; }
  </style>
</head>
<body>
  <nav>
    <div class="nav-inner">
      <a class="nav-brand" href="#">
        <div class="brand-icon">T</div>
        <span>TiendaOnline</span>
      </a>
      <div class="nav-badge">
        <span class="nav-badge-dot"></span>
        Dashboard de Auditoría
      </div>
    </div>
  </nav>

  <div class="container">
    <div class="page-heading">
      <h1>Dashboard TiendaOnline</h1>
      <p>Registro de eventos del sistema en tiempo real — se actualiza cada 30 segundos</p>
    </div>

    <div class="filters-card">
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
          <option value="cierre_sesion">cierre_sesion</option>
          <option value="registro_usuario">registro_usuario</option>
          <option value="validacion_cuenta">validacion_cuenta</option>
          <option value="compra">compra</option>
          <option value="pago_exitoso">pago_exitoso</option>
          <option value="pago_fallido">pago_fallido</option>
          <option value="subida_archivo">subida_archivo</option>
          <option value="eliminacion_archivo">eliminacion_archivo</option>
          <option value="crear_producto">crear_producto</option>
          <option value="error_sistema">error_sistema</option>
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
      <button class="btn-filter" onclick="cargar()">Filtrar</button>
      <button class="btn-reset" onclick="resetFiltros()">Limpiar</button>
    </div>

    <div class="stats">
      <div class="stat-card"><div class="stat-num" id="s-total">—</div><div class="stat-lbl">Eventos mostrados</div></div>
      <div class="stat-card"><div class="stat-num" id="s-logins">—</div><div class="stat-lbl">Logins</div></div>
      <div class="stat-card"><div class="stat-num" id="s-compras">—</div><div class="stat-lbl">Compras</div></div>
      <div class="stat-card"><div class="stat-num" id="s-archivos">—</div><div class="stat-lbl">Archivos subidos</div></div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Servicio</th>
            <th>Tipo evento</th>
            <th>Usuario</th>
            <th>IP Origen</th>
            <th>Detalle</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
      <div id="status">Cargando eventos...</div>
    </div>
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
              <td style="color:var(--text-3);font-size:0.8rem">${e.ip_origen ?? '—'}</td>
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
