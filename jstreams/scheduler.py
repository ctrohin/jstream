import os
import datetime
import importlib
from time import sleep
import time
from typing import Any, Callable, Optional

from threading import Lock, Thread
from jstreams.stream import Opt
from jstreams.thread import LoopingThread
from jstreams.try_opt import Try

"""
Provides functionality for scheduling tasks to run periodically, daily, hourly,
or after a specific duration. Includes a Duration class for time representation,
a Job class for task encapsulation, and a singleton Scheduler class that manages
and executes jobs. Decorators are provided for easy scheduling of functions.
"""


class Duration:
    """
    Represents a duration of time specified in days, hours, and minutes.

    Handles normalization (e.g., 70 minutes becomes 1 hour and 10 minutes).
    Supports addition (+) and subtraction (-) with other Duration objects,
    calculating the absolute difference for subtraction.
    Can convert the duration to the total number of seconds.

    Attributes:
        _days (int): Number of days in the duration.
        _hours (int): Number of hours in the duration (0-23 after normalization).
        _minutes (int): Number of minutes in the duration (0-59 after normalization).
    """

    __slots__ = ["_days", "_hours", "_minutes"]

    def __init__(self, days: int = 0, hours: int = 0, minutes: int = 0) -> None:
        """
        Initializes a Duration object and normalizes the time units.

        Args:
            days (int): The number of days. Defaults to 0.
            hours (int): The number of hours. Defaults to 0.
            minutes (int): The number of minutes. Defaults to 0.
        """
        self._days = days
        self._hours = hours
        self._minutes = minutes
        self._normalize()

    def to_seconds(self) -> int:
        """
        Computes the total number of seconds represented by this duration.

        Returns:
            int: The total number of seconds.
        """
        total_seconds = (
            (self._days * 24 * 60 * 60) + (self._hours * 60 * 60) + (self._minutes * 60)
        )
        return total_seconds

    def _normalize(self) -> None:
        """
        Internal method to normalize the duration values.
        Converts excess minutes into hours and excess hours into days.
        Ensures `_minutes` is < 60 and `_hours` is < 24.
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
            other (Duration): The other Duration object to add.

        Returns:
            Duration: A new Duration object representing the sum.

        Raises:
            TypeError: If 'other' is not a Duration object.
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
        # Normalization happens in the constructor of the new Duration
        return result

    def __sub__(self, other: "Duration") -> "Duration":
        """
        Overloads the subtraction operator (-) for Duration objects.
        Calculates the absolute difference between the two durations.

        Args:
            other (Duration): The other Duration object to subtract.

        Returns:
            Duration: A new Duration object representing the absolute difference.

        Raises:
            TypeError: If 'other' is not a Duration object.
        """
        if not isinstance(other, Duration):
            raise TypeError(
                "Unsupported operand type for -: 'Duration' and '{}'".format(
                    type(other).__name__
                )
            )

        total_seconds_self = self.to_seconds()
        total_seconds_other = other.to_seconds()
        diff_seconds = abs(
            total_seconds_self - total_seconds_other
        )  # Compute absolute difference

        new_days = diff_seconds // (24 * 60 * 60)
        remaining_seconds = diff_seconds % (24 * 60 * 60)
        new_hours = remaining_seconds // (60 * 60)
        new_minutes = (remaining_seconds % (60 * 60)) // 60

        # No need to normalize here as calculations are based on positive diff_seconds
        return Duration(new_days, new_hours, new_minutes)


class _Job:
    """
    Internal class representing a scheduled job.

    Encapsulates the function to be executed, its execution period,
    the last run time, and whether it should run only once.
    """

    __slots__ = [
        "name",
        "func",
        "period",
        "last_run",
        "run_once",
        "has_ran",
        "on_success",
        "on_error",
        "__logger",
    ]

    def __init__(
        self,
        name: str,
        period: int,
        func: Callable[[], Any],
        run_once: bool = False,
        start_at: int = 0,
        on_success: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
        logger: Optional[Callable[[Exception], Any]] = None,
    ) -> None:
        """
        Initializes a _Job instance.

        Args:
            name (str): The name of the job (often the function name).
            period (int): The execution period in seconds. For jobs scheduled at specific times (daily/hourly),
                          this is the interval between those times (e.g., 24*60*60 for daily).
            func (Callable[[], Any]): The function to execute.
            run_once (bool): If True, the job will run only once and then be removed. Defaults to False.
            start_at (int): The Unix timestamp when the job should first be considered for running.
            on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion. Receives the job's return value. Defaults to None.
            on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure. Receives the exception. Defaults to None.
                            Used for daily/hourly jobs to align the first run. Defaults to 0 (effectively now).
        """
        self.name = name
        self.func = func
        self.period = period
        # Use start_at if provided and it's in the future, otherwise default to ~now for periodic jobs
        self.last_run = start_at if start_at > 0 else int(time.time() - period)
        self.run_once = run_once
        self.has_ran = False
        self.on_success = on_success
        self.on_error = on_error
        self.__logger = logger

    def should_run(self) -> bool:
        """
        Checks if the job is due to run based on its last run time and period.

        Returns:
            bool: True if the job should run, False otherwise.
        """
        # Check if the job should run based on the last run time and period
        # If the last run time plus the period is less than or equal to the current time, it should run
        return self.last_run + self.period <= time.time()

    def should_remove(self) -> bool:
        """
        Checks if a 'run_once' job has already run and should be removed.

        Returns:
            bool: True if the job is run_once and has_ran is True.
        """
        return self.run_once and self.has_ran

    def run_if_needed(self) -> None:
        """
        Executes the job if `should_run()` returns True.
        Updates the last run time after execution.
        """
        if self.should_run():
            self.run()
            # Update the last run time to the current time
            # This ensures that the job will not run again until the period has passed
            # after the last run
            self.last_run = int(time.time())
            self.has_ran = True

    def _run_job_internal(self) -> None:
        """Internal wrapper to execute the job function, handle errors, and call callbacks."""
        (
            Try(self.func)
            .and_then(
                lambda result: Opt(self.on_success).if_present(
                    lambda success: success(result)
                )
            )
            .on_failure(
                lambda e: Opt(self.on_error or self.__logger).if_present(
                    lambda error: error(e)
                )
            )
            .get()
        )

    def run(self) -> None:
        """
        Executes the job's function in a new background thread.
        """
        # Run the job function in a separate thread to avoid blocking the scheduler loop
        Thread(target=self._run_job_internal).start()


class _Scheduler(LoopingThread):
    """
    Singleton scheduler class that manages and executes scheduled jobs.

    Inherits from LoopingThread to run its main loop in a background thread.
    Reads optional configuration from environment variables:
    - SCH_ENFORCE (bool, default True): Enforces a minimum period for periodic jobs.
    - SCH_POLLING (int, default 10): The interval in seconds at which the scheduler checks for due jobs.
    """

    instance: Optional["_Scheduler"] = None
    instance_lock: Lock = Lock()

    def __init__(self) -> None:
        """
        Initializes the Scheduler. Reads environment variables for configuration.
        Should not be called directly; use `scheduler()` or `_Scheduler.get_instance()`.
        """
        super().__init__()
        self.__jobs: list[_Job] = []
        self.__started = False
        self.__start_lock: Lock = Lock()
        # Read environment variables safely using Try/Opt
        self.__enforce_minimum_period = (
            Try(lambda: bool(os.environ.get("SCH_ENFORCE", "True") == "True"))
            .get()
            .or_else(True)  # Ensure correct bool conversion
        )
        self.__polling_period = (
            Try(lambda: int(os.environ.get("SCH_POLLING", "10"))).get().or_else(10)
        )
        # Ensure polling period is at least 1 second
        if self.__polling_period < 1:
            self.__polling_period = 1

        self.__logger: Optional[Callable[[Exception], Any]] = None

    @staticmethod
    def get_instance() -> "_Scheduler":
        """
        Gets the singleton instance of the Scheduler, creating it if necessary.
        This method is thread-safe.

        Returns:
            _Scheduler: The singleton scheduler instance.
        """
        # Double-checked locking for thread-safe singleton initialization
        if _Scheduler.instance is None:
            with _Scheduler.instance_lock:
                if _Scheduler.instance is None:
                    _Scheduler.instance = _Scheduler()
        return _Scheduler.instance

    @staticmethod
    def reset() -> None:
        """
        Resets the singleton instance of the Scheduler.
        This is useful for testing or reinitializing the scheduler.

        Note: This will stop the scheduler if it is running.
        """
        if _Scheduler.instance is not None:
            _Scheduler.instance.stop()
            _Scheduler.instance = None

    def log_with(self, logger: Callable[[Exception], Any]) -> None:
        """
        Sets a logger function to be called on job errors.

        Args:
            logger (Callable[[Exception], Any]): The logger function to set.
        """
        self.__logger = logger

    def add_job(self, job: _Job) -> None:
        """
        Adds a job to the scheduler's list.
        Starts the scheduler's background thread if it hasn't been started yet.

        Args:
            job (_Job): The job to add.
        """
        self.__jobs.append(job)
        # Start the scheduler thread automatically when the first job is added
        if not self.__started:
            with self.__start_lock:
                if not self.__started:
                    self.start()  # Start the LoopingThread's run() method
                    self.__started = True

    def loop(self) -> None:
        """
        The main execution loop for the scheduler thread.
        Periodically checks all jobs, runs due jobs, and cleans up completed 'run_once' jobs.
        Sleeps for the configured polling period between checks.
        """
        remove_jobs: list[_Job] = []
        # Iterate safely over a copy in case jobs are added/removed concurrently (though add_job is locked)
        current_jobs = self.__jobs[:]
        for job in current_jobs:
            if job.should_remove():
                remove_jobs.append(job)
            else:
                # Run the job if its time has come
                job.run_if_needed()

        # Cleanup run_once jobs that have already run
        if remove_jobs:
            # Modify the original list safely
            self.__jobs = [job for job in self.__jobs if job not in remove_jobs]

        # Wait for the next polling interval
        sleep(self.__polling_period)

    def enforce_minimum_period(self, flag: bool) -> None:
        """
        Sets whether to enforce a minimum period (currently > 10s) for periodic jobs.

        Args:
            flag (bool): True to enforce, False to allow any period.
        """
        self.__enforce_minimum_period = flag

    def set_polling_period(self, period: int) -> None:
        """
        Sets the polling period (how often the scheduler checks for due jobs).
        Minimum period is 1 second.

        Args:
            period (int): The new polling period in seconds.
        """
        self.__polling_period = max(1, period)  # Ensure minimum of 1 second

    def stop(self) -> None:
        """
        Stops the scheduler thread gracefully.
        Waits for the thread to finish execution.
        """
        if self.is_running():
            self.cancel()  # Signal the LoopingThread to stop
            # Wait for the thread to complete its current loop and exit
            # Use a timeout to prevent indefinite blocking if something goes wrong
            self.join(timeout=self.__polling_period + 1)
            self.__started = False  # Reset started flag

    def scan_modules(
        self,
        modules: list[str],
    ) -> None:
        """
        Imports the specified modules.
        This is useful for discovering functions decorated with scheduling decorators.

        Args:
            modules (list[str]): A list of module names (e.g., ["mypackage.tasks", "other.jobs"]).
        """
        for module in modules:
            try:
                importlib.import_module(module)
            except ImportError as e:
                self.__logger(e) if self.__logger is not None else print(
                    f"Warning: Could not import module '{module}' during scan: {e}"
                )

    def schedule_periodic(
        self,
        func: Callable[[], Any],
        period: int,
        one_time: bool = False,
        on_success: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> "_Scheduler":
        """
        Schedules a function to run periodically or just once after a delay.

        Args:
            func (Callable[[], Any]): The function to schedule.
            on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                        Receives the job's return value. Defaults to None.
            on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                            Receives the exception. Defaults to None.
            period (int): The period in seconds between runs, or the delay for one_time jobs.
            one_time (bool): If True, run the job only once after the initial period. Defaults to False.

        Returns:
            _Scheduler: The scheduler instance for chaining.

        Raises:
            ValueError: If `enforce_minimum_period` is True and the period is <= 10 seconds.
        """
        if self.__enforce_minimum_period and period <= 10 and not one_time:
            raise ValueError(
                "Period must be greater than 10 seconds when enforcement is active"
            )

        self.add_job(
            _Job(
                func.__name__,
                period,
                func,
                one_time,
                on_success=on_success,
                on_error=on_error,
                logger=self.__logger,
            )
        )
        return self

    def schedule_daily(
        self,
        func: Callable[[], Any],
        hour: int,
        minute: int,
        on_success: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> "_Scheduler":
        """
        Schedules a function to run daily at a specific hour and minute (local time).

        Args:
            func (Callable[[], Any]): The function to schedule.
            hour (int): The hour of the day (0-23).
            minute (int): The minute of the hour (0-59).
            on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                        Receives the job's return value. Defaults to None.
            on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                            Receives the exception. Defaults to None.

        Returns:
            _Scheduler: The scheduler instance for chaining.
        """
        period = 24 * 60 * 60  # Daily period in seconds
        start_ts = get_timestamp_today(hour, minute)

        # If the calculated start time is in the past for today, set the first run for tomorrow
        if start_ts < time.time():
            start_ts += period

        job = _Job(
            func.__name__,
            period,
            func,
            False,
            start_ts,
            on_success=on_success,
            on_error=on_error,
        )
        self.add_job(job)
        return self

    def schedule_hourly(
        self,
        func: Callable[[], Any],
        minute: int,
        on_success: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> "_Scheduler":
        """
        Schedules a function to run hourly at a specific minute (local time).

        Args:
            func (Callable[[], Any]): The function to schedule.
            minute (int): The minute of the hour (0-59).
            on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                        Receives the job's return value. Defaults to None.
            on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                            Receives the exception. Defaults to None.

        Returns:
            _Scheduler: The scheduler instance for chaining.
        """
        period = 60 * 60  # Hourly period in seconds
        start_ts = get_timestamp_current_hour(minute)

        # If the calculated start time is in the past for this hour, set the first run for the next hour
        if start_ts < time.time():
            start_ts += period

        job = _Job(
            func.__name__,
            period,
            func,
            False,
            start_ts,
            on_success=on_success,
            on_error=on_error,
        )
        self.add_job(job)
        return self

    def schedule_duration(
        self,
        func: Callable[[], Any],
        duration: Duration,
        on_success: Optional[Callable[[Any], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ) -> "_Scheduler":
        """
        Schedules a function to run periodically based on a Duration object.

        Args:
            func (Callable[[], Any]): The function to schedule.
            on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                        Receives the job's return value. Defaults to None.
            on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                            Receives the exception. Defaults to None.
            duration (Duration): The interval between runs.

        Returns:
            _Scheduler: The scheduler instance for chaining.
        """
        return self.schedule_periodic(
            func, duration.to_seconds(), on_success=on_success, on_error=on_error
        )


def scheduler() -> _Scheduler:
    """
    Convenience function to get the singleton _Scheduler instance.

    Returns:
        _Scheduler: The singleton scheduler instance.
    """
    return _Scheduler.get_instance()


def schedule_periodic(
    period: int,
    one_time: bool = False,
    on_success: Optional[Callable[[Any], Any]] = None,
    on_error: Optional[Callable[[Exception], Any]] = None,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to be executed periodically or once.

    The decorated function will be added to the singleton scheduler.

    **Important Constraints:**
    - The decorated function must be a static method or a standalone function.
    - It cannot be an instance method, lambda, generator, coroutine, or nested function,
      as the scheduler executes it without an instance context.

    Args:
        period (int): The period in seconds between runs, or the delay for one_time jobs.
        one_time (bool): If True, run the job only once after the initial period. Defaults to False.
        on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                    Receives the job's return value. Defaults to None.
        on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                        Receives the exception. Defaults to None.

    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: The decorator function.

    Raises:
        ValueError: If `enforce_minimum_period` is True and the period is <= 10 seconds (for periodic jobs).
    """

    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        scheduler().schedule_periodic(
            func, period, one_time, on_success=on_success, on_error=on_error
        )
        return func  # Return the original function

    return decorator


