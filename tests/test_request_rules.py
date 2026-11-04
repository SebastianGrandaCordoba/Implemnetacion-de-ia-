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
