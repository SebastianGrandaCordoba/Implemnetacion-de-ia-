import unittest

from app.domain.prompt import build_prompt

BASE = {"material_text": "x", "subject": "Patrones de Diseño", "target_level": "MEDIUM", "learning_objective": ""}


class PromptStyleTests(unittest.TestCase):
    def test_guided_work_keeps_the_class_budget(self) -> None:
        prompt = build_prompt(**BASE, activity_styles=("GUIDED",))
        self.assertIn("entre 25 y 50 minutos", prompt)
        self.assertIn("Máximo 100 palabras", prompt)

    def test_code_and_deploy_get_a_staged_challenge(self) -> None:
        prompt = build_prompt(**BASE, activity_styles=("CODE", "DEPLOY"))
        self.assertIn("reto práctico por etapas", prompt)
        self.assertIn("entre 60 y 240 minutos", prompt)
        self.assertIn("Máximo 180 palabras", prompt)
        self.assertIn("esqueleto inicial", prompt)
        self.assertIn("sin publicar claves", prompt)

    def test_quizzes_ignore_activity_types(self) -> None:
        prompt = build_prompt(**BASE, generation_type="QUIZ", activity_styles=("APP",))
        self.assertNotIn("historias de usuario", prompt)
        self.assertIn("entre 25 y 50 minutos", prompt)


if __name__ == "__main__":
    unittest.main()
