"""Puntaje de encaje contra el perfil real de Luca.

Reglas explícitas, no magia: cada punto tiene un motivo visible en el tablero, así se puede
discutir y ajustar. Stack objetivo: React/Next.js/TypeScript + C#/.NET, fullstack SSR, remoto
(LatAm o global), pago en USD.
"""

from __future__ import annotations

import re

from .modelo import Oferta

# (patrón, puntos, motivo)
SENALES: list[tuple[str, int, str]] = [
    (r"\b(next\.?js)\b", 3, "Next.js"),
    (r"\breact\b", 3, "React"),
    (r"\btypescript\b", 2, "TypeScript"),
    (r"(c#|csharp|\.net\b|dotnet\b|asp\.net\b)", 4, ".NET / C#"),
    (r"\bfull[- ]?stack\b", 3, "Fullstack"),
    (r"\bssr\b", 1, "SSR"),
    (r"\bnode(\.js)?\b", 1, "Node"),
    (r"\b(postgres|postgresql|sql server|sql)\b", 1, "SQL"),
    (r"\bazure\b", 1, "Azure"),
    (r"\b(docker|kubernetes)\b", 1, "Contenedores"),
    (r"\b(remoto|remote|anywhere|worldwide)\b", 2, "Remoto"),
    (r"\b(argentina|latam|latin america|south america)\b", 2, "Región accesible"),
    (r"\busd\b|\bu\$s\b|\bus\$", 2, "Paga en USD"),
]

# (patrón, puntos, motivo): motivos negativos que restan
PENALIDADES: list[tuple[str, int, str]] = [
    (r"\b(us|u\.s\.|usa) only\b", -5, "Solo EE.UU."),
    (r"must be (located|based) in", -4, "Restricción de residencia"),
    (r"(authorized|eligible) to work in the (us|united states)", -5, "Permiso de trabajo en EE.UU."),
    (r"\bsecurity clearance\b", -5, "Requiere clearance"),
    (r"\b(on[- ]?site|presencial)\b", -3, "Presencial"),
    (r"\bhybrid\b", -2, "Híbrido"),
    (r"\b(1[0-9]|[2-9][0-9])\+? years\b", -3, "Pide 10+ años"),
    (r"\b(principal|staff engineer|head of engineering)\b", -3, "Seniority muy alto"),
    (r"\b(intern|internship|trainee|pasantía)\b", -5, "Pasantía"),
    (r"\b(unpaid|equity only|sin remuneración)\b", -8, "Sin pago"),
    (r"\b(salesforce|servicenow|sap abap|cobol)\b", -3, "Stack fuera de foco"),
]

# Si el título no menciona nada de esto, probablemente no es un rol de desarrollo
TECH = re.compile(
    r"\b(develop|engineer|programmer|software|fullstack|full[- ]?stack|frontend|front-end|"
    r"backend|back-end|react|\.net|c#|node|typescript|web|devops|sre|architect)\w*",
    re.IGNORECASE,
)

UMBRAL_PUBLICABLE = 6


def _texto(oferta: Oferta) -> str:
    return " ".join([oferta.titulo, oferta.ubicacion, " ".join(oferta.tags), oferta.descripcion[:1500]]).lower()


def es_rol_tech(oferta: Oferta) -> bool:
    return bool(TECH.search(oferta.titulo))


def puntuar(oferta: Oferta) -> Oferta:
    """Asigna `puntaje` (0-100) y la lista de motivos que lo explican."""
    texto = _texto(oferta)
    total = 0
    motivos: list[str] = []

    for patron, puntos, motivo in SENALES:
        if re.search(patron, texto):
            total += puntos
            motivos.append(f"+{puntos} {motivo}")

    for patron, puntos, motivo in PENALIDADES:
        if re.search(patron, texto):
            total += puntos
            motivos.append(f"{puntos} {motivo}")

    oferta.puntaje = max(0, min(100, total * 4))
    oferta.motivos = motivos
    return oferta
