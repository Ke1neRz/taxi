"""Чистые функции сезонности спроса на поездки такси."""

from __future__ import annotations

import math
from datetime import datetime


def diurnal_demand_factor(at: datetime) -> float:
    """Вернуть суточный множитель спроса в диапазоне от 0 до 1."""

    hour = at.hour + at.minute / 60.0 + at.second / 3600.0
    morning_peak = math.exp(-((hour - 8.0) ** 2) / 8.0)
    evening_peak = math.exp(-((hour - 18.0) ** 2) / 10.0)
    night_penalty = 0.18 if hour < 6.0 or hour >= 23.0 else 0.0
    return min(1.0, 0.2 + 0.55 * morning_peak + 0.7 * evening_peak - night_penalty)


def weekly_demand_factor(at: datetime) -> float:
    """Вернуть множитель спроса для буднего дня или выходного."""

    return 0.9 if at.weekday() < 5 else 0.72


def trend_factor(at: datetime, origin: datetime) -> float:
    """Вернуть плавный линейный тренд спроса относительно начальной даты."""

    days = max(0.0, (at - origin).total_seconds() / 86400.0)
    return 1.0 + min(days, 365.0) / 365.0 * 0.25


def demand_factor(at: datetime, origin: datetime) -> float:
    """Объединить суточную сезонность, неделю и тренд спроса."""

    return diurnal_demand_factor(at) * weekly_demand_factor(at) * trend_factor(at, origin)
