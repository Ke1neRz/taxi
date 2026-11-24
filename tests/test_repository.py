from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from generator.config import ClickHouseSettings
from generator.models import GeoPoint, Trip, User
from generator.repository.clickhouse import ClickHouseRepository
from generator.repository.in_memory import InMemoryRepository


def _user(user_id: int) -> User:
    return User(
        id=user_id,
        name="Ivan",
        second_name="Petrov",
        count_trips=10,
        rating=4.8,
        phone_number=f"+7000{user_id:07d}",
        gender="male",
    )


def _trip(trip_id: int, user_id: int, taxist_id: int) -> Trip:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return Trip(
        id=trip_id,
        user_id=user_id,
        taxist_id=taxist_id,
        tarif_id=1,
        weather_id=1,
        date_start_id=20260101,
        time_start_id=0,
        date_end_id=20260101,
        time_end_id=20,
        start_point=GeoPoint(55.7, 37.6),
        end_point=GeoPoint(55.8, 37.7),
        intermediate_point=(),
        datetime_start=start,
        datetime_end=start + timedelta(minutes=20),
        child_seat=False,
        pets=False,
        rating=5.0,
        cost=500.0,
        distance_km=8.5,
        taxist_count=8,
    )


def test_in_memory_repository_upserts_users_and_inserts_trip_batch() -> None:
    repository = InMemoryRepository()
    repository.ensure_schema()
    repository.upsert_users([_user(1), _user(2)])
    repository.insert_trips([_trip(1, user_id=1, taxist_id=2)])

    assert len(repository.users) == 2
    assert repository.users[0].id == 1
    assert len(repository.trips) == 1
    assert repository.max_timestamp() == repository.trips[0].datetime_start
    assert repository.trips[0].taxist_id == 2


def test_clickhouse_repository_creates_four_materialized_views() -> None:
    client = MagicMock()

    with patch(
        "generator.repository.clickhouse.clickhouse_connect.get_client",
        return_value=client,
    ):
        repository = ClickHouseRepository(ClickHouseSettings(database="taxi"))
        repository.ensure_schema()

    commands = [call.args[0] for call in client.command.call_args_list]
    for table_name in (
        "trips_by_hour",
        "trips_by_weekday",
        "trips_by_weather",
        "trips_by_tarif",
    ):
        assert any(f"{table_name}" in command for command in commands)
        assert any("MATERIALIZED VIEW" in command for command in commands)
    assert sum("AggregatingMergeTree" in command for command in commands) == 4


def test_clickhouse_repository_inserts_trip_batch_once() -> None:
    client = MagicMock()

    with patch(
        "generator.repository.clickhouse.clickhouse_connect.get_client",
        return_value=client,
    ):
        repository = ClickHouseRepository(ClickHouseSettings(database="taxi"))
        repository.insert_trips([_trip(1, user_id=1, taxist_id=2)])

    client.insert.assert_called_once()
    table_name, rows, = client.insert.call_args.args
    assert table_name == "taxi.trips"
    assert len(rows) == 1
