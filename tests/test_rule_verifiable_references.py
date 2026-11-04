import unittest

from app.domain.validation import verifiable_references
from app.schemas import AssessmentQuestion, WorkshopActivity, WorkshopResponse


def workshop(**over) -> WorkshopResponse:
    data = dict(title="Taller de refuerzo: ciclos", subject="Programación", targetLevel="LOW", summary="Repaso",
                learningObjectives=["Usar for", "Usar while"],
                activities=[WorkshopActivity(title="A{i}", instructions="1. Haz", estimatedMinutes=15) for i in range(3)],
                assessment=[AssessmentQuestion(question="P{i}", options=["a", "b"], correctAnswer="a", explanation="e") for i in range(3)],
                sourceReferences=["Página 2"])
    data.update(over)
    return WorkshopResponse(**data)


MATERIAL = "[Página 1] Introducción\n[Página 2] Ciclos for y while"

class VerifiableReferencesTests(unittest.TestCase):
    def test_accepts_labels_present_in_the_material(self) -> None:
        self.assertIsNone(verifiable_references(workshop(sourceReferences=["Ver página 2, ejemplo"]), MATERIAL))

    def test_rejects_invented_pages(self) -> None:
        self.assertIsNotNone(verifiable_references(workshop(sourceReferences=["Página 12"]), MATERIAL))

    def test_unlabeled_material_needs_the_fragment_reference(self) -> None:
        self.assertIsNone(verifiable_references(workshop(sourceReferences=["Fragmento inicial del material"]), "texto sin etiquetas"))
        self.assertIsNotNone(verifiable_references(workshop(sourceReferences=["Página 1"]), "texto sin etiquetas"))


if __name__ == "__main__":
    unittest.main()
