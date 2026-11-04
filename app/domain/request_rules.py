"""Validation of the teacher's request, independent from FastAPI."""

import re

MAX_OBJECTIVE_CHARS = 1000
MAX_CONTEXT_CHARS = 2500
MAX_MATERIALS = 6
GENERATION_TYPES = frozenset({"WORKSHOP", "QUIZ"})
LEVEL_ALIASES = {
    "LOW": "LOW", "BAJO": "LOW",
    "MEDIUM": "MEDIUM", "INTERMEDIO": "MEDIUM", "MEDIO": "MEDIUM",
    "HIGH": "HIGH", "ALTO": "HIGH",
}
_FILENAME = re.compile(r"[\w .()_-]{1,180}\.(pdf|docx|txt)", flags=re.IGNORECASE)


class InvalidRequest(ValueError):
    """A request the teacher can fix; the message is shown as is."""


def normalize_level(raw: str) -> str:
    level = LEVEL_ALIASES.get(raw.strip().upper())
    if level is None:
        raise InvalidRequest("El nivel debe ser LOW, MEDIUM o HIGH.")
    return level
