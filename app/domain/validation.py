"""Quality rules a generated workshop must pass before it reaches the teacher.

Each rule is a small function (Specification pattern): it returns an error message or None.
`validate_workshop` runs them in order and stops at the first broken rule.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

from app.schemas import WorkshopResponse

Rule = Callable[[WorkshopResponse, str], "str | None"]


class InvalidWorkshop(ValueError):
    """The model answered, but the workshop does not meet FairTeam's quality rules."""


def validate_workshop(
    workshop: WorkshopResponse, material_text: str, rules: list[Rule] | None = None, max_minutes: int = 60,
    generation_type: str = "WORKSHOP",
) -> WorkshopResponse:
    if rules is None:
        rules = rules_for(generation_type, max_minutes)
    for rule in rules:
        problem = rule(workshop, material_text)
        if problem:
            raise InvalidWorkshop(problem)
    return workshop

def _between(low: int, high: int, field: str, message: str) -> Rule:
    def rule(workshop: WorkshopResponse, _material: str) -> str | None:
        return None if low <= len(getattr(workshop, field)) <= high else message

    rule.__name__ = f"{field}_between_{low}_{high}"
    return rule


ACTIVITIES_MESSAGE = "El taller no cumple la cantidad esperada de actividades."
QUESTIONS_MESSAGE = "El taller no cumple la cantidad esperada de preguntas."
OBJECTIVES_MESSAGE = "El taller no cumple la cantidad esperada de objetivos."

# Defaults kept for the classic workshop; rules_for() tightens or loosens them per request type.
activity_count = _between(3, 5, "activities", ACTIVITIES_MESSAGE)
question_count = _between(3, 5, "assessment", QUESTIONS_MESSAGE)
objective_count = _between(2, 4, "learningObjectives", OBJECTIVES_MESSAGE)

def activity_minutes_up_to(limit: int) -> Rule:
    """Each activity lasts between 5 minutes and `limit` (60 for class work, 120 for code or projects)."""
    def rule(workshop: WorkshopResponse, _material: str) -> str | None:
        if any(not 5 <= activity.estimatedMinutes <= limit for activity in workshop.activities):
            return "Una actividad tiene una duración fuera del rango permitido."
        return None

    rule.__name__ = f"activity_minutes_up_to_{limit}"
    return rule


activity_minutes = activity_minutes_up_to(60)

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


def _without_accents(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def _cites(reference: str, label: str, number: str) -> bool:
    """Matches "Página 2", "pagina 2" or "[Página 2]"; the model often drops accents."""
    pattern = rf"{_without_accents(label)}\s*{number}(?!\d)"
    return re.search(pattern, _without_accents(reference), flags=re.IGNORECASE) is not None


def verifiable_references(workshop: WorkshopResponse, material: str) -> str | None:
    """Every citation must point to a label that exists in the extracted material."""
    if not material.strip():
        return None  # Written from the teacher's prompt: there is nothing to cite.
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



def rules_for(generation_type: str, max_minutes: int = 60) -> list[Rule]:
    """The same rules for every request, with the counts each kind of request asks for."""
    from app.domain.prompt import shape_for

    shape = shape_for(generation_type)
    # One item more (or one question less) is tolerated: a usable workshop beats another 30 s wait.
    counts = {
        activity_count: _between(shape.activities[0], shape.activities[1] + 1, "activities", ACTIVITIES_MESSAGE),
        question_count: _between(
            max(0, shape.questions[0] - 1), shape.questions[1] + 1, "assessment", QUESTIONS_MESSAGE
        ),
        objective_count: _between(
            shape.objectives[0], shape.objectives[1] + 1, "learningObjectives", OBJECTIVES_MESSAGE
        ),
        activity_minutes: activity_minutes_up_to(max_minutes),
    }
    return [counts.get(rule, rule) for rule in RULES]
