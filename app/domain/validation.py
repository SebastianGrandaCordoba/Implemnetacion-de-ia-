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


def validate_workshop(workshop: WorkshopResponse, material_text: str, rules: list[Rule] | None = None) -> WorkshopResponse:
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


RULES: list[Rule] = [activity_count, question_count]

