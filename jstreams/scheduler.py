from time import sleep
import time
from typing import Any, Callable, Optional

from threading import Lock
from jstreams.thread import LoopingThread
from jstreams.utils import each

ENFORCE_MINIMUM_PERIOD = True


class _Job:
    """
    Job class to represent a job.
    """

    __slots__ = ["name", "func", "period", "last_run", "run_once"]

    def __init__(
        self, name: str, period: int, func: Callable[[], Any], run_once: bool = False
    ) -> None:
        self.name = name
        self.func = func
        self.period = period
        self.last_run = 0
        self.run_once = run_once

    def should_run(self) -> bool:
        """
        Check if the job should run.
        Returns:
            bool: True if the job should run, False otherwise.
        """
        return self.last_run + self.period <= time.time()
        # Check if the job should run based on the last run time and period
        # If the last run time plus the period is less than or equal to the current time, it should run

    def run_if_needed(self) -> None:
        """
        Run the job if needed.
        """
        if self.should_run():
            self.run()
            self.last_run = int(time.time())
            # Update the last run time to the current time
            # This ensures that the job will not run again until the period has passed
            # after the last run
            # This is useful for jobs that need to run periodically

    def run(self) -> None:
        """
        Run the job.
        """
        self.func()
        self.last_run = int(time.time())

    def has_run(self) -> bool:
        """
        Check if the job has run.
        Returns:
            bool: True if the job has run once, False otherwise.
        """
        return self.last_run > 0
        # Check if the job has run by checking if the last run time is greater than 0
        # This is useful for jobs that need to run only once
        # after the first run


class _Scheduler(LoopingThread):
    """
    Scheduler class to manage the scheduling of jobs.
    """

    instance: Optional["_Scheduler"] = None
    instance_lock: Lock = Lock()

    def __init__(self) -> None:
        super().__init__()
        self.__jobs: list[_Job] = []
        self.__started = False
        self.__start_lock: Lock = Lock()

    @staticmethod
    def get_instance() -> "_Scheduler":
        # If the instance is not initialized
        if _Scheduler.instance is None:
            # Lock for instantiation
            with _Scheduler.instance_lock:
                # Check if the instance was not already initialized before acquiring the lock
                if _Scheduler.instance is None:
                    # Initialize
                    _Scheduler.instance = _Scheduler()
        return _Scheduler.instance
        # Return the singleton instance

    def add_job(self, job: _Job) -> None:
        """
        Add a job to the scheduler.
        Args:
            job (_Job): Job to add.
        """
        self.__jobs.append(job)
        # Add the job to the list of jobs
        if not self.__started:
            with self.__start_lock:
                # If the scheduler is not running, start it
                if not self.__started:
                    self.start()
                    # Start the scheduler thread
                    # This will start the loop method in a separate thread
                    self.__started = True
                    # Set the started flag to True

    def loop(self) -> None:
        each(
            self.__jobs,
            lambda job: job.run_if_needed(),
        )
        sleep(5)


def enforce_minimum_period(flag: bool) -> None:
    """
    Enforce a minimum period for the scheduler.
    Args:
        period (int): Period in seconds.
    """
    global ENFORCE_MINIMUM_PERIOD
    ENFORCE_MINIMUM_PERIOD = flag


def stop_scheduler() -> None:
    """
    Stop the scheduler.
    """
    scheduler = _Scheduler.get_instance()
    if scheduler.is_running():
        scheduler.cancel()
        # Cancel the scheduler thread
        # This will stop the loop method from running
        # and exit the thread
        scheduler.join()
        # Wait for the thread to finish
        # This is useful to ensure that all jobs have completed before stopping the scheduler


def schedule_periodic(
    period: int,
    one_time: bool = False,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to be executed periodically.
    Args:
        period (int): Period in seconds.
    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: Decorated function.
    """

    if ENFORCE_MINIMUM_PERIOD and period <= 10:
        raise ValueError("Period must be greater than 10 seconds")
        # Check if the period is greater than 10 seconds

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        job = _Job(func.__name__, period, func, one_time)
        scheduler = _Scheduler.get_instance()
        scheduler.add_job(job)
        return func

    return decorator
