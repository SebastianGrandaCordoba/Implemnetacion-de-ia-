import unittest

from app.document_parser import extract_text
from tests.fixtures import txt


class TxtParsingTests(unittest.TestCase):
    def test_lines_are_numbered_for_citations(self) -> None:
        text = extract_text("tema.txt", txt("Fracciones", "Suma de fracciones"), 5000)
        self.assertEqual(text, "[Línea 1] Fracciones\n[Línea 2] Suma de fracciones")

    def test_blank_lines_and_padding_are_ignored(self) -> None:
        text = extract_text("tema.txt", txt("", "  Célula  ", "", "Núcleo"), 5000)
        self.assertEqual(text, "[Línea 1] Célula\n[Línea 2] Núcleo")

    def test_utf8_bom_is_removed(self) -> None:
        text = extract_text("tema.txt", "\ufeffÁtomo".encode("utf-8"), 5000)
        self.assertEqual(text, "[Línea 1] Átomo")

    def test_extension_is_case_insensitive(self) -> None:
        self.assertIn("Energía", extract_text("TEMA.TXT", txt("Energía"), 5000))


if __name__ == "__main__":
    unittest.main()
