"""Registro de postulaciones: un JSONL que es la única fuente de verdad del funnel.

Cada línea: {"fecha", "id", "empresa", "titulo", "estado", "nota", "url"}.
Se agrega con la CLI y el tablero lo lee para mostrar el estado de cada oferta.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA = RAIZ / "postulaciones.jsonl"

ESTADOS = [
    "por_postular",
    "aplicada",
    "respondida",
    "entrevista",
    "tecnica",
    "oferta",
    "descartada",
]

EMOJIS = {
    "por_postular": "·",
    "aplicada": "→",
    "respondida": "↩",
    "entrevista": "☎",
    "tecnica": "⚙",
    "oferta": "★",
    "descartada": "×",
}


def leer() -> list[dict]:
    """Las filas válidas del registro.

    Tolera lo que pasa en la vida real: BOM al principio (Notepad guarda así),
    líneas cortadas a la mitad y filas que no son objetos. Las que no se pueden
    leer se avisan por stderr en vez de desaparecer en silencio.
    """
    if not RUTA.exists():
        return []

    filas: list[dict] = []
    descartadas = 0
    # utf-8-sig: si el archivo tiene BOM, la primera línea no rompe el JSON.
    for linea in RUTA.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            fila = json.loads(linea)
        except json.JSONDecodeError:
            descartadas += 1
            continue
        if not isinstance(fila, dict) or not fila.get("id"):
            descartadas += 1
            continue
        filas.append(fila)

    if descartadas:
        print(f"aviso: {descartadas} línea(s) ilegible(s) en {RUTA.name}", file=sys.stderr)
    return filas


def por_id() -> dict[str, dict]:
    """Último estado conocido de cada oferta (gana la última línea)."""
    ultimo: dict[str, dict] = {}
    for fila in leer():
        if fila.get("id"):
            ultimo[fila["id"]] = fila
    return ultimo


def agregar(id_oferta: str, estado: str, empresa: str = "", titulo: str = "", url: str = "", nota: str = "") -> dict:
    if estado not in ESTADOS:
        raise ValueError(f"estado inválido: {estado}. Usar uno de: {', '.join(ESTADOS)}")
    fila = {
        "fecha": date.today().isoformat(),
        "id": id_oferta,
        "empresa": empresa,
        "titulo": titulo,
        "estado": estado,
        "url": url,
        "nota": nota,
    }

    # Si el archivo no termina en salto de línea (lo tocó un editor a mano), el
    # modo "append" pega la fila nueva a la anterior y se pierden las dos.
    separador = ""
    if RUTA.exists() and RUTA.stat().st_size > 0:
        with RUTA.open("rb") as archivo:
            archivo.seek(-1, os.SEEK_END)
            if archivo.read(1) != b"\n":
                separador = "\n"

    with RUTA.open("a", encoding="utf-8") as archivo:
        archivo.write(separador + json.dumps(fila, ensure_ascii=False) + "\n")
    return fila


def resumen() -> dict[str, int]:
    conteo = {estado: 0 for estado in ESTADOS}
    for fila in por_id().values():
        estado = fila.get("estado")
        if estado in conteo:
            conteo[estado] += 1
    return conteo


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="jobradar.estado", description="Registro de postulaciones")
    sub = parser.add_subparsers(dest="cmd", required=True)

    alta = sub.add_parser("add", help="registrar o mover una postulación")
    alta.add_argument("id")
    alta.add_argument("estado", choices=ESTADOS)
    alta.add_argument("--empresa", default="")
    alta.add_argument("--titulo", default="")
    alta.add_argument("--url", default="")
    alta.add_argument("--nota", default="")

    sub.add_parser("list", help="ver el funnel")
    sub.add_parser("resumen", help="conteo por estado")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        fila = agregar(args.id, args.estado, args.empresa, args.titulo, args.url, args.nota)
        print(f"registrado: {fila['fecha']} {fila['estado']} {fila['empresa']} - {fila['titulo']}")
    elif args.cmd == "list":
        for fila in leer():
            marca = EMOJIS.get(fila.get("estado", ""), "?")
            print(
                f"{fila.get('fecha', '')} {marca} {fila.get('estado', ''):<12} "
                f"{fila.get('empresa', '')[:24]:<24} {fila.get('titulo', '')[:48]}"
            )
    else:
        for estado, total in resumen().items():
            if total:
                print(f"{estado:<12} {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
