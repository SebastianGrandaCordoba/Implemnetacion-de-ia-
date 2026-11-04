import unittest

from app.domain.request_rules import (
    InvalidRequest,
    check_material_count,
    check_text_limits,
    normalize_generation_type,
    normalize_level,
    safe_filename,
)


class LevelTests(unittest.TestCase):
    def test_spanish_and_english_aliases(self) -> None:
        self.assertEqual(normalize_level(" bajo "), "LOW")
        self.assertEqual(normalize_level("Intermedio"), "MEDIUM")
        self.assertEqual(normalize_level("medio"), "MEDIUM")
        self.assertEqual(normalize_level("HIGH"), "HIGH")

    def test_unknown_levels_are_rejected(self) -> None:
        with self.assertRaises(InvalidRequest):
            normalize_level("experto")


class GenerationTypeTests(unittest.TestCase):
    def test_types_are_normalized_and_default_to_workshop(self) -> None:
        self.assertEqual(normalize_generation_type(" quiz "), "QUIZ")
        self.assertEqual(normalize_generation_type(""), "WORKSHOP")

    def test_unknown_types_are_rejected(self) -> None:
        with self.assertRaises(InvalidRequest):
            normalize_generation_type("exam")


class TextLimitTests(unittest.TestCase):
    def test_limits_are_inclusive(self) -> None:
        check_text_limits("a" * 1000, "b" * 2500)

    def test_long_objective_or_context_is_rejected(self) -> None:
        with self.assertRaises(InvalidRequest):
            check_text_limits("a" * 1001, "")
        with self.assertRaises(InvalidRequest):
            check_text_limits("", "b" * 2501)
