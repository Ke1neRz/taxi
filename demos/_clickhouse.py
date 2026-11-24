"""Общие проверки доступности ClickHouse для демонстрационных сценариев."""

from __future__ import annotations

import urllib.request

import clickhouse_connect

from generator.config import ClickHouseSettings


def is_ready(settings: ClickHouseSettings, timeout: float = 2.0) -> bool:
    """Проверить ответ HTTP endpoint /ping без авторизации."""

    url = f"http://{settings.host}:{settings.port}/ping"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def client(settings: ClickHouseSettings):
    """Создать клиент ClickHouse с настройками проекта."""

    return clickhouse_connect.get_client(
        host=settings.host,
        port=settings.port,
        username=settings.user,
        password=settings.password,
        database=settings.database,
    )
