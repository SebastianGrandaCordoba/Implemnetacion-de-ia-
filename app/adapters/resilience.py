"""Decorators around the WorkshopGenerator port (Decorator pattern).

Each wrapper has the same call signature as the generator it wraps, so the
composition root can stack them without the use case noticing.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
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
        budget_seconds: float = 25,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._inner = inner
        self._attempts = max(1, attempts)
        self._base_delay = base_delay
        self._sleep = sleep
        self._budget = budget_seconds
        self._clock = clock

    def __call__(self, settings, **request) -> WorkshopResponse:
        started = self._clock()
        for attempt in range(1, self._attempts + 1):
            try:
                return self._inner(settings, **request)
            except GeminiGenerationError as exc:
                delay = self._base_delay * 2 ** (attempt - 1)
                # Only retry while a second full generation still fits before the backend gives up.
                late = self._clock() - started + delay > self._budget
                if attempt == self._attempts or late or not is_retryable(str(exc)):
                    raise
                logger.info("Retrying workshop generation in %.1fs (attempt %d)", delay, attempt + 1)
                self._sleep(delay)
        raise AssertionError("unreachable")


class CachedWorkshopGenerator:
    """Remembers recent results so regenerating the same request does not spend quota."""

    def __init__(
        self,
        inner: WorkshopGenerator,
        max_entries: int = 32,
        ttl_seconds: float = 1800,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._inner = inner
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, WorkshopResponse]] = OrderedDict()

    @staticmethod
    def key(request: dict[str, str]) -> str:
        digest = hashlib.sha256()
        for name in sorted(request):
            digest.update(name.encode())
            digest.update(b"\0")
            digest.update(str(request[name]).encode())
            digest.update(b"\1")
        return digest.hexdigest()

    def __call__(self, settings, **request) -> WorkshopResponse:
        if self._max_entries <= 0:
            return self._inner(settings, **request)
        key = self.key(request)
        now = self._clock()
        cached = self._entries.get(key)
        if cached and now - cached[0] < self._ttl:
            self._entries.move_to_end(key)
            return cached[1].model_copy(deep=True)
        result = self._inner(settings, **request)
        self._entries[key] = (now, result)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)
        return result.model_copy(deep=True)

    def __len__(self) -> int:
        return len(self._entries)


class TimedWorkshopGenerator:
    """Logs how long each generation takes, which helps tune GEMINI_TIMEOUT_MS."""

    def __init__(self, inner: WorkshopGenerator, clock: Callable[[], float] = time.perf_counter) -> None:
        self._inner = inner
        self._clock = clock
        self.last_duration: float | None = None

    def __call__(self, settings, **request) -> WorkshopResponse:
        started = self._clock()
        try:
            return self._inner(settings, **request)
        finally:
            self.last_duration = self._clock() - started
            logger.info(
                "Generation %s took %.2fs", request.get("generation_type", "WORKSHOP"), self.last_duration
            )
