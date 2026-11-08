"""Тесты разбора индекса реестра Cargo (без обращения к сети)."""

import io
import json
import unittest
import urllib.error
from unittest import mock

import helpers  # noqa: F401  (добавляет src в sys.path)

from cargo_index import (CargoRegistry, Dependency, RegistryError,
                         direct_dependencies, fetch_index, index_path,
                         parse_versions, select_latest, version_key)


def make_index(*versions):
    """Собрать текст файла индекса из словарей версий."""
    return "\n".join(json.dumps(item) for item in versions) + "\n"


SAMPLE = make_index(
    {"name": "demo", "vers": "1.0.0", "yanked": False, "deps": []},
    {"name": "demo", "vers": "1.2.0", "yanked": False, "deps": [
        {"name": "alpha", "req": "^1", "kind": "normal"},
        {"name": "beta", "req": "^2", "kind": None},
        {"name": "tester", "req": "^1", "kind": "dev"},
        {"name": "builder", "req": "^1", "kind": "build"},
        {"name": "extra", "req": "^1", "kind": "normal", "optional": True},
        {"name": "short", "req": "^3", "kind": "normal",
         "package": "real-name", "target": "cfg(windows)"},
    ]},
    {"name": "demo", "vers": "2.0.0", "yanked": True, "deps": []},
    {"name": "demo", "vers": "1.3.0-beta", "yanked": False, "deps": []},
)


class IndexPathTest(unittest.TestCase):
    """Проверка путей пакетов в sparse-индексе."""

    def test_paths(self):
        """Пути для имён разной длины."""
        self.assertEqual(index_path("a"), "1/a")
        self.assertEqual(index_path("ab"), "2/ab")
        self.assertEqual(index_path("abc"), "3/a/abc")
        self.assertEqual(index_path("Serde"), "se/rd/serde")


class ParseTest(unittest.TestCase):
    """Проверка разбора версий и зависимостей."""

    def test_parse_versions(self):
        """Каждая строка — отдельная версия."""
        self.assertEqual(len(parse_versions(SAMPLE)), 4)

    def test_bad_json(self):
        """Строка не JSON — ошибка с номером строки."""
        with self.assertRaisesRegex(RegistryError, "строка 2"):
            parse_versions('{"vers": "1.0.0"}\n{oops\n')

    def test_version_key(self):
        """Сравнение версий: числа и предварительные версии."""
        self.assertLess(version_key("1.9.0"), version_key("1.10.0"))
        self.assertLess(version_key("1.3.0-beta"), version_key("1.3.0"))

    def test_select_latest(self):
        """Отозванные и предварительные версии не выбираются."""
        latest = select_latest(parse_versions(SAMPLE))
        self.assertEqual(latest["vers"], "1.3.0-beta")
        stable = [v for v in parse_versions(SAMPLE) if "-" not in v["vers"]]
        self.assertEqual(select_latest(stable)["vers"], "1.2.0")

    def test_all_yanked(self):
        """Все версии отозваны — ошибка."""
        with self.assertRaises(RegistryError):
            select_latest([{"vers": "1.0.0", "yanked": True}])

    def test_direct_dependencies(self):
        """Только обычные обязательные зависимости, с настоящими именами."""
        version = parse_versions(SAMPLE)[1]
        self.assertEqual(direct_dependencies(version), [
            Dependency("alpha", "^1"), Dependency("beta", "^2"),
            Dependency("real-name", "^3", "cfg(windows)")])


class FetchTest(unittest.TestCase):
    """Проверка загрузки индекса и обработки сетевых ошибок."""

    def test_not_found(self):
        """HTTP 404 — пакет не найден."""
        error = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(RegistryError, "не найден"):
                fetch_index("https://index.crates.io", "nothing")

    def test_no_network(self):
        """Сеть недоступна — ошибка подключения."""
        error = urllib.error.URLError("no route")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(RegistryError, "подключиться"):
                fetch_index("https://index.crates.io", "serde")

    def test_success(self):
        """Текст индекса возвращается из ответа сервера."""
        response = io.BytesIO(SAMPLE.encode("utf-8"))
        with mock.patch("urllib.request.urlopen", return_value=response):
            self.assertEqual(fetch_index("https://x.org/", "demo"), SAMPLE)

    def test_registry_cache(self):
        """Реестр скачивает индекс пакета только один раз."""
        fetch = mock.Mock(return_value=SAMPLE)
        registry = CargoRegistry("https://x.org", fetch=fetch)
        registry.dependencies("demo")
        registry.dependencies("demo")
        fetch.assert_called_once_with("https://x.org", "demo")


if __name__ == "__main__":
    unittest.main()
