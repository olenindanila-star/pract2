"""Порядок загрузки зависимостей (топологическая сортировка)."""

from collections import deque


def build_dependents(graph):
    """Построить обратные связи: пакет → пакеты, которые от него зависят.

    :param graph: словарь «пакет → список зависимостей»
    :return: словарь «пакет → список зависящих от него пакетов»
    """
    dependents = {name: [] for name in graph}
    for name, deps in graph.items():
        for dep in set(deps):
            dependents.setdefault(dep, []).append(name)
    return dependents


def load_order(graph):
    """Вычислить порядок загрузки: зависимости раньше зависящих пакетов.

    Алгоритм Кана (без рекурсии). Сначала загружаются пакеты без
    зависимостей; пакет загружается, когда загружены все его зависимости.
    Пакеты, входящие в цикл (и зависящие от цикла), упорядочить нельзя —
    они возвращаются отдельным списком.

    :param graph: словарь «пакет → список зависимостей»
    :return: кортеж (порядок загрузки, неупорядоченные пакеты)
    """
    waiting = {name: len(set(deps)) for name, deps in graph.items()}
    dependents = build_dependents(graph)
    queue = deque(sorted(name for name, count in waiting.items()
                         if not count))
    order = []
    while queue:
        name = queue.popleft()
        order.append(name)
        for parent in sorted(dependents.get(name, [])):
            waiting[parent] -= 1
            if not waiting[parent]:
                queue.append(parent)
    loaded = set(order)
    blocked = [name for name in graph if name not in loaded]
    return order, blocked


def describe_load_order(graph):
    """Сформировать вывод порядка загрузки зависимостей.

    :param graph: словарь «пакет → список зависимостей»
    :return: список строк
    """
    order, blocked = load_order(graph)
    lines = ["Порядок загрузки зависимостей (сначала зависимости):"]
    lines += [f"  {number}. {name}"
              for number, name in enumerate(order, start=1)]
    if blocked:
        lines.append("Не могут быть загружены из-за циклических "
                     f"зависимостей: {', '.join(blocked)}")
    return lines
