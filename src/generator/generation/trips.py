"""Генератор реалистичных батчей фактов поездок такси."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from generator.generation.anomalies import AnomalyKind, AnomalyPolicy
from generator.generation.catalog import TaxiCatalog
from generator.generation.seasonality import demand_factor
from generator.models import Trip


class TripBatchGenerator:
    """Собрать связанные факты поездок из каталога и временной динамики."""

    def __init__(
        self,
        catalog: TaxiCatalog,
        seed: int,
        anomaly_policy: AnomalyPolicy,
        origin: datetime,
    ) -> None:
        """Создать генератор поездок с детерминированным случайным потоком."""

        self._catalog = catalog
        self._rng = random.Random(seed)
        self._anomaly_policy = anomaly_policy
        self._origin = origin
        self._next_trip_id = 1

    @property
    def users(self):
        """Вернуть пользователей, которых нужно записать в справочник."""

        return self._catalog.users()

    def generate_batch(self, at: datetime, size: int) -> list[Trip]:
        """Создать batch связанных поездок, начинающихся около указанного времени."""

        if size < 1:
            raise ValueError("batch size must be positive")
        trips = [self._generate_trip(at + timedelta(seconds=index)) for index in range(size)]
        return trips

    def _generate_trip(self, start: datetime) -> Trip:
        """Создать одну поездку с метриками, связями и возможной аномалией."""

        passenger = self._catalog.random_user()
        driver = self._catalog.random_driver()
        route = self._catalog.random_route()
        tarif = self._catalog.random_tarif()
        weather = self._catalog.random_weather()
        anomaly = self._anomaly_policy.decide()
        demand = demand_factor(start, self._origin)

        tariff_multiplier = {"economy": 1.0, "comfort": 1.35, "business": 1.8}[tarif.value]
        speed_kmh = self._rng.uniform(22.0, 38.0)
        duration = route.distance / speed_kmh * 3600.0
        duration *= 1.0 + demand * 0.35
        duration *= self._rng.uniform(0.85, 1.15)

        taxist_count = max(1, int(self._rng.gauss(12.0 + demand * 10.0, 2.5)))
        base_cost = 180.0 + route.distance * 32.0 + duration / 60.0 * 8.0
        cost = base_cost * tariff_multiplier

        if anomaly is AnomalyKind.LONG_TRIP:
            duration *= self._anomaly_policy.strength
        elif anomaly is AnomalyKind.PRICE_SPIKE:
            cost *= self._anomaly_policy.strength
        elif anomaly is AnomalyKind.TRAFFIC_JAM:
            duration *= 1.0 + self._anomaly_policy.strength
        elif anomaly is AnomalyKind.DRIVER_SHORTAGE:
            taxist_count = max(1, int(taxist_count / self._anomaly_policy.strength))

        trip = Trip(
            id=self._next_trip_id,
            user_id=passenger.id,
            taxist_id=driver.id,
            tarif=tarif,
            weather=weather,
            start_point=route.start_point,
            end_point=route.end_point,
            intermediate_point=route.intermediate_point,
            distance=route.distance,
            datetime_start=start,
            datetime_end=start + timedelta(seconds=duration),
            child_seat=self._rng.random() < 0.08,
            pets=self._rng.random() < 0.05,
            rating=round(self._rng.uniform(4.0, 5.0), 2),
            cost=round(cost, 2),
            taxist_count=taxist_count,
            is_anomaly=anomaly is not None,
        )
        self._next_trip_id += 1
        return trip
