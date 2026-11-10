import unittest

from app.application.workshop_use_case import GenerateWorkshop, WorkshopRequest
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

        def extract(filename: str, raw: bytes, max_chars: int, focus: str = "") -> str:
            budgets.append(max_chars)
            return raw.decode() * 10

        def generate(_settings, **kwargs):
            seen.update(kwargs)
            return response()

        GenerateWorkshop(extract, generate).execute(Settings(), WorkshopRequest(
            "a.txt", b"uno ", "Física", "LOW", "", additional_materials=(("b.txt", b"dos "),)))
        self.assertEqual(budgets[0], 600)
        self.assertLess(budgets[1], 1200)
        self.assertIn("[Material 1: a.txt]", seen["material_text"])
        self.assertIn("[Material 2: b.txt]", seen["material_text"])

    def test_the_first_long_material_does_not_crowd_out_the_others(self) -> None:
        seen: dict = {}

        def generate(_settings, **kwargs):
            seen.update(kwargs)
            return response()

        use_case = GenerateWorkshop(lambda name, raw, max_chars, focus="": "x" * (max_chars - 100), generate)
        request = WorkshopRequest("a.txt", b"1", "F", "LOW", "", additional_materials=(("b.txt", b"2"),))
        use_case.execute(Settings(), request)
        self.assertIn("[Material 2: b.txt]", seen["material_text"])

    def test_the_request_decides_which_pages_matter(self) -> None:
        focuses: list[str] = []

        def extract(name, raw, max_chars, focus=""):
            focuses.append(focus)
            return "[Página 1] texto"

        request = WorkshopRequest("a.pdf", b"1", "Álgebra", "LOW", "Gauss", teacher_prompt="determinantes")
        GenerateWorkshop(extract, lambda *_a, **_k: response()).execute(Settings(), request)
        self.assertIn("Gauss", focuses[0])
        self.assertIn("determinantes", focuses[0])


if __name__ == "__main__":
    unittest.main()
