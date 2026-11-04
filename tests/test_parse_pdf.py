import unittest

from app.document_parser import extract_text
from tests.fixtures import pdf


class PdfParsingTests(unittest.TestCase):
    def test_each_page_is_labeled(self) -> None:
        text = extract_text("guia.pdf", pdf("Ecosistemas", "Cadenas troficas"), 5000)
        self.assertIn("[Página 1]", text)
        self.assertIn("Ecosistemas", text)
        self.assertIn("[Página 2]", text)
        self.assertIn("Cadenas troficas", text)

    def test_empty_pages_are_skipped(self) -> None:
        text = extract_text("guia.pdf", pdf("Inicio", " ", "Cierre"), 5000)
        self.assertNotIn("[Página 2]", text)
        self.assertIn("[Página 3]", text)


if __name__ == "__main__":
    unittest.main()
