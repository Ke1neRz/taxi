"""Генератор фактов поездок для обновлённой taxi-звезды."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from generator.generation.anomalies import AnomalyKind, AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.seasonality import demand_factor
from generator.models import DimDate, DimTime, Tarif, Taxist, Trip, User, Weather


class TripBatchGenerator:
    """Собрать batch поездок со ссылками на отдельные справочники."""

    def __init__(
        self, catalog: TaxiCatalog, seed: int, anomaly_policy: AnomalyPolicy, origin: datetime
    ) -> None:
        """Создать генератор поездок с воспроизводимым случайным потоком."""

        self._catalog = catalog
        self._rng = random.Random(seed)
        self._anomaly_policy = anomaly_policy
        self._origin = origin
        self._next_trip_id = 1

    @property
    def users(self) -> list[User]:
        """Вернуть пассажиров для загрузки справочника."""

        return self._catalog.users()

    @property
    def taxists(self) -> list[Taxist]:
        """Вернуть водителей для загрузки справочника."""

        return self._catalog.taxists()

    @property
    def tarifs(self) -> list[Tarif]:
        """Вернуть тарифы для загрузки справочника."""

        return self._catalog.tarifs()

    @property
    def weathers(self) -> list[Weather]:
        """Вернуть погоду для загрузки справочника."""

        return self._catalog.weathers()

    def generate_batch(self, at: datetime, size: int) -> list[Trip]:
        """Создать batch поездок с последовательными временными метками."""

        if size < 1:
            raise ValueError("размер batch должен быть положительным")
        return [
            self._generate_trip(at + timedelta(seconds=index)) for index in range(size)
        ]

    def generate_sequence(
        self, start: datetime, size: int, step_seconds: float
    ) -> list[Trip]:
        """Создать последовательность поездок с заданным шагом времени."""

        if size < 1:
            raise ValueError("размер batch должен быть положительным")
        if step_seconds < 0.1:
            raise ValueError("шаг времени должен быть не меньше 0.1 секунды")
        return [
            self._generate_trip(start + timedelta(seconds=index * step_seconds))
            for index in range(size)
        ]

    def dimensions_for(self, at: datetime) -> tuple[DimDate, DimTime]:
        """Вернуть измерения даты и времени для указанной метки."""

        return self._catalog.date_dimension(at), self._catalog.time_dimension(at)

    def _generate_trip(self, start: datetime) -> Trip:
        """Создать одну поездку с FK на справочники и аналитическими метриками."""

        passenger = self._catalog.random_user()
        taxist = self._catalog.random_taxist()
        route = self._catalog.random_route()
        tarif = self._catalog.random_tarif()
        weather = self._catalog.random_weather()
        date_start, time_start = self.dimensions_for(start)
        end = start + timedelta(seconds=1)
        date_end, time_end = self.dimensions_for(end)
        anomaly = self._anomaly_policy.decide()
        demand = demand_factor(start, self._origin)
        speed_kmh = self._rng.uniform(22.0, 38.0)
        duration = route.distance_km / speed_kmh * 3600.0
        duration *= (1.0 + demand * 0.35) * self._rng.uniform(0.85, 1.15)
        cost = tarif.base_cost + route.distance_km * tarif.cost_per_km + duration / 60.0 * 8.0
        taxist_count = max(1, int(self._rng.gauss(12.0 + demand * 10.0, 2.5)))
        if anomaly is AnomalyKind.LONG_TRIP:
            duration *= self._anomaly_policy.strength
        elif anomaly is AnomalyKind.PRICE_SPIKE:
            cost *= self._anomaly_policy.strength
        elif anomaly is AnomalyKind.TRAFFIC_JAM:
            duration *= 1.0 + self._anomaly_policy.strength
        elif anomaly is AnomalyKind.DRIVER_SHORTAGE:
            taxist_count = max(1, int(taxist_count / max(1.0, self._anomaly_policy.strength)))
        trip = Trip(
            id=self._next_trip_id,
            user_id=passenger.id,
            taxist_id=taxist.id,
            tarif_id=tarif.id,
            weather_id=weather.id,
            date_start_id=date_start.id,
            time_start_id=time_start.id,
            date_end_id=date_end.id,
            time_end_id=time_end.id,
            start_point=route.start_point,
            end_point=route.end_point,
            intermediate_point=route.intermediate_point,
            datetime_start=start,
            datetime_end=start + timedelta(seconds=duration),
            child_seat=self._rng.random() < 0.08,
            pets=self._rng.random() < 0.05,
            rating=round((taxist.rating + self._rng.uniform(4.0, 5.0)) / 2.0, 2),
            cost=round(cost, 2),
            distance_km=route.distance_km,
            taxist_count=taxist_count,
            is_anomaly=anomaly is not None,
            weather_category=weather.weather,
            tarif_name=tarif.name,
        )
        self._next_trip_id += 1
        return trip
