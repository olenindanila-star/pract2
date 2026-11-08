"""Тесты разбора и проверки параметров командной строки."""

import unittest

from helpers import example

from config import ConfigError, format_config, parse_config


class ParseConfigTest(unittest.TestCase):
    """Проверка parse_config: значения по умолчанию и ошибки."""

    def assert_error(self, argv, text):
        """Проверить, что параметры вызывают ConfigError с текстом."""
        with self.assertRaises(ConfigError) as context:
            parse_config(argv)
        self.assertIn(text, str(context.exception))

    def test_defaults(self):
        """Заданы только обязательные параметры."""
        config = parse_config(["--package", "serde"])
        self.assertEqual(config.repo, "https://index.crates.io")
        self.assertEqual(config.mode, "real")
        self.assertEqual(config.output, "graph.svg")
        self.assertFalse(config.ascii_tree)
        self.assertIsNone(config.exclude)

    def test_all_params(self):
        """Все параметры заданы в тестовом режиме."""
        config = parse_config([
            "-p", "A", "-r", example("simple.txt"), "-m", "test",
            "-o", "out.svg", "-a", "yes", "-f", "B"])
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.exclude, "B")

    def test_missing_package(self):
        """Имя пакета обязательно."""
        self.assert_error([], "--package")

    def test_bad_package_name(self):
        """Недопустимые символы в имени пакета."""
        self.assert_error(["-p", "1bad name"], "недопустимое имя")

    def test_long_package_name(self):
        """Слишком длинное имя пакета."""
        self.assert_error(["-p", "a" * 65], "длиннее")

    def test_test_mode_lowercase(self):
        """В тестовом режиме имя — большие латинские буквы."""
        self.assert_error(["-p", "a", "-m", "test", "-r",
                           example("simple.txt")], "большие латинские")

    def test_bad_url(self):
        """Репозиторий в обычном режиме должен быть URL."""
        self.assert_error(["-p", "serde", "-r", "index.crates.io"], "URL")

    def test_missing_test_file(self):
        """Файл тестового репозитория должен существовать."""
        self.assert_error(["-p", "A", "-m", "test", "-r", "nofile.txt"],
                          "не найден")

    def test_bad_mode(self):
        """Неизвестный режим работы."""
        self.assert_error(["-p", "serde", "-m", "fast"], "--mode")

    def test_bad_output_ext(self):
        """Файл изображения должен быть .svg."""
        self.assert_error(["-p", "serde", "-o", "graph.png"], ".svg")

    def test_output_missing_folder(self):
        """Папка для изображения должна существовать."""
        self.assert_error(["-p", "serde", "-o", "no/such/dir/g.svg"],
                          "не существует")

    def test_bad_ascii_tree(self):
        """Режим ASCII-дерева — только yes или no."""
        self.assert_error(["-p", "serde", "-a", "maybe"], "--ascii-tree")

    def test_empty_filter(self):
        """Пустая подстрока фильтра — ошибка."""
        self.assert_error(["-p", "serde", "-f", ""], "--filter")

    def test_unknown_option(self):
        """Неизвестный параметр командной строки."""
        self.assert_error(["-p", "serde", "--color"], "неверные параметры")

    def test_format_config(self):
        """Вывод параметров в формате ключ-значение."""
        lines = format_config(parse_config(["-p", "serde", "-f", "test"]))
        self.assertIn("package = serde", lines)
        self.assertIn("filter = test", lines)
        self.assertIn("ascii-tree = no", lines)


if __name__ == "__main__":
    unittest.main()
