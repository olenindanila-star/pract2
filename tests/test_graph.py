"""Тесты построения графа (BFS) и поиска циклов."""

import unittest
from unittest import mock

from helpers import example

from graph import GraphError, build_graph, count_edges, find_cycles
from local_repo import LocalRepository


def graph_of(name, exclude=None):
    """Построить граф пакета A из файла examples/<name>."""
    return build_graph("A", LocalRepository(example(name)), exclude)


class BuildGraphTest(unittest.TestCase):
    """Проверка build_graph на тестовых репозиториях."""

    def test_simple(self):
        """Ромб: общая зависимость D обрабатывается один раз."""
        graph = graph_of("simple.txt")
        self.assertEqual(graph, {"A": ["B", "C"], "B": ["D"],
                                 "C": ["D"], "D": []})
        self.assertEqual(count_edges(graph), 4)

    def test_bfs_order(self):
        """Пакеты обходятся по уровням (в ширину)."""
        graph = graph_of("complex.txt")
        self.assertEqual(list(graph)[:7], ["A", "B", "C", "D", "E", "F", "G"])

    def test_unreachable_not_included(self):
        """Недостижимый пакет M не попадает в граф."""
        self.assertNotIn("M", graph_of("complex.txt"))

    def test_cycle_terminates(self):
        """Цикл не приводит к бесконечному обходу."""
        self.assertEqual(graph_of("cycle.txt")["C"], ["A", "D"])

    def test_filter(self):
        """Пакеты с подстрокой фильтра не анализируются."""
        graph = graph_of("complex.txt", exclude="F")
        self.assertNotIn("F", graph)
        self.assertEqual(graph["B"], ["E"])

    def test_root_filtered(self):
        """Исходный пакет под фильтром — ошибка."""
        with self.assertRaises(GraphError):
            graph_of("simple.txt", exclude="A")

    def test_each_package_requested_once(self):
        """Зависимости каждого пакета запрашиваются один раз."""
        repo = LocalRepository(example("cycle.txt"))
        with mock.patch.object(repo, "dependencies",
                               wraps=repo.dependencies) as spy:
            build_graph("A", repo)
        self.assertEqual(spy.call_count, 4)


class FindCyclesTest(unittest.TestCase):
    """Проверка поиска циклических зависимостей."""

    def test_no_cycles(self):
        """В ромбе циклов нет."""
        self.assertEqual(find_cycles(graph_of("simple.txt")), [])

    def test_cycle(self):
        """Цикл A -> B -> C -> A."""
        self.assertEqual(find_cycles(graph_of("cycle.txt")),
                         [["A", "B", "C", "A"]])

    def test_self_cycle(self):
        """Пакет зависит сам от себя."""
        self.assertEqual(find_cycles(graph_of("self_cycle.txt")),
                         [["A", "A"]])

    def test_two_cycles(self):
        """В большом графе два цикла."""
        cycles = find_cycles(graph_of("complex.txt"))
        self.assertIn(["B", "E", "I", "B"], cycles)
        self.assertIn(["J", "K", "L", "J"], cycles)


if __name__ == "__main__":
    unittest.main()
