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


class CustomRequestTests(ApiCase):
    PROMPT = "Taller de 4 ejercicios de JOIN con una base de datos de una tienda de barrio"

    def test_custom_requests_work_without_material(self) -> None:
        response = self.post(None, generationType="CUSTOM", teacherPrompt=f"  {self.PROMPT}  ")
        self.assertEqual(response.status_code, 200, response.text)
        request = self.use_case.requests[0]
        self.assertEqual(request.generation_type, "CUSTOM")
        self.assertEqual(request.teacher_prompt, self.PROMPT)
        self.assertEqual(request.filename, "")

    def test_custom_requests_need_instructions(self) -> None:
        self.assertRejected(self.post(None, generationType="CUSTOM", teacherPrompt="hola"), 400, "Describe")

    def test_workshops_without_material_need_a_topic(self) -> None:
        self.assertRejected(self.post(None, learningObjective=""), 400, "indica el tema")
        quiz = self.post(None, generationType="QUIZ", learningObjective="Duda metódica de Descartes")
        self.assertEqual(quiz.status_code, 200)


if __name__ == "__main__":
    unittest.main()
