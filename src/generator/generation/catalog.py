"""Детерминированные справочники звездообразной модели такси."""

from __future__ import annotations

import random
from datetime import datetime, time

from generator.models import DimDate, DimTime, GeoPoint, Route, Tarif, Taxist, User, Weather

_NAMES = ("Иван", "Анна", "Павел", "Мария", "Сергей", "Елена")
_SURNAMES = ("Петров", "Соколов", "Смирнова", "Волков", "Кузнецов", "Орлова")
_GENDERS = ("мужчина", "женщина")
_CAR_MODELS = ("Lada Vesta", "Kia Rio", "Hyundai Solaris", "Toyota Camry")
_WEATHER_DATA = {
    "clear": ("ясно", 21.0, "нет", 3.0, 45),
    "cloudy": ("облачно", 15.0, "нет", 4.0, 60),
    "rain": ("дождь", 10.0, "дождь", 6.0, 80),
    "snow": ("снег", -4.0, "снег", 5.0, 75),
}
_DAY_NAMES = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")


class TaxiCatalog:
    """Создать справочники пользователей, таксистов, тарифов и погоды."""

    def __init__(
        self,
        cities: list[str],
        tariffs: list[str],
        weather_types: list[str],
        user_count: int = 100,
        seed: int = 42,
    ) -> None:
        """Создать воспроизводимый набор справочных данных."""

        if not cities:
            raise ValueError("необходим хотя бы один город")
        if user_count < 1:
            raise ValueError("количество пользователей должно быть положительным")
        self._rng = random.Random(seed)
        self._users = tuple(self._build_users(user_count))
        self._taxists = tuple(self._build_taxists(max(1, user_count // 5)))
        self._tarifs = tuple(self._build_tarifs(tariffs))
        self._weathers = tuple(self._build_weathers(weather_types))
        self._routes = tuple(self._build_routes(cities))
        if not self._tarifs or not self._weathers or not self._routes:
            raise ValueError("справочники тарифов, погоды и маршрутов не должны быть пустыми")

    def users(self) -> list[User]:
        """Вернуть справочник пассажиров."""

        return list(self._users)

    def taxists(self) -> list[Taxist]:
        """Вернуть справочник водителей."""

        return list(self._taxists)

    def tarifs(self) -> list[Tarif]:
        """Вернуть справочник тарифов."""

        return list(self._tarifs)

    def weathers(self) -> list[Weather]:
        """Вернуть справочник погоды."""

        return list(self._weathers)

    def routes(self) -> list[Route]:
        """Вернуть справочник маршрутов."""

        return list(self._routes)

    def random_user(self) -> User:
        """Выбрать пассажира из справочника."""

        return self._rng.choice(self._users)

    def random_taxist(self) -> Taxist:
        """Выбрать водителя из справочника."""

        return self._rng.choice(self._taxists)

    def random_route(self) -> Route:
        """Выбрать маршрут из справочника."""

        return self._rng.choice(self._routes)

    def random_tarif(self) -> Tarif:
        """Выбрать тариф из справочника."""

        return self._rng.choice(self._tarifs)

    def random_weather(self) -> Weather:
        """Выбрать погоду из справочника."""

        return self._rng.choice(self._weathers)

    @staticmethod
    def date_dimension(at: datetime) -> DimDate:
        """Построить измерение даты для временной метки."""

        current = at.date()
        return DimDate(
            id=int(current.strftime("%Y%m%d")),
            date_value=current,
            day=current.day,
            month=current.month,
            year=current.year,
            day_of_week=_DAY_NAMES[current.weekday()],
            week=current.isocalendar().week,
            quarter=(current.month - 1) // 3 + 1,
        )

    @staticmethod
    def time_dimension(at: datetime) -> DimTime:
        """Построить измерение времени для временной метки."""

        hour = at.hour
        part = "ночь" if hour < 6 else "утро" if hour < 12 else "день" if hour < 18 else "вечер"
        return DimTime(
            id=hour * 60 + at.minute,
            time_value=time(hour, at.minute),
            hour=hour,
            minute=at.minute,
            part_of_day=part,
        )

    def _build_users(self, count: int) -> list[User]:
        """Создать пользователей с реалистичными базовыми атрибутами."""

        return [
            User(
                id=index,
                name=self._rng.choice(_NAMES),
                second_name=self._rng.choice(_SURNAMES),
                count_trips=self._rng.randint(0, 500),
                rating=round(self._rng.uniform(3.8, 5.0), 2),
                phone_number=f"+7000{index:07d}",
                gender=self._rng.choice(_GENDERS),
            )
            for index in range(1, count + 1)
        ]

    def _build_taxists(self, count: int) -> list[Taxist]:
        """Создать отдельный справочник водителей и автомобилей."""

        return [
            Taxist(
                id=index,
                name=self._rng.choice(_NAMES),
                second_name=self._rng.choice(_SURNAMES),
                phone_number=f"+7999{index:07d}",
                gender=self._rng.choice(_GENDERS),
                rating=round(self._rng.uniform(4.0, 5.0), 2),
                license_number=f"LIC-{index:08d}",
                car_model=self._rng.choice(_CAR_MODELS),
                car_number=f"A{index:03d}AA",
                experience=self._rng.randint(1, 25),
            )
            for index in range(1, count + 1)
        ]

    @staticmethod
    def _build_tarifs(names: list[str]) -> list[Tarif]:
        """Создать тарифы с базовой ценой и ценой километра."""

        defaults = {"economy": (180.0, 32.0), "comfort": (260.0, 45.0), "business": (400.0, 70.0)}
        return [
            Tarif(
                id=index,
                name=name,
                base_cost=defaults.get(name, (200.0, 35.0))[0],
                cost_per_km=defaults.get(name, (200.0, 35.0))[1],
                description=f"Тариф {name}",
            )
            for index, name in enumerate(names, start=1)
        ]

    @staticmethod
    def _build_weathers(names: list[str]) -> list[Weather]:
        """Создать погодные категории с измерениями условий поездки."""

        return [
            Weather(index, *_WEATHER_DATA.get(name, (name, 12.0, "нет", 4.0, 60)))
            for index, name in enumerate(names, start=1)
        ]

    @staticmethod
    def _build_routes(cities: list[str]) -> list[Route]:
        """Создать маршруты с координатами выбранных городов."""

        routes: list[Route] = []
        for index, _city in enumerate(cities, start=1):
            start = GeoPoint(55.0 + index * 0.1, 37.0 + index * 0.1)
            end = GeoPoint(start.latitude + 0.05, start.longitude + 0.08)
            routes.append(Route(start, end, (), round(3.0 + index * 2.5, 2)))
        return routes
