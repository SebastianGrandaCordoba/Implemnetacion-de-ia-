import unittest

from app import main
from app.domain.rubric import (
    InvalidRubric,
    RubricCriterionDraft,
    RubricLevelText,
    RubricRequest,
    RubricResponse,
    build_rubric_prompt,
    normalized_weights,
    repair_rubric,
    validate_rubric,
)
from tests.api_support import FakeUseCase, client_with, close

LEVELS = RubricLevelText(excellent="Implementa el patrón y lo justifica con un diagrama.",
                         good="Implementa el patrón con una falla menor en la justificación.",
                         basic="Implementa el patrón sin justificarlo.",
                         insufficient="No implementa el patrón o no compila.")


def criterion(name: str, weight: float, levels: RubricLevelText = LEVELS) -> RubricCriterionDraft:
    return RubricCriterionDraft(name=name, description="Qué se evalúa.", weight=weight, levels=levels)


def rubric(*criteria: RubricCriterionDraft) -> RubricResponse:
    return RubricResponse(title=" Rúbrica  Observer ", description="Para el taller.", criteria=list(criteria))


class RubricDomainTests(unittest.TestCase):
    def test_weights_add_up_to_one_hundred(self) -> None:
        self.assertEqual(normalized_weights([1, 1, 1]), [34, 33, 33])
        self.assertEqual(normalized_weights([30, 30, 30]), [34, 33, 33])
        self.assertEqual(normalized_weights([0, 0]), [50, 50])
        self.assertEqual(sum(normalized_weights([12.5, 40, 7, 3])), 100)

    def test_repair_trims_duplicates_and_extra_criteria(self) -> None:
        fixed = repair_rubric(rubric(criterion("Diseño", 50), criterion("diseño", 20), criterion("Código", 30),
                                     criterion("Pruebas", 10), criterion("Informe", 10)), expected=3)
        self.assertEqual([c.name for c in fixed.criteria], ["Diseño", "Código", "Pruebas"])
        self.assertEqual(sum(c.weight for c in fixed.criteria), 100)
        self.assertEqual(fixed.title, "Rúbrica Observer")
        validate_rubric(fixed)

    def test_levels_must_be_distinct_and_filled(self) -> None:
        same = RubricLevelText(excellent="Lo hace bien", good="Lo hace bien", basic="Lo hace bien", insufficient="No")
        with self.assertRaises(InvalidRubric):
            validate_rubric(repair_rubric(rubric(criterion("A", 1), criterion("B", 1), criterion("C", 1, same)), 3))
        with self.assertRaises(InvalidRubric):
            validate_rubric(rubric(criterion("A", 100)))

    def test_prompt_fences_the_activity_and_keeps_teacher_notes(self) -> None:
        prompt = build_rubric_prompt(RubricRequest(subject="Patrones", activity="Implementar Observer en Java",
                                                   criteriaCount=5, teacherPrompt="Incluye trabajo en equipo"))
        self.assertIn("Exactamente 5 criterios", prompt)
        self.assertIn("Incluye trabajo en equipo", prompt)
        self.assertTrue(prompt.rstrip().endswith("</actividad>"))


class RubricApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calls: list[RubricRequest] = []

        def fake(request: RubricRequest) -> RubricResponse:
            self.calls.append(request)
            return rubric(criterion("Diseño", 40), criterion("Código", 40), criterion("Informe", 20))

        self.client = client_with(FakeUseCase())
        main.app.dependency_overrides[main.get_rubric_generator] = lambda: fake

    def tearDown(self) -> None:
        close(self.client)

    def post(self, body: dict, token: str | None = "test-token"):
        headers = {"X-AI-Service-Token": token} if token else {}
        return self.client.post("/generate-rubric", json=body, headers=headers)

    def test_returns_the_rubric(self) -> None:
        response = self.post({"subject": "Patrones", "activity": "Taller de Observer con entrega en GitHub"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["criteria"]), 3)
        self.assertEqual(self.calls[0].criteriaCount, 4)

    def test_requires_the_backend_token(self) -> None:
        response = self.post({"subject": "Patrones", "activity": "Taller de Observer"}, token=None)
        self.assertEqual(response.status_code, 401)

    def test_rejects_short_activities_and_odd_counts(self) -> None:
        self.assertEqual(self.post({"subject": "Patrones", "activity": "corta"}).status_code, 422)
        many = {"subject": "Patrones", "activity": "Taller de Observer largo", "criteriaCount": 9}
        self.assertEqual(self.post(many).status_code, 422)
