from datetime import UTC, datetime, timedelta

from generator.models import Tarif, Trip, User, Weather
from generator.repository.in_memory import InMemoryRepository


def _user(user_id: int, is_taxist: bool = False) -> User:
    return User(
        id=user_id,
        name="Ivan",
        second_name="Petrov",
        count_trips=10,
        rating=4.8,
        phone_number=f"+7000{user_id:07d}",
        gender="male",
        is_taxist=is_taxist,
        balance=100.0,
    )


def _trip(trip_id: int, user_id: int, taxist_id: int) -> Trip:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return Trip(
        id=trip_id,
        user_id=user_id,
        taxist_id=taxist_id,
        tarif=Tarif.ECONOMY,
        weather=Weather.CLEAR,
        start_point="Moscow Center",
        end_point="Moscow Station",
        intermediate_point=None,
        distance=8.5,
        datetime_start=start,
        datetime_end=start + timedelta(minutes=20),
        child_seat=False,
        pets=False,
        rating=5.0,
        cost=500.0,
        taxist_count=8,
    )


def test_in_memory_repository_upserts_users_and_inserts_trip_batch() -> None:
    repository = InMemoryRepository()
    repository.ensure_schema()
    repository.upsert_users([_user(1), _user(2, is_taxist=True)])
    repository.upsert_users([_user(1, is_taxist=True)])
    repository.insert_trips([_trip(1, user_id=1, taxist_id=2)])

    assert len(repository.users) == 2
    assert repository.users[0].is_taxist is True
    assert len(repository.trips) == 1
    assert repository.trips[0].taxist_id == 2
