"""Повторные попытки с экспоненциальной задержкой для отказоустойчивости."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Ошибка, возникающая после исчерпания всех попыток."""


class RetryPolicy:
    """Выполнить операцию с ограниченным числом повторов и backoff."""

    def __init__(
        self,
        max_attempts: int,
        base_delay: float,
        max_delay: float,
        backoff_factor: float = 2.0,
        jitter: float = 0.1,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Создать политику повторов с проверенными параметрами задержки."""

        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if base_delay < 0.0 or max_delay < 0.0:
            raise ValueError("delays must not be negative")
        if backoff_factor < 1.0:
            raise ValueError("backoff_factor must be at least 1")
        if jitter < 0.0:
            raise ValueError("jitter must not be negative")
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._backoff_factor = backoff_factor
        self._jitter = jitter
        self._sleep = sleep

    def execute(self, fn: Callable[[], T]) -> T:
        """Выполнить функцию и повторить её после временной ошибки."""

        for attempt in range(1, self._max_attempts + 1):
            try:
                return fn()
            except Exception as exc:
                if attempt >= self._max_attempts:
                    raise RetryError(
                        f"операция не выполнена после {self._max_attempts} попыток"
                    ) from exc
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "Ошибка попытки %d/%d (%s); повтор через %.2fs",
                    attempt,
                    self._max_attempts,
                    exc,
                    delay,
                )
                self._sleep(delay)
        raise AssertionError("retry loop must return or raise")

    def _backoff_delay(self, attempt: int) -> float:
        """Рассчитать ограниченную экспоненциальную задержку с jitter."""

        base = self._base_delay * (self._backoff_factor ** (attempt - 1))
        capped = min(base, self._max_delay)
        return capped * (1.0 + random.uniform(-self._jitter, self._jitter))
