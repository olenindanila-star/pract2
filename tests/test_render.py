"""Тесты визуализации: D2, SVG и ASCII-дерево."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from unittest import mock

import helpers  # noqa: F401  (добавляет src в sys.path)

from render import (RenderError, ascii_tree, builtin_svg, compute_levels,
                    run_d2, save_visualization, to_d2)

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
CYCLE = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}


class D2Test(unittest.TestCase):
    """Проверка текста на языке D2."""

    def test_nodes_and_edges(self):
        """Все пакеты и связи попадают в описание."""
        text = to_d2(DIAMOND, "A")
        self.assertIn('"A" -> "B"', text)
        self.assertIn('"C" -> "D"', text)
        self.assertIn('"D": {style.fill', text)

    def test_quotes_in_names(self):
        """Кавычки в имени экранируются."""
        self.assertIn('"a\\"b"', to_d2({'a"b': []}, 'a"b'))


class SvgTest(unittest.TestCase):
    """Проверка встроенного рисования SVG."""

    def test_levels(self):
        """Уровни по расстоянию от исходного пакета."""
        self.assertEqual(compute_levels(DIAMOND, "A"),
                         [["A"], ["B", "C"], ["D"]])

    def test_valid_svg(self):
        """Получается корректный XML с подписями всех пакетов."""
        for graph in (DIAMOND, CYCLE, {"A": ["A"]}):
            root = ElementTree.fromstring(builtin_svg(graph, "A"))
            texts = {node.text for node in root.iter()
                     if node.tag.endswith("text")}
            self.assertEqual(texts, set(graph))


class AsciiTreeTest(unittest.TestCase):
    """Проверка ASCII-дерева."""

    def test_diamond(self):
        """Повтор пакета без зависимостей не помечается."""
        self.assertEqual(ascii_tree(DIAMOND, "A"), [
            "A", "├── B", "│   └── D", "└── C", "    └── D"])

    def test_repeated_with_deps(self):
        """Повтор пакета с зависимостями помечается (*)."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["B"], "D": []}
        self.assertIn("    └── B (*)", ascii_tree(graph, "A"))

    def test_cycle(self):
        """Возврат в пакет текущей ветки помечается (цикл)."""
        self.assertIn("        ├── A (цикл)", ascii_tree(CYCLE, "A"))


class SaveTest(unittest.TestCase):
    """Проверка сохранения файлов D2 и SVG."""

    def setUp(self):
        """Временная папка для файлов."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.svg = os.path.join(self.folder.name, "graph.svg")

    def test_without_d2(self):
        """Без программы d2 используется встроенное рисование."""
        with mock.patch("shutil.which", return_value=None):
            d2_path, svg_path, method = save_visualization(
                DIAMOND, "A", self.svg)
        self.assertTrue(os.path.isfile(d2_path))
        self.assertTrue(os.path.isfile(svg_path))
        self.assertIn("встроенное", method)

    def test_d2_failure(self):
        """Ошибка программы d2 превращается в RenderError."""
        failed = mock.Mock(returncode=1, stderr="bad syntax")
        with mock.patch("shutil.which", return_value="d2"), \
                mock.patch("subprocess.run", return_value=failed):
            with self.assertRaisesRegex(RenderError, "bad syntax"):
                run_d2("in.d2", self.svg)

    def test_unwritable_path(self):
        """Нельзя записать файл — RenderError."""
        path = os.path.join(self.folder.name, "missing", "graph.svg")
        with self.assertRaises(RenderError):
            save_visualization(DIAMOND, "A", path)


if __name__ == "__main__":
    unittest.main()
