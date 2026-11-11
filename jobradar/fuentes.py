"""Fuentes de ofertas con API pública. Sin scraping, sin login, sin dependencias.

Cada función devuelve una lista de `Oferta`. Si una fuente falla, se informa y el resto
sigue funcionando: el radar nunca se cae entero por una API caída.

Una fila rara (un `tags: null`, un salario como texto) descarta esa fila, no la fuente:
la API es de otro y no controlamos lo que manda.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from .modelo import Oferta, limpiar_html

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
TIEMPO_MAXIMO = 20
MAXIMO_BYTES = 8 * 1024 * 1024
INTENTOS = 3
# Identificarse con el repo y no con un mail personal: la política de las APIs
# pide un contacto, y el repo público alcanza (además de no dejar el mail en el código).
AGENTE = "job-radar/1.0 (+https://github.com/lucabaello1998/job-radar)"


def _json(url: str) -> object:
    """GET JSON con reintentos para 429 y 5xx.

    Las tres APIs son gratuitas y rate-limitean: un 429 aislado no debería hacer
    perder el día entero de ofertas.
    """
    ultimo_error: Exception | None = None
    for intento in range(INTENTOS):
        pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=TIEMPO_MAXIMO) as respuesta:
                crudo = respuesta.read(MAXIMO_BYTES + 1)
                if len(crudo) > MAXIMO_BYTES:
                    raise ValueError(f"respuesta demasiado grande ({len(crudo)} bytes)")
                return json.loads(crudo.decode("utf-8", "replace"))
        except urllib.error.HTTPError as error:
            ultimo_error = error
            if error.code not in (429, 500, 502, 503, 504) or intento == INTENTOS - 1:
                raise
            time.sleep(2**intento)
        except (urllib.error.URLError, TimeoutError) as error:
            ultimo_error = error
            if intento == INTENTOS - 1:
                raise
            time.sleep(2**intento)

    raise ultimo_error or RuntimeError("no se pudo traer la respuesta")


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


def _filas(datos: object, clave: str, nombre: str) -> list:
    """Las filas de la respuesta, o un error si el payload no tiene la forma esperada.

    Antes, un JSON de error (`{"errors": [...]}`) o un fixture que no existe
    contaban como "fuente ok con 0 ofertas": el tablero se achicaba sin que nadie
    se enterara.
    """
    if datos is None:
        raise ValueError("sin datos (¿falta el fixture en --offline?)")
    if not isinstance(datos, dict) or clave not in datos:
        raise ValueError(f"respuesta inesperada: no tiene '{clave}'")
    filas = datos[clave]
    if not isinstance(filas, list):
        raise ValueError(f"'{clave}' no es una lista")
    return filas


def _tags(valor: object, limite: int = 12) -> list[str]:
    if not isinstance(valor, list):
        return []
    return [str(t).strip() for t in valor if str(t).strip()][:limite]


def _salario(valor: object) -> int | None:
    """Un monto que puede venir como número o como texto ("1500", "1,500")."""
    if valor is None or valor == "" or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return int(valor)
    limpio = str(valor).strip().replace(",", "").replace(" ", "")
    try:
        return int(float(limpio))
    except ValueError:
        return None


def _en_pesos(monto: int) -> str:
    return f"{monto:,}".replace(",", ".")


def remotive(offline: bool = False, guardar: bool = False) -> list[Oferta]:
    datos = _traer("remotive", "https://remotive.com/api/remote-jobs?category=software-dev", offline, guardar)
    ofertas = []
    descartadas = 0
    for fila in _filas(datos, "jobs", "remotive"):
        try:
            if not isinstance(fila, dict):
                raise TypeError("fila no es un objeto")
            ofertas.append(
                Oferta(
                    id=f"remotive:{fila.get('id')}",
                    fuente="Remotive",
                    titulo=str(fila.get("title") or ""),
                    empresa=str(fila.get("company_name") or ""),
                    url=str(fila.get("url") or ""),
                    ubicacion=str(fila.get("candidate_required_location") or "Remoto"),
                    salario=str(fila.get("salary") or ""),
                    publicado=str(fila.get("publication_date") or "")[:10],
                    descripcion=limpiar_html(fila.get("description")),
                    tags=_tags(fila.get("tags")),
                )
            )
        except (TypeError, ValueError, AttributeError):
            descartadas += 1
    _avisar("Remotive", descartadas)
    return ofertas


def remoteok(offline: bool = False, guardar: bool = False) -> list[Oferta]:
    datos = _traer("remoteok", "https://remoteok.com/api", offline, guardar)
    if datos is None:
        raise ValueError("sin datos (¿falta el fixture en --offline?)")
    if not isinstance(datos, list):
        raise ValueError("respuesta inesperada: no es una lista")

    ofertas = []
    descartadas = 0
    for fila in datos:
        try:
            if not isinstance(fila, dict) or not fila.get("id") or not fila.get("position"):
                continue  # el primer elemento es el aviso legal de la API
            minimo, maximo = _salario(fila.get("salary_min")), _salario(fila.get("salary_max"))
            salario = ""
            if minimo and maximo:
                salario = f"USD {_en_pesos(minimo)} - {_en_pesos(maximo)}/año"
            elif minimo:
                salario = f"USD {_en_pesos(minimo)}/año"
            ofertas.append(
                Oferta(
                    id=f"remoteok:{fila.get('id')}",
                    fuente="RemoteOK",
                    titulo=str(fila.get("position") or ""),
                    empresa=str(fila.get("company") or ""),
                    url=str(fila.get("apply_url") or fila.get("url") or ""),
                    ubicacion=str(fila.get("location") or "Remoto"),
                    salario=salario,
                    publicado=str(fila.get("date") or "")[:10],
                    descripcion=limpiar_html(fila.get("description")),
                    tags=_tags(fila.get("tags")),
                )
            )
        except (TypeError, ValueError, AttributeError):
            descartadas += 1
    _avisar("RemoteOK", descartadas)
    return ofertas


def getonboard(offline: bool = False, guardar: bool = False) -> list[Oferta]:
    # el filtro va URL-encoded: con corchetes y comillas crudas, urllib recibe 400
    url = "https://www.getonbrd.com/api/v0/categories/programming/jobs?per_page=100&expand=" + quote('["company"]')
    datos = _traer("getonboard", url, offline, guardar)
    ofertas = []
    descartadas = 0
    for fila in _filas(datos, "data", "getonboard"):
        try:
            if not isinstance(fila, dict):
                raise TypeError("fila no es un objeto")
            atributos = fila.get("attributes") or {}
            empresa = ((atributos.get("company") or {}).get("data") or {}).get("attributes") or {}
            paises = ", ".join(str(p) for p in (atributos.get("countries") or [])) or "Remoto"
            modalidad = str(atributos.get("remote_modality") or "")
            ubicacion = "Remoto" if modalidad == "remote" else f"{paises} ({modalidad or 'presencial'})"
            salario = ""
            minimo, maximo = _salario(atributos.get("min_salary")), _salario(atributos.get("max_salary"))
            if minimo and maximo:
                moneda = "CLP" if "Chile" in (atributos.get("countries") or []) else ""
                salario = f"{moneda} {_en_pesos(minimo)} - {_en_pesos(maximo)}".strip()
            ofertas.append(
                Oferta(
                    id=f"getonboard:{fila.get('id')}",
                    fuente="GetOnBoard",
                    titulo=str(atributos.get("title") or ""),
                    empresa=str(empresa.get("name") or ""),
                    url=str((fila.get("links") or {}).get("public_url") or ""),
                    ubicacion=ubicacion,
                    salario=salario,
                    publicado=_fecha(atributos.get("published_at")),
                    descripcion=limpiar_html(
                        " ".join(
                            str(atributos.get(campo) or "")
                            for campo in ("description", "functions", "desirable", "benefits")
                        )
                    ),
                    tags=_tags(atributos.get("tags")),
                )
            )
        except (TypeError, ValueError, AttributeError):
            descartadas += 1
    _avisar("GetOnBoard", descartadas)
    return ofertas


def _avisar(fuente: str, descartadas: int) -> None:
    if descartadas:
        print(f"aviso: {fuente} descartó {descartadas} fila(s) con datos raros", file=sys.stderr)


def _fecha(epoch: object) -> str:
    try:
        return datetime.fromtimestamp(int(epoch), tz=UTC).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError, OverflowError):
        return ""


FUENTES: dict[str, Callable[..., list[Oferta]]] = {
    "remotive": remotive,
    "remoteok": remoteok,
    "getonboard": getonboard,
}
