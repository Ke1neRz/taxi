"""Конфигурация генератора такси из переменных окружения."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickHouseSettings(BaseSettings):
    """Настройки подключения к ClickHouse с префиксом CLICKHOUSE_."""

    model_config = SettingsConfigDict(
        env_prefix="CLICKHOUSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    host: str = Field(default="localhost")
    port: int = Field(default=8123, ge=1, le=65535)
    database: str = Field(default="taxi")
    user: str = Field(default="default")
    password: str = Field(default="")


class GeneratorSettings(BaseSettings):
    """Настройки генерации с префиксом GENERATOR_."""

    model_config = SettingsConfigDict(
        env_prefix="GENERATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    batch_size: int = Field(default=100, ge=1)
    interval_seconds: float = Field(default=1.0, ge=0.0)
    seed: int = Field(default=42)
    anomaly_probability: float = Field(default=0.02, ge=0.0, le=1.0)
    anomaly_strength: float = Field(default=3.0, ge=0.0)
    cities: str = Field(default="Moscow,Kazan,Sochi,Irkutsk")
    tariffs: str = Field(default="economy,comfort,business")
    weather_types: str = Field(default="clear,cloudy,rain,snow")
    log_level: str = Field(default="INFO")
    retry_max_attempts: int = Field(default=5, ge=1)
    retry_base_delay_seconds: float = Field(default=0.5, ge=0.0)
    retry_max_delay_seconds: float = Field(default=30.0, ge=0.0)
    retry_backoff_factor: float = Field(default=2.0, ge=1.0)

    @staticmethod
    def _split_values(value: str) -> list[str]:
        """Разделить значение из env со списком через запятую на элементы."""

        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def city_list(self) -> list[str]:
        """Вернуть настроенные города в виде списка."""

        return self._split_values(self.cities)

    @property
    def tariff_list(self) -> list[str]:
        """Вернуть настроенные тарифы в виде списка."""

        return self._split_values(self.tariffs)

    @property
    def weather_type_list(self) -> list[str]:
        """Вернуть категории погоды поездки в виде списка."""

        return self._split_values(self.weather_types)


@dataclass(frozen=True, slots=True)
class Settings:
    """Единая точка доступа к настройкам генератора и ClickHouse."""

    generator: GeneratorSettings
    clickhouse: ClickHouseSettings


@lru_cache
def get_settings() -> Settings:
    """Создать и закэшировать настройки приложения на время процесса."""

    return Settings(generator=GeneratorSettings(), clickhouse=ClickHouseSettings())
