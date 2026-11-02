"""Tablero HTML autocontenido: sin build, sin CDN, se abre offline."""

from __future__ import annotations

import html
import json
from pathlib import Path

from .modelo import ahora

CSS = """
:root{--bg:#0b0f14;--panel:#121a23;--panel2:#182430;--linea:#22303e;--txt:#e8eef6;--tenue:#93a6ba;
--ok:#35d39a;--medio:#fbbf24;--mal:#f87171;--acento:#60a5fa}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 600px at 50% -10%,#14202c 0%,#0b0f14 60%);
color:var(--txt);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
line-height:1.5;padding:32px 20px 80px}
.ancho{max-width:1080px;margin:0 auto}
header{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:space-between;
padding-bottom:20px;border-bottom:1px solid var(--linea)}
h1{font-size:30px;margin:0;letter-spacing:-.03em}
h1 span{color:var(--acento)}
.sub{color:var(--tenue);font-size:14px;margin:6px 0 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}
.kpi{background:var(--panel);border:1px solid var(--linea);border-radius:14px;padding:14px 16px}
.kpi b{display:block;font-size:24px;letter-spacing:-.02em}
.kpi small{color:var(--tenue);font-size:12px;text-transform:uppercase;letter-spacing:.08em}
.barra{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 22px}
input,select{background:var(--panel2);border:1px solid var(--linea);color:var(--txt);
border-radius:10px;padding:9px 12px;font-size:14px;font-family:inherit}
input{flex:1;min-width:200px}
input:focus,select:focus{outline:2px solid var(--acento);outline-offset:1px}
.oferta{background:var(--panel);border:1px solid var(--linea);border-radius:16px;padding:18px 18px 14px;
margin:0 0 12px}
.oferta:hover{border-color:#2e4155}
.fila{display:flex;gap:12px;align-items:flex-start;justify-content:space-between}
.oferta h3{margin:0 0 2px;font-size:17px;letter-spacing:-.01em}
.empresa{color:var(--tenue);font-size:14px}
.meta{display:flex;gap:14px;flex-wrap:wrap;color:var(--tenue);font-size:13px;margin:8px 0}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;
border:1px solid var(--linea);color:var(--tenue);margin:2px 4px 2px 0}
.pts{min-width:56px;text-align:center;border-radius:12px;padding:6px 8px;font-weight:700;font-size:18px}
.pts.alto{background:rgba(53,211,154,.14);color:var(--ok);border:1px solid rgba(53,211,154,.35)}
.pts.medio{background:rgba(251,191,36,.12);color:var(--medio);border:1px solid rgba(251,191,36,.32)}
.pts.bajo{background:rgba(248,113,113,.1);color:var(--mal);border:1px solid rgba(248,113,113,.3)}
.acciones{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
a.btn,button.btn{background:var(--panel2);border:1px solid var(--linea);color:var(--txt);
padding:7px 13px;border-radius:9px;font-size:13px;text-decoration:none;cursor:pointer;font-family:inherit}
a.btn:hover,button.btn:hover{border-color:var(--acento);color:#fff}
a.btn.principal{background:rgba(96,165,250,.14);border-color:rgba(96,165,250,.4)}
.estado{font-size:12px;color:var(--medio)}
footer{margin-top:34px;padding-top:18px;border-top:1px solid var(--linea);color:var(--tenue);font-size:13px}
footer a{color:var(--acento)}
.oculto{display:none}
"""