def get_timestamp_current_hour(minute: int) -> int:
    """
    Computes the Unix timestamp for a given minute within the current hour
    using the machine's local timezone.

    Args:
        minute (int): An integer representing the minute (0-59).

    Returns:
        int: The Unix timestamp (seconds since the epoch) for the specified
             minute of the current hour in the machine's local timezone.

    Raises:
        ValueError: If minute is outside the range 0-59.
    """
    if not 0 <= minute <= 59:
        raise ValueError("Minute must be between 0 and 59")

    now_local = datetime.datetime.now()
    # Create a datetime object for the target time within the current hour and day
    target_time = now_local.replace(minute=minute, second=0, microsecond=0)

    # Convert the datetime object to a Unix timestamp
    timestamp = time.mktime(target_time.timetuple())
    return int(timestamp)


def get_timestamp_today(hour: int, minute: int) -> int:
    """
    Computes the Unix timestamp for a given hour and minute for the current day
    using the machine's local timezone.

    Args:
        hour (int): An integer representing the hour (0-23).
        minute (int): An integer representing the minute (0-59).

    Returns:
        int: The Unix timestamp (seconds since the epoch) for the specified time today
             in the machine's local timezone.

    Raises:
        ValueError: If hour or minute are outside their valid ranges.
    """
    if not 0 <= hour <= 23:
        raise ValueError("Hour must be between 0 and 23")
    if not 0 <= minute <= 59:
        raise ValueError("Minute must be between 0 and 59")

    now_local = datetime.datetime.now()
    # Create a datetime object for the target time on the current date
    target_time = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Convert the datetime object to a Unix timestamp
    timestamp = time.mktime(target_time.timetuple())
    return int(timestamp)


