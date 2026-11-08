@echo off
rem Run the dependency graph visualizer on Windows.
chcp 65001 >nul
cd /d "%~dp0"
python src\main.py %*
