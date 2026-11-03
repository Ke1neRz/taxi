"""Pure domain models for taxi users and trips."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Tarif(StrEnum):
    """Tariff category used as a trip dimension."""

    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"


class Weather(StrEnum):
    """Weather category recorded at the time of a trip."""

    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"


@dataclass(frozen=True, slots=True)
class User:
    """User directory record; taxi drivers are users with is_taxist enabled."""

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
class Trip:
    """Taxi trip fact with dimensions and metrics needed by the MVs."""

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

    @property
    def travel_time_seconds(self) -> int:
        """Return the non-negative trip duration in whole seconds."""

        return max(0, int((self.datetime_end - self.datetime_start).total_seconds()))
