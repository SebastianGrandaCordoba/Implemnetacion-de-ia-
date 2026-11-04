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

def _plain(text: str) -> str:
    return " ".join(text.lower().split())


def answers_in_options(workshop: WorkshopResponse, _material: str) -> str | None:
    """A multiple-choice answer key must point at one of its options, or the teacher grades wrong."""
    for question in workshop.assessment:
        if not question.options:
            continue
        answer = _plain(question.correctAnswer)
        options = [_plain(option) for option in question.options]
        if not any(answer == option or option.startswith(answer) or answer.startswith(option) for option in options):
            return "Una pregunta de opción múltiple tiene una respuesta que no está entre sus opciones."
    return None


def distinct_questions(workshop: WorkshopResponse, _material: str) -> str | None:
    questions = [_plain(question.question) for question in workshop.assessment]
    if len(set(questions)) != len(questions):
        return "El taller repite preguntas de evaluación."
    return None


def option_count(workshop: WorkshopResponse, _material: str) -> str | None:
    for question in workshop.assessment:
        if question.options and not 2 <= len(question.options) <= 5:
            return "Una pregunta de opción múltiple debe tener entre 2 y 5 opciones."
        if len({_plain(option) for option in question.options}) != len(question.options):
            return "Una pregunta repite opciones de respuesta."
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
    option_count,
    answers_in_options,
    distinct_questions,
]

