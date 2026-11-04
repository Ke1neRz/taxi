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


def _service() -> tuple[GeneratorService, InMemoryRepository]:
    settings = Settings(
        generator=GeneratorSettings(batch_size=4, interval_seconds=0.0, seed=5),
        clickhouse=ClickHouseSettings(),
    )
    catalog = TaxiCatalog(
        settings.generator.city_list,
        settings.generator.tariff_list,
        settings.generator.weather_type_list,
        user_count=20,
        seed=settings.generator.seed,
    )
    batch_generator = TripBatchGenerator(
        catalog=catalog,
        seed=settings.generator.seed,
        anomaly_policy=AnomalyPolicy(0.0, 2.0, random.Random(5)),
        origin=datetime(2026, 1, 1, tzinfo=UTC),
    )
    repository = InMemoryRepository()
    service = GeneratorService(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        retry=RetryPolicy(2, 0.0, 1.0, sleep=lambda _: None),
        stop_event=threading.Event(),
        clock=lambda: datetime(2026, 1, 5, 8, tzinfo=UTC),
        sleep=lambda _: None,
    )
    return service, repository


def test_run_once_writes_users_and_trip_batch() -> None:
    service, repository = _service()

    service.run_once()

    assert len(repository.users) == 20
    assert len(repository.trips) == 4
    driver_ids = {user.id for user in repository.users if user.is_taxist}
    assert all(trip.taxist_id in driver_ids for trip in repository.trips)
