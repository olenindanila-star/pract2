"""Тесты порядка загрузки зависимостей."""

import unittest

from helpers import example

from graph import build_graph
from load_order import describe_load_order, load_order
from local_repo import LocalRepository


def order_of(name):
    """Порядок загрузки пакета A из файла examples/<name>."""
    graph = build_graph("A", LocalRepository(example(name)))
    return load_order(graph)


class LoadOrderTest(unittest.TestCase):
    """Проверка load_order на тестовых репозиториях."""

    def assert_before(self, order, first, second):
        """Проверить, что пакет first загружается раньше second."""
        self.assertLess(order.index(first), order.index(second))

    def test_simple(self):
        """Ромб: D первым, A последним."""
        self.assertEqual(order_of("simple.txt"), (["D", "B", "C", "A"], []))

    def test_layers(self):
        """Каждая зависимость раньше зависящего от неё пакета."""
        order, blocked = order_of("layers.txt")
        self.assertEqual(blocked, [])
        graph = LocalRepository(example("layers.txt")).graph
        for name, deps in graph.items():
            for dep in deps:
                self.assert_before(order, dep, name)

    def test_cycle(self):
        """Пакеты цикла упорядочить нельзя, D — можно."""
        self.assertEqual(order_of("cycle.txt"), (["D"], ["A", "B", "C"]))

    def test_self_cycle(self):
        """Пакет, зависящий сам от себя, не упорядочивается."""
        self.assertEqual(order_of("self_cycle.txt"), (["B"], ["A"]))

    def test_duplicate_edges(self):
        """Повторная зависимость не мешает загрузке."""
        self.assertEqual(load_order({"A": ["B", "B"], "B": []}),
                         (["B", "A"], []))

    def test_describe(self):
        """Вывод: нумерованный список и пакеты в циклах."""
        lines = describe_load_order({"A": ["B"], "B": ["A"], "C": []})
        self.assertIn("  1. C", lines)
        self.assertIn("A, B", lines[-1])


if __name__ == "__main__":
    unittest.main()
