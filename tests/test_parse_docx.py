import unittest

from app.document_parser import extract_text
from tests.fixtures import docx


class DocxParsingTests(unittest.TestCase):
    def test_paragraphs_become_numbered_sections(self) -> None:
        text = extract_text("clase.docx", docx(["Introducción", "", "Desarrollo"]), 5000)
        self.assertIn("[Sección 1] Introducción", text)
        self.assertIn("[Sección 3] Desarrollo", text)
        self.assertNotIn("[Sección 2]", text)

    def test_tables_are_kept_as_rows(self) -> None:
        raw = docx(["Notas"], table=[["Concepto", "Ejemplo"], ["Mitosis", "Piel"]])
        text = extract_text("clase.docx", raw, 5000)
        self.assertIn("[Tabla 1]", text)
        self.assertIn("Concepto | Ejemplo", text)
        self.assertIn("Mitosis | Piel", text)


if __name__ == "__main__":
    unittest.main()
