"""Точка входа: визуализатор графа зависимостей пакетов Rust (Cargo)."""

import sys

from cargo_index import CargoRegistry, RegistryError
from config import MODE_TEST, ConfigError, parse_config
from console import setup_console


def show_direct_dependencies(config):
    """Вывести прямые зависимости пакета из реестра Cargo.

    :param config: объект Config
    """
    registry = CargoRegistry(config.repo)
    version = registry.latest(config.package)
    deps = registry.dependencies(config.package)
    print(f"Пакет: {version['name']} {version['vers']}")
    print(f"Прямые зависимости ({len(deps)}):")
    for dep in deps:
        target = f"  [только для {dep.target}]" if dep.target else ""
        print(f"  {dep.name} {dep.req}{target}")


def main(argv=None):
    """Разобрать параметры и вывести прямые зависимости пакета.

    :param argv: параметры командной строки (None — взять из sys.argv)
    :return: код завершения: 0 — успех, 1 — ошибка
    """
    setup_console()
    try:
        config = parse_config(argv)
        if config.mode == MODE_TEST:
            raise ConfigError("режим test поддерживается начиная с этапа 3")
        show_direct_dependencies(config)
    except (ConfigError, RegistryError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
