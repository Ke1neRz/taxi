import random
from datetime import UTC, datetime

import pytest

from generator.generation.anomalies import AnomalyKind, AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.trips import TripBatchGenerator


def _generator(policy: AnomalyPolicy, seed: int = 12) -> TripBatchGenerator:
    catalog = TaxiCatalog(
        cities=["Moscow", "Kazan"],
        tariffs=["economy", "comfort", "business"],
        weather_types=["clear", "rain"],
        user_count=30,
        seed=seed,
    )
    return TripBatchGenerator(
        catalog=catalog,
        seed=seed,
        anomaly_policy=policy,
        origin=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_trip_batch_contains_human_readable_metrics_and_links() -> None:
    generator = _generator(AnomalyPolicy(0.0, 2.0, random.Random(12)))

    batch = generator.generate_batch(datetime(2026, 1, 5, 8, tzinfo=UTC), 25)
    driver_ids = {user.id for user in generator.users if user.is_taxist}

    assert len(batch) == 25
    assert [trip.id for trip in batch] == list(range(1, 26))
    assert all(trip.user_id in {user.id for user in generator.users} for trip in batch)
    assert all(trip.taxist_id in driver_ids for trip in batch)
    assert all(2.5 <= trip.distance <= 33.1 for trip in batch)
    assert all(trip.cost > 0.0 for trip in batch)
    assert all(0 < trip.travel_time_seconds < 7200 for trip in batch)
    assert all(1 <= trip.rating <= 5 for trip in batch)
    assert all(not trip.is_anomaly for trip in batch)


def test_trip_batch_is_reproducible_with_seed() -> None:
    first = _generator(AnomalyPolicy(0.2, 2.0, random.Random(12)))
    second = _generator(AnomalyPolicy(0.2, 2.0, random.Random(12)))
    at = datetime(2026, 1, 5, 18, tzinfo=UTC)

    assert first.generate_batch(at, 10) == second.generate_batch(at, 10)


def test_long_trip_anomaly_increases_duration() -> None:
    class FixedPolicy:
        strength = 3.0

        def decide(self) -> AnomalyKind:
            return AnomalyKind.LONG_TRIP

    normal = _generator(AnomalyPolicy(0.0, 3.0, random.Random(12)), seed=12)
    anomalous = _generator(FixedPolicy(), seed=12)  # type: ignore[arg-type]
    at = datetime(2026, 1, 5, 12, tzinfo=UTC)

    normal_trip = normal.generate_batch(at, 1)[0]
    anomalous_trip = anomalous.generate_batch(at, 1)[0]

    assert anomalous_trip.is_anomaly is True
    assert anomalous_trip.travel_time_seconds > normal_trip.travel_time_seconds


def test_batch_size_must_be_positive() -> None:
    generator = _generator(AnomalyPolicy(0.0, 2.0, random.Random(1)))

    with pytest.raises(ValueError):
        generator.generate_batch(datetime.now(UTC), 0)
