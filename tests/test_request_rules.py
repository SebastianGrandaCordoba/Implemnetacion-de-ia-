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


class FilenameTests(unittest.TestCase):
    def test_paths_are_stripped_to_the_base_name(self) -> None:
        self.assertEqual(safe_filename("C:\\docs\\Guía 1.pdf"), "Guía 1.pdf")
        self.assertEqual(safe_filename("../../etc/clase.txt"), "clase.txt")

    def test_unsupported_or_missing_names_are_rejected(self) -> None:
        for name in (None, "", "virus.exe", "notas.pdf.sh", "a;b.pdf"):
            with self.subTest(name=name), self.assertRaises(InvalidRequest):
                safe_filename(name)

    def test_material_count_between_one_and_six(self) -> None:
        check_material_count(1)
        check_material_count(6)
        for count in (0, 7):
            with self.subTest(count=count), self.assertRaises(InvalidRequest):
                check_material_count(count)


if __name__ == "__main__":
    unittest.main()
