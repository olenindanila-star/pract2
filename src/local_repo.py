"""Тестовый репозиторий: описание графа пакетов в текстовом файле.

Формат файла — по одной строке на пакет::

    # комментарий
    A: B C      <- пакет A зависит от B и C
    B: D
    D:          <- у пакета D нет зависимостей

Пакеты называются большими латинскими буквами. Пакет, который
упоминается только как зависимость, считается пакетом без зависимостей.
"""

import re

from cargo_index import Dependency

NAME_RE = re.compile(r"^[A-Z]+$")
COMMENT = "#"
ANY_VERSION = "*"


class LocalRepoError(Exception):
    """Ошибка в файле тестового репозитория."""


def check_name(name, number):
    """Проверить имя пакета: только большие латинские буквы.

    :param name: имя пакета
    :param number: номер строки файла (для сообщения об ошибке)
    :raises LocalRepoError: если имя недопустимо
    """
    if not NAME_RE.match(name):
        raise LocalRepoError(
            f"строка {number}: недопустимое имя пакета {name!r} "
            "(только большие латинские буквы)")


def parse_line(line, number):
    """Разобрать строку ``ИМЯ: ЗАВИСИМОСТЬ ЗАВИСИМОСТЬ ...``.

    :param line: строка файла без комментария
    :param number: номер строки
    :return: кортеж (имя пакета, список зависимостей)
    :raises LocalRepoError: если строка имеет неверный формат
    """
    name, colon, rest = line.partition(":")
    if not colon:
        raise LocalRepoError(
            f"строка {number}: ожидается формат 'ИМЯ: ЗАВИСИМОСТИ'")
    name, deps = name.strip(), rest.split()
    for item in [name] + deps:
        check_name(item, number)
    return name, deps


def parse_local_repo(text):
    """Разобрать текст файла тестового репозитория.

    :param text: содержимое файла
    :return: словарь «пакет → список зависимостей»
    :raises LocalRepoError: при ошибке формата или повторе пакета
    """
    graph = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        name, deps = parse_line(line, number)
        if name in graph:
            raise LocalRepoError(
                f"строка {number}: пакет {name} описан повторно")
        graph[name] = deps
    return graph


class LocalRepository:
    """Источник зависимостей: файл тестового репозитория."""

    def __init__(self, path):
        """Загрузить файл тестового репозитория.

        :param path: путь к файлу
        :raises LocalRepoError: если файл не читается или неверен
        """
        try:
            with open(path, encoding="utf-8") as file:
                self.graph = parse_local_repo(file.read())
        except OSError as error:
            raise LocalRepoError(
                f"не удалось прочитать {path}: {error.strerror}") from error

    def check_package(self, name):
        """Проверить, что пакет описан в репозитории.

        :raises LocalRepoError: если пакета нет
        """
        if name not in self.graph:
            raise LocalRepoError(
                f"пакет {name} не найден в тестовом репозитории")

    def dependencies(self, name):
        """Вернуть прямые зависимости пакета.

        :param name: имя пакета
        :return: список Dependency
        """
        return [Dependency(dep, ANY_VERSION)
                for dep in self.graph.get(name, [])]
