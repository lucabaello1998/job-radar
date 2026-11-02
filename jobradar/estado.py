"""Registro de postulaciones: un JSONL que es la única fuente de verdad del funnel.

Cada línea: {"fecha", "id", "empresa", "titulo", "estado", "nota", "url"}.
Se agrega con la CLI y el tablero lo lee para mostrar el estado de cada oferta.
"""

from __future__ import annotations

import json
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
    "respondida": "✉",
    "entrevista": "🗣",
    "tecnica": "🔧",
    "oferta": "★",
    "descartada": "×",
}


def leer() -> list[dict]:
    if not RUTA.exists():
        return []
    filas = []
    for linea in RUTA.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            filas.append(json.loads(linea))
        except json.JSONDecodeError:
            continue
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
    with RUTA.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
    return fila


def resumen() -> dict[str, int]:
    conteo = {estado: 0 for estado in ESTADOS}
    for fila in por_id().values():
        conteo[fila["estado"]] = conteo.get(fila["estado"], 0) + 1
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
        print(f"registrado: {fila['fecha']} {fila['estado']} {fila['empresa']} — {fila['titulo']}")
    elif args.cmd == "list":
        for fila in leer():
            marca = EMOJIS.get(fila["estado"], "?")
            print(
                f"{fila['fecha']} {marca} {fila['estado']:<12} {fila.get('empresa', '')[:24]:<24} {fila.get('titulo', '')[:48]}"
            )
    else:
        for estado, total in resumen().items():
            if total:
                print(f"{estado:<12} {total}")
    return 0
