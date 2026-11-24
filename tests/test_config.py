from generator.config import ClickHouseSettings, GeneratorSettings


def test_taxi_defaults() -> None:
    generator = GeneratorSettings()
    clickhouse = ClickHouseSettings()

    assert generator.city_list == ["Moscow", "Kazan", "Sochi", "Irkutsk"]
    assert generator.tariff_list == ["economy", "comfort", "business"]
    assert clickhouse.database == "taxi"


def test_backfill_settings_are_parsed() -> None:
    generator = GeneratorSettings(
        backfill_start="2026-01-01T00:00:00",
        backfill_step_seconds=60.0,
        realtime_step_seconds=1.0,
    )

    assert generator.backfill_start_dt.year == 2026
    assert generator.backfill_step_seconds == 60.0
    assert generator.realtime_step_seconds == 1.0
