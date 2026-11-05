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

    def test_default_rules_include_quiz_checks(self) -> None:
        from app.domain.validation import RULES, answers_in_options, distinct_questions, option_count
        for rule in (answers_in_options, distinct_questions, option_count):
            self.assertIn(rule, RULES)

    def test_longer_activities_pass_only_with_a_higher_limit(self) -> None:
        from app.schemas import WorkshopActivity
        long = workshop(activities=[WorkshopActivity(title="A", instructions="1.", estimatedMinutes=90)] * 3)
        with self.assertRaises(InvalidWorkshop):
            validate_workshop(long, MATERIAL)
        validate_workshop(long, MATERIAL, max_minutes=120)

    def test_accepts_a_custom_rule_set(self) -> None:
        def no_long_titles(w, _m):
            return "Título largo" if len(w.title) > 10 else None
        with self.assertRaisesRegex(InvalidWorkshop, "Título largo"):
            validate_workshop(workshop(), MATERIAL, rules=[no_long_titles])


if __name__ == "__main__":
    unittest.main()