def schedule_daily(
    hour: int,
    minute: int,
    on_success: Optional[Callable[[Any], Any]] = None,
    on_error: Optional[Callable[[Exception], Any]] = None,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to run daily at a specific hour and minute (local time).

    The decorated function will be added to the singleton scheduler.

    **Important Constraints:**
    - The decorated function must be a static method or a standalone function.
    - See `schedule_periodic` decorator for more details on constraints.

    Args:
        hour (int): The hour of the day (0-23).
        minute (int): The minute of the hour (0-59).
        on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                    Receives the job's return value. Defaults to None.
        on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                        Receives the exception. Defaults to None.

    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: The decorator function.

    Raises:
        ValueError: If hour or minute are outside their valid ranges.
    """

    # Input validation happens in get_timestamp_today called by schedule_daily method
    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        scheduler().schedule_daily(
            func, hour, minute, on_success=on_success, on_error=on_error
        )
        return func  # Return the original function

    return decorator


def schedule_hourly(
    minute: int,
    on_success: Optional[Callable[[Any], Any]] = None,
    on_error: Optional[Callable[[Exception], Any]] = None,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to run hourly at a specific minute (local time).

    The decorated function will be added to the singleton scheduler.

    **Important Constraints:**
    - The decorated function must be a static method or a standalone function.
    - See `schedule_periodic` decorator for more details on constraints.

    Args:
        minute (int): The minute of the hour (0-59).
        on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                    Receives the job's return value. Defaults to None.
        on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                        Receives the exception. Defaults to None.

    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: The decorator function.

    Raises:
        ValueError: If minute is outside the range 0-59.
    """

    # Input validation happens in get_timestamp_current_hour called by schedule_hourly method
    def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
        # Note: The original code passed a timestamp here, but the method expects minute. Correcting.
        scheduler().schedule_hourly(
            func, minute, on_success=on_success, on_error=on_error
        )
        return func  # Return the original function

    return decorator


def schedule_duration(
    duration: Duration,
    on_success: Optional[Callable[[Any], Any]] = None,
    on_error: Optional[Callable[[Exception], Any]] = None,
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """
    Decorator to schedule a function to run periodically based on a Duration object.

    The decorated function will be added to the singleton scheduler.

    **Important Constraints:**
    - The decorated function must be a static method or a standalone function.
    - See `schedule_periodic` decorator for more details on constraints.

    Args:
        duration (Duration): The interval between runs.
        on_success (Optional[Callable[[Any], Any]]): Callback executed on successful job completion.
                                                    Receives the job's return value. Defaults to None.
        on_error (Optional[Callable[[Exception], Any]]): Callback executed on job failure.
                                                        Receives the exception. Defaults to None.

    Returns:
        Callable[[Callable[[], Any]], Callable[[], Any]]: The decorator function.

    Raises:
        ValueError: If `enforce_minimum_period` is True and the duration is <= 10 seconds.
    """
    # Validation happens within the schedule_periodic call
    return schedule_periodic(
        duration.to_seconds(), on_success=on_success, on_error=on_error
    )
