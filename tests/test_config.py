from generator.config import ClickHouseSettings, GeneratorSettings


def test_taxi_defaults() -> None:
    generator = GeneratorSettings()
    clickhouse = ClickHouseSettings()

    assert generator.city_list == ["Moscow", "Kazan", "Sochi", "Irkutsk"]
    assert generator.tariff_list == ["economy", "comfort", "business"]
    assert clickhouse.database == "taxi"
