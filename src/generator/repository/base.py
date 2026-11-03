"""Порт репозитория для хранения пользователей и поездок такси."""

from __future__ import annotations

from typing import Protocol

from generator.models import Trip, User


class Repository(Protocol):
    """Контракт хранилища, от которого зависит сервис генерации."""

    def ensure_schema(self) -> None:
        """Подготовить структуру хранилища к записи данных."""
        ...

    def upsert_users(self, users: list[User]) -> None:
        """Сохранить пачку пользователей и водителей."""
        ...

    def insert_trips(self, trips: list[Trip]) -> None:
        """Сохранить пачку фактов поездок одним batch-вызовом."""
        ...
