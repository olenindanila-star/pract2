"""Тесты точки входа: вывод и коды завершения программы."""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from helpers import example

from main import main

INDEX = json.dumps({"name": "demo", "vers": "1.0.0", "deps": [
    {"name": "alpha", "req": "^1", "kind": "normal"}]})


def run_main(argv):
    """Запустить main и вернуть (код, вывод, вывод ошибок)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка main с подменённой загрузкой индекса."""

    def test_prints_direct_dependencies(self):
        """Выводятся прямые зависимости пакета."""
        with mock.patch("cargo_index.fetch_index", return_value=INDEX):
            code, out, _ = run_main(["-p", "demo"])
        self.assertEqual(code, 0)
        self.assertIn("Пакет: demo 1.0.0", out)
        self.assertIn("alpha ^1", out)

    def test_error_exit_code(self):
        """Ошибка в параметрах — код 1 и сообщение в stderr."""
        code, _, err = run_main(["-p", "serde", "-o", "x.png"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: --output", err)

    def test_test_mode_not_ready(self):
        """Тестовый режим появляется на этапе 3."""
        code, _, err = run_main(["-p", "A", "-m", "test",
                                 "-r", example("simple.txt")])
        self.assertEqual(code, 1)
        self.assertIn("этапа 3", err)


if __name__ == "__main__":
    unittest.main()
