"""Quality rules a generated workshop must pass before it reaches the teacher.

Each rule is a small function (Specification pattern): it returns an error message or None.
`validate_workshop` runs them in order and stops at the first broken rule.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from app.schemas import WorkshopResponse

Rule = Callable[[WorkshopResponse, str], "str | None"]


class InvalidWorkshop(ValueError):
    """The model answered, but the workshop does not meet FairTeam's quality rules."""


def validate_workshop(
    workshop: WorkshopResponse, material_text: str, rules: list[Rule] | None = None
) -> WorkshopResponse:
    for rule in rules or RULES:
        problem = rule(workshop, material_text)
        if problem:
            raise InvalidWorkshop(problem)
    return workshop

def activity_count(workshop: WorkshopResponse, _material: str) -> str | None:
    if not 3 <= len(workshop.activities) <= 5:
        return "El taller no cumple la cantidad esperada de actividades."
    return None

def question_count(workshop: WorkshopResponse, _material: str) -> str | None:
    if not 3 <= len(workshop.assessment) <= 5:
        return "El taller no cumple la cantidad esperada de preguntas."
    return None

def objective_count(workshop: WorkshopResponse, _material: str) -> str | None:
    if not 2 <= len(workshop.learningObjectives) <= 4:
        return "El taller no cumple la cantidad esperada de objetivos."
    return None

def activity_minutes(workshop: WorkshopResponse, _material: str) -> str | None:
    if any(not 5 <= activity.estimatedMinutes <= 60 for activity in workshop.activities):
        return "Una actividad tiene una duración fuera del rango permitido."
    return None

def has_references(workshop: WorkshopResponse, _material: str) -> str | None:
    if not workshop.sourceReferences:
        return "El taller no incluye referencias al material."
    return None

LABEL = re.compile(r"\[(Página|Sección|Tabla|Línea) (\d+)\]")
NO_LABELS = "fragmento inicial del material"


def _cites(reference: str, label: str, number: str) -> bool:
    return re.search(rf"{label}\s*{number}(?!\d)", reference, flags=re.IGNORECASE) is not None


def verifiable_references(workshop: WorkshopResponse, material: str) -> str | None:
    """Every citation must point to a label that exists in the extracted material."""
    labels = set(LABEL.findall(material))
    for reference in workshop.sourceReferences:
        if labels:
            if not any(_cites(reference, label, number) for label, number in labels):
                return "El taller cita una página o sección que no se pudo verificar."
        elif reference.strip().lower() != NO_LABELS:
            return "El taller cita una página o sección que no se pudo verificar."
    return None


RULES: list[Rule] = [
    activity_count,
    question_count,
    objective_count,
    activity_minutes,
    has_references,
    verifiable_references,
]

