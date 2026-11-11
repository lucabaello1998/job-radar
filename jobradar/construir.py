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
PREVIA = RAIZ / "docs-preview"

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


def procesar(ofertas: list[Oferta], registradas: dict[str, dict], minimo: int = UMBRAL_PUBLICABLE) -> list[dict]:
    vistas: dict[str, Oferta] = {}
    for oferta in ofertas:
        if not oferta.titulo or not oferta.url or not es_rol_tech(oferta):
            continue
        if not oferta.url.startswith(("http://", "https://")):
            continue  # una URL que no es http(s) termina como link roto o peor: javascript:
        puntuar(oferta)
        if oferta.puntaje < minimo:
            continue
        previa = vistas.get(oferta.clave)
        if previa is None or oferta.puntaje > previa.puntaje:
            vistas[oferta.clave] = oferta

    salida = []
    # `empresa` puede venir vacía o nula de la API: ordenar por None revienta el sort.
    for oferta in sorted(vistas.values(), key=lambda o: (-o.puntaje, (o.empresa or "").lower())):
        fila = oferta.a_dict()
        fila["idioma"] = idioma(oferta)
        fila["estado"] = registradas.get(oferta.id, {}).get("estado", "")
        salida.append(fila)
    return salida


def destino(offline: bool, docs: Path | None, solo: bool = False) -> Path:
    """Una corrida parcial no pisa el tablero publicado.

    Pasa con `--offline` (fixtures) y con `--solo` (una fuente): el tablero que
    sale de ahí le faltarían las otras fuentes, así que va a `docs-preview/`.
    """
    if docs is not None:
        return docs
    return PREVIA if (offline or solo) else DOCS


def _escribir_atomico(ruta: Path, texto: str) -> None:
    """Escribe a un temporal y reemplaza.

    Si el proceso muere entre el HTML y el JSON, o el archivo está abierto en otro
    lado, el tablero publicado no queda a medias.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(texto, encoding="utf-8")
    temporal.replace(ruta)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobradar", description="Radar de ofertas para fullstack SSR")
    parser.add_argument("--offline", action="store_true", help="usar fixtures, sin red")
    parser.add_argument("--guardar-fixtures", action="store_true", help="guardar las respuestas crudas (solo con red)")
    parser.add_argument("--solo", help="correr una sola fuente (escribe en docs-preview/)")
    parser.add_argument(
        "--docs", type=Path, default=None, help="carpeta de salida (default: docs/, o docs-preview/ si es parcial)"
    )
    parser.add_argument(
        "--minimo",
        type=int,
        default=UMBRAL_PUBLICABLE,
        help=f"puntaje mínimo para publicar (default {UMBRAL_PUBLICABLE}; 0 publica todo lo que sea tech)",
    )
    parser.add_argument(
        "--privado",
        action="store_true",
        help="no publicar el estado de cada postulación (el registro se sigue usando para el resumen)",
    )
    args = parser.parse_args(argv)
    if args.minimo < 0:
        parser.error("--minimo no puede ser negativo")
    salida = destino(args.offline, args.docs, solo=bool(args.solo))

    ofertas, ok, errores = recolectar(args.offline, args.guardar_fixtures, args.solo)
    print(f"recolectadas: {len(ofertas)} · fuentes ok: {ok} · caídas: {errores}")

    publicables = procesar(ofertas, estado.por_id(), args.minimo)
    if args.privado:
        for fila in publicables:
            fila["estado"] = ""

    if not publicables:
        # Dos casos distintos: la corrida no trajo nada (todas las fuentes caídas:
        # eso sí es un error) o trajo ofertas pero ninguna pasa el corte (normal
        # un domingo: no se toca el tablero y no se marca el CI en rojo).
        if not ofertas:
            print("error: ninguna fuente devolvió ofertas; no se toca el tablero")
            return 1
        print(f"sin ofertas que pasen el corte ({args.minimo}): no se toca el tablero")
        return 0

    destino_html = salida / "index.html"
    html = tablero.render(publicables, estado.resumen(), [f.split(" ")[0] for f in ok], errores)
    datos = salida / "data" / "ofertas.json"
    # Primero el JSON (fuente de datos) y después el HTML: si algo falla, el
    # tablero viejo sigue apuntando a los datos viejos.
    _escribir_atomico(
        datos,
        json.dumps(
            {"corrida": ahora(), "total": len(publicables), "ofertas": publicables}, ensure_ascii=False, indent=1
        ),
    )
    _escribir_atomico(destino_html, html)

    print(f"\n{'':<3}{'pts':>4}  {'empresa':<24}{'puesto':<46}{'fuente':<11}salario")
    print("-" * 108)
    for oferta in publicables[:12]:
        print(
            f"{oferta['puntaje']:>4}  {(oferta['empresa'] or '')[:23]:<24}{oferta['titulo'][:45]:<46}"
            f"{oferta['fuente'][:10]:<11}{oferta['salario'][:28]}"
        )
    print(f"\nescrito: {destino_html}")
    print(f"escrito: {datos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
