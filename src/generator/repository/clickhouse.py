"""ClickHouse-адаптер batch-хранилища taxi-звезды."""

from __future__ import annotations

from typing import Any

import clickhouse_connect

from generator.config import ClickHouseSettings
from generator.models import DimDate, DimTime, Tarif, Taxist, Trip, User, Weather

from .base import Repository


class ClickHouseRepository(Repository):
    """Создать taxi-звезду и записывать справочники batch-вызовами."""

    def __init__(self, settings: ClickHouseSettings) -> None:
        """Сохранить настройки ClickHouse и отложить соединение."""

        self._settings = settings
        self._client: Any | None = None

    def _conn(self) -> Any:
        """Вернуть лениво созданный клиент без привязки к существующей базе."""

        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self._settings.host,
                port=self._settings.port,
                username=self._settings.user,
                password=self._settings.password,
            )
        return self._client

    def ensure_schema(self) -> None:
        """Идемпотентно создать таблицы taxi-звезды и фактов поездок."""

        database = self._settings.database
        client = self._conn()
        client.command(f"CREATE DATABASE IF NOT EXISTS {database}")
        definitions = {
            "users": (
                "id UInt64, name String, second_name String, count_trips UInt32, "
                "rating Float32, phone_number String, gender LowCardinality(String)"
            ),
            "taxists": (
                "id UInt64, name String, second_name String, phone_number String, "
                "gender LowCardinality(String), rating Float32, license_number String, "
                "car_model String, car_number String, experience UInt16"
            ),
            "tarifs": (
                "id UInt64, name LowCardinality(String), base_cost Float64, "
                "cost_per_km Float64, description String"
            ),
            "weather": (
                "id UInt64, weather LowCardinality(String), temperature Float32, "
                "precipitation LowCardinality(String), wind_speed Float32, humidity UInt8"
            ),
            "dim_date": (
                "id UInt32, date_value Date, day UInt8, month UInt8, year UInt16, "
                "day_of_week LowCardinality(String), week UInt8, quarter UInt8"
            ),
            "dim_time": "id UInt32, hour UInt8, minute UInt8, part_of_day LowCardinality(String)",
            "trips": (
                "id UInt64, user_id UInt64, taxist_id UInt64, tarif_id UInt64, "
                "weather_id UInt64, date_start_id UInt32, time_start_id UInt32, "
                "date_end_id UInt32, time_end_id UInt32, start_latitude Float64, "
                "start_longitude Float64, end_latitude Float64, end_longitude Float64, "
                "intermediate_points Array(Tuple(Float64, Float64)), "
                "datetime_start DateTime64(3, 'UTC'), datetime_end DateTime64(3, 'UTC'), "
                "child_seat UInt8, pets UInt8, rating Float32, cost Float64, "
                "distance_km Float64, travel_time_seconds UInt32, taxist_count UInt32, "
                "is_anomaly UInt8"
            ),
        }
        order_by = {
            "users": "id",
            "taxists": "id",
            "tarifs": "id",
            "weather": "id",
            "dim_date": "id",
            "dim_time": "id",
            "trips": "(datetime_start, id)",
        }
        for table, columns in definitions.items():
            partition = (
                " PARTITION BY toYYYYMM(datetime_start)" if table == "trips" else ""
            )
            client.command(
                f"CREATE TABLE IF NOT EXISTS {database}.{table} ({columns}) "
                f"ENGINE = MergeTree{partition} ORDER BY {order_by[table]}"
            )

        aggregations = {
            "trips_by_hour": (
                "hour_start UInt8, part_of_day LowCardinality(String), "
                "count_trip AggregateFunction(count), "
                "avg_travel_time AggregateFunction(avg, UInt32), "
                "avg_count_taxist AggregateFunction(avg, UInt32), "
                "average_cost AggregateFunction(avg, Float64)",
                "hour_start",
            ),
            "trips_by_weekday": (
                "day_of_week LowCardinality(String), part_of_week LowCardinality(String), "
                "count_trip AggregateFunction(count), "
                "avg_travel_time AggregateFunction(avg, UInt32), "
                "average_cost AggregateFunction(avg, Float64)",
                "day_of_week",
            ),
            "trips_by_weather": (
                "weather LowCardinality(String), count_trip AggregateFunction(count), "
                "avg_travel_time AggregateFunction(avg, UInt32), "
                "avg_count_taxist AggregateFunction(avg, UInt32), "
                "average_cost AggregateFunction(avg, Float64)",
                "weather",
            ),
            "trips_by_tarif": (
                "tarif LowCardinality(String), count_trip AggregateFunction(count), "
                "avg_travel_time AggregateFunction(avg, UInt32), "
                "average_cost AggregateFunction(avg, Float64), "
                "avg_count_taxist AggregateFunction(avg, UInt32)",
                "tarif",
            ),
        }
        for table, (columns, key) in aggregations.items():
            client.command(
                f"CREATE TABLE IF NOT EXISTS {database}.{table} ({columns}) "
                f"ENGINE = AggregatingMergeTree ORDER BY {key}"
            )

        materialized_views = (
            (
                "trips_by_hour_mv",
                "trips_by_hour",
                "dt.hour AS hour_start, dt.part_of_day AS part_of_day, countState() AS count_trip, "
                "avgState(travel_time_seconds) AS avg_travel_time, "
                "avgState(taxist_count) AS avg_count_taxist, avgState(cost) AS average_cost",
                f"FROM {database}.trips AS t "
                f"INNER JOIN {database}.dim_time AS dt ON dt.id = t.time_start_id "
                "GROUP BY dt.hour, dt.part_of_day",
            ),
            (
                "trips_by_weekday_mv",
                "trips_by_weekday",
                "dd.day_of_week AS day_of_week, "
                "multiIf(dd.day_of_week IN ('суббота', 'воскресенье'), "
                "'выходные', 'будни') AS part_of_week, "
                "countState() AS count_trip, "
                "avgState(travel_time_seconds) AS avg_travel_time, avgState(cost) AS average_cost",
                f"FROM {database}.trips AS t "
                f"INNER JOIN {database}.dim_date AS dd ON dd.id = t.date_start_id "
                "GROUP BY dd.day_of_week, "
                "multiIf(dd.day_of_week IN ('суббота', 'воскресенье'), 'выходные', 'будни')",
            ),
            (
                "trips_by_weather_mv",
                "trips_by_weather",
                "w.weather AS weather, countState() AS count_trip, "
                "avgState(travel_time_seconds) AS avg_travel_time, "
                "avgState(taxist_count) AS avg_count_taxist, avgState(cost) AS average_cost",
                f"FROM {database}.trips AS t "
                f"INNER JOIN {database}.weather AS w ON w.id = t.weather_id "
                "GROUP BY w.weather",
            ),
            (
                "trips_by_tarif_mv",
                "trips_by_tarif",
                "tf.name AS tarif, countState() AS count_trip, "
                "avgState(travel_time_seconds) AS avg_travel_time, "
                "avgState(cost) AS average_cost, avgState(taxist_count) AS avg_count_taxist",
                f"FROM {database}.trips AS t "
                f"INNER JOIN {database}.tarifs AS tf ON tf.id = t.tarif_id "
                "GROUP BY tf.name",
            ),
        )
        for mv_name, target, select_columns, source in materialized_views:
            client.command(
                f"CREATE MATERIALIZED VIEW IF NOT EXISTS {database}.{mv_name} "
                f"TO {database}.{target} AS SELECT {select_columns} {source}"
            )

    def _insert(
        self, table: str, columns: list[str], rows: list[tuple[Any, ...]]
    ) -> None:
        """Выполнить непустую batch-вставку в таблицу."""

        if rows:
            self._conn().insert(
                f"{self._settings.database}.{table}", rows, column_names=columns
            )

    def upsert_users(self, users: list[User]) -> None:
        """Вставить batch пассажиров."""

        self._insert(
            "users",
            ["id", "name", "second_name", "count_trips", "rating", "phone_number", "gender"],
            [
                (
                    item.id,
                    item.name,
                    item.second_name,
                    item.count_trips,
                    item.rating,
                    item.phone_number,
                    item.gender,
                )
                for item in users
            ],
        )

    def upsert_taxists(self, taxists: list[Taxist]) -> None:
        """Вставить batch водителей."""

        self._insert(
            "taxists",
            [
                "id",
                "name",
                "second_name",
                "phone_number",
                "gender",
                "rating",
                "license_number",
                "car_model",
                "car_number",
                "experience",
            ],
            [
                (
                    item.id,
                    item.name,
                    item.second_name,
                    item.phone_number,
                    item.gender,
                    item.rating,
                    item.license_number,
                    item.car_model,
                    item.car_number,
                    item.experience,
                )
                for item in taxists
            ],
        )

    def upsert_tarifs(self, tarifs: list[Tarif]) -> None:
        """Вставить batch тарифов."""

        self._insert(
            "tarifs",
            ["id", "name", "base_cost", "cost_per_km", "description"],
            [
                (item.id, item.name, item.base_cost, item.cost_per_km, item.description)
                for item in tarifs
            ],
        )

    def upsert_weathers(self, weathers: list[Weather]) -> None:
        """Вставить batch погодных категорий."""

        self._insert(
            "weather",
            ["id", "weather", "temperature", "precipitation", "wind_speed", "humidity"],
            [
                (
                    item.id,
                    item.weather,
                    item.temperature,
                    item.precipitation,
                    item.wind_speed,
                    item.humidity,
                )
                for item in weathers
            ],
        )

    def upsert_dates(self, dates: list[DimDate]) -> None:
        """Вставить batch измерений дат."""

        self._insert(
            "dim_date",
            ["id", "date_value", "day", "month", "year", "day_of_week", "week", "quarter"],
            [
                (
                    item.id,
                    item.date_value,
                    item.day,
                    item.month,
                    item.year,
                    item.day_of_week,
                    item.week,
                    item.quarter,
                )
                for item in dates
            ],
        )

    def upsert_times(self, times: list[DimTime]) -> None:
        """Вставить batch измерений времени."""

        self._insert(
            "dim_time",
            ["id", "hour", "minute", "part_of_day"],
            [(item.id, item.hour, item.minute, item.part_of_day) for item in times],
        )

    def insert_trips(self, trips: list[Trip]) -> None:
        """Вставить batch фактов поездок с координатами маршрута."""

        rows = [
            (
                item.id,
                item.user_id,
                item.taxist_id,
                item.tarif_id,
                item.weather_id,
                item.date_start_id,
                item.time_start_id,
                item.date_end_id,
                item.time_end_id,
                item.start_point.latitude,
                item.start_point.longitude,
                item.end_point.latitude,
                item.end_point.longitude,
                [(point.latitude, point.longitude) for point in item.intermediate_point],
                item.datetime_start,
                item.datetime_end,
                int(item.child_seat),
                int(item.pets),
                item.rating,
                item.cost,
                item.distance_km,
                item.travel_time_seconds,
                item.taxist_count,
                int(item.is_anomaly),
            )
            for item in trips
        ]
        self._insert(
            "trips",
            [
                "id",
                "user_id",
                "taxist_id",
                "tarif_id",
                "weather_id",
                "date_start_id",
                "time_start_id",
                "date_end_id",
                "time_end_id",
                "start_latitude",
                "start_longitude",
                "end_latitude",
                "end_longitude",
                "intermediate_points",
                "datetime_start",
                "datetime_end",
                "child_seat",
                "pets",
                "rating",
                "cost",
                "distance_km",
                "travel_time_seconds",
                "taxist_count",
                "is_anomaly",
            ],
            rows,
        )
