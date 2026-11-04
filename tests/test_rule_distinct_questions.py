import unittest

from app.domain.validation import distinct_questions
from app.schemas import AssessmentQuestion
from tests.workshops import workshop


def question(text: str) -> AssessmentQuestion:
    return AssessmentQuestion(question=text, options=[], correctAnswer="r", explanation="e")


class DistinctQuestionsTests(unittest.TestCase):
    def test_distinct_questions_pass(self) -> None:
        self.assertIsNone(distinct_questions(workshop(), ""))

    def test_repeated_questions_fail_ignoring_case(self) -> None:
        repeated = workshop(assessment=[question("¿Qué es un ciclo?"), question("¿qué es  un ciclo?"), question("Otra")])
        self.assertIsNotNone(distinct_questions(repeated, ""))


if __name__ == "__main__":
    unittest.main()
