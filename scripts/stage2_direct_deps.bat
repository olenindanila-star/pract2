@echo off
rem Stage 2: direct dependencies of a package from the Cargo registry.
chcp 65001 >nul
cd /d "%~dp0.."
echo === serde ===
python src\main.py -p serde
echo.
echo === regex ===
python src\main.py -p regex
echo.
echo === reqwest (has platform-specific dependencies) ===
python src\main.py -p reqwest
echo.
echo === Error: package does not exist ===
python src\main.py -p no-such-crate-xyz123
echo.
echo === Error: repository is not reachable ===
python src\main.py -p serde -r https://no-such-host.invalid
