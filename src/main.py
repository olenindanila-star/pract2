"""Точка входа: визуализатор графа зависимостей пакетов Rust (Cargo)."""

import sys

from cargo_index import CargoRegistry, RegistryError
from config import MODE_TEST, ConfigError, parse_config
from console import setup_console
from graph import GraphError, build_graph, count_edges, find_cycles
from local_repo import LocalRepoError, LocalRepository

ERRORS = (ConfigError, RegistryError, LocalRepoError, GraphError)


def make_source(config):
    """Создать источник зависимостей по режиму работы.

    :param config: объект Config
    :return: LocalRepository (режим test) или CargoRegistry (режим real)
    """
    if config.mode == MODE_TEST:
        repo = LocalRepository(config.repo)
        repo.check_package(config.package)
        return repo
    return CargoRegistry(config.repo)


def describe_graph(config, graph):
    """Сформировать текстовое описание графа зависимостей.

    :param config: объект Config
    :param graph: словарь «пакет → список зависимостей»
    :return: список строк для вывода
    """
    source = "тестовый" if config.mode == MODE_TEST else "реестр Cargo"
    lines = [f"Граф зависимостей пакета {config.package}",
             f"Репозиторий ({source}): {config.repo}"]
    if config.exclude:
        lines.append(f"Фильтр: исключены пакеты с {config.exclude!r}")
    for name, deps in graph.items():
        lines.append(f"  {name} -> {', '.join(deps) or '(нет зависимостей)'}")
    lines.append(f"Пакетов: {len(graph)}, связей: {count_edges(graph)}")
    cycles = find_cycles(graph)
    if not cycles:
        lines.append("Циклические зависимости: не обнаружены")
    for cycle in cycles:
        lines.append(f"Циклическая зависимость: {' -> '.join(cycle)}")
    return lines


def main(argv=None):
    """Разобрать параметры, построить граф зависимостей и вывести его.

    :param argv: параметры командной строки (None — взять из sys.argv)
    :return: код завершения: 0 — успех, 1 — ошибка
    """
    setup_console()
    try:
        config = parse_config(argv)
        source = make_source(config)
        graph = build_graph(config.package, source, config.exclude)
    except ERRORS as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    for line in describe_graph(config, graph):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
