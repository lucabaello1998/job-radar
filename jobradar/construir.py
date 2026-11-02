"""Corrida del radar: trae, deduplica, puntúa y publica el tablero."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import estado, fuentes, tablero
from .modelo import Oferta, ahora
from .puntuar import UMBRAL_PUBLICABLE, es_rol_tech, puntuar

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

# Palabras que delatan el idioma del aviso: alcanza para elegir la plantilla de mensaje.
INGLES = re.compile(r"\b(the|and|with|you|we|our|is|are|will|team|experience)\b", re.IGNORECASE)
ESPANOL = re.compile(r"\b(el|la|los|las|que|con|para|una|del|nuestro|equipo|experiencia)\b", re.IGNORECASE)


def idioma(oferta: Oferta) -> str:
    texto = oferta.descripcion[:600]
    return "en" if len(INGLES.findall(texto)) > len(ESPANOL.findall(texto)) else "es"


def recolectar(
    offline: bool = False, guardar: bool = False, solo: str | None = None
) -> tuple[list[Oferta], list[str], list[str]]:
    acumuladas: list[Oferta] = []
    buenas: list[str] = []
    errores: list[str] = []
    for nombre, fuente in fuentes.FUENTES.items():
        if solo and nombre != solo:
            continue
        try:
            encontradas = fuente(offline=offline, guardar=guardar)
        except Exception as error:  # una fuente caída no voltea la corrida
            errores.append(f"{nombre}: {type(error).__name__}")
            continue
        acumuladas.extend(encontradas)
        buenas.append(f"{nombre} ({len(encontradas)})")
    return acumuladas, buenas, errores


def procesar(ofertas: list[Oferta], registradas: dict[str, dict]) -> list[dict]:
    vistas: dict[str, Oferta] = {}
    for oferta in ofertas:
        if not oferta.titulo or not oferta.url or not es_rol_tech(oferta):
            continue
        puntuar(oferta)
        if oferta.puntaje < UMBRAL_PUBLICABLE:
            continue
        previa = vistas.get(oferta.clave)
        if previa is None or oferta.puntaje > previa.puntaje:
            vistas[oferta.clave] = oferta

    salida = []
    for oferta in sorted(vistas.values(), key=lambda o: (-o.puntaje, o.empresa)):
        fila = oferta.a_dict()
        fila["idioma"] = idioma(oferta)
        fila["estado"] = registradas.get(oferta.id, {}).get("estado", "")
        salida.append(fila)
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobradar", description="Radar de ofertas para fullstack SSR")
    parser.add_argument("--offline", action="store_true", help="usar fixtures, sin red")
    parser.add_argument("--guardar-fixtures", action="store_true", help="guardar las respuestas crudas")
    parser.add_argument("--solo", help="correr una sola fuente")
    parser.add_argument("--docs", type=Path, default=DOCS, help="carpeta de salida")
    parser.add_argument("--minimo", type=int, default=UMBRAL_PUBLICABLE, help="puntaje mínimo")
    args = parser.parse_args(argv)

    ofertas, ok, errores = recolectar(args.offline, args.guardar_fixtures, args.solo)
    print(f"recolectadas: {len(ofertas)} · fuentes ok: {ok} · caídas: {errores}")

    publicables = procesar(ofertas, estado.por_id())
    if args.minimo != UMBRAL_PUBLICABLE:
        publicables = [o for o in publicables if o["puntaje"] >= args.minimo]

    if not publicables:
        print("sin ofertas publicables: no se toca el tablero")
        return 1

    destino_html = args.docs / "index.html"
    tablero.escribir(publicables, estado.resumen(), [f.split(" ")[0] for f in ok], errores, destino_html)
    datos = args.docs / "data" / "ofertas.json"
    datos.parent.mkdir(parents=True, exist_ok=True)
    datos.write_text(
        json.dumps(
            {"corrida": ahora(), "total": len(publicables), "ofertas": publicables}, ensure_ascii=False, indent=1
        ),
        encoding="utf-8",
    )

    print(f"\n{'':<3}{'pts':>4}  {'empresa':<24}{'puesto':<46}{'fuente':<11}salario")
    print("-" * 108)
    for oferta in publicables[:12]:
        print(
            f"{oferta['puntaje']:>4}  {oferta['empresa'][:23]:<24}{oferta['titulo'][:45]:<46}"
            f"{oferta['fuente'][:10]:<11}{oferta['salario'][:28]}"
        )
    print(f"\nescrito: {destino_html}")
    print(f"escrito: {datos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
