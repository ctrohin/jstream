import datetime
from time import sleep
import time
from typing import Any, Callable, Optional

from threading import Lock, Thread
from jstreams.thread import LoopingThread
from jstreams.utils import each

ENFORCE_MINIMUM_PERIOD = True
POLLING_PERIOD = 5


class _Job:
    """
    Job class to represent a job.
    """

    __slots__ = ["name", "func", "period", "last_run", "run_once"]

    def __init__(
        self,
        name: str,
        period: int,
        func: Callable[[], Any],
        run_once: bool = False,
        start_at: int = 0,
    ) -> None:
        self.name = name
        self.func = func
        self.period = period
        self.last_run = start_at
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
        self.last_run = int(time.time())
        Thread(target=self.func).start()

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
        sleep(POLLING_PERIOD)


def scheduler_enforce_minimum_period(flag: bool) -> None:
    """
    Enforce a minimum period for the scheduler.
    Args:
        period (int): Period in seconds.
    """
    global ENFORCE_MINIMUM_PERIOD
    ENFORCE_MINIMUM_PERIOD = flag


def scheduler_set_polling_period(period: int) -> None:
    """
    Set the polling period for the scheduler

    Args:
        period (int): The new period
    """
    global POLLING_PERIOD
    POLLING_PERIOD = period


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
    Since the scheduler needs to execute the given function at specified intervals, the function must be available and not depend on a specific instance.
    This means that the function should not rely on instance variables or methods.
    Instead, it should be a static method or a standalone function.
    The function should not be a lambda function, as it will not be able to access the instance variables or methods.
    The function should not be a class method, as it will not be able to access the instance variables or methods.
    The function should not be a generator function, as it will not be able to access the instance variables or methods.
    The function should not be a coroutine function, as it will not be able to access the instance variables or methods.
    The function should not be a nested function, as it will not be able to access the instance variables or methods.
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


def get_timestamp_current_hour(minute: int) -> float:
    """
    Computes the Unix timestamp for a given minute within the current hour using the machine's local timezone.

    Args:
        minute: An integer representing the minute (0-59).

    Returns:
        A float representing the Unix timestamp (seconds since the epoch) for the specified minute of the current hour in the machine's local timezone.
    """
    now_local = datetime.datetime.now()
    current_hour = now_local.hour
    today = now_local.date()

    current_hour_at_minute = datetime.datetime(
        today.year, today.month, today.day, current_hour, minute
    )

    # Convert the datetime object to a timestamp in the local timezone
    timestamp = time.mktime(current_hour_at_minute.timetuple())
    return timestamp


def get_timestamp_today(hour: int, minute: int) -> int:
    """
    Computes the Unix timestamp for a given hour and minute for the current day in Craiova, Romania.

    Args:
        hour: An integer representing the hour (0-23).
        minute: An integer representing the minute (0-59).

    Returns:
        An int representing the Unix timestamp (seconds since the epoch) for the specified time today.
    """
    today = datetime.date.today()
    today_at_time = datetime.datetime(today.year, today.month, today.day, hour, minute)

    # However, without knowing the exact date, we can't definitively say if DST is active.
    # For simplicity, we'll assume the local timezone of the machine running this code.
    # For a more robust solution, you would need to explicitly handle the timezone.

    timestamp = today_at_time.timestamp()
    return int(timestamp)


def schedule_daily(
    hour: int,
    minute: int,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to be executed at a fixed time.
    Since the scheduler needs to execute the given function at specified intervals, the function must be available and not depend on a specific instance.
    This means that the function should not rely on instance variables or methods.
    Instead, it should be a static method or a standalone function.
    The function should not be a lambda function, as it will not be able to access the instance variables or methods.
    The function should not be a class method, as it will not be able to access the instance variables or methods.
    The function should not be a generator function, as it will not be able to access the instance variables or methods.
    The function should not be a coroutine function, as it will not be able to access the instance variables or methods.
    The function should not be a nested function, as it will not be able to access the instance variables or methods.

    Args:
        hour (int): Hour of the day (0-23).
        minute (int): Minute of the hour (0-59).
        second (int): Second of the minute (0-59).
    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: Decorated function.
    """

    period = 24 * 60 * 60
    # Calculate the period in seconds

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        job = _Job(
            func.__name__, period, func, False, get_timestamp_today(hour, minute)
        )
        scheduler = _Scheduler.get_instance()
        scheduler.add_job(job)
        return func

    return decorator


def schedule_hourly(
    minute: int,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to be executed at a fixed time.
    Since the scheduler needs to execute the given function at specified intervals, the function must be available and not depend on a specific instance.
    This means that the function should not rely on instance variables or methods.
    Instead, it should be a static method or a standalone function.
    The function should not be a lambda function, as it will not be able to access the instance variables or methods.
    The function should not be a class method, as it will not be able to access the instance variables or methods.
    The function should not be a generator function, as it will not be able to access the instance variables or methods.
    The function should not be a coroutine function, as it will not be able to access the instance variables or methods.
    The function should not be a nested function, as it will not be able to access the instance variables or methods.

    Args:
        hour (int): Hour of the day (0-23).
        minute (int): Minute of the hour (0-59).
        second (int): Second of the minute (0-59).
    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: Decorated function.
    """

    period = 60 * 60
    # Calculate the period in seconds

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        job = _Job(
            func.__name__, period, func, False, get_timestamp_current_hour(minute)
        )
        scheduler = _Scheduler.get_instance()
        scheduler.add_job(job)
        return func

    return decorator
