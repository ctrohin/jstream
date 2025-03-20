#/bin/sh
rm -rf tests_integration/__pycache__
for dir in tests_integration/*; do 
    (cd "$dir" && python3.10 run.py); 
    if [ $? -eq 0 ]
    then
    echo "$dir integration test has passed"
    else
    echo "$dir integration test has FAILED"
    exit 1
    fi
done