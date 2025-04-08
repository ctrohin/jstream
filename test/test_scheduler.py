from time import sleep

from baseTest import BaseTestCase
from jstreams.scheduler import (
    scheduler_enforce_minimum_period,
    schedule_periodic,
    scheduler_set_polling_period,
    stop_scheduler,
)


class TestScheduler(BaseTestCase):
    def test_scheduler(self) -> None:
        scheduler_enforce_minimum_period(False)
        scheduler_set_polling_period(1)
        global run_times
        run_times = 0

        class RunTest:
            @schedule_periodic(2)
            @staticmethod
            def run_every_2_seconds() -> None:
                global run_times
                run_times += 1
                print("Running every 2 seconds")

        RunTest()

        sleep(5)
        stop_scheduler()
        self.assertGreaterEqual(
            run_times, 2, "The job should have run at least 2 times"
        )
