"""Точка входа: визуализатор графа зависимостей пакетов Rust (Cargo)."""

import sys

from config import ConfigError, format_config, parse_config
from console import setup_console


def main(argv=None):
    """Разобрать параметры и вывести их в формате ключ-значение.

    :param argv: параметры командной строки (None — взять из sys.argv)
    :return: код завершения: 0 — успех, 1 — ошибка
    """
    setup_console()
    try:
        config = parse_config(argv)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    for line in format_config(config):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
