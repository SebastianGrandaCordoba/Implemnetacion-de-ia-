import unittest

from app.domain.activity_styles import DEFAULT, STYLES, max_minutes, style_rules
from app.domain.request_rules import InvalidRequest, normalize_activity_styles


class ActivityStyleTests(unittest.TestCase):
    def test_empty_means_guided_exercises(self) -> None:
        self.assertEqual(normalize_activity_styles(""), DEFAULT)

    def test_styles_are_normalized_and_deduplicated(self) -> None:
        self.assertEqual(normalize_activity_styles(" code, Deploy ,code"), ("CODE", "DEPLOY"))

    def test_unknown_or_too_many_styles_are_rejected(self) -> None:
        with self.assertRaises(InvalidRequest):
            normalize_activity_styles("DANCE")
        with self.assertRaises(InvalidRequest):
            normalize_activity_styles("CODE,APP,DEPLOY,TEAM")

    def test_extended_work_gets_two_hours_per_activity(self) -> None:
        self.assertEqual(max_minutes(("GUIDED", "CASE")), 60)
        self.assertEqual(max_minutes(("CASE", "DEPLOY")), 120)

    def test_rules_name_each_chosen_style(self) -> None:
        text = style_rules(("CODE", "DEPLOY"))
        self.assertIn("Programar código", text)
        self.assertIn("URL pública", text)
        self.assertIn("```", text)
        self.assertNotIn("Caso de estudio", text)

    def test_every_style_has_a_label_and_rules(self) -> None:
        for style in STYLES.values():
            self.assertTrue(style.label and len(style.rules) > 40)


if __name__ == "__main__":
    unittest.main()


class AreaStylesTests(unittest.TestCase):
    def test_every_area_has_its_own_kinds_of_work(self) -> None:
        from app.domain.activity_styles import STYLES
        for style in ("PROBLEMS", "LAB", "SOURCES", "ESSAY", "READING", "WRITING", "ORAL"):
            self.assertIn(style, STYLES)
        self.assertTrue(STYLES["LAB"].extended)
        self.assertFalse(STYLES["PROBLEMS"].extended)
