import abc
from threading import Thread
from typing import Any, Callable, Protocol


class Cancellable(Protocol):
    def cancel(self) -> None:
        pass


class LoopingThread(Thread, abc.ABC, Cancellable):
    """
    This thread loops until canceled. This class is abstract and requires the implementation of the loop method.
    All sleeps need to be handled in the loop method implementation.
    """

    __slots__ = ("__running",)

    def __init__(self) -> None:
        """
        Constructor.
        """
        Thread.__init__(self)
        self.__running = False

    @abc.abstractmethod
    def loop(self) -> None:
        pass

    def cancel(self) -> None:
        """
        Cancels this looping thread
        """
        self.__running = False

    def run(self) -> None:
        self.__running = True
        while self.__running:
            self.loop()

    def is_running(self) -> bool:
        """
        Check if the thread is running.

        Returns:
            bool: True if the thread is running, False otherwise.
        """
        return self.__running


class CallbackLoopingThread(LoopingThread):
    """
    Extension of LoopingThread. Provide your own callback instead of implementing the loop method.
    """

    __slots__ = ("__target",)

    def __init__(self, callback: Callable[[], Any]) -> None:
        """
        Constructor. All sleeps must be handled in the callback

        Args:
            callback (Callable[[], Any]): The callback to be executed in a loop
        """
        LoopingThread.__init__(self)
        self.__target = callback

    def loop(self) -> None:
        self.__target()


def cancel_thread(thread: Cancellable) -> None:
    thread.cancel()
