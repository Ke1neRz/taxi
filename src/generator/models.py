"""Чистые доменные модели пользователей и поездок такси."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Tarif(StrEnum):
    """Категория тарифа как измерение поездки."""

    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"


class Weather(StrEnum):
    """Категория погоды, записанная во время поездки."""

    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"


@dataclass(frozen=True, slots=True)
class User:
    """Запись справочника пользователей; водитель имеет is_taxist=True."""

    id: int
    name: str
    second_name: str
    count_trips: int
    rating: float
    phone_number: str
    gender: str
    is_taxist: bool
    balance: float


@dataclass(frozen=True, slots=True)
class Route:
    """Справочный маршрут для создания реалистичных фактов поездок."""

    start_point: str
    end_point: str
    intermediate_point: str | None
    distance: float


@dataclass(frozen=True, slots=True)
class Trip:
    """Факт поездки такси с измерениями и метриками для MV."""

    id: int
    user_id: int
    taxist_id: int
    tarif: Tarif
    weather: Weather
    start_point: str
    end_point: str
    intermediate_point: str | None
    distance: float
    datetime_start: datetime
    datetime_end: datetime
    child_seat: bool
    pets: bool
    rating: float
    cost: float
    taxist_count: int
    is_anomaly: bool = False

    @property
    def travel_time_seconds(self) -> int:
        """Вернуть неотрицательную длительность поездки в целых секундах."""

        return max(0, int((self.datetime_end - self.datetime_start).total_seconds()))
