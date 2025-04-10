import os
import datetime
import importlib
from time import sleep
import time
from typing import Any, Callable, Optional

from threading import Lock, Thread
from jstreams.thread import LoopingThread
from jstreams.try_opt import Try


class Duration:
    """
    Represents a duration of time with days, hours, and minutes.
    Supports addition and subtraction operators.
    """

    __slots__ = ["_days", "_hours", "_minutes"]

    def __init__(self, days: int = 0, hours: int = 0, minutes: int = 0) -> None:
        """
        Initializes a Duration object.

        Args:
            days: The number of days. Defaults to 0.
            hours: The number of hours. Defaults to 0.
            minutes: The number of minutes. Defaults to 0.
        """
        self._days = days
        self._hours = hours
        self._minutes = minutes
        self._normalize()

    def to_seconds(self) -> int:
        """
        Instance method to compute the total number of seconds for this duration.

        Returns:
            The total number of seconds.
        """
        total_seconds = (
            (self._days * 24 * 60 * 60) + (self._hours * 60 * 60) + (self._minutes * 60)
        )
        return total_seconds

    def _normalize(self) -> None:
        """
        Internal method to normalize the duration values (carry over minutes to hours, etc.).
        """
        total_minutes = self._minutes
        self._minutes = total_minutes % 60
        carry_hours = total_minutes // 60
        self._hours += carry_hours

        total_hours = self._hours
        self._hours = total_hours % 24
        carry_days = total_hours // 24
        self._days += carry_days

    def __add__(self, other: "Duration") -> "Duration":
        """
        Overloads the addition operator (+) for Duration objects.

        Args:
            other: The other Duration object to add.

        Returns:
            A new Duration object representing the sum.
        """
        if not isinstance(other, Duration):
            raise TypeError(
                "Unsupported operand type for +: 'Duration' and '{}'".format(
                    type(other).__name__
                )
            )
        new_days = self._days + other._days
        new_hours = self._hours + other._hours
        new_minutes = self._minutes + other._minutes
        result = Duration(new_days, new_hours, new_minutes)
        result._normalize()
        return result

    def __sub__(self, other: "Duration") -> "Duration":
        """
        Overloads the subtraction operator (-) for Duration objects.

        Args:
            other: The other Duration object to subtract.

        Returns:
            A new Duration object representing the difference.
        """
        if not isinstance(other, Duration):
            raise TypeError(
                "Unsupported operand type for -: 'Duration' and '{}'".format(
                    type(other).__name__
                )
            )

        total_seconds_self = self.to_seconds()
        total_seconds_other = other.to_seconds()
        diff_seconds = total_seconds_self - total_seconds_other

        if diff_seconds < 0:
            # Always compute absolute difference
            diff_seconds = -diff_seconds

        new_days = diff_seconds // (24 * 60 * 60)
        remaining_seconds = diff_seconds % (24 * 60 * 60)
        new_hours = remaining_seconds // (60 * 60)
        new_minutes = (remaining_seconds % (60 * 60)) // 60

        return Duration(new_days, new_hours, new_minutes)


