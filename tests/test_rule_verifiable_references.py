import unittest

from app.domain.validation import verifiable_references
from tests.workshops import workshop

MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class VerifiableReferencesTests(unittest.TestCase):
    def test_accepts_labels_present_in_the_material(self) -> None:
        self.assertIsNone(verifiable_references(workshop(sourceReferences=["Ver página 2, ejemplo"]), MATERIAL))

    def test_accepts_citations_without_accents(self) -> None:
        self.assertIsNone(verifiable_references(workshop(sourceReferences=["Pagina 2"]), MATERIAL))

    def test_rejects_invented_pages(self) -> None:
        self.assertIsNotNone(verifiable_references(workshop(sourceReferences=["Página 12"]), MATERIAL))

    def test_unlabeled_material_needs_the_fragment_reference(self) -> None:
        plain = "texto sin etiquetas"
        self.assertIsNone(verifiable_references(workshop(sourceReferences=["Fragmento inicial del material"]), plain))
        self.assertIsNotNone(verifiable_references(workshop(sourceReferences=["Página 1"]), plain))


if __name__ == "__main__":
    unittest.main()
