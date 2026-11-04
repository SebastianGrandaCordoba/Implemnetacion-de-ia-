import unittest

from app.domain.validation import question_count
from tests.workshops import workshop

MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class QuestionCountTests(unittest.TestCase):
    def test_requires_three_to_five_questions(self) -> None:
        self.assertIsNone(question_count(workshop(), MATERIAL))
        self.assertIsNotNone(question_count(workshop(assessment=[]), MATERIAL))


if __name__ == "__main__":
    unittest.main()
