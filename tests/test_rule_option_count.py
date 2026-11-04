import unittest

from app.domain.validation import option_count
from app.schemas import AssessmentQuestion
from tests.workshops import workshop


def with_options(*options: str):
    item = AssessmentQuestion(question="P", options=list(options), correctAnswer="a", explanation="e")
    return workshop(assessment=[item] * 3)


class OptionCountTests(unittest.TestCase):
    def test_two_to_five_options_pass(self) -> None:
        self.assertIsNone(option_count(with_options("a", "b"), ""))
        self.assertIsNone(option_count(with_options("a", "b", "c", "d", "e"), ""))

    def test_open_questions_pass(self) -> None:
        self.assertIsNone(option_count(with_options(), ""))

    def test_one_or_six_options_fail(self) -> None:
        self.assertIsNotNone(option_count(with_options("a"), ""))
        self.assertIsNotNone(option_count(with_options(*"abcdef"), ""))

    def test_duplicate_options_fail(self) -> None:
        self.assertIsNotNone(option_count(with_options("Verdadero", "verdadero", "Falso"), ""))


if __name__ == "__main__":
    unittest.main()
