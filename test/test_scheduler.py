from time import sleep

from baseTest import BaseTestCase
from jstreams.scheduler import (
    schedule_periodic,
    scheduler,
)


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
