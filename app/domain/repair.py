"""Fixes small, safe defects in a generated workshop instead of throwing the whole answer away.

A rejected workshop costs the teacher another 20-40 s wait, so anything that can be corrected
without inventing content is corrected here; `validate_workshop` then only rejects what cannot.
"""

from __future__ import annotations

import re

from app.domain.validation import LABEL, NO_LABELS, _cites, _plain
from app.schemas import AssessmentQuestion, WorkshopActivity, WorkshopResponse

MAX_ACTIVITIES = 6
MAX_QUESTIONS = 9
MAX_OBJECTIVES = 4
MAX_OPTIONS = 5
MAX_HINTS = 3
MAX_TEACHER_NOTES = 5
_LETTER = re.compile(r"^\(?([a-e])[).:]?$", flags=re.IGNORECASE)


def repair_workshop(workshop: WorkshopResponse, material_text: str, max_minutes: int = 60) -> WorkshopResponse:
    return workshop.model_copy(
        update={
            "learningObjectives": _unique([o.strip() for o in workshop.learningObjectives if o.strip()])[
                :MAX_OBJECTIVES
            ],
            "activities": [_repair_activity(a, max_minutes) for a in workshop.activities][:MAX_ACTIVITIES],
            "assessment": _repair_questions(workshop.assessment)[:MAX_QUESTIONS],
            "sourceReferences": _repair_references(workshop.sourceReferences, material_text),
            "teacherNotes": _unique([n.strip() for n in workshop.teacherNotes if n.strip()])[:MAX_TEACHER_NOTES],
            "studentIntro": workshop.studentIntro.strip(),
        }
    )


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        if _plain(item) not in seen:
            seen.add(_plain(item))
            result.append(item)
    return result


def _repair_activity(activity: WorkshopActivity, max_minutes: int) -> WorkshopActivity:
    return activity.model_copy(update={
        "estimatedMinutes": max(5, min(max_minutes, activity.estimatedMinutes)),
        "hints": _unique([h.strip() for h in activity.hints if h.strip()])[:MAX_HINTS],
        "goal": activity.goal.strip(),
        "deliverable": activity.deliverable.strip(),
    })


def _repair_questions(questions: list[AssessmentQuestion]) -> list[AssessmentQuestion]:
    seen: set[str] = set()
    repaired = []
    for question in questions:
        key = _plain(question.question)
        if not key or key in seen:
            continue
        seen.add(key)
        repaired.append(_repair_options(question))
    return repaired


def _repair_options(question: AssessmentQuestion) -> AssessmentQuestion:
    options = _unique([option.strip() for option in question.options if option.strip()])
    answer = question.correctAnswer.strip()
    letter = _LETTER.match(answer)
    if letter and options:
        index = ord(letter.group(1).lower()) - ord("a")
        if index < len(options):
            answer = options[index]
    if options and not _answer_listed(answer, options):
        # The key does not match any option: keep the question as an open one with its expected answer
        # rather than handing the teacher a wrong answer key.
        options = []
    if len(options) > MAX_OPTIONS:
        keep = [o for o in options if _answer_listed(answer, [o])][:1]
        options = (keep + [o for o in options if o not in keep])[:MAX_OPTIONS]
    if len(options) == 1:
        options = []
    return question.model_copy(update={"options": options, "correctAnswer": answer})


def _answer_listed(answer: str, options: list[str]) -> bool:
    plain = _plain(answer)
    return any(plain == _plain(o) or _plain(o).startswith(plain) or plain.startswith(_plain(o)) for o in options)


def _repair_references(references: list[str], material_text: str) -> list[str]:
    cleaned = _unique([r.strip() for r in references if r.strip()])
    if not material_text.strip():
        from app.domain.prompt import NO_MATERIAL_REFERENCE

        return [NO_MATERIAL_REFERENCE]
    labels = set(LABEL.findall(material_text))
    if not labels:
        return [NO_LABELS.capitalize()]
    verifiable = [r for r in cleaned if any(_cites(r, label, number) for label, number in labels)]
    # Drop invented citations only when real ones remain; otherwise let validation reject it.
    return verifiable or cleaned
