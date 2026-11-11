"""Modelo y utilidades compartidas."""

from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

ETIQUETAS = re.compile(r"<[^>]+>")
ESPACIOS = re.compile(r"\s+")


def limpiar_html(texto: str | None, limite: int = 4000) -> str:
    """Convierte HTML a texto plano legible, sin entidades ni etiquetas.

    `html.unescape` ya resuelve todas las entidades conocidas (y las numéricas).
    Hacerle un segundo reemplazo a mano, además, convertía `&amp;lt;` en `<`: el
    texto publicado no era el que escribió la empresa.
    """
    if not texto:
        return ""
    sin_etiquetas = ETIQUETAS.sub(" ", texto)
    sin_entidades = html.unescape(sin_etiquetas)
    return ESPACIOS.sub(" ", sin_entidades).strip()[:limite]


def slug(texto: str, largo: int = 80) -> str:
    """Identificador estable a partir de empresa + título."""
    base = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return base[:largo].rstrip("-") or "oferta"


def ahora() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Oferta:
    id: str
    fuente: str
    titulo: str
    empresa: str
    url: str
    ubicacion: str = ""
    salario: str = ""
    publicado: str = ""
    descripcion: str = ""
    tags: list[str] = field(default_factory=list)
    puntaje: int = 0
    motivos: list[str] = field(default_factory=list)

    def a_dict(self) -> dict:
        return asdict(self)

    @property
    def clave(self) -> str:
        """Empresa + título normalizados, para deduplicar entre fuentes."""
        return slug(f"{self.empresa} {self.titulo}", 120)
