"""Проверить ожидание готовности ClickHouse перед запуском генератора."""

from __future__ import annotations

import argparse
import time

from _clickhouse import is_ready

from generator.config import get_settings


def main() -> None:
    """Ожидать ClickHouse ограниченное время и вернуть понятный результат."""

    parser = argparse.ArgumentParser(description="Ожидание готовности ClickHouse")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    settings = get_settings().clickhouse
    deadline = time.monotonic() + args.timeout

    print(f"Ожидаю ClickHouse на {settings.host}:{settings.port}")
    while time.monotonic() < deadline:
        if is_ready(settings):
            print("ClickHouse готов.")
            return
        time.sleep(1.0)

    raise SystemExit(f"ClickHouse не готов за {args.timeout:.0f} секунд.")


if __name__ == "__main__":
    main()
