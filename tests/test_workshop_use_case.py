import unittest

from app.application.workshop_use_case import GenerateWorkshop, WorkshopRequest
from app.schemas import WorkshopResponse


class FakeSettings:
    max_extracted_chars = 5000


class GenerateWorkshopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = FakeSettings()

    def test_coordinates_document_and_generation_ports(self) -> None:
        calls: list[tuple] = []
        expected = WorkshopResponse(
            title="Repaso",
            subject="Programación",
            targetLevel="LOW",
            summary="Conceptos básicos",
            learningObjectives=["Comprender variables", "Aplicar variables"],
            activities=[],
            assessment=[],
            sourceReferences=["Página 1"],
        )

        def extract(filename: str, raw: bytes, max_chars: int) -> str:
            calls.append(("extract", filename, raw, max_chars))
            return "[Página 1] Variables"

        def generate(settings: FakeSettings, **kwargs) -> WorkshopResponse:
            calls.append(("generate", settings, kwargs))
            return expected

        use_case = GenerateWorkshop(extract, generate)
        result = use_case.execute(
            self.settings,
            WorkshopRequest("material.pdf", b"pdf-bytes", "Programación", "LOW", "Repasar"),
        )

        self.assertIs(result, expected)
        self.assertEqual(calls[0], ("extract", "material.pdf", b"pdf-bytes", 5000))
        self.assertEqual(calls[1][0], "generate")
        self.assertEqual(calls[1][2]["material_text"], "[Página 1] Variables")
        self.assertEqual(calls[1][2]["learning_objective"], "Repasar")

    def test_propagates_adapter_errors_to_http_boundary(self) -> None:
        def fail_extract(*_args) -> str:
            raise ValueError("document unreadable")

        use_case = GenerateWorkshop(fail_extract, lambda *_args, **_kwargs: self.fail("should not generate"))
        with self.assertRaisesRegex(ValueError, "document unreadable"):
            use_case.execute(
                self.settings,
                WorkshopRequest("material.pdf", b"bad", "Programación", "LOW", ""),
            )


if __name__ == "__main__":
    unittest.main()
