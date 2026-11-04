"""ClickHouse-реализация batch-репозитория такси."""

from __future__ import annotations

from typing import Any

import clickhouse_connect

from generator.config import ClickHouseSettings
from generator.models import Trip, User

from .base import Repository

_USERS_COLUMNS = [
    "id",
    "name",
    "second_name",
    "count_trips",
    "rating",
    "phone_number",
    "gender",
    "is_taxist",
    "balance",
]

_TRIPS_COLUMNS = [
    "id",
    "user_id",
    "taxist_id",
    "tarif",
    "weather",
    "start_point",
    "end_point",
    "intermediate_point",
    "distance",
    "cost",
    "datetime_start",
    "datetime_end",
    "child_seat",
    "pets",
    "rating",
    "travel_time_seconds",
    "taxist_count",
    "is_anomaly",
]


class ClickHouseRepository(Repository):
    """Записывать пользователей и поездки в ClickHouse батчами."""

    def __init__(self, settings: ClickHouseSettings) -> None:
        """Сохранить настройки и отложить создание соединения."""

        self._settings = settings
        self._client: Any | None = None

    def _conn(self) -> Any:
        """Вернуть лениво созданный клиент ClickHouse."""

        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._settings.host,
                port=self._settings.port,
                username=self._settings.user,
                password=self._settings.password,
                database=self._settings.database,
            )
        return self._client

    def ensure_schema(self) -> None:
        """Идемпотентно создать исходные таблицы пользователей и поездок."""

        database = self._settings.database
        client = self._conn()
        client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
        client.command(
            f"""
            CREATE TABLE IF NOT EXISTS {database}.users (
                id UInt64,
                name String,
                second_name String,
                count_trips UInt32,
                rating Float32,
                phone_number String,
                gender String,
                is_taxist UInt8,
                balance Float64
            ) ENGINE = MergeTree
            ORDER BY id
            """
        )
        client.command(
            f"""
            CREATE TABLE IF NOT EXISTS {database}.trips (
                id UInt64,
                user_id UInt64,
                taxist_id UInt64,
                tarif String,
                weather String,
                start_point String,
                end_point String,
                intermediate_point String,
                distance Float64,
                cost Float64,
                datetime_start DateTime64(3, 'UTC'),
                datetime_end DateTime64(3, 'UTC'),
                child_seat UInt8,
                pets UInt8,
                rating Float32,
                travel_time_seconds UInt32,
                taxist_count UInt32,
                is_anomaly UInt8
            ) ENGINE = MergeTree
            PARTITION BY toYYYYMM(datetime_start)
            ORDER BY (datetime_start, id)
            """
        )

    def upsert_users(self, users: list[User]) -> None:
        """Вставить справочник пользователей одной пачкой."""

        rows = [
            (
                user.id,
                user.name,
                user.second_name,
                user.count_trips,
                user.rating,
                user.phone_number,
                user.gender,
                int(user.is_taxist),
                user.balance,
            )
            for user in users
        ]
        if rows:
            self._conn().insert(
                f"{self._settings.database}.users",
                rows,
                column_names=_USERS_COLUMNS,
            )

    def insert_trips(self, trips: list[Trip]) -> None:
        """Вставить факты поездок одним batch-вызовом."""

        rows = [
            (
                trip.id,
                trip.user_id,
                trip.taxist_id,
                trip.tarif.value,
                trip.weather.value,
                trip.start_point,
                trip.end_point,
                trip.intermediate_point or "",
                trip.distance,
                trip.cost,
                trip.datetime_start,
                trip.datetime_end,
                int(trip.child_seat),
                int(trip.pets),
                trip.rating,
                trip.travel_time_seconds,
                trip.taxist_count,
                int(trip.is_anomaly),
            )
            for trip in trips
        ]
        if rows:
            self._conn().insert(
                f"{self._settings.database}.trips",
                rows,
                column_names=_TRIPS_COLUMNS,
            )
