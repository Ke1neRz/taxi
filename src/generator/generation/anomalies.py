"""Политика такси-аномалий для редких выбросов в данных поездок."""

from __future__ import annotations

import random
from enum import StrEnum


class AnomalyKind(StrEnum):
    """Типы необычного поведения поездки или рынка такси."""

    LONG_TRIP = "long_trip"
    PRICE_SPIKE = "price_spike"
    TRAFFIC_JAM = "traffic_jam"
    DRIVER_SHORTAGE = "driver_shortage"


class AnomalyPolicy:
    """Решить, должна ли текущая поездка получить аномалию."""

    def __init__(self, probability: float, strength: float, rng: random.Random) -> None:
        """Создать policy с вероятностью и силой аномального отклонения."""

        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if strength < 0.0:
            raise ValueError("strength must not be negative")
        self._probability = probability
        self._strength = strength
        self._rng = rng

    @property
    def strength(self) -> float:
        """Вернуть множитель силы аномалии."""

        return self._strength

    def decide(self) -> AnomalyKind | None:
        """Вернуть тип аномалии или None для обычной поездки."""

        if self._rng.random() >= self._probability:
            return None
        return self._rng.choice(list(AnomalyKind))
