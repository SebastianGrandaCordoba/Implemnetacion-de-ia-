import unittest

from app.domain.validation import objective_count
from tests.workshops import workshop

MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class ObjectiveCountTests(unittest.TestCase):
    def test_requires_two_to_four_objectives(self) -> None:
        self.assertIsNone(objective_count(workshop(), MATERIAL))
        self.assertIsNotNone(objective_count(workshop(learningObjectives=["solo uno"]), MATERIAL))
        self.assertIsNotNone(objective_count(workshop(learningObjectives=["x"] * 5), MATERIAL))


if __name__ == "__main__":
    unittest.main()
