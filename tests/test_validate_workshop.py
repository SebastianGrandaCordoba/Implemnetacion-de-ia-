import unittest

from app.domain.validation import InvalidWorkshop, validate_workshop
from tests.workshops import workshop

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
