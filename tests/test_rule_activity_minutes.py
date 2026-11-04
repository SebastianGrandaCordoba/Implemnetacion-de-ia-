import unittest

from app.domain.validation import activity_minutes
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

class ActivityMinutesTests(unittest.TestCase):
    def test_each_activity_lasts_five_to_sixty_minutes(self) -> None:
        self.assertIsNone(activity_minutes(workshop(), MATERIAL))
        long = [WorkshopActivity(title="A", instructions="1.", estimatedMinutes=90)] * 3
        self.assertIsNotNone(activity_minutes(workshop(activities=long), MATERIAL))


if __name__ == "__main__":
    unittest.main()
