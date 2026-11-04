import unittest

from app.application.workshop_use_case import GenerateWorkshop, WorkshopRequest
from app.document_parser import MaterialError
from app.schemas import WorkshopResponse


class Settings:
    max_extracted_chars = 1200


def response() -> WorkshopResponse:
    return WorkshopResponse(title="t", subject="s", targetLevel="LOW", summary="r", learningObjectives=["a", "b"],
                            activities=[], assessment=[], sourceReferences=["Fragmento inicial del material"])


class MultipleMaterialsTests(unittest.TestCase):
    def test_labels_each_material_and_shares_the_character_budget(self) -> None:
        budgets: list[int] = []
        seen: dict = {}

        def extract(filename: str, raw: bytes, max_chars: int) -> str:
            budgets.append(max_chars)
            return raw.decode() * 10

        def generate(_settings, **kwargs):
            seen.update(kwargs)
            return response()

        GenerateWorkshop(extract, generate).execute(Settings(), WorkshopRequest(
            "a.txt", b"uno ", "Física", "LOW", "", additional_materials=(("b.txt", b"dos "),)))
        self.assertEqual(budgets[0], 1200)
        self.assertLess(budgets[1], 1200)
        self.assertIn("[Material 1: a.txt]", seen["material_text"])
        self.assertIn("[Material 2: b.txt]", seen["material_text"])

    def test_stops_when_materials_exhaust_the_budget(self) -> None:
        use_case = GenerateWorkshop(lambda name, raw, max_chars: "x" * (max_chars - 100), lambda *_a, **_k: response())
        with self.assertRaisesRegex(MaterialError, "demasiado texto"):
            request = WorkshopRequest("a.txt", b"1", "F", "LOW", "", additional_materials=(("b.txt", b"2"),))
            use_case.execute(Settings(), request)


if __name__ == "__main__":
    unittest.main()
