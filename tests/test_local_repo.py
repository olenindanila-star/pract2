"""Тесты тестового репозитория (файл с графом пакетов)."""

import unittest

from helpers import example

from local_repo import LocalRepoError, LocalRepository, parse_local_repo


class ParseLocalRepoTest(unittest.TestCase):
    """Проверка разбора файла тестового репозитория."""

    def test_parse(self):
        """Строки «ИМЯ: ЗАВИСИМОСТИ», комментарии и пустые строки."""
        text = "# граф\n\nA: B C  # комментарий\nB:\n"
        self.assertEqual(parse_local_repo(text), {"A": ["B", "C"], "B": []})

    def test_no_colon(self):
        """Строка без двоеточия — ошибка с номером строки."""
        with self.assertRaisesRegex(LocalRepoError, "строка 2"):
            parse_local_repo("A: B\nB C\n")

    def test_lowercase_name(self):
        """Имена — только большие латинские буквы."""
        with self.assertRaisesRegex(LocalRepoError, "недопустимое имя"):
            parse_local_repo("A: b\n")

    def test_duplicate(self):
        """Пакет нельзя описать дважды."""
        with self.assertRaisesRegex(LocalRepoError, "повторно"):
            parse_local_repo("A: B\nA: C\n")


class LocalRepositoryTest(unittest.TestCase):
    """Проверка источника зависимостей из файла."""

    def test_dependencies(self):
        """Зависимости читаются из файла; неописанный пакет — лист."""
        repo = LocalRepository(example("simple.txt"))
        self.assertEqual([d.name for d in repo.dependencies("A")],
                         ["B", "C"])
        self.assertEqual(repo.dependencies("Z"), [])

    def test_missing_package(self):
        """Исходного пакета нет в репозитории — ошибка."""
        repo = LocalRepository(example("simple.txt"))
        with self.assertRaisesRegex(LocalRepoError, "не найден"):
            repo.check_package("Z")

    def test_missing_file(self):
        """Файл не найден — ошибка."""
        with self.assertRaises(LocalRepoError):
            LocalRepository(example("no_such_file.txt"))

    def test_error_files(self):
        """Примеры файлов с ошибками отклоняются."""
        for name in ("bad_name.txt", "bad_format.txt"):
            with self.assertRaises(LocalRepoError):
                LocalRepository(example(name))


if __name__ == "__main__":
    unittest.main()
