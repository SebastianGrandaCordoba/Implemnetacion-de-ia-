import unittest

from app.domain.validation import has_references
from tests.workshops import workshop

MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class HasReferencesTests(unittest.TestCase):
    def test_requires_at_least_one_reference(self) -> None:
        self.assertIsNone(has_references(workshop(), MATERIAL))
        self.assertIsNotNone(has_references(workshop(sourceReferences=[]), MATERIAL))


if __name__ == "__main__":
    unittest.main()
