"""In-memory реализация репозитория для тестов без ClickHouse."""

from __future__ import annotations

from generator.models import Trip, User


class InMemoryRepository:
    """Хранить пользователей и поездки в оперативной памяти."""

    def __init__(self) -> None:
        """Создать пустое in-memory хранилище."""

        self.users: list[User] = []
        self.trips: list[Trip] = []

    def ensure_schema(self) -> None:
        """Ничего не делать: in-memory хранилищу схема не нужна."""

    def upsert_users(self, users: list[User]) -> None:
        """Добавить или заменить пользователей по идентификатору."""

        by_id = {user.id: user for user in self.users}
        by_id.update({user.id: user for user in users})
        self.users = sorted(by_id.values(), key=lambda user: user.id)

    def insert_trips(self, trips: list[Trip]) -> None:
        """Добавить факты поездок одной переданной пачкой."""

        self.trips.extend(trips)
