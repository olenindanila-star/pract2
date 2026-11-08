@echo off
rem Stage 4: load order of dependencies (test repository and real packages).
chcp 65001 >nul
cd /d "%~dp0.."
echo === 1. Diamond: D must be loaded before B and C, A is last ===
python src\main.py -p A -m test -r examples\simple.txt -l yes
echo.
echo === 2. Several levels without cycles ===
python src\main.py -p A -m test -r examples\layers.txt -l yes
echo.
echo === 3. Cycle: A, B, C cannot be ordered, D can ===
python src\main.py -p A -m test -r examples\cycle.txt -l yes
echo.
echo === 4. Package depends on itself ===
python src\main.py -p A -m test -r examples\self_cycle.txt -l yes
echo.
echo === 5. Cycle broken by the filter: packages with "C" are skipped ===
python src\main.py -p A -m test -r examples\cycle.txt -f C -l yes
echo.
echo === 6. Real package: thiserror ===
python src\main.py -p thiserror -l yes
echo.
echo === 7. Real package: serde ===
python src\main.py -p serde -l yes
