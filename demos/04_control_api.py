"""Показать остановку непрерывного генератора через HTTP API."""

from __future__ import annotations

import random
import threading
from datetime import UTC, datetime
from http.client import HTTPConnection

from generator.config import ClickHouseSettings, GeneratorSettings, Settings
from generator.control import ControlServer
from generator.generation.anomalies import AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.trips import TripBatchGenerator
from generator.repository.in_memory import InMemoryRepository
from generator.retry import RetryPolicy
from generator.service.generator import GeneratorService


def build_service(stop_event: threading.Event) -> tuple[GeneratorService, InMemoryRepository]:
    """Собрать быстрый непрерывный сервис для HTTP-демонстрации."""

    settings = Settings(
        generator=GeneratorSettings(
            batch_size=2,
            interval_seconds=0.0,
            backfill_start="2026-01-01T00:00:00",
            backfill_step_seconds=86400.0,
            realtime_step_seconds=1.0,
            seed=42,
        ),
        clickhouse=ClickHouseSettings(),
    )
    catalog = TaxiCatalog(
        settings.generator.city_list,
        settings.generator.tariff_list,
        settings.generator.weather_type_list,
        seed=settings.generator.seed,
    )
    batch_generator = TripBatchGenerator(
        catalog=catalog,
        seed=settings.generator.seed,
        anomaly_policy=AnomalyPolicy(0.0, 1.0, random.Random(settings.generator.seed)),
        origin=datetime(2026, 1, 1, tzinfo=UTC),
    )
    repository = InMemoryRepository()
    service = GeneratorService(
        settings=settings,
        batch_generator=batch_generator,
        repository=repository,
        retry=RetryPolicy(2, 0.0, 1.0, sleep=lambda _: None),
        stop_event=stop_event,
        sleep=lambda _: None,
    )
    return service, repository


def request(server: ControlServer, method: str, path: str) -> str:
    """Выполнить HTTP-запрос к локальному control server."""

    host, port = server.address
    connection = HTTPConnection(host, port, timeout=2)
    connection.request(method, path)
    response = connection.getresponse()
    body = response.read().decode("utf-8")
    connection.close()
    return body


def main() -> None:
    """Запустить сервис и остановить его через POST /stop."""

    stop_event = threading.Event()
    service, repository = build_service(stop_event)
    control = ControlServer("127.0.0.1", 0, stop_event)
    service_thread = threading.Thread(target=service.run)
    control.start()
    service_thread.start()
    try:
        print(f"GET /health: {request(control, 'GET', '/health')}")
        print(f"GET /status: {request(control, 'GET', '/status')}")
        print(f"POST /stop: {request(control, 'POST', '/stop')}")
        service_thread.join(timeout=3.0)
        print(f"Поездок в памяти: {len(repository.trips)}")
    finally:
        stop_event.set()
        service_thread.join(timeout=3.0)
        control.close()


if __name__ == "__main__":
    main()
