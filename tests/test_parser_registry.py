import unittest

from app.document_parser import EXTRACTORS, SUPPORTED_EXTENSIONS, normalize


class RegistryTests(unittest.TestCase):
    def test_supported_extensions_match_the_registry(self) -> None:
        self.assertEqual(SUPPORTED_EXTENSIONS, (".pdf", ".docx", ".txt"))
        self.assertTrue(all(callable(extractor) for extractor in EXTRACTORS.values()))

    def test_normalize_trims_and_drops_blank_lines(self) -> None:
        self.assertEqual(normalize("  a  \n\n\t\n b"), "a\nb")


if __name__ == "__main__":
    unittest.main()
