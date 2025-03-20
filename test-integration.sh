#/bin/sh
rm -rf tests_integration/__pycache__
for dir in tests_integration/*; do (cd "$dir" && python3.10 run.py); done