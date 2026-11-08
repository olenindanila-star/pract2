@echo off
rem Stage 1: error handling for every parameter.
chcp 65001 >nul
cd /d "%~dp0.."
echo === package: not given ===
python src\main.py
echo === package: invalid characters ===
python src\main.py -p "my package!"
echo === package: longer than 64 characters ===
python src\main.py -p aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
echo === package: lowercase name in test mode ===
python src\main.py -p a -m test -r examples\simple.txt
echo === repo: not a URL in real mode ===
python src\main.py -p serde -r index.crates.io
echo === repo: test repository file not found ===
python src\main.py -p A -m test -r examples\no_such_file.txt
echo === mode: unknown mode ===
python src\main.py -p serde -m fast
echo === output: wrong extension ===
python src\main.py -p serde -o graph.png
echo === output: folder does not exist ===
python src\main.py -p serde -o no_such_dir\graph.svg
echo === ascii-tree: not yes/no ===
python src\main.py -p serde -a maybe
echo === filter: empty substring ===
python src\main.py -p serde -f ""
echo === unknown option ===
python src\main.py -p serde --color red
