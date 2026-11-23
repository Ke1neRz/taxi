"""Порт репозитория для звездообразной модели аналитики такси."""

from __future__ import annotations

from typing import Protocol

from generator.models import DimDate, DimTime, Tarif, Taxist, Trip, User, Weather


class Repository(Protocol):
    """Контракт batch-хранилища справочников и фактов поездок."""

    def ensure_schema(self) -> None:
        """Создать структуру хранилища, если её ещё нет."""
        ...

    def upsert_users(self, users: list[User]) -> None:
        """Сохранить справочник пассажиров."""
        ...

    def upsert_taxists(self, taxists: list[Taxist]) -> None:
        """Сохранить справочник водителей."""
        ...

    def upsert_tarifs(self, tarifs: list[Tarif]) -> None:
        """Сохранить справочник тарифов."""
        ...

    def upsert_weathers(self, weathers: list[Weather]) -> None:
        """Сохранить справочник погодных условий."""
        ...

    def upsert_dates(self, dates: list[DimDate]) -> None:
        """Сохранить измерение дат."""
        ...

    def upsert_times(self, times: list[DimTime]) -> None:
        """Сохранить измерение времени."""
        ...

    def insert_trips(self, trips: list[Trip]) -> None:
        """Сохранить batch фактов поездок."""
        ...
