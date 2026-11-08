"""Настройка консоли для корректного вывода русского текста."""

import sys


def setup_console():
    """Переключить вывод программы на кодировку UTF-8.

    Нужно в Windows: иначе при перенаправлении вывода в файл русские
    буквы и символы псевдографики могут не отобразиться.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
