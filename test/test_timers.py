from baseTest import BaseTestCase
from jstreams import Timer, CountdownTimer
from time import sleep

class TestTimers(BaseTestCase):
    def test_timer(self) -> None:
        val: int = []
        t = Timer(2, 0.5, lambda: val.append(1))
        t.start()
        self.assertEqual(len(val), 0, "Before timer completes, there should be no values added")
        sleep(3)
        self.assertEqual(len(val), 1, "After timer completes, there should be a value added")

    def test_timer_cancel(self) -> None:
        val: int = []
        t = Timer(2, 0.5, lambda: val.append(1))
        t.start()
        self.assertEqual(len(val), 0, "Before timer completes, there should be no values added")
        sleep(1)
        t.cancel()
        sleep(2)
        self.assertEqual(len(val), 0, "After timer completes, with the timer canceled, there should be no values added")

    def test_countDownTimer(self) -> None:
        val: int = []
        t = CountdownTimer(2, lambda: val.append(1))
        t.start()
        self.assertEqual(len(val), 0, "Before timer completes, there should be no values added")
        sleep(3)
        self.assertEqual(len(val), 1, "After timer completes, there should be a value added")
