#/bin/sh

rm -rf dist

python3.10 -m pip install --upgrade packaging
python3.10 -m pip install --upgrade build
python3.10 -m pip install --upgrade twine

python3.10 -m build