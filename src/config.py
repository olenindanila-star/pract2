"""Параметры командной строки и их проверка."""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

DEFAULT_REPO = "https://index.crates.io"
DEFAULT_OUTPUT = "graph.svg"
MODE_REAL = "real"
MODE_TEST = "test"
MODES = (MODE_REAL, MODE_TEST)
YES = "yes"
YES_NO = (YES, "no")
IMAGE_EXT = ".svg"
MAX_NAME_LEN = 64
CRATE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")
URL_SCHEMES = ("http", "https")


class ConfigError(Exception):
    """Ошибка в параметрах командной строки."""


@dataclass
class Config:
    """Настройки, заданные пользователем.

    :ivar package: имя анализируемого пакета
    :ivar repo: URL-адрес репозитория или путь к файлу тестового репозитория
    :ivar mode: режим работы: ``real`` или ``test``
    :ivar output: имя файла с изображением графа (SVG)
    :ivar ascii_tree: выводить ли зависимости в виде ASCII-дерева
    :ivar exclude: подстрока для фильтрации пакетов (или None)
    :ivar load_order: выводить ли порядок загрузки зависимостей
    """

    package: str
    repo: str
    mode: str
    output: str
    ascii_tree: bool
    exclude: str = None
    load_order: bool = False


class RussianArgumentParser(argparse.ArgumentParser):
    """Парсер аргументов, который бросает ConfigError вместо выхода."""

    def error(self, message):
        """Превратить ошибку argparse в ConfigError."""
        raise ConfigError(f"неверные параметры командной строки: {message}")


def build_parser():
    """Создать парсер параметров командной строки.

    :return: объект ArgumentParser
    """
    parser = RussianArgumentParser(
        description="Визуализатор графа зависимостей пакетов Rust (Cargo)")
    parser.add_argument("-p", "--package", help="имя анализируемого пакета")
    parser.add_argument("-r", "--repo", default=DEFAULT_REPO,
                        help="URL репозитория или путь к тестовому файлу")
    parser.add_argument("-m", "--mode", default=MODE_REAL,
                        help="режим работы: real или test")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        help="имя файла с изображением графа (.svg)")
    parser.add_argument("-a", "--ascii-tree", default="no",
                        help="вывод ASCII-дерева: yes или no")
    parser.add_argument("-f", "--filter", dest="exclude",
                        help="исключить пакеты, содержащие подстроку")
    parser.add_argument("-l", "--load-order", default="no",
                        help="вывод порядка загрузки: yes или no")
    return parser


def validate_mode(mode):
    """Проверить режим работы."""
    if mode not in MODES:
        raise ConfigError(
            f"--mode: неизвестный режим {mode!r}, допустимо: real, test")


def validate_package(name, mode):
    """Проверить имя пакета с учётом режима работы."""
    if not name:
        raise ConfigError("--package: имя пакета не задано")
    if len(name) > MAX_NAME_LEN:
        raise ConfigError(
            f"--package: имя длиннее {MAX_NAME_LEN} символов")
    if mode == MODE_TEST and not TEST_NAME_RE.match(name):
        raise ConfigError(
            "--package: в режиме test имя пакета — большие латинские буквы")
    if not CRATE_NAME_RE.match(name):
        raise ConfigError(
            f"--package: недопустимое имя пакета {name!r} (разрешены "
            "латинские буквы, цифры, '-' и '_', начало — с буквы)")


def validate_repo(repo, mode):
    """Проверить URL репозитория или путь к тестовому файлу."""
    if not repo:
        raise ConfigError("--repo: репозиторий не задан")
    if mode == MODE_TEST:
        if not os.path.isfile(repo):
            raise ConfigError(
                f"--repo: файл тестового репозитория {repo!r} не найден")
        return
    url = urlparse(repo)
    if url.scheme not in URL_SCHEMES or not url.netloc:
        raise ConfigError(
            f"--repo: {repo!r} не является URL-адресом (http/https)")


def validate_output(path):
    """Проверить имя файла с изображением графа."""
    base, ext = os.path.splitext(os.path.basename(path))
    if not base:
        raise ConfigError("--output: имя файла не задано")
    if ext.lower() != IMAGE_EXT:
        raise ConfigError(
            f"--output: файл должен иметь расширение {IMAGE_EXT}")
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        raise ConfigError(f"--output: папка {folder!r} не существует")


def validate_yes_no(value, option):
    """Проверить значение yes/no."""
    if value not in YES_NO:
        raise ConfigError(f"{option}: ожидается yes или no, а не {value!r}")


def validate_filter(value):
    """Проверить подстроку для фильтрации пакетов."""
    if value is None:
        return
    if not value or value != value.strip() or " " in value:
        raise ConfigError(
            "--filter: подстрока не должна быть пустой и содержать пробелы")


def parse_config(argv=None):
    """Разобрать и проверить параметры командной строки.

    :param argv: список параметров (None — взять из sys.argv)
    :return: объект Config
    :raises ConfigError: если параметр задан неверно
    """
    args = build_parser().parse_args(argv)
    validate_mode(args.mode)
    validate_package(args.package, args.mode)
    validate_repo(args.repo, args.mode)
    validate_output(args.output)
    validate_yes_no(args.ascii_tree, "--ascii-tree")
    validate_filter(args.exclude)
    validate_yes_no(args.load_order, "--load-order")
    return Config(package=args.package, repo=args.repo, mode=args.mode,
                  output=args.output, ascii_tree=args.ascii_tree == YES,
                  exclude=args.exclude, load_order=args.load_order == YES)


def format_config(config):
    """Сформировать вывод параметров в формате ключ-значение.

    :param config: объект Config
    :return: список строк ``ключ = значение``
    """
    pairs = [
        ("package", config.package),
        ("repo", config.repo),
        ("mode", config.mode),
        ("output", config.output),
        ("ascii-tree", YES if config.ascii_tree else "no"),
        ("filter", config.exclude),
        ("load-order", YES if config.load_order else "no"),
    ]
    return [f"{key} = {value}" for key, value in pairs]
