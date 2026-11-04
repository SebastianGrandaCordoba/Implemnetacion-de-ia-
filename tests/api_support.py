"""Shared helpers for HTTP tests: a fake use case and an authenticated client."""

import os
from unittest import mock

from fastapi.testclient import TestClient

from app.main import app, get_use_case
from app.schemas import WorkshopResponse

TOKEN = "test-token"


def sample_workshop(level: str = "MEDIUM") -> WorkshopResponse:
    return WorkshopResponse(
        title="Taller de fracciones",
        subject="Matemáticas",
        targetLevel=level,
        summary="Practica fracciones equivalentes.",
        learningObjectives=["Comparar fracciones", "Simplificar fracciones"],
        activities=[],
        assessment=[],
        sourceReferences=["[Línea 1]"],
    )


class FakeUseCase:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result or sample_workshop()
        self.error = error
        self.requests = []

    def execute(self, settings, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.result


def client_with(use_case: FakeUseCase, token: str = TOKEN) -> TestClient:
    app.dependency_overrides[get_use_case] = lambda: use_case
    patcher = mock.patch.dict(os.environ, {"AI_SERVICE_TOKEN": token, "GEMINI_API_KEY": "k"})
    patcher.start()
    client = TestClient(app)
    client._patcher = patcher
    return client


def close(client: TestClient) -> None:
    client._patcher.stop()
    app.dependency_overrides.clear()


def form(**overrides: str) -> dict[str, str]:
    data = {"subject": "Matemáticas", "targetLevel": "MEDIUM", "learningObjective": "Fracciones"}
    data.update(overrides)
    return data


def headers(token: str = TOKEN) -> dict[str, str]:
    return {"X-AI-Service-Token": token}
