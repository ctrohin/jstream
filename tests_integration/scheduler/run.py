from time import sleep
import unittest
import sys

sys.path.append("../../")

from jstreams.scheduler import scheduler

scheduler().enforce_minimum_period(False)
scheduler().set_polling_period(1)

scheduler().scan_modules(["schedule"])
sleep(10)
scheduler().stop()

from schedule import two_seconds_counter, two_seconds_class_counter

tc = unittest.TestCase()
tc.assertGreaterEqual(
    two_seconds_counter, 5, "The function should have been called at least 5 times"
)
tc.assertGreaterEqual(
    two_seconds_class_counter,
    5,
    "The static function should have been called at least 5 times",
)
