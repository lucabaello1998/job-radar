"""Fuentes de ofertas con API pública. Sin scraping, sin login, sin dependencias.

Cada función devuelve una lista de `Oferta`. Si una fuente falla, se informa y el resto
sigue funcionando: el radar nunca se cae entero por una API caída.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from datetime import UTC
from pathlib import Path
from urllib.parse import quote

from .modelo import Oferta, limpiar_html

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
TIEMPO_MAXIMO = 20
AGENTE = "job-radar/1.0 (busqueda laboral personal; contacto: luca.baello@gmail.com)"


def _json(url: str) -> object:
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    with urllib.request.urlopen(pedido, timeout=TIEMPO_MAXIMO) as respuesta:
        return json.loads(respuesta.read().decode("utf-8", "replace"))


def _fixture(nombre: str) -> object | None:
    ruta = FIXTURES / f"{nombre}.json"
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def _traer(nombre: str, url: str, offline: bool, guardar: bool) -> object | None:
    if offline:
        return _fixture(nombre)
    datos = _json(url)
    if guardar:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        (FIXTURES / f"{nombre}.json").write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def remotive(offline: bool = False, guardar: bool = False) -> list[Oferta]:
    datos = _traer("remotive", "https://remotive.com/api/remote-jobs?category=software-dev", offline, guardar)
    ofertas = []
    for fila in (datos or {}).get("jobs", []):
        titulo = fila.get("title", "")
        empresa = fila.get("company_name", "")
        ofertas.append(
            Oferta(
                id=f"remotive:{fila.get('id')}",
                fuente="Remotive",
                titulo=titulo,
                empresa=empresa,
                url=fila.get("url", ""),
                ubicacion=fila.get("candidate_required_location", "") or "Remoto",
                salario=fila.get("salary", "") or "",
                publicado=(fila.get("publication_date", "") or "")[:10],
                descripcion=limpiar_html(fila.get("description")),
                tags=[str(t).strip() for t in fila.get("tags", [])][:12],
            )
        )
    return ofertas


def remoteok(offline: bool = False, guardar: bool = False) -> list[Oferta]:
    datos = _traer("remoteok", "https://remoteok.com/api", offline, guardar)
    ofertas = []
    for fila in datos or []:
        if not isinstance(fila, dict) or not fila.get("id") or not fila.get("position"):
            continue  # el primer elemento es el aviso legal de la API
        minimo, maximo = fila.get("salary_min"), fila.get("salary_max")
        salario = ""
        if minimo and maximo:
            salario = f"USD {int(float(minimo)):,} - {int(float(maximo)):,}/año".replace(",", ".")
        elif minimo:
            salario = f"USD {int(float(minimo)):,}/año".replace(",", ".")
        ofertas.append(
            Oferta(
                id=f"remoteok:{fila.get('id')}",
                fuente="RemoteOK",
                titulo=fila.get("position", ""),
                empresa=fila.get("company", ""),
                url=fila.get("apply_url") or fila.get("url") or "",
                ubicacion=fila.get("location") or "Remoto",
                salario=salario,
                publicado=(fila.get("date", "") or "")[:10],
                descripcion=limpiar_html(fila.get("description")),
                tags=[str(t).strip() for t in fila.get("tags", [])][:12],
            )
        )
    return ofertas


def getonboard(offline: bool = False, guardar: bool = False) -> list[Oferta]:
    # el filtro va URL-encoded: con corchetes y comillas crudas, urllib recibe 400
    url = "https://www.getonbrd.com/api/v0/categories/programming/jobs?per_page=100&expand=" + quote('["company"]')
    datos = _traer("getonboard", url, offline, guardar)
    ofertas = []
    for fila in (datos or {}).get("data", []):
        atributos = fila.get("attributes", {}) or {}
        empresa = ((atributos.get("company") or {}).get("data") or {}).get("attributes") or {}
        paises = ", ".join(atributos.get("countries") or []) or "Remoto"
        modalidad = atributos.get("remote_modality") or ""
        ubicacion = "Remoto" if modalidad == "remote" else f"{paises} ({modalidad or 'presencial'})"
        salario = ""
        if atributos.get("min_salary") and atributos.get("max_salary"):
            moneda = "CLP" if "Chile" in (atributos.get("countries") or []) else ""
            salario = f"{moneda} {atributos['min_salary']:,} - {atributos['max_salary']:,}".strip()
        ofertas.append(
            Oferta(
                id=f"getonboard:{fila.get('id')}",
                fuente="GetOnBoard",
                titulo=atributos.get("title", ""),
                empresa=empresa.get("name", ""),
                url=(fila.get("links") or {}).get("public_url", ""),
                ubicacion=ubicacion,
                salario=salario,
                publicado=_fecha(atributos.get("published_at")),
                descripcion=limpiar_html(
                    " ".join(
                        str(atributos.get(campo) or "")
                        for campo in ("description", "functions", "desirable", "benefits")
                    )
                ),
                tags=[str(t).strip() for t in (atributos.get("tags") or [])][:12],
            )
        )
    return ofertas


def _fecha(epoch: object) -> str:
    from datetime import datetime

    try:
        return datetime.fromtimestamp(int(epoch), tz=UTC).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return ""


FUENTES: dict[str, Callable[..., list[Oferta]]] = {
    "remotive": remotive,
    "remoteok": remoteok,
    "getonboard": getonboard,
}
