"""Проверить создание схемы и batch-запись поездок в ClickHouse."""

from __future__ import annotations

import random
import threading
from datetime import UTC, datetime

from _clickhouse import client, is_ready

from generator.config import get_settings
from generator.generation.anomalies import AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.trips import TripBatchGenerator
from generator.repository.clickhouse import ClickHouseRepository
from generator.service.generator import build_service


def main() -> None:
    """Создать схему, записать один batch и проверить факт в таблице trips."""

    settings = get_settings()
    clickhouse = settings.clickhouse
    print(f"Проверяю ClickHouse: {clickhouse.host}:{clickhouse.port}")
    if not is_ready(clickhouse):
        print("ClickHouse недоступен. Запустите `docker compose up -d clickhouse`.")
        return

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
    repository = ClickHouseRepository(clickhouse)
    service = build_service(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        stop_event=threading.Event(),
    )
    service.run_once()

    result = client(clickhouse).query(
        f"SELECT count(), min(datetime_start), max(datetime_start) "
        f"FROM {clickhouse.database}.trips"
    ).result_rows[0]
    print(f"Записано поездок: {result[0]}")
    print(f"Диапазон времени: {result[1]} - {result[2]}")


if __name__ == "__main__":
    main()
