"""Shared builder for valid workshops used across the validation tests."""

from app.schemas import AssessmentQuestion, WorkshopActivity, WorkshopResponse


def workshop(**overrides) -> WorkshopResponse:
    data = {
        "title": "Taller de refuerzo: ciclos",
        "subject": "Programación",
        "targetLevel": "LOW",
        "summary": "Repaso",
        "learningObjectives": ["Usar for", "Usar while"],
        "activities": [
            WorkshopActivity(title=f"A{i}", instructions="1. Haz", estimatedMinutes=15) for i in range(3)
        ],
        "assessment": [
            AssessmentQuestion(question=f"P{i}", options=["a", "b"], correctAnswer="a", explanation="e")
            for i in range(3)
        ],
        "sourceReferences": ["Página 2"],
    }
    data.update(overrides)
    return WorkshopResponse(**data)
