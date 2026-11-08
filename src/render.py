"""Визуализация графа: язык диаграмм D2, изображение SVG, ASCII-дерево."""

import html
import os
import shutil
import subprocess
from collections import deque

D2_EXT = ".d2"
ROOT_COLOR = "#fde68a"
NODE_COLOR = "#dbeafe"
CHAR_WIDTH = 8
NODE_PADDING = 24
NODE_HEIGHT = 36
GAP_X = 30
GAP_Y = 70
MARGIN = 20
D2_TIMEOUT_SEC = 120
BULGE = 45


class RenderError(Exception):
    """Ошибка построения изображения графа."""


def quote(name):
    """Записать имя пакета в кавычках для языка D2."""
    return '"' + name.replace('"', '\\"') + '"'


def to_d2(graph, root):
    """Сформировать текстовое описание графа на языке диаграмм D2.

    :param graph: словарь «пакет → список зависимостей»
    :param root: исходный пакет (выделяется цветом)
    :return: текст на языке D2
    """
    lines = [f"# Граф зависимостей пакета {root}", "direction: down", ""]
    for name in graph:
        color = ROOT_COLOR if name == root else NODE_COLOR
        lines.append(f"{quote(name)}: {{style.fill: \"{color}\"}}")
    lines.append("")
    for name, deps in graph.items():
        for dep in deps:
            lines.append(f"{quote(name)} -> {quote(dep)}")
    return "\n".join(lines) + "\n"


def compute_levels(graph, root):
    """Разбить пакеты на уровни по расстоянию от исходного (BFS).

    :return: список уровней, каждый — список пакетов
    """
    depth = {root: 0}
    queue = deque([root])
    while queue:
        name = queue.popleft()
        for dep in graph.get(name, []):
            if dep not in depth:
                depth[dep] = depth[name] + 1
                queue.append(dep)
    levels = [[] for _ in range(max(depth.values()) + 1)]
    for name in graph:
        levels[depth[name]].append(name)
    return levels


def layout(levels):
    """Рассчитать прямоугольники пакетов: уровни сверху вниз.

    :return: (словарь «пакет → (x, y, ширина)», ширина, высота рисунка)
    """
    boxes, width = {}, 0
    for row, names in enumerate(levels):
        x = MARGIN
        y = MARGIN + row * (NODE_HEIGHT + GAP_Y)
        for name in names:
            box_width = len(name) * CHAR_WIDTH + NODE_PADDING
            boxes[name] = (x, y, box_width)
            x += box_width + GAP_X
        width = max(width, x - GAP_X + MARGIN + BULGE)
    height = MARGIN * 2 + len(levels) * (NODE_HEIGHT + GAP_Y) - GAP_Y
    return boxes, width, height


def svg_edge(start, end):
    """Нарисовать стрелку от пакета к его зависимости.

    Зависимость ниже по уровню — прямая линия вниз. Зависимость на том же
    или более высоком уровне (так бывает, например, в циклах) — пунктирная
    дуга справа от прямоугольников, чтобы не накладываться на другие.
    """
    x1, y1, w1 = start
    x2, y2, w2 = end
    if y2 > y1:
        return (f'<line x1="{x1 + w1 / 2}" y1="{y1 + NODE_HEIGHT}" '
                f'x2="{x2 + w2 / 2}" y2="{y2}" stroke="#475569" '
                'marker-end="url(#arrow)"/>')
    if y2 == y1 and start != end:
        return side_edge(start, end)
    sx, sy = x1 + w1, y1 + NODE_HEIGHT / 2
    ex, ey = x2 + w2, y2 + NODE_HEIGHT / 2
    if start == end:
        ey += NODE_HEIGHT / 4
        sy -= NODE_HEIGHT / 4
    return (f'<path d="M{sx},{sy} C{sx + BULGE},{sy} {ex + BULGE},{ey} '
            f'{ex},{ey}" fill="none" stroke="#dc2626" '
            'stroke-dasharray="5,4" marker-end="url(#arrow)"/>')


