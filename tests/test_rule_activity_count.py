import unittest

from app.domain.validation import activity_count
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

class ActivityCountTests(unittest.TestCase):
    def test_accepts_three_to_five_activities(self) -> None:
        self.assertIsNone(activity_count(workshop(), MATERIAL))

    def test_rejects_too_few_or_too_many(self) -> None:
        one = workshop().activities[:1]
        self.assertIsNotNone(activity_count(workshop(activities=one), MATERIAL))
        self.assertIsNotNone(activity_count(workshop(activities=one * 6), MATERIAL))


if __name__ == "__main__":
    unittest.main()
