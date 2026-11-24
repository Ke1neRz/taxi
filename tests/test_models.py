from datetime import UTC, datetime, timedelta

from generator.models import GeoPoint, Tarif, Trip, Weather


def test_trip_calculates_travel_time() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    trip = Trip(
        id=1,
        user_id=10,
        taxist_id=20,
        tarif_id=2,
        weather_id=1,
        date_start_id=20260101,
        time_start_id=720,
        date_end_id=20260101,
        time_end_id=745,
        start_point=GeoPoint(55.7, 37.6),
        end_point=GeoPoint(55.8, 37.7),
        intermediate_point=(),
        datetime_start=start,
        datetime_end=start + timedelta(minutes=25, seconds=30),
        child_seat=False,
        pets=False,
        rating=5.0,
        cost=850.0,
        distance_km=12.5,
        taxist_count=12,
    )

    assert trip.travel_time_seconds == 1530


def test_reference_records_have_separate_tarif_and_weather_dimensions() -> None:
    tarif = Tarif(2, "comfort", 260.0, 45.0, "Комфорт")
    weather = Weather(1, "ясно", 21.0, "нет", 3.0, 45)

    assert tarif.name == "comfort"
    assert weather.weather == "ясно"