JS = """
const ofertas = JSON.parse(document.getElementById('datos').textContent);
const caja = document.getElementById('lista');
const buscador = document.getElementById('buscar');
const orden = document.getElementById('orden');

function plantilla(o, idioma) {
  const saludo = idioma === 'en'
    ? `Hi ${o.empresa} team,`
    : `Hola equipo de ${o.empresa},`;
  const cuerpo = idioma === 'en'
    ? `I'm applying for the ${o.titulo} role. I'm a fullstack developer (5 years) working mainly with React/Next.js and C#/.NET, shipping end-to-end: database schema, API, deployment and monitoring. Most recently I built an offline-first PWA used in production (sole frontend developer) and acted as release manager for a Next.js ERP. I also build my own tools: a payroll engine in .NET 8 with the law as data, and a legacy-audit CLI in Python.`
    : `Me interesa el puesto de ${o.titulo}. Soy desarrollador fullstack (5 años) con foco en React/Next.js y C#/.NET, y trabajo end-to-end: esquema de base de datos, API, despliegue y monitoreo. Lo último que hice fue una PWA offline-first en producción (único dev del front) y fui release manager de un ERP en Next.js. También construyo herramientas propias: un motor de liquidación en .NET 8 con la ley como dato y un CLI de auditoría de sistemas legacy en Python.`;
  const cierre = idioma === 'en'
    ? `Happy to share details or do a technical challenge. Thanks!`
    : `Quedo a disposición para ampliar o hacer un challenge técnico. Gracias.`;
  return `${saludo}\\n\\n${cuerpo}\\n\\n${cierre}\\n\\nGitHub: github.com/lucabaello1998`;
}

function pintar() {
  const texto = buscador.value.toLowerCase();
  const criterio = orden.value;
  const lista = ofertas
    .filter(o => !texto || (o.titulo + ' ' + o.empresa + ' ' + (o.tags || []).join(' ')).toLowerCase().includes(texto))
    .sort((a, b) => criterio === 'fecha' ? (b.publicado || '').localeCompare(a.publicado || '') : b.puntaje - a.puntaje);

  caja.innerHTML = lista.map(o => {
    const nivel = o.puntaje >= 60 ? 'alto' : o.puntaje >= 30 ? 'medio' : 'bajo';
    const tags = (o.tags || []).slice(0, 8).map(t => `<span class="chip">${escapar(t)}</span>`).join('');
    const motivos = (o.motivos || []).slice(0, 6).map(m => `<span class="chip">${escapar(m)}</span>`).join('');
    const salario = o.salario ? `<span>💵 ${escapar(o.salario)}</span>` : '';
    const estado = o.estado ? `<span class="estado">${escapar(o.estado.replace('_', ' '))}</span>` : '';
    return `<article class="oferta">
      <div class="fila">
        <div>
          <h3>${escapar(o.titulo)}</h3>
          <div class="empresa">${escapar(o.empresa)} · ${escapar(o.fuente)}</div>
          <div class="meta">
            <span>📍 ${escapar(o.ubicacion || 'sin dato')}</span>
            ${salario}
            <span>🗓 ${escapar(o.publicado || 'sin fecha')}</span>
            ${estado}
          </div>
          <div>${tags}</div>
          <div style="margin-top:6px;color:#93a6ba;font-size:12px">${motivos}</div>
        </div>
        <div class="pts ${nivel}">${o.puntaje}</div>
      </div>
      <div class="acciones">
        <a class="btn principal" href="${escapar(o.url)}" target="_blank" rel="noopener">Ver oferta ↗</a>
        <button class="btn" data-i="${o.id}">Copiar mensaje</button>
      </div>
    </article>`;
  }).join('') || '<p style="color:#93a6ba">Nada con ese filtro.</p>';

  caja.querySelectorAll('button[data-i]').forEach(boton => {
    boton.addEventListener('click', async () => {
      const o = ofertas.find(x => x.id === boton.dataset.i);
      try {
        await navigator.clipboard.writeText(plantilla(o, o.idioma));
        boton.textContent = 'Copiado ✓';
      } catch {
        boton.textContent = 'No se pudo copiar';
      }
      setTimeout(() => { boton.textContent = 'Copiar mensaje'; }, 1600);
    });
  });
}

function escapar(t) {
  return String(t).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

buscador.addEventListener('input', pintar);
orden.addEventListener('change', pintar);
pintar();
"""


def _tarjeta_kpi(valor: str, etiqueta: str) -> str:
    return f'<div class="kpi"><b>{html.escape(valor)}</b><small>{html.escape(etiqueta)}</small></div>'


def render(ofertas: list[dict], resumen: dict[str, int], fuentes_ok: list[str], fuentes_error: list[str]) -> str:
    total = len(ofertas)
    alto = sum(1 for o in ofertas if o["puntaje"] >= 60)
    aplicadas = sum(resumen.get(e, 0) for e in ("aplicada", "respondida", "entrevista", "tecnica", "oferta"))
    kpis = "".join(
        [
            _tarjeta_kpi(str(total), "ofertas rankeadas"),
            _tarjeta_kpi(str(alto), "encaje alto (60+)"),
            _tarjeta_kpi(str(aplicadas), "postulaciones activas"),
            _tarjeta_kpi(str(len(fuentes_ok)), f"fuentes ok · {len(fuentes_error)} caídas"),
        ]
    )
    datos = json.dumps(ofertas, ensure_ascii=False).replace("</", "<\\/")
    caidas = (
        f"<p style='color:#f87171;font-size:13px'>Fuentes caídas en esta corrida: {html.escape(', '.join(fuentes_error))}</p>"
        if fuentes_error
        else ""
    )
    return f"""<!doctype html>
<html lang="es-AR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job radar · ofertas rankeadas para fullstack SSR</title>
<meta name="description" content="Ofertas remotas de desarrollo rankeadas contra un perfil fullstack SSR (React/Next.js + .NET). Se actualiza solo todos los días.">
<style>{CSS}</style>
</head>
<body>
<div class="ancho">
  <header>
    <div>
      <h1>Job <span>radar</span></h1>
      <p class="sub">Ofertas remotas rankeadas contra el perfil: React/Next.js · TypeScript · C#/.NET · fullstack SSR.
      Cada punto tiene un motivo, no es una caja negra.</p>
    </div>
    <div class="sub">Actualizado: {html.escape(ahora())}</div>
  </header>

  <div class="kpis">{kpis}</div>
  {caidas}

  <div class="barra">
    <input id="buscar" type="search" placeholder="Filtrar por puesto, empresa o tecnología…" aria-label="Filtrar">
    <select id="orden" aria-label="Orden">
      <option value="puntaje">Mejor encaje</option>
      <option value="fecha">Más recientes</option>
    </select>
  </div>

  <main id="lista"></main>

  <footer>
    <p>Fuentes: Remotive, RemoteOK y GetOnBoard (APIs públicas). El radar <b>no postula solo</b>:
    rankear y escribir el borrador sí se automatiza, apretar enviar lo hacés vos.</p>
    <p>Registro de postulaciones: <code>python -m jobradar.estado add &lt;id&gt; aplicada</code> ·
    <a href="https://github.com/lucabaello1998/job-radar">Código</a></p>
  </footer>
</div>
<script id="datos" type="application/json">{datos}</script>
<script>{JS}</script>
</body>
</html>
"""


def escribir(
    ofertas: list[dict], resumen: dict[str, int], fuentes_ok: list[str], fuentes_error: list[str], destino: Path
) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(render(ofertas, resumen, fuentes_ok, fuentes_error), encoding="utf-8")
    return destino
