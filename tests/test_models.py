from datetime import datetime, timedelta, timezone

from generator.models import Tarif, Trip, User, Weather


def test_trip_calculates_travel_time() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    trip = Trip(
        id=1,
        user_id=10,
        taxist_id=20,
        tarif=Tarif.COMFORT,
        weather=Weather.CLEAR,
        start_point="A",
        end_point="B",
        intermediate_point=None,
        distance=12.5,
        datetime_start=start,
        datetime_end=start + timedelta(minutes=25, seconds=30),
        child_seat=False,
        pets=False,
        rating=5.0,
        cost=850.0,
        taxist_count=12,
    )

    assert trip.travel_time_seconds == 1530


def test_taxist_is_a_user() -> None:
    driver = User(
        id=20,
        name="Ivan",
        second_name="Petrov",
        count_trips=100,
        rating=4.9,
        phone_number="+70000000000",
        gender="male",
        is_taxist=True,
        balance=1000.0,
    )

    assert driver.is_taxist is True
