"""Тесты точки входа: вывод и коды завершения программы."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from helpers import example

from main import main

INDEX = json.dumps({"name": "demo", "vers": "1.0.0", "deps": [
    {"name": "alpha", "req": "^1", "kind": "normal"}]})
LEAF = json.dumps({"name": "alpha", "vers": "1.0.0", "deps": []})


def run_main(argv):
    """Запустить main и вернуть (код, вывод, вывод ошибок)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка main с подменённой загрузкой индекса."""

    def setUp(self):
        """Изображения сохраняются во временную папку, без программы d2."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.svg = os.path.join(folder.name, "graph.svg")
        patcher = mock.patch("shutil.which", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_ok(self, argv):
        """Запустить main с выводом изображения во временную папку."""
        code, out, err = run_main(argv + ["-o", self.svg])
        self.assertEqual(code, 0, err)
        return out

    def test_real_mode_graph(self):
        """Граф строится по данным реестра (загрузка подменена)."""
        index = {"demo": INDEX, "alpha": LEAF}
        with mock.patch("cargo_index.fetch_index",
                        side_effect=lambda repo, name: index[name]):
            out = self.run_ok(["-p", "demo"])
        self.assertIn("demo -> alpha", out)
        self.assertIn("alpha -> (нет зависимостей)", out)

    def test_test_mode_graph(self):
        """Граф тестового репозитория с циклом."""
        out = self.run_ok(["-p", "A", "-m", "test",
                           "-r", example("cycle.txt")])
        self.assertIn("A -> B", out)
        self.assertIn("Циклическая зависимость: A -> B -> C -> A", out)

    def test_error_exit_code(self):
        """Ошибка в параметрах — код 1 и сообщение в stderr."""
        code, _, err = run_main(["-p", "serde", "-o", "x.png"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: --output", err)

    def test_load_order(self):
        """С --load-order yes выводится порядок загрузки."""
        out = self.run_ok(["-p", "A", "-m", "test", "-l", "yes",
                           "-r", example("simple.txt")])
        self.assertIn("Порядок загрузки", out)
        self.assertIn("  4. A", out)

    def test_visualization(self):
        """Сохраняются D2 и SVG, выводится ASCII-дерево."""
        out = self.run_ok(["-p", "A", "-m", "test", "-a", "yes",
                           "-r", example("simple.txt")])
        self.assertTrue(os.path.isfile(self.svg))
        self.assertTrue(os.path.isfile(self.svg[:-4] + ".d2"))
        self.assertIn("ASCII-дерево", out)
        self.assertIn("└── C", out)

    def test_missing_test_package(self):
        """Пакета нет в тестовом репозитории — код 1."""
        code, _, err = run_main(["-p", "Z", "-m", "test",
                                 "-r", example("simple.txt")])
        self.assertEqual(code, 1)
        self.assertIn("не найден", err)


if __name__ == "__main__":
    unittest.main()
