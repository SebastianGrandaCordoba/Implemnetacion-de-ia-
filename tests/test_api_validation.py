import unittest

from tests.api_case import ApiCase, txt


class FormValidationTests(ApiCase):
    def test_unknown_level(self) -> None:
        self.assertRejected(self.post([txt()], targetLevel="EXPERTO"), 400, "LOW, MEDIUM o HIGH")

    def test_unknown_generation_type(self) -> None:
        self.assertRejected(self.post([txt()], generationType="EXAM"), 400, "WORKSHOP o QUIZ")

    def test_objective_too_long(self) -> None:
        self.assertRejected(self.post([txt()], learningObjective="a" * 1001), 400, "1000")

    def test_missing_subject_is_a_validation_error(self) -> None:
        response = self.client.post("/api/v1/workshops/generate", data={"targetLevel": "LOW"},
                                    files=[txt()], headers={"X-AI-Service-Token": "test-token"})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
