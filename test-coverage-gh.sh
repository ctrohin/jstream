#/bin/sh

python3 -m coverage run --source=./jstreams --omit __init__.py -m unittest discover tests "test_*.py" -s "./test"
if [ $? -eq 0 ]
then
  echo "All tests passed."
else
  echo "Failure: Tests failure!"
  exit 1
fi

python3 -m coverage report --fail-under 55
if [ $? -eq 0 ]
then
  echo "Test coverage over the desired percent."
else
  echo "Failure: Coverage failure!"
  exit 1
fi