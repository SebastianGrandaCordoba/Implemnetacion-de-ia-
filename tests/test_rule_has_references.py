import unittest

from app.domain.validation import has_references
from app.schemas import AssessmentQuestion, WorkshopActivity, WorkshopResponse


def workshop(**over) -> WorkshopResponse:
    data = dict(title="Taller de refuerzo: ciclos", subject="Programación", targetLevel="LOW", summary="Repaso",
                learningObjectives=["Usar for", "Usar while"],
                activities=[WorkshopActivity(title=f"A{{i}}", instructions="1. Haz", estimatedMinutes=15) for i in range(3)],
                assessment=[AssessmentQuestion(question=f"P{{i}}", options=["a", "b"], correctAnswer="a", explanation="e") for i in range(3)],
                sourceReferences=["Página 2"])
    data.update(over)
    return WorkshopResponse(**data)


MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class HasReferencesTests(unittest.TestCase):
    def test_requires_at_least_one_reference(self) -> None:
        self.assertIsNone(has_references(workshop(), MATERIAL))
        self.assertIsNotNone(has_references(workshop(sourceReferences=[]), MATERIAL))


if __name__ == "__main__":
    unittest.main()
