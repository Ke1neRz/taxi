"""In-memory реализация звездообразного репозитория такси."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from generator.models import DimDate, DimTime, Tarif, Taxist, Trip, User, Weather


class InMemoryRepository:
    """Хранить справочники и поездки в памяти для быстрых тестов."""

    def __init__(self) -> None:
        """Создать пустое хранилище всех таблиц звезды."""

        self.users: list[User] = []
        self.taxists: list[Taxist] = []
        self.tarifs: list[Tarif] = []
        self.weathers: list[Weather] = []
        self.dates: list[DimDate] = []
        self.times: list[DimTime] = []
        self.trips: list[Trip] = []

    def ensure_schema(self) -> None:
        """Ничего не делать: памяти не нужна схема базы данных."""

    def upsert_users(self, users: list[User]) -> None:
        """Добавить или заменить пассажиров по id."""

        self.users = self._upsert(self.users, users)

    def upsert_taxists(self, taxists: list[Taxist]) -> None:
        """Добавить или заменить водителей по id."""

        self.taxists = self._upsert(self.taxists, taxists)

    def upsert_tarifs(self, tarifs: list[Tarif]) -> None:
        """Добавить или заменить тарифы по id."""

        self.tarifs = self._upsert(self.tarifs, tarifs)

    def upsert_weathers(self, weathers: list[Weather]) -> None:
        """Добавить или заменить погодные категории по id."""

        self.weathers = self._upsert(self.weathers, weathers)

    def upsert_dates(self, dates: list[DimDate]) -> None:
        """Добавить или заменить даты по id."""

        self.dates = self._upsert(self.dates, dates)

    def upsert_times(self, times: list[DimTime]) -> None:
        """Добавить или заменить время по id."""

        self.times = self._upsert(self.times, times)

    def max_timestamp(self) -> datetime | None:
        """Вернуть максимальную временную метку из фактов в памяти."""

        if not self.trips:
            return None
        return max(trip.datetime_start for trip in self.trips)

    def insert_trips(self, trips: list[Trip]) -> None:
        """Добавить факты поездок одной batch-пачкой."""

        self.trips.extend(trips)

    @staticmethod
    def _upsert(existing: list[Any], incoming: list[Any]) -> list[Any]:
        """Объединить записи с заменой по общему полю id."""

        by_id = {item.id: item for item in existing}
        by_id.update({item.id: item for item in incoming})
        return [by_id[item_id] for item_id in sorted(by_id)]
