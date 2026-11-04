import unittest

from app.domain.validation import InvalidWorkshop, validate_workshop
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

class ValidateWorkshopTests(unittest.TestCase):
    def test_returns_valid_workshops_unchanged(self) -> None:
        good = workshop()
        self.assertIs(validate_workshop(good, MATERIAL), good)

    def test_reports_the_first_broken_rule(self) -> None:
        with self.assertRaisesRegex(InvalidWorkshop, "actividades"):
            validate_workshop(workshop(activities=[], sourceReferences=[]), MATERIAL)

    def test_accepts_a_custom_rule_set(self) -> None:
        def no_long_titles(w, _m):
            return "Título largo" if len(w.title) > 10 else None
        with self.assertRaisesRegex(InvalidWorkshop, "Título largo"):
            validate_workshop(workshop(), MATERIAL, rules=[no_long_titles])


if __name__ == "__main__":
    unittest.main()
