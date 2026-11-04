"""Final touches applied to every generated workshop before it leaves the service."""

from app.schemas import WorkshopResponse


def finalize_workshop(workshop: WorkshopResponse, *, subject: str, target_level: str, quiz: bool) -> WorkshopResponse:
    """Trusts the teacher's subject and level over the model's, and labels quizzes clearly."""
    updates: dict[str, str] = {"subject": subject, "targetLevel": target_level}
    if quiz and not workshop.title.lower().startswith("quiz"):
        updates["title"] = f"Quiz breve: {subject}"
    return workshop.model_copy(update=updates)
