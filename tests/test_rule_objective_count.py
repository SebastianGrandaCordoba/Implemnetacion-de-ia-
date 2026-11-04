import unittest

from app.domain.validation import objective_count
from app.schemas import AssessmentQuestion, WorkshopActivity, WorkshopResponse


def workshop(**over) -> WorkshopResponse:
    data = dict(title="Taller de refuerzo: ciclos", subject="Programación", targetLevel="LOW", summary="Repaso",
                learningObjectives=["Usar for", "Usar while"],
                activities=[WorkshopActivity(title="A{i}", instructions="1. Haz", estimatedMinutes=15) for i in range(3)],
                assessment=[AssessmentQuestion(question="P{i}", options=["a", "b"], correctAnswer="a", explanation="e") for i in range(3)],
                sourceReferences=["Página 2"])
    data.update(over)
    return WorkshopResponse(**data)


MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class ObjectiveCountTests(unittest.TestCase):
    def test_requires_two_to_four_objectives(self) -> None:
        self.assertIsNone(objective_count(workshop(), MATERIAL))
        self.assertIsNotNone(objective_count(workshop(learningObjectives=["solo uno"]), MATERIAL))
        self.assertIsNotNone(objective_count(workshop(learningObjectives=["x"] * 5), MATERIAL))


if __name__ == "__main__":
    unittest.main()
