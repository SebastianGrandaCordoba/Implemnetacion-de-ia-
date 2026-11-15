# Workshop quality rules

Every generated workshop goes through `validate_workshop` before reaching the teacher. If a rule fails,
the service answers 502 with the rule's message and the backend can ask for another attempt.

| Rule | What it requires |
| --- | --- |
| `activity_count` | Between 3 and 5 activities |
| `question_count` | Between 3 and 5 assessment questions |
| `objective_count` | Between 2 and 4 learning objectives |
| `activity_minutes` | Each activity lasts between 5 and 60 minutes |
| `has_references` | At least one reference to the material |
| `verifiable_references` | The cited pages, sections or lines exist in the material |
| `option_count` | Closed questions have between 2 and 5 distinct options |
| `answers_in_options` | The correct answer of a closed question is among its options |
| `distinct_questions` | No repeated questions |

To add a rule: write a function `(workshop, material_text) -> str | None`, test it in
`tests/test_rule_<name>.py` and add it to `RULES`.
