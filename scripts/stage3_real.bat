@echo off
rem Stage 3: transitive dependency graphs of real Cargo packages.
chcp 65001 >nul
cd /d "%~dp0.."
echo === serde ===
python src\main.py -p serde
echo.
echo === serde without packages containing "proc" ===
python src\main.py -p serde -f proc
echo.
echo === regex ===
python src\main.py -p regex
