"""Сервисный цикл генерации и batch-записи поездок такси."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from generator.config import Settings
from generator.generation.trips import TripBatchGenerator
from generator.models import Trip
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
        """Выполнить бэкфилл и затем непрерывную realtime-гнерацию."""

        self._repository.ensure_schema()
        self._write_users()
        try:
            self._backfill()
            self._run_realtime()
        except RetryError as exc:
            logger.error("Запись данных не удалась: %s", exc)
        finally:
            logger.info("Генератор поездок остановлен.")

    def _backfill(self) -> None:
        """Заполнить исторический диапазон до текущего времени."""

        settings = self._settings.generator
        now = self._clock()
        last = self._repository.max_timestamp()
        next_timestamp = (
            last + timedelta(seconds=settings.backfill_step_seconds)
            if last is not None and last >= settings.backfill_start_dt
            else settings.backfill_start_dt
        )
        while next_timestamp <= now and not self._stop_event.is_set():
            remaining = (now - next_timestamp).total_seconds()
            count = min(settings.batch_size, int(remaining // settings.backfill_step_seconds) + 1)
            batch = self._batch_generator.generate_sequence(
                next_timestamp, count, settings.backfill_step_seconds
            )
            self._store(batch)
            next_timestamp = batch[-1].datetime_start + timedelta(
                seconds=settings.backfill_step_seconds
            )

    def _run_realtime(self) -> None:
        """Дописывать поездки с realtime-шагом после завершения бэкфилла."""

        settings = self._settings.generator
        last = self._repository.max_timestamp()
        next_timestamp = (
            last + timedelta(seconds=settings.realtime_step_seconds)
            if last is not None
            else self._clock()
        )
        while not self._stop_event.is_set():
            now = self._clock()
            if next_timestamp > now:
                self._sleep(min(1.0, (next_timestamp - now).total_seconds()))
                continue
            batch = self._batch_generator.generate_sequence(
                next_timestamp, 1, settings.realtime_step_seconds
            )
            self._store(batch)
            next_timestamp += timedelta(seconds=settings.realtime_step_seconds)
            self._sleep(settings.realtime_step_seconds)

    def _store(self, batch: list[Trip]) -> None:
        """Записать date/time dimensions и batch поездок через retry-policy."""

        dates = {}
        times = {}
        for trip in batch:
            date_dimension, time_dimension = self._batch_generator.dimensions_for(
                trip.datetime_start
            )
            dates[date_dimension.id] = date_dimension
            times[time_dimension.id] = time_dimension
        self._retry.execute(lambda: self._repository.upsert_dates(list(dates.values())))
        self._retry.execute(lambda: self._repository.upsert_times(list(times.values())))
        self._retry.execute(lambda: self._repository.insert_trips(batch))

    def run_once(self) -> None:
        """Инициализировать хранилище и записать ровно один batch."""

        self._repository.ensure_schema()
        self._write_users()
        self._produce_and_store_batch()

    def _write_users(self) -> None:
        """Записать статические справочники через retry."""

        self._retry.execute(lambda: self._repository.upsert_users(self._batch_generator.users))
        self._retry.execute(
            lambda: self._repository.upsert_taxists(self._batch_generator.taxists)
        )
        self._retry.execute(
            lambda: self._repository.upsert_tarifs(self._batch_generator.tarifs)
        )
        self._retry.execute(
            lambda: self._repository.upsert_weathers(self._batch_generator.weathers)
        )

    def _produce_and_store_batch(self) -> None:
        """Создать и записать один batch поездок, соблюдая интервал."""

        started = time.monotonic()
        batch = self._batch_generator.generate_batch(
            self._clock(), self._settings.generator.batch_size
        )
        dates = {}
        times = {}
        for trip in batch:
            date_dimension, time_dimension = self._batch_generator.dimensions_for(
                trip.datetime_start
            )
            dates[date_dimension.id] = date_dimension
            times[time_dimension.id] = time_dimension
        self._retry.execute(lambda: self._repository.upsert_dates(list(dates.values())))
        self._retry.execute(lambda: self._repository.upsert_times(list(times.values())))
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
