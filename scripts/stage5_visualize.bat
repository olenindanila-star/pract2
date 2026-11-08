@echo off
rem Stage 5: D2 description, SVG image and ASCII tree for three packages.
rem If the d2 program is installed, it draws the SVG; otherwise the
rem built-in renderer is used.
chcp 65001 >nul
cd /d "%~dp0.."
if not exist output mkdir output
echo === 1. serde_json ===
python src\main.py -p serde_json -o output\serde_json.svg -a yes
echo.
echo === 2. thiserror ===
python src\main.py -p thiserror -o output\thiserror.svg -a yes
echo.
echo === 3. clap ===
python src\main.py -p clap -o output\clap.svg -a yes
echo.
echo === 4. Test repository with cycles ===
python src\main.py -p A -m test -r examples\complex.txt -o output\test_complex.svg -a yes
echo.
echo Images are in the "output" folder. Opening the first one...
start "" output\serde_json.svg
