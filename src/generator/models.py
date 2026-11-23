"""Доменные модели звездообразной модели аналитики такси."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True, slots=True)
class User:
    """Пассажир из справочника пользователей."""

    id: int
    name: str
    second_name: str
    count_trips: int
    rating: float
    phone_number: str
    gender: str


@dataclass(frozen=True, slots=True)
class Taxist:
    """Водитель из отдельного справочника таксистов."""

    id: int
    name: str
    second_name: str
    phone_number: str
    gender: str
    rating: float
    license_number: str
    car_model: str
    car_number: str
    experience: int


@dataclass(frozen=True, slots=True)
class Tarif:
    """Тариф с базовой ценой и стоимостью километра."""

    id: int
    name: str
    base_cost: float
    cost_per_km: float
    description: str


@dataclass(frozen=True, slots=True)
class Weather:
    """Категория погоды и её измерения на момент поездки."""

    id: int
    weather: str
    temperature: float
    precipitation: str
    wind_speed: float
    humidity: int


@dataclass(frozen=True, slots=True)
class DimDate:
    """Измерение календарной даты поездки."""

    id: int
    date_value: date
    day: int
    month: int
    year: int
    day_of_week: str
    week: int
    quarter: int


@dataclass(frozen=True, slots=True)
class DimTime:
    """Измерение времени суток поездки."""

    id: int
    time_value: time
    hour: int
    minute: int
    part_of_day: str


@dataclass(frozen=True, slots=True)
class GeoPoint:
    """Координата точки маршрута."""

    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class Route:
    """Справочный маршрут с координатами и расстоянием."""

    start_point: GeoPoint
    end_point: GeoPoint
    intermediate_point: tuple[GeoPoint, ...]
    distance_km: float


@dataclass(frozen=True, slots=True)
class Trip:
    """Факт поездки со ссылками на справочники и измерения."""

    id: int
    user_id: int
    taxist_id: int
    tarif_id: int
    weather_id: int
    date_start_id: int
    time_start_id: int
    date_end_id: int
    time_end_id: int
    start_point: GeoPoint
    end_point: GeoPoint
    intermediate_point: tuple[GeoPoint, ...]
    datetime_start: datetime
    datetime_end: datetime
    child_seat: bool
    pets: bool
    rating: float
    cost: float
    distance_km: float
    taxist_count: int
    is_anomaly: bool = False

    @property
    def travel_time_seconds(self) -> int:
        """Вернуть длительность поездки в целых секундах."""

        return max(0, int((self.datetime_end - self.datetime_start).total_seconds()))
