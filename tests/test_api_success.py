import unittest

from tests.api_case import ApiCase, txt


class SuccessTests(ApiCase):
    def test_returns_the_generated_workshop(self) -> None:
        response = self.post([txt()])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["title"], "Taller de fracciones")

    def test_request_is_normalized_before_reaching_the_use_case(self) -> None:
        self.post([txt()], subject="  Biología ", targetLevel="bajo", generationType="quiz",
                  learningObjective="  Células  ")
        request = self.use_case.requests[0]
        self.assertEqual(request.subject, "Biología")
        self.assertEqual(request.target_level, "LOW")
        self.assertEqual(request.generation_type, "QUIZ")
        self.assertEqual(request.learning_objective, "Células")


class ActivityStyleRequestTests(ApiCase):
    def test_activity_types_reach_the_use_case(self) -> None:
        self.post([txt()], activityStyles="code, deploy")
        self.assertEqual(self.use_case.requests[0].activity_styles, ("CODE", "DEPLOY"))

    def test_unknown_activity_types_are_rejected(self) -> None:
        self.assertRejected(self.post([txt()], activityStyles="DANCE"), 400, "no reconocido")


if __name__ == "__main__":
    unittest.main()
