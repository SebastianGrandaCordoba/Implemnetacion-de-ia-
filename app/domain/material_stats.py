"""Describes extracted material so the teacher knows what the AI will read."""

import re
from dataclasses import dataclass

_UNIT = re.compile(r"^\[(Página|Sección|Línea|Tabla) \d+\]", flags=re.MULTILINE)
CHARS_PER_TOKEN = 4
PREVIEW_CHARS = 280


@dataclass(frozen=True)
class MaterialStats:
    filename: str
    characters: int
    words: int
    units: dict[str, int]
    estimated_tokens: int
    preview: str


def describe(filename: str, text: str) -> MaterialStats:
    units: dict[str, int] = {}
    for match in _UNIT.finditer(text):
        units[match.group(1)] = units.get(match.group(1), 0) + 1
    plain = _UNIT.sub("", text)
    preview = " ".join(plain.split())[:PREVIEW_CHARS]
    return MaterialStats(
        filename=filename,
        characters=len(text),
        words=len(plain.split()),
        units=units,
        estimated_tokens=max(1, len(text) // CHARS_PER_TOKEN),
        preview=preview,
    )
