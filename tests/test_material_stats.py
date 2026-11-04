import unittest

from app.domain.material_stats import PREVIEW_CHARS, describe


class DescribeTests(unittest.TestCase):
    def test_counts_citation_units_by_kind(self) -> None:
        stats = describe("guia.pdf", "[Página 1]\nHola mundo\n\n[Página 2]\nAdiós")
        self.assertEqual(stats.units, {"Página": 2})
        self.assertEqual(stats.words, 3)

    def test_preview_hides_labels_and_is_bounded(self) -> None:
        stats = describe("t.txt", "[Línea 1] " + "palabra " * 200)
        self.assertFalse(stats.preview.startswith("["))
        self.assertLessEqual(len(stats.preview), PREVIEW_CHARS)

    def test_token_estimate_is_at_least_one(self) -> None:
        self.assertEqual(describe("t.txt", "ab").estimated_tokens, 1)
        self.assertEqual(describe("t.txt", "a" * 400).estimated_tokens, 100)


if __name__ == "__main__":
    unittest.main()
