"""Тесты точки входа: коды завершения программы."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import helpers  # noqa: F401  (добавляет src в sys.path)

from main import main


def run_main(argv):
    """Запустить main и вернуть (код, вывод, вывод ошибок)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка main: успешный запуск и ошибка параметров."""

    def test_prints_params(self):
        """Успешный запуск выводит параметры «ключ = значение»."""
        code, out, _ = run_main(["-p", "serde"])
        self.assertEqual(code, 0)
        self.assertIn("package = serde", out)
        self.assertIn("mode = real", out)

    def test_error_exit_code(self):
        """Ошибка в параметрах — код 1 и сообщение в stderr."""
        code, _, err = run_main(["-p", "serde", "-o", "x.png"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка: --output", err)


if __name__ == "__main__":
    unittest.main()
