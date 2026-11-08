#!/bin/sh
# Запуск визуализатора графа зависимостей (Linux/macOS).
cd "$(dirname "$0")" || exit 1
python3 src/main.py "$@"
