"""Сервисный цикл генерации и batch-записи поездок такси."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from generator.config import Settings
from generator.generation.trips import TripBatchGenerator
from generator.repository.base import Repository
from generator.retry import RetryError, RetryPolicy

Clock = Callable[[], datetime]
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Вернуть текущее время UTC для начала batch."""

    return datetime.now(UTC)


class GeneratorService:
    """Оркестрировать и надёжно выполнять непрерывный цикл генерации."""

    def __init__(
        self,
        *,
        settings: Settings,
        batch_generator: TripBatchGenerator,
        repository: Repository,
        retry: RetryPolicy,
        stop_event: threading.Event,
        clock: Clock = utc_now,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Создать сервис с внедряемыми временем, ожиданием и хранилищем."""

        self._settings = settings
        self._batch_generator = batch_generator
        self._repository = repository
        self._retry = retry
        self._stop_event = stop_event
        self._clock = clock
        self._sleep = sleep

    def run(self) -> None:
        """Запускать batch-цикл до graceful shutdown или RetryError."""

        self._repository.ensure_schema()
        self._write_users()
        try:
            while not self._stop_event.is_set():
                self._produce_and_store_batch()
        except RetryError as exc:
            logger.error("Запись данных не удалась: %s", exc)
        finally:
            logger.info("Генератор поездок остановлен.")

    def run_once(self) -> None:
        """Инициализировать хранилище и записать ровно один batch."""

        self._repository.ensure_schema()
        self._write_users()
        self._produce_and_store_batch()

    def _write_users(self) -> None:
        """Записать справочник пользователей через retry."""

        self._retry.execute(lambda: self._repository.upsert_users(self._batch_generator.users))

    def _produce_and_store_batch(self) -> None:
        """Создать и записать один batch поездок, соблюдая интервал."""

        started = time.monotonic()
        batch = self._batch_generator.generate_batch(
            self._clock(), self._settings.generator.batch_size
        )
        self._retry.execute(lambda: self._repository.insert_trips(batch))
        logger.info(
            "Записано поездок: %d, аномалий: %d",
            len(batch),
            sum(trip.is_anomaly for trip in batch),
        )
        elapsed = time.monotonic() - started
        self._sleep(max(0.0, self._settings.generator.interval_seconds - elapsed))


def build_service(
    *,
    settings: Settings,
    batch_generator: TripBatchGenerator,
    repository: Repository,
    stop_event: threading.Event,
) -> GeneratorService:
    """Собрать сервис и retry policy из настроек приложения."""

    retry = RetryPolicy(
        max_attempts=settings.generator.retry_max_attempts,
        base_delay=settings.generator.retry_base_delay_seconds,
        max_delay=settings.generator.retry_max_delay_seconds,
        backoff_factor=settings.generator.retry_backoff_factor,
    )
    return GeneratorService(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        retry=retry,
        stop_event=stop_event,
    )
