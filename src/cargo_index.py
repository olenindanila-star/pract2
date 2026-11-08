"""Получение зависимостей пакетов Rust из индекса реестра (Cargo).

Используется формат «sparse index» реестра crates.io. Для каждого пакета
по адресу ``<repo>/<путь пакета>`` лежит текстовый файл, в котором каждая
строка — JSON-описание одной версии пакета: имя, номер версии, список
зависимостей. Сторонние библиотеки и менеджеры пакетов не используются:
файл скачивается модулем ``urllib`` и разбирается модулем ``json``.
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

TIMEOUT_SEC = 30
SHORT_NAME_MAX = 2
MEDIUM_NAME_LEN = 3
PREFIX_LEN = 2
HTTP_NOT_FOUND = 404
NORMAL_KIND = "normal"
USER_AGENT = "dependency-graph-student-project (python urllib)"


class RegistryError(Exception):
    """Ошибка получения данных из репозитория пакетов."""


@dataclass(frozen=True)
class Dependency:
    """Прямая зависимость пакета.

    :ivar name: имя пакета-зависимости
    :ivar req: требование к версии, например ``^1.0``
    :ivar target: условие платформы (например ``cfg(windows)``) или None
    """

    name: str
    req: str
    target: str = None


def index_path(name):
    """Вернуть путь к файлу пакета в sparse-индексе Cargo.

    Правила Cargo: имена из 1–2 символов лежат в папках ``1/`` и ``2/``,
    из 3 символов — в ``3/<первая буква>/``, остальные — в
    ``<символы 1-2>/<символы 3-4>/``.

    :param name: имя пакета
    :return: относительный путь, например ``se/rd/serde``
    """
    name = name.lower()
    if len(name) <= SHORT_NAME_MAX:
        return f"{len(name)}/{name}"
    if len(name) == MEDIUM_NAME_LEN:
        return f"{MEDIUM_NAME_LEN}/{name[0]}/{name}"
    first, second = name[:PREFIX_LEN], name[PREFIX_LEN:2 * PREFIX_LEN]
    return f"{first}/{second}/{name}"


def fetch_index(repo, name):
    """Скачать файл индекса пакета из репозитория.

    :param repo: URL-адрес репозитория, например ``https://index.crates.io``
    :param name: имя пакета
    :return: текст файла индекса
    :raises RegistryError: если пакет не найден или сеть недоступна
    """
    url = f"{repo.rstrip('/')}/{index_path(name)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SEC) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RegistryError(
                f"пакет {name!r} не найден в репозитории {repo}") from error
        raise RegistryError(
            f"ошибка HTTP {error.code} при загрузке {url}") from error
    except urllib.error.URLError as error:
        raise RegistryError(
            f"не удалось подключиться к {repo}: {error.reason}") from error


def parse_versions(text):
    """Разобрать файл индекса: по одной JSON-записи версии в строке.

    :param text: текст файла индекса
    :return: список словарей с описанием версий
    :raises RegistryError: если строка не является JSON
    """
    versions = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            versions.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise RegistryError(
                f"неверный формат индекса (строка {number})") from error
    return versions


def version_key(vers):
    """Ключ для сравнения номеров версий вида ``1.2.3`` и ``1.2.3-beta``.

    Предварительные версии (с ``-``) считаются младше обычных.

    :param vers: номер версии
    :return: кортеж для сравнения
    """
    release, _, pre = vers.split("+")[0].partition("-")
    numbers = [int(part) if part.isdigit() else 0
               for part in release.split(".")]
    return tuple(numbers), not pre


def select_latest(versions):
    """Выбрать последнюю версию пакета, не отозванную (не yanked).

    Обычные версии предпочитаются предварительным (alpha, beta, rc).

    :param versions: список словарей версий
    :return: словарь выбранной версии
    :raises RegistryError: если подходящих версий нет
    """
    available = [item for item in versions if not item.get("yanked")]
    if not available:
        raise RegistryError("у пакета нет доступных (не отозванных) версий")
    return max(available, key=lambda item: version_key(item["vers"]))


def direct_dependencies(version):
    """Извлечь прямые зависимости из описания версии пакета.

    Учитываются обычные (``normal``) обязательные зависимости.
    Зависимости для разработки (``dev``), сборки (``build``) и
    необязательные (``optional``) пропускаются. Для переименованных
    зависимостей берётся настоящее имя пакета (поле ``package``).

    :param version: словарь версии из индекса
    :return: отсортированный список Dependency без повторов
    """
    found = {}
    for dep in version.get("deps", []):
        kind = dep.get("kind") or NORMAL_KIND
        if kind != NORMAL_KIND or dep.get("optional"):
            continue
        name = dep.get("package") or dep["name"]
        found.setdefault(name, Dependency(name, dep.get("req", "*"),
                                          dep.get("target")))
    return [found[name] for name in sorted(found)]


class CargoRegistry:
    """Источник зависимостей: реестр пакетов Cargo по URL-адресу."""

    def __init__(self, repo, fetch=None):
        """Создать источник.

        :param repo: URL-адрес репозитория (индекса)
        :param fetch: функция загрузки индекса (для тестов)
        """
        self.repo = repo
        self.fetch = fetch or fetch_index
        self.cache = {}

    def latest(self, name):
        """Вернуть описание последней версии пакета (с кэшированием)."""
        if name not in self.cache:
            text = self.fetch(self.repo, name)
            self.cache[name] = select_latest(parse_versions(text))
        return self.cache[name]

    def dependencies(self, name):
        """Вернуть прямые зависимости последней версии пакета.

        :param name: имя пакета
        :return: список Dependency
        """
        return direct_dependencies(self.latest(name))
