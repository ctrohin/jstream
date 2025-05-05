from time import sleep
from typing import Any

from baseTest import BaseTestCase
from jstreams.scheduler import (
    schedule_periodic,
    scheduler,
)
from jstreams.utils import Value


class TestScheduler(BaseTestCase):
    def test_scheduler(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)
        global run_times
        run_times = 0

        class RunTest:
            @staticmethod
            @schedule_periodic(2)
            def run_every_2_seconds() -> None:
                global run_times
                run_times += 1

        sleep(5)
        scheduler().stop()
        self.assertGreaterEqual(
            run_times, 2, "The job should have run at least 2 times"
        )

    def test_scheduler_callback(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)
        global run_times
        run_times = 0

        def run_callback(param: Any) -> None:
            global run_times
            run_times += 1

        class RunTest:
            @staticmethod
            @schedule_periodic(2, on_success=run_callback)
            def run_every_2_seconds() -> None:
                pass

        sleep(5)
        scheduler().stop()
        self.assertGreaterEqual(
            run_times, 2, "The job should have run at least 2 times"
        )

    def test_scheduler_callback_value(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)

        val = Value(0)

        class RunTest:
            @staticmethod
            @schedule_periodic(period=1, one_time=True, on_success=val.set)
            def run_every_2_seconds() -> int:
                return 10

        sleep(5)
        scheduler().stop()
        self.assertEqual(
            val.get(), 10, "The callback should have been called with the return value"
        )

    def test_scheduler_callback_error(self) -> None:
        scheduler().enforce_minimum_period(False)
        scheduler().set_polling_period(1)

        val = Value(0)
        err = Value(None)

        class RunTest:
            @staticmethod
            @schedule_periodic(
                period=1, one_time=True, on_success=val.set, on_error=err.set
            )
            def run_every_2_seconds() -> int:
                raise Exception("Test exception")

        sleep(5)
        scheduler().stop()
        self.assertEqual(
            val.get(),
            0,
            "The callback should not have been called with the return value",
        )
        self.assertIsInstance(err.get(), Exception)
        self.assertEqual(
            str(err.get()),
            "Test exception",
            "The callback should have been called with the exception",
        )
