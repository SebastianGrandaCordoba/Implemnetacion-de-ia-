"""Decorators around the WorkshopGenerator port (Decorator pattern).

Each wrapper has the same call signature as the generator it wraps, so the
composition root can stack them without the use case noticing.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from app.application.ports import WorkshopGenerator
from app.domain.errors import is_retryable
from app.gemini_service import GeminiGenerationError
from app.schemas import WorkshopResponse

logger = logging.getLogger(__name__)


class RetryingWorkshopGenerator:
    """Retries rate-limit and timeout failures with exponential backoff."""

    def __init__(
        self,
        inner: WorkshopGenerator,
        attempts: int = 2,
        base_delay: float = 1.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._inner = inner
        self._attempts = max(1, attempts)
        self._base_delay = base_delay
        self._sleep = sleep

    def __call__(self, settings, **request) -> WorkshopResponse:
        for attempt in range(1, self._attempts + 1):
            try:
                return self._inner(settings, **request)
            except GeminiGenerationError as exc:
                if attempt == self._attempts or not is_retryable(str(exc)):
                    raise
                delay = self._base_delay * 2 ** (attempt - 1)
                logger.info("Retrying workshop generation in %.1fs (attempt %d)", delay, attempt + 1)
                self._sleep(delay)
        raise AssertionError("unreachable")
