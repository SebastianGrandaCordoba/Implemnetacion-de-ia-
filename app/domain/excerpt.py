"""Picks the part of a long document that matters for the request.

Teachers upload whole textbooks; the model gets a fixed budget of characters. Instead of rejecting the
book, the pages (or sections) that talk about the requested topic are kept, in their original order, so
the citations still point to real page numbers.
"""

import re
import unicodedata

BLOCK = re.compile(r"(?=^\[(?:Página|Sección|Tabla|Línea) \d+\])", re.MULTILINE)
WORD = re.compile(r"[a-z0-9ñ]{4,}")
STOPWORDS = frozenset((
    "para", "como", "este", "esta", "estos", "estas", "pero", "sobre", "entre", "desde", "hasta", "donde",
    "cuando", "cual", "cuales", "que", "quien", "tema", "temas", "taller", "talleres", "curso", "cursos", "grupo",
    "nivel", "clase", "clases", "estudiante", "estudiantes", "docente", "actividad", "actividades", "ejercicio",
    "ejercicios", "practica", "practicar", "aprender", "comprender", "reforzar", "refuerzo", "conceptos",
    "concepto", "clave", "material", "materiales", "notas", "hacer", "crear", "incluye", "incluir", "trabajen",
    "trabajo", "minutos", "parejas", "ejemplo", "ejemplos", "usando", "usar", "cada", "todos", "todas", "tiene",
    "tienen", "sean", "puede", "pueden",
))


def plain(text: str) -> str:
    """Lowercase without accents, so 'Gauss', 'gaussiana' and 'GAUSS' meet."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c)).replace("ñ", "ñ")


def terms(focus: str) -> set[str]:
    """Stems (first six letters) of the meaningful words of the request."""
    return {word[:6] for word in WORD.findall(plain(focus)) if word not in STOPWORDS}


def blocks(text: str) -> list[str]:
    parts = [part.strip() for part in BLOCK.split(text) if part.strip()]
    return parts or [text]


def score(block: str, wanted: set[str]) -> int:
    if not wanted:
        return 0
    counts: dict[str, int] = {}
    for word in WORD.findall(plain(block)):
        stem = word[:6]
        if stem in wanted:
            counts[stem] = counts.get(stem, 0) + 1
    # Distinct terms matter more than repeating one: a page about "Gauss" and "determinante" beats a page
    # that says "matriz" twenty times.
    return len(counts) * 10 + min(sum(counts.values()), 30)


def select_excerpt(text: str, focus: str, max_chars: int) -> str:
    """The most relevant blocks that fit in ``max_chars``, in document order, with a note on what was kept."""
    if len(text) <= max_chars:
        return text
    parts = blocks(text)
    wanted = terms(focus)
    ranked = sorted(range(len(parts)), key=lambda i: (-score(parts[i], wanted), i))
    if not wanted or score(parts[ranked[0]], wanted) == 0:
        ranked = list(range(len(parts)))  # Nothing matched: keep the beginning of the document.
    note = "[Nota: el documento es largo; se incluyen solo las partes más relacionadas con el tema pedido.]"
    budget = max_chars - len(note) - 2
    chosen: list[int] = []
    used = 0
    for index in ranked:
        size = len(parts[index]) + 2
        if used + size > budget:
            if not chosen and budget > 200:
                chosen.append(index)  # A single huge block: keep its start rather than nothing.
                used = budget
            continue
        chosen.append(index)
        used += size
        if used >= budget - 200:
            break
    pieces = [parts[i] if len(parts[i]) + 2 <= budget else parts[i][: budget - 2] for i in sorted(chosen)]
    return note + "\n\n" + "\n\n".join(pieces)