class _Job:
    """
    Job class to represent a job.
    """

    __slots__ = ["name", "func", "period", "last_run", "run_once", "has_ran"]

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
        self.has_ran = False

    def should_run(self) -> bool:
        """
        Check if the job should run.
        Returns:
            bool: True if the job should run, False otherwise.
        """
        return self.last_run + self.period <= time.time()
        # Check if the job should run based on the last run time and period
        # If the last run time plus the period is less than or equal to the current time, it should run

    def should_remove(self) -> bool:
        return self.run_once and self.has_ran

    def run_if_needed(self) -> None:
        """
        Run the job if needed.
        """
        if self.should_run():
            self.run()
            self.last_run = int(time.time())
            self.has_ran = True
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
        self.__enforce_minimum_period = (
            Try(lambda: bool(os.environ.get("SCH_ENFORCE", True))).get().or_else(True)
        )
        self.__polling_period = (
            Try(lambda: int(os.environ.get("SCH_POLLING", 10))).get().or_else(10)
        )

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
        remove_jobs: list[_Job] = []
        for job in self.__jobs:
            if job.should_remove():
                remove_jobs.append(job)
            else:
                job.run_if_needed()
        # Cleanup run once jobs that have already ran
        for remove_job in remove_jobs:
            self.__jobs.remove(remove_job)
        sleep(self.__polling_period)

    def enforce_minimum_period(self, flag: bool) -> None:
        """
        Enforce a minimum period for the scheduler.
        Args:
            period (int): Period in seconds.
        """
        self.__enforce_minimum_period = flag

    def set_polling_period(self, period: int) -> None:
        """
        Set the polling period for the scheduler

        Args:
            period (int): The new period
        """
        self.__polling_period = period

    def stop(self) -> None:
        """
        Stop the scheduler.
        """
        if self.is_running():
            self.cancel()
            # Cancel the scheduler thread
            # This will stop the loop method from running
            # and exit the thread
            self.join()
            # Wait for the thread to finish
            # This is useful to ensure that all jobs have completed before stopping the scheduler

    def scan_modules(
        self,
        modules: list[str],
    ) -> None:
        for module in modules:
            importlib.import_module(module)

    def schedule_periodic(
        self, func: Callable[[], Any], period: int, one_time: bool = False
    ) -> "_Scheduler":
        """
        Schedule a function to be executed periodically.
        Args:
            period (int): Period in seconds.
        """
        if self.__enforce_minimum_period and period <= 10:
            raise ValueError("Period must be greater than 10 seconds")
            # Check if the period is greater than 10 seconds

        self.add_job(_Job(func.__name__, period, func, one_time))
        return self

    def schedule_daily(
        self,
        func: Callable[[], Any],
        hour: int,
        minute: int,
    ) -> "_Scheduler":
        """
        Schedule a function to be executed at a fixed time.

        Args:
            hour (int): Hour of the day (0-23).
            minute (int): Minute of the hour (0-59).
            second (int): Second of the minute (0-59).
        """

        period = 24 * 60 * 60
        # Calculate the period in seconds

        job = _Job(
            func.__name__, period, func, False, get_timestamp_today(hour, minute)
        )
        self.add_job(job)
        return self

    def schedule_hourly(
        self,
        func: Callable[[], Any],
        minute: int,
    ) -> "_Scheduler":
        """
        Schedule a function to be executed at a fixed time.

        Args:
            minute (int): Minute of the hour (0-59).
        """

        period = 60 * 60
        # Calculate the period in seconds

        job = _Job(
            func.__name__, period, func, False, get_timestamp_current_hour(minute)
        )
        self.add_job(job)
        return self

    def schedule_duration(
        self,
        func: Callable[[], Any],
        duration: Duration,
    ) -> "_Scheduler":
        return self.schedule_periodic(func, duration.to_seconds())


def scheduler() -> _Scheduler:
    return _Scheduler.get_instance()


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

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        scheduler().schedule_periodic(func, period, one_time)
        return func

    return decorator


def get_timestamp_current_hour(minute: int) -> int:
    """
    Computes the Unix timestamp for a given minute within the current hour using the machine's local timezone.

    Args:
        minute: An integer representing the minute (0-59).

    Returns:
        An int representing the Unix timestamp (seconds since the epoch) for the specified minute of the current hour in the machine's local timezone.
    """
    now_local = datetime.datetime.now()
    current_hour = now_local.hour
    today = now_local.date()

    current_hour_at_minute = datetime.datetime(
        today.year, today.month, today.day, current_hour, minute
    )

    # Convert the datetime object to a timestamp in the local timezone
    timestamp = time.mktime(current_hour_at_minute.timetuple())
    return int(timestamp)


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

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        scheduler().schedule_daily(func, hour, minute)
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

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        scheduler().schedule_hourly(func, get_timestamp_current_hour(minute))
        return func

    return decorator


def schedule_duration(
    duration: Duration,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    return schedule_periodic(duration.to_seconds())
