from time import sleep

from baseTest import BaseTestCase
from jstreams.scheduler import enforce_minimum_period, schedule_periodic, stop_scheduler


class TestScheduler(BaseTestCase):
    def test_scheduler(self) -> None:
        enforce_minimum_period(False)
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
