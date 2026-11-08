"""Построение графа зависимостей и поиск циклов (без рекурсии)."""

from collections import deque


class GraphError(Exception):
    """Ошибка построения графа зависимостей."""


def is_excluded(name, exclude):
    """Проверить, исключён ли пакет фильтром.

    :param name: имя пакета
    :param exclude: подстрока фильтра или None
    :return: True, если имя содержит подстроку
    """
    return bool(exclude) and exclude in name


def build_graph(root, source, exclude=None):
    """Построить граф зависимостей пакета обходом в ширину (BFS).

    Рекурсия не используется: пакеты обрабатываются по очереди (deque).
    Каждый пакет обрабатывается один раз (множество ``seen``), поэтому
    циклические зависимости не приводят к бесконечному обходу.

    :param root: имя исходного пакета
    :param source: источник с методом ``dependencies(name)``
    :param exclude: подстрока; пакеты, содержащие её, не анализируются
    :return: словарь «пакет → список прямых зависимостей» в порядке BFS
    :raises GraphError: если исходный пакет сам попадает под фильтр
    """
    if is_excluded(root, exclude):
        raise GraphError(
            f"пакет {root} содержит подстроку фильтра {exclude!r}")
    graph = {}
    seen = {root}
    queue = deque([root])
    while queue:
        name = queue.popleft()
        deps = [dep.name for dep in source.dependencies(name)
                if not is_excluded(dep.name, exclude)]
        graph[name] = deps
        for dep in deps:
            if dep not in seen:
                seen.add(dep)
                queue.append(dep)
    return graph


def find_cycles(graph):
    """Найти циклические зависимости обходом в глубину со стеком.

    Рекурсия не используется: путь обхода хранится в явном стеке.
    Пакет «серый», пока он на текущем пути; ребро в серый пакет
    означает цикл.

    :param graph: словарь «пакет → список зависимостей»
    :return: список циклов, каждый — список пакетов ``[A, B, A]``
    """
    on_path, done, cycles = set(), set(), []
    for start in graph:
        if start in done:
            continue
        stack = [(start, iter(graph.get(start, [])))]
        path = [start]
        on_path.add(start)
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                path.pop()
                on_path.discard(node)
                done.add(node)
            elif child in on_path:
                cycles.append(path[path.index(child):] + [child])
            elif child not in done:
                stack.append((child, iter(graph.get(child, []))))
                path.append(child)
                on_path.add(child)
    return cycles


def count_edges(graph):
    """Посчитать количество связей (рёбер) в графе."""
    return sum(len(deps) for deps in graph.values())
