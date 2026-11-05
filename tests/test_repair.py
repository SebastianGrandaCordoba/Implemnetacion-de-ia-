import unittest

from app.domain.repair import repair_workshop
from app.domain.validation import validate_workshop
from app.schemas import AssessmentQuestion, WorkshopActivity
from tests.workshops import workshop

MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"


def question(text="P", options=("a", "b"), answer="a") -> AssessmentQuestion:
    return AssessmentQuestion(question=text, options=list(options), correctAnswer=answer, explanation="e")


class RepairTests(unittest.TestCase):
    def test_valid_workshops_are_unchanged(self) -> None:
        original = workshop()
        self.assertEqual(repair_workshop(original, MATERIAL), original)

    def test_extra_items_are_trimmed(self) -> None:
        activities = [WorkshopActivity(title=f"A{i}", instructions="1.", estimatedMinutes=10) for i in range(7)]
        objectives = [f"Objetivo {i}" for i in range(6)]
        repaired = repair_workshop(workshop(activities=activities, learningObjectives=objectives), MATERIAL)
        self.assertEqual(len(repaired.activities), 5)
        self.assertEqual(len(repaired.learningObjectives), 4)

    def test_minutes_are_clamped(self) -> None:
        activities = [WorkshopActivity(title="A", instructions="1.", estimatedMinutes=m) for m in (0, 30, 120)]
        minutes = [a.estimatedMinutes for a in repair_workshop(workshop(activities=activities), MATERIAL).activities]
        self.assertEqual(minutes, [5, 30, 60])

    def test_repeated_questions_are_dropped(self) -> None:
        items = [question("¿Qué es?"), question("¿qué  es?"), question("Otra"), question("Otra más")]
        repaired = repair_workshop(workshop(assessment=items), MATERIAL)
        self.assertEqual([q.question for q in repaired.assessment], ["¿Qué es?", "Otra", "Otra más"])

    def test_letter_answers_become_the_option_text(self) -> None:
        item = question(options=["10", "12", "14"], answer="b)")
        repaired = repair_workshop(workshop(assessment=[item] * 3), MATERIAL).assessment[0]
        self.assertEqual(repaired.correctAnswer, "12")

    def test_wrong_answer_keys_turn_into_open_questions(self) -> None:
        item = question(options=["10", "12"], answer="Catorce, porque 7x2")
        repaired = repair_workshop(workshop(assessment=[item] * 3), MATERIAL).assessment[0]
        self.assertEqual(repaired.options, [])
        self.assertEqual(repaired.correctAnswer, "Catorce, porque 7x2")

    def test_duplicate_options_are_merged(self) -> None:
        item = question(options=["Verdadero", "verdadero", "Falso"], answer="Falso")
        self.assertEqual(repair_workshop(workshop(assessment=[item] * 3), MATERIAL).assessment[0].options,
                         ["Verdadero", "Falso"])

    def test_too_many_options_keep_the_answer(self) -> None:
        item = question(options=list("abcdefg"), answer="g")
        options = repair_workshop(workshop(assessment=[item] * 3), MATERIAL).assessment[0].options
        self.assertEqual(len(options), 5)
        self.assertIn("g", options)

    def test_invented_citations_are_dropped_when_real_ones_remain(self) -> None:
        repaired = repair_workshop(workshop(sourceReferences=["Página 2", "Página 40"]), MATERIAL)
        self.assertEqual(repaired.sourceReferences, ["Página 2"])

    def test_only_invented_citations_still_fail_validation(self) -> None:
        repaired = repair_workshop(workshop(sourceReferences=["Página 40"]), MATERIAL)
        with self.assertRaises(Exception):
            validate_workshop(repaired, MATERIAL)

    def test_repaired_defects_pass_validation(self) -> None:
        items = [question("P1", ["10", "12"], "B"), question("P2", ["x", "x", "y"], "y"),
                 question("P3", ["1", "2"], "tres"), question("P1", ["10", "12"], "12")]
        broken = workshop(assessment=items, sourceReferences=["Pagina 2", "Página 9"])
        validate_workshop(repair_workshop(broken, MATERIAL), MATERIAL)


if __name__ == "__main__":
    unittest.main()
