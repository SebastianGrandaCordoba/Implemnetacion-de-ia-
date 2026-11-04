import unittest

from app.domain.validation import answers_in_options
from app.schemas import AssessmentQuestion
from tests.workshops import workshop


def quiz(answer: str, options: list[str]):
    return workshop(assessment=[AssessmentQuestion(question="P", options=options, correctAnswer=answer,
                                                   explanation="e")] * 3)


class AnswersInOptionsTests(unittest.TestCase):
    def test_exact_answers_are_accepted_ignoring_case_and_spaces(self) -> None:
        self.assertIsNone(answers_in_options(quiz("  Doce ", ["once", "doce"]), ""))

    def test_letter_answers_match_lettered_options(self) -> None:
        self.assertIsNone(answers_in_options(quiz("B)", ["A) 10", "B) 12"]), ""))
        self.assertIsNone(answers_in_options(quiz("B) 12, porque 3x4", ["A) 10", "B) 12"]), ""))

    def test_answers_outside_the_options_are_rejected(self) -> None:
        self.assertIsNotNone(answers_in_options(quiz("14", ["10", "12"]), ""))

    def test_open_questions_are_not_checked(self) -> None:
        self.assertIsNone(answers_in_options(quiz("Explica con tus palabras", []), ""))


if __name__ == "__main__":
    unittest.main()
