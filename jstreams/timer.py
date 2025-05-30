from threading import Lock, Thread
from time import sleep
from typing import Any, Callable

from jstreams.thread import LoopingThread, Cancellable


class Timer(Thread, Cancellable):
    """
    Timer is a class providing delayed execution for a given callback.
    It can be cancelled at any time before the time ellapses. The cancellation
    polling interval is 1 second.

    """

    __slots__ = (
        "__time",
        "__cancel_polling_time",
        "__callback",
        "__canceled",
        "__lock",
    )

    def __init__(
        self, time: float, cancel_polling_time: float, callback: Callable[[], Any]
    ) -> None:
        """
        Constructor.

        Args:
            time (float): Number of seconds until execution
            cancelPollingTime (float): Number of seconds at which this timer will poll for cancel flag
            callback (Callable[[], Any]): The callback to be executed
        """
        if time <= 0 or cancel_polling_time <= 0:
            raise ValueError(
                "time and cancelPollingTime parameters must be higher than 0"
            )

        if cancel_polling_time >= time:
            raise ValueError("cancelPollingTime cannot be higher than time")

        self.__time = time
        self.__cancel_polling_time = cancel_polling_time
        self.__callback: Callable[[], Any] = callback
        self.__canceled: bool = False
        self.__lock = Lock()
        Thread.__init__(self)

    def cancel(self) -> None:
        """
        Cancel this timer.
        """
        with self.__lock:
            self.__canceled = True

    def run(self) -> None:
        while self.__time > 0:
            sleep(self.__cancel_polling_time)
            self.__time = self.__time - self.__cancel_polling_time
            with self.__lock:
                if self.__canceled:
                    return
        should_execute = False
        with self.__lock:
            if not self.__canceled:
                should_execute = True
        if should_execute:
            self.__callback()


class Interval(LoopingThread):
    """
    This thread calls the given callback at the given interval, until canceled.
    """

    __slots__ = ("__interval", "__callback")

    def __init__(self, interval: float, callback: Callable[[], Any]) -> None:
        """
        The interval thread calls the given callback at intervals defined by the interval parameter (in seconds).

        Args:
            interval (float): The interval at which the callback will be called
            callback (Callable[[], Any]): The callback

        Raises:
            ValueError: _description_
        """
        LoopingThread.__init__(self)
        if interval <= 0:
            raise ValueError("interval parameter must be higher than 0")
        self.__interval = interval
        self.__callback = callback

    def loop(self) -> None:
        sleep(self.__interval)
        self.__callback()


class CountdownTimer(Thread):
    """
    CountdownTimer is similar to Timer, but doesn't poll for cancellation.
    This is a fire and forget timer that unconditionally executes the callback
    once the time has ellapsed.
    """

    __slots__ = ("__timeout", "__callback")

    def __init__(self, timeout: float, callback: Callable[[], Any]) -> None:
        """
        Constructor. This object cannot be cancelled. Once started, the callback will be
        unconditionally executed after the given time has ellapsed. This implementation
        is an optimization of the Timer class in the sense that it doesn't periodically
        poll for a cancel state.

        Args:
            timeout (float): The number of seconds that should pass until the execution of the callback
            callback (Callable[[], Any]): The callback function
        """
        Thread.__init__(self)
        if timeout <= 0:
            raise ValueError("timeout parameter must be higher than 0")

        self.__timeout = timeout
        self.__callback = callback

    def run(self) -> None:
        sleep(self.__timeout)
        self.__callback()


def set_timer(timeout: float, callback: Callable[[], Any]) -> Cancellable:
    timer = Timer(timeout, 1, callback)
    timer.start()
    return timer


def set_interval(interval: float, callback: Callable[[], Any]) -> Cancellable:
    timer = Interval(interval, callback)
    timer.start()
    return timer


def clear(cancellable: Cancellable) -> None:
    cancellable.cancel()
