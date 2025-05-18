#/bin/sh

ruff check jstreams
if [ $? -eq 0 ]
then
  echo "Ruff check passed."
else
  echo "Failure: Ruff check failed!"
  exit 1
fi

mypy jstreams --strict
if [ $? -eq 0 ]
then
  echo "Mypy check passed."
else
  echo "Failure: Mypy check failed!"
  exit 1
fi

pylint jstreams
if [ $? -eq 0 ]
then
  echo "Pylint check passed."
else
  echo "Failure: Pylint check failed!"
  exit 1
fi
