"""Общие настройки тестов: путь к исходному коду и данным."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
EXAMPLES = os.path.join(ROOT, "examples")

if SRC not in sys.path:
    sys.path.insert(0, SRC)


def example(name):
    """Вернуть путь к файлу из папки examples."""
    return os.path.join(EXAMPLES, name)
