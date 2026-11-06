import unittest

from app.domain.prompt import NO_MATERIAL_REFERENCE, build_prompt, shape_for
from app.domain.repair import repair_workshop
from app.domain.request_rules import InvalidRequest, check_material_count, check_teacher_prompt
from app.domain.validation import validate_workshop
from app.schemas import WorkshopActivity
from tests.workshops import workshop

BASE = {"subject": "Bases de Datos", "target_level": "MEDIUM", "learning_objective": ""}


class CustomPromptTests(unittest.TestCase):
    def test_teacher_instructions_lead_a_custom_request(self) -> None:
        prompt = build_prompt(**BASE, material_text="", generation_type="CUSTOM",
                              teacher_prompt="Dos ejercicios de JOIN con una tienda y una pregunta abierta")
        self.assertIn("INDICACIONES DEL DOCENTE", prompt)
        self.assertIn("Dos ejercicios de JOIN", prompt)
        self.assertIn("SIN MATERIAL ADJUNTO", prompt)
        self.assertIn(NO_MATERIAL_REFERENCE, prompt)
        self.assertNotIn("<material>", prompt)

    def test_extra_instructions_do_not_change_the_workshop_counts(self) -> None:
        prompt = build_prompt(**BASE, material_text="[Página 1] SQL", teacher_prompt="Usa ejemplos de fútbol")
        self.assertIn("INDICACIONES ADICIONALES DEL DOCENTE", prompt)
        self.assertIn("entre 3 y 4 actividades", prompt)
        self.assertTrue(prompt.rstrip().endswith("</material>"))

    def test_each_request_type_has_its_shape(self) -> None:
        self.assertEqual(shape_for("QUIZ").questions, (5, 8))
        self.assertEqual(shape_for("custom").activities, (1, 6))
        self.assertEqual(shape_for("anything").activities, (3, 4))


class CustomRuleTests(unittest.TestCase):
    def test_custom_requests_need_a_real_prompt_but_no_material(self) -> None:
        check_material_count(0, optional=True)
        check_teacher_prompt("Un taller de normalización hasta 3FN con dos ejercicios", "CUSTOM")
        with self.assertRaises(InvalidRequest):
            check_teacher_prompt("taller", "CUSTOM")
        with self.assertRaises(InvalidRequest):
            check_material_count(0)
        with self.assertRaises(InvalidRequest):
            check_teacher_prompt("x" * 2001, "WORKSHOP")

    def test_a_custom_workshop_without_material_cites_the_teacher(self) -> None:
        single = [WorkshopActivity(title="Reto", instructions="1. Haz", estimatedMinutes=40)]
        repaired = repair_workshop(workshop(activities=single, assessment=[], sourceReferences=["Libro X p. 4"]), "")
        self.assertEqual(repaired.sourceReferences, [NO_MATERIAL_REFERENCE])
        validate_workshop(repaired, "", generation_type="CUSTOM")

    def test_a_workshop_still_needs_three_activities(self) -> None:
        single = [WorkshopActivity(title="Reto", instructions="1. Haz", estimatedMinutes=40)]
        with self.assertRaises(ValueError):
            validate_workshop(workshop(activities=single), "[Página 2]", generation_type="WORKSHOP")

    def test_new_fields_are_cleaned(self) -> None:
        activity = WorkshopActivity(title="A", instructions="1.", estimatedMinutes=10,
                                    hints=["uno", " ", "uno", "dos", "tres", "cuatro"])
        repaired = repair_workshop(workshop(activities=[activity] * 3, teacherNotes=[" a ", "a", ""]), "[Página 2]")
        self.assertEqual(repaired.activities[0].hints, ["uno", "dos", "tres"])
        self.assertEqual(repaired.teacherNotes, ["a"])


if __name__ == "__main__":
    unittest.main()
