"""Показать генерацию одного batch поездок без внешней базы данных."""

from __future__ import annotations

import random
import threading
from datetime import UTC, datetime

from generator.config import ClickHouseSettings, GeneratorSettings, Settings
from generator.generation.anomalies import AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.trips import TripBatchGenerator
from generator.repository.in_memory import InMemoryRepository
from generator.retry import RetryPolicy
from generator.service.generator import GeneratorService


def build_service_for_demo() -> tuple[GeneratorService, InMemoryRepository]:
    """Собрать сервис с in-memory repository для демонстрации."""

    settings = Settings(
        generator=GeneratorSettings(batch_size=8, interval_seconds=0.0, seed=42),
        clickhouse=ClickHouseSettings(),
    )
    catalog = TaxiCatalog(
        settings.generator.city_list,
        settings.generator.tariff_list,
        settings.generator.weather_type_list,
        seed=settings.generator.seed,
    )
    batch_generator = TripBatchGenerator(
        catalog=catalog,
        seed=settings.generator.seed,
        anomaly_policy=AnomalyPolicy(
            settings.generator.anomaly_probability,
            settings.generator.anomaly_strength,
            random.Random(settings.generator.seed),
        ),
        origin=datetime(2026, 1, 1, tzinfo=UTC),
    )
    repository = InMemoryRepository()
    service = GeneratorService(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        retry=RetryPolicy(2, 0.0, 1.0, sleep=lambda _: None),
        stop_event=threading.Event(),
        sleep=lambda _: None,
    )
    return service, repository


def main() -> None:
    """Сгенерировать и вывести несколько поездок из памяти."""

    service, repository = build_service_for_demo()
    service.run_once()
    print(f"Сгенерировано поездок: {len(repository.trips)}")
    print(f"Справочников пользователей: {len(repository.users)}")
    for trip in repository.trips[:3]:
        print(
            f"trip={trip.id} user={trip.user_id} taxist={trip.taxist_id} "
            f"cost={trip.cost:.2f} duration={trip.travel_time_seconds}s"
        )


if __name__ == "__main__":
    main()
