from datetime import UTC, datetime, timedelta

from generator.generation.seasonality import (
    demand_factor,
    diurnal_demand_factor,
    trend_factor,
    weekly_demand_factor,
)


def _dt(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 1, 5, hour, tzinfo=UTC) + timedelta(days=day)


def test_demand_is_higher_during_commute_peaks() -> None:
    assert diurnal_demand_factor(_dt(0, 8)) > diurnal_demand_factor(_dt(0, 3))
    assert diurnal_demand_factor(_dt(0, 18)) > diurnal_demand_factor(_dt(0, 3))


def test_weekdays_have_higher_baseline_than_weekends() -> None:
    monday = datetime(2026, 1, 5, 12, tzinfo=UTC)
    saturday = datetime(2026, 1, 10, 12, tzinfo=UTC)

    assert weekly_demand_factor(monday) > weekly_demand_factor(saturday)


def test_trend_grows_but_is_bounded() -> None:
    origin = _dt(0)

    assert trend_factor(_dt(30), origin) > trend_factor(origin, origin)
    assert trend_factor(_dt(1000), origin) == trend_factor(_dt(365), origin)


def test_combined_demand_is_positive() -> None:
    origin = _dt(0)

    assert demand_factor(_dt(10, 8), origin) > 0.0
