import unittest

from app.domain.prompt import DEFAULT_GUIDANCE, deliverable_name, deliverable_rules, is_quiz, level_guidance


class LevelGuidanceTests(unittest.TestCase):
    def test_each_level_has_its_own_guidance(self) -> None:
        self.assertIn("apoyo inicial", level_guidance("LOW"))
        self.assertIn("práctica guiada", level_guidance(" medium "))
        self.assertIn("transferencia", level_guidance("high"))

    def test_unknown_levels_get_a_safe_default(self) -> None:
        self.assertEqual(level_guidance("EXPERT"), DEFAULT_GUIDANCE)


class DeliverableTests(unittest.TestCase):
    def test_quiz_and_workshop_have_different_titles(self) -> None:
        self.assertTrue(is_quiz(" quiz "))
        self.assertEqual(deliverable_name("QUIZ"), "quiz breve de comprobación")
        self.assertEqual(deliverable_name("WORKSHOP"), "taller de refuerzo")
        self.assertIn("'Quiz breve:'", deliverable_rules("QUIZ"))
        self.assertIn("'Taller de refuerzo:'", deliverable_rules("WORKSHOP"))


if __name__ == "__main__":
    unittest.main()