def side_edge(start, end):
    """Нарисовать пунктирную стрелку между пакетами одного уровня."""
    x1, y1, w1 = start
    x2, _, w2 = end
    y = y1 + NODE_HEIGHT / 2
    sx, ex = (x1 + w1, x2) if x2 > x1 else (x1, x2 + w2)
    return (f'<line x1="{sx}" y1="{y}" x2="{ex}" y2="{y}" '
            'stroke="#dc2626" stroke-dasharray="5,4" '
            'marker-end="url(#arrow)"/>')


def svg_node(name, box, color):
    """Нарисовать прямоугольник пакета с подписью."""
    x, y, width = box
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{NODE_HEIGHT}" '
            f'rx="6" fill="{color}" stroke="#1e3a8a"/>'
            f'<text x="{x + width / 2}" y="{y + NODE_HEIGHT / 2 + 5}" '
            f'text-anchor="middle">{html.escape(name)}</text>')


def builtin_svg(graph, root):
    """Нарисовать граф в SVG без внешних программ (запасной вариант).

    Пакеты располагаются по уровням: исходный пакет сверху, ниже —
    пакеты по расстоянию от него.

    :return: текст SVG-файла
    """
    boxes, width, height = layout(compute_levels(graph, root))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" font-family="monospace" font-size="13">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#475569"/></marker></defs>',
        f'<rect width="{width}" height="{height}" fill="white"/>']
    for name, deps in graph.items():
        parts += [svg_edge(boxes[name], boxes[dep]) for dep in deps]
    for name in graph:
        color = ROOT_COLOR if name == root else NODE_COLOR
        parts.append(svg_node(name, boxes[name], color))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def run_d2(d2_path, svg_path):
    """Получить SVG из файла D2 программой d2 (если она установлена).

    :return: True, если программа d2 найдена и отработала
    :raises RenderError: если d2 завершилась с ошибкой
    """
    program = shutil.which("d2")
    if program is None:
        return False
    result = subprocess.run([program, d2_path, svg_path],
                            capture_output=True, text=True,
                            timeout=D2_TIMEOUT_SEC, check=False)
    if result.returncode:
        raise RenderError(f"программа d2 завершилась с ошибкой: "
                          f"{result.stderr.strip()}")
    return True


def save_visualization(graph, root, svg_path):
    """Сохранить описание графа на D2 и изображение в SVG.

    Изображение строится программой d2, а если она не установлена —
    встроенным рисованием.

    :return: кортеж (путь к .d2, путь к .svg, чем построено изображение)
    """
    d2_path = os.path.splitext(svg_path)[0] + D2_EXT
    try:
        with open(d2_path, "w", encoding="utf-8") as file:
            file.write(to_d2(graph, root))
        if run_d2(d2_path, svg_path):
            return d2_path, svg_path, "программа d2"
        with open(svg_path, "w", encoding="utf-8") as file:
            file.write(builtin_svg(graph, root))
    except OSError as error:
        raise RenderError(f"не удалось сохранить файл: {error}") from error
    return d2_path, svg_path, "встроенное рисование (d2 не найдена)"


def ascii_tree(graph, root):
    """Построить ASCII-дерево зависимостей (обход со стеком, без рекурсии).

    Как в ``cargo tree``: пакет, зависимости которого уже показаны выше,
    помечается ``(*)``; возврат в пакет текущей ветки — ``(цикл)``.

    :return: список строк дерева
    """
    lines, shown = [root], {root}
    stack = children_entries(graph, root, "", (root,))
    while stack:
        name, prefix, last, path = stack.pop()
        branch = prefix + ("└── " if last else "├── ")
        if name in path:
            lines.append(f"{branch}{name} (цикл)")
        elif name in shown and graph.get(name):
            lines.append(f"{branch}{name} (*)")
        else:
            shown.add(name)
            lines.append(branch + name)
            child_prefix = prefix + ("    " if last else "│   ")
            stack += children_entries(graph, name, child_prefix,
                                      path + (name,))
    return lines


def children_entries(graph, name, prefix, path):
    """Подготовить записи стека для зависимостей пакета.

    Записи кладутся в обратном порядке, чтобы первая зависимость
    оказалась на вершине стека и была выведена первой.
    """
    deps = graph.get(name, [])
    entries = [(dep, prefix, index == len(deps) - 1, path)
               for index, dep in enumerate(deps)]
    return entries[::-1]
