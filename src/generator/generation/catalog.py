"""Детерминированные справочники для генерации поездок такси."""

from __future__ import annotations

import random
from dataclasses import dataclass

from generator.models import Route, Tarif, User, Weather

_NAMES = ("Ivan", "Anna", "Pavel", "Maria", "Sergey", "Elena")
_SURNAMES = ("Petrov", "Sokolov", "Smirnova", "Volkov", "Kuznetsov", "Orlova")
_GENDERS = ("male", "female")
_POINT_TYPES = ("Center", "Station", "Mall", "Airport")


@dataclass(frozen=True, slots=True)
class _CityPoint:
    """Именованная точка маршрута, связанная с городом."""

    city: str
    point_type: str

    @property
    def label(self) -> str:
        """Вернуть отображаемое имя точки для факта поездки."""

        return f"{self.city} {self.point_type}"


class TaxiCatalog:
    """Создать пользователей, водителей, маршруты и измерения поездки."""

    def __init__(
        self,
        cities: list[str],
        tariffs: list[str],
        weather_types: list[str],
        user_count: int = 100,
        seed: int = 42,
    ) -> None:
        """Создать детерминированный каталог из настроек предметной области."""

        if not cities:
            raise ValueError("at least one city is required")
        if user_count < 2:
            raise ValueError("at least two users are required")

        self._rng = random.Random(seed)
        self._tariffs = tuple(Tarif(value) for value in tariffs)
        self._weather_types = tuple(Weather(value) for value in weather_types)
        if not self._tariffs or not self._weather_types:
            raise ValueError("tariffs and weather types must not be empty")

        self._users = tuple(self._build_users(user_count))
        self._drivers = tuple(user for user in self._users if user.is_taxist)
        self._routes = tuple(self._build_routes(cities))
        if not self._drivers or not self._routes:
            raise ValueError("catalog must contain drivers and routes")

    def users(self) -> list[User]:
        """Вернуть всех сгенерированных пользователей, включая водителей."""

        return list(self._users)

    def drivers(self) -> list[User]:
        """Вернуть пользователей, допустимых для связи через taxist_id."""

        return list(self._drivers)

    def routes(self) -> list[Route]:
        """Вернуть детерминированный справочник маршрутов."""

        return list(self._routes)

    def random_user(self) -> User:
        """Выбрать воспроизводимого пассажира или водителя из каталога."""

        return self._rng.choice(self._users)

    def random_driver(self) -> User:
        """Выбрать воспроизводимого водителя из каталога."""

        return self._rng.choice(self._drivers)

    def random_route(self) -> Route:
        """Выбрать воспроизводимый маршрут с положительной дистанцией."""

        return self._rng.choice(self._routes)

    def random_tarif(self) -> Tarif:
        """Выбрать настроенную категорию тарифа."""

        return self._rng.choice(self._tariffs)

    def random_weather(self) -> Weather:
        """Выбрать настроенную категорию погоды для поездки."""

        return self._rng.choice(self._weather_types)

    def _build_users(self, user_count: int) -> list[User]:
        """Создать пользователей и отметить часть из них водителями."""

        users: list[User] = []
        driver_count = max(1, user_count // 5)
        driver_ids = set(self._rng.sample(range(1, user_count + 1), driver_count))

        for user_id in range(1, user_count + 1):
            users.append(
                User(
                    id=user_id,
                    name=self._rng.choice(_NAMES),
                    second_name=self._rng.choice(_SURNAMES),
                    count_trips=self._rng.randint(0, 500),
                    rating=round(self._rng.uniform(3.8, 5.0), 2),
                    phone_number=f"+7000{user_id:07d}",
                    gender=self._rng.choice(_GENDERS),
                    is_taxist=user_id in driver_ids,
                    balance=round(self._rng.uniform(0.0, 10000.0), 2),
                )
            )
        return users

    @staticmethod
    def _build_routes(cities: list[str]) -> list[Route]:
        """Создать шаблоны маршрутов из городских точек."""

        points = [_CityPoint(city, point_type) for city in cities for point_type in _POINT_TYPES]
        routes: list[Route] = []
        for index, start in enumerate(points):
            end = points[(index + 3) % len(points)]
            if start.label == end.label:
                continue
            routes.append(
                Route(
                    start_point=start.label,
                    end_point=end.label,
                    intermediate_point=None,
                    distance=round(2.5 + (index % 18) * 1.7, 2),
                )
            )
        return routes
