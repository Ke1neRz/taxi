"""Командная точка входа генератора такси."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Разобрать параметры генератора до реализации сервисного цикла."""

    parser = argparse.ArgumentParser(prog="taxi-generator")
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--repository", choices=("in-memory", "clickhouse"), default="in-memory"
    )
    parser.parse_args(argv)
    raise NotImplementedError("generation service is added in a later roadmap step")


if __name__ == "__main__":
    raise SystemExit(main())
