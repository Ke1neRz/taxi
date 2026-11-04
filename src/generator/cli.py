"""Командная точка входа генератора такси."""

from __future__ import annotations

import argparse
import logging
import random
import signal
import threading
from collections.abc import Sequence
from datetime import UTC, datetime

from generator.config import get_settings
from generator.generation.anomalies import AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.trips import TripBatchGenerator
from generator.repository.base import Repository
from generator.repository.clickhouse import ClickHouseRepository
from generator.repository.in_memory import InMemoryRepository
from generator.service.generator import build_service


def _setup_logging(level: str) -> None:
    """Настроить единый формат логов генератора."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def _install_signal_handlers(stop_event: threading.Event) -> None:
    """Преобразовать SIGINT и SIGTERM в событие graceful shutdown."""

    def handler(signum: int, frame: object) -> None:
        del signum, frame
        stop_event.set()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Разобрать параметры выбора repository и режима запуска."""

    parser = argparse.ArgumentParser(prog="taxi-generator")
    parser.add_argument("--once", action="store_true", help="записать один batch и выйти")
    parser.add_argument(
        "--repository", choices=("in-memory", "clickhouse"), default="in-memory"
    )
    return parser.parse_args(argv)


def _make_repository(kind: str) -> Repository:
    """Создать выбранную реализацию repository."""

    if kind == "clickhouse":
        return ClickHouseRepository(get_settings().clickhouse)
    return InMemoryRepository()


def main(argv: Sequence[str] | None = None) -> int:
    """Собрать зависимости и запустить генератор поездок."""

    args = _parse_args(argv)
    settings = get_settings()
    _setup_logging(settings.generator.log_level)
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
        origin=datetime.now(UTC),
    )
    stop_event = threading.Event()
    _install_signal_handlers(stop_event)
    service = build_service(
        settings=settings,
        batch_generator=batch_generator,
        repository=_make_repository(args.repository),
        stop_event=stop_event,
    )
    if args.once:
        service.run_once()
    else:
        service.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
