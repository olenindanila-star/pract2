@echo off
rem Stage 3: dependency graph (BFS), filter, cycles, test repository mode.
chcp 65001 >nul
cd /d "%~dp0.."
echo === 1. Simple graph without cycles (diamond) ===
python src\main.py -p A -m test -r examples\simple.txt
echo.
echo === 2. Cycle A -> B -> C -> A ===
python src\main.py -p A -m test -r examples\cycle.txt
echo.
echo === 3. Package depends on itself ===
python src\main.py -p A -m test -r examples\self_cycle.txt
echo.
echo === 4. Big graph with two cycles ===
python src\main.py -p A -m test -r examples\complex.txt
echo.
echo === 5. Same graph, packages containing "F" are skipped ===
python src\main.py -p A -m test -r examples\complex.txt -f F
echo.
echo === 6. Graph of another package (D) ===
python src\main.py -p D -m test -r examples\complex.txt
echo.
echo === 7. Error: lowercase name in the file ===
python src\main.py -p A -m test -r examples\bad_name.txt
echo === 8. Error: line without a colon ===
python src\main.py -p A -m test -r examples\bad_format.txt
echo === 9. Error: package is not in the repository ===
python src\main.py -p Z -m test -r examples\simple.txt
echo === 10. Error: the package itself matches the filter ===
python src\main.py -p A -m test -r examples\simple.txt -f A
