@echo off
rem Stage 1: valid runs, all parameters are printed as key = value.
chcp 65001 >nul
cd /d "%~dp0.."
echo === 1. Only the package name (defaults for everything else) ===
python src\main.py --package serde
echo.
echo === 2. All parameters, real mode ===
python src\main.py -p tokio -r https://index.crates.io -m real -o tokio.svg -a yes -f test
echo.
echo === 3. Test mode with a test repository file ===
python src\main.py -p A -r examples\simple.txt -m test -o simple.svg -a no
