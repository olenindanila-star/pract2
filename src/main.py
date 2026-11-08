"""Точка входа: визуализатор графа зависимостей пакетов Rust (Cargo)."""

import sys

from cargo_index import CargoRegistry, RegistryError
from config import MODE_TEST, ConfigError, parse_config
from console import setup_console
from graph import GraphError, build_graph, count_edges, find_cycles
from load_order import describe_load_order
from local_repo import LocalRepoError, LocalRepository
from render import RenderError, ascii_tree, save_visualization

ERRORS = (ConfigError, RegistryError, LocalRepoError, GraphError,
          RenderError)


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


def visualize(config, graph):
    """Сохранить D2 и SVG и сформировать вывод визуализации.

    :param config: объект Config
    :param graph: словарь «пакет → список зависимостей»
    :return: список строк для вывода
    """
    d2_path, svg_path, method = save_visualization(
        graph, config.package, config.output)
    lines = [f"Описание графа на языке D2: {d2_path}",
             f"Изображение графа (SVG): {svg_path} — {method}"]
    if config.ascii_tree:
        lines += ["ASCII-дерево зависимостей:"]
        lines += ascii_tree(graph, config.package)
    return lines


def run(config):
    """Построить граф и вывести всё, что запросил пользователь.

    :param config: объект Config
    :return: список строк для вывода
    """
    graph = build_graph(config.package, make_source(config), config.exclude)
    lines = describe_graph(config, graph)
    if config.load_order:
        lines += describe_load_order(graph)
    return lines + visualize(config, graph)


def main(argv=None):
    """Разобрать параметры, построить и визуализировать граф зависимостей.

    :param argv: параметры командной строки (None — взять из sys.argv)
    :return: код завершения: 0 — успех, 1 — ошибка
    """
    setup_console()
    try:
        lines = run(parse_config(argv))
    except ERRORS as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
