import unittest

from app.document_parser import MaterialError, extract_text
from tests.fixtures import pdf, txt


class ParserErrorTests(unittest.TestCase):
    def assertMaterialError(self, fragment: str, filename: str, raw: bytes, max_chars: int = 5000) -> None:
        with self.assertRaises(MaterialError) as raised:
            extract_text(filename, raw, max_chars)
        self.assertIn(fragment, str(raised.exception))

    def test_unsupported_extensions_are_rejected(self) -> None:
        self.assertMaterialError("PDF, DOCX y TXT", "notas.pptx", b"data")

    def test_corrupt_files_get_a_friendly_message(self) -> None:
        self.assertMaterialError("dañado o protegido", "notas.docx", b"not a zip")

    def test_documents_without_text_suggest_ocr(self) -> None:
        self.assertMaterialError("OCR", "escaneo.pdf", pdf(" "))

    def test_whitespace_only_text_is_empty(self) -> None:
        self.assertMaterialError("OCR", "vacio.txt", txt(" ", "\t"))

    def test_long_documents_are_trimmed_instead_of_rejected(self) -> None:
        self.assertLessEqual(len(extract_text("libro.txt", txt("a" * 2000), 1500)), 1500)

    def test_invalid_utf8_is_reported_as_unreadable(self) -> None:
        self.assertMaterialError("dañado", "notas.txt", b"\xff\xfe\xfa")


if __name__ == "__main__":
    unittest.main()
