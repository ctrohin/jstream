from logging import Logger
import logging
from time import sleep
from typing import Final, TypeVar, Callable, Optional, Any, Generic, Protocol, Union

from jstreams.stream import Opt
from jstreams.utils import require_non_null

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

UNCAUGHT_EXCEPTION_LOGGER_NAME: Final[str] = "uncaught_exception_logger"


class ErrorLog(Protocol):
    def error(self, msg: Any, *args: Any, **kwargs: Any) -> Any:
        pass


ErrorLogger = Union[ErrorLog, Logger]


def catch(
    fn: Callable[[], T],
    logger: Optional[ErrorLogger] = None,
) -> Optional[T]:
    try:
        return fn()
    except Exception as e:
        logger.error(e, exc_info=True) if logger is not None else logging.getLogger(
            UNCAUGHT_EXCEPTION_LOGGER_NAME
        ).error(e, exc_info=True)
        return None


def catchWith(
    with_val: T,
    fn: Callable[[T], V],
    logger: Optional[ErrorLogger] = None,
) -> Optional[V]:
    try:
        return fn(with_val)
    except Exception as e:
        logger.error(
            "Uncaught exception", e, exc_info=True
        ) if logger is not None else logging.getLogger(
            UNCAUGHT_EXCEPTION_LOGGER_NAME
        ).error("Uncaught exception", e, exc_info=True)
        return None


class Try(Generic[T]):
    __slots__ = (
        "__fn",
        "__then_chain",
        "__on_failure_chain",
        "__error_log",
        "__error_message",
        "__has_failed",
        "__logger",
        "__finally_chain",
        "__failure_exception_supplier",
        "__recovery_supplier",
        "__retries",
        "__retries_delay",
    )

    def __init__(self, fn: Callable[[], T]) -> None:
        self.__fn = fn
        self.__then_chain: list[Callable[[T], Any]] = []
        self.__finally_chain: list[Callable[[Optional[T]], Any]] = []
        self.__on_failure_chain: list[Callable[[BaseException], Any]] = []
        self.__error_log: Optional[ErrorLogger] = None
        self.__error_message: Optional[str] = None
        self.__has_failed = False
        self.__failure_exception_supplier: Optional[Callable[[], Exception]] = None
        self.__recovery_supplier: Optional[Callable[[Optional[Exception]], T]] = None
        self.__retries: int = 0
        self.__retries_delay: float = 0

    def with_logger(self, logger: ErrorLogger) -> "Try[T]":
        self.__error_log = logger
        return self

    def with_error_message(self, error_message: str) -> "Try[T]":
        self.__error_message = error_message
        return self

    def with_retries(self, retries: int, delay_between: float = 0) -> "Try[T]":
        self.__retries = retries
        self.__retries_delay = delay_between
        return self

    def and_then(self, fn: Callable[[T], Any]) -> "Try[T]":
        self.__then_chain.append(fn)
        return self

    def on_failure(self, fn: Callable[[BaseException], Any]) -> "Try[T]":
        self.__on_failure_chain.append(fn)
        return self

    def and_finally(self, fn: Callable[[Optional[T]], Any]) -> "Try[T]":
        self.__finally_chain.append(fn)
        return self

    def on_failure_log(self, message: str, error_log: ErrorLog) -> "Try[T]":
        return self.with_error_message(message).with_logger(error_log)

    def __handle_exception(self, e: Exception) -> None:
        # When we have a failure, set the failed flag
        self.__has_failed = True
        # If we have a logger set, log the error
        if self.__error_log is not None:
            self.__error_log.error(
                self.__error_message
                if self.__error_message is not None
                else "Exception within Try",
                e,
                exc_info=True,
            )
        # Then call all the failure chain methods
        for fail_fn in self.__on_failure_chain:
            catchWith(e, fail_fn, self.__error_log)

        if self.__failure_exception_supplier is not None:
            raise self.__failure_exception_supplier()

    def __finally(self, val: Optional[T]) -> None:
        for finally_fn in self.__finally_chain:
            catchWith(val, finally_fn, self.__error_log)

    def get(self) -> Opt[T]:
        self.__has_failed = False
        val: Optional[T] = None
        retry = self.__retries - 1
        exit = False
        exception: Optional[Exception] = None
        while not exit:
            try:
                # Try to execute the constructor function in order to get the initial value
                val = self.__fn()
                # Then execut every function in the "then" chain
                for fn in self.__then_chain:
                    fn(val)
                # Upon success, return an optional with the constructor produced value
                exit = True
                return Opt(val)
            except Exception as e:
                exception = e
                if retry <= 0:
                    exit = True
                elif self.__retries_delay > 0:
                    # If we have retries, sleep for the delay time
                    sleep(self.__retries_delay)
                # Decrement the retry count
                retry -= 1
                if exit:
                    # Handle the exception
                    self.__handle_exception(e)
            finally:
                if exit:
                    # And finally call all the finally chain methods
                    self.__finally(val)
        return Opt(
            self.__recovery_supplier(exception)
            if self.__recovery_supplier is not None
            else None
        )

    def on_failure_raise(self, exception_supplier: Callable[[], Exception]) -> "Try[T]":
        self.__failure_exception_supplier = exception_supplier
        return self

    def recover(
        self, recovery_supplier: Callable[[Optional[Exception]], T]
    ) -> "Try[T]":
        self.__recovery_supplier = recovery_supplier
        return self

    def has_failed(self) -> bool:
        self.get()
        return self.__has_failed

    @staticmethod
    def of(val: Optional[K]) -> "Try[K]":
        return Try(lambda: require_non_null(val))


def try_(fn: Callable[[], T]) -> Try[T]:
    return Try(fn)


def try_of(value: Optional[T]) -> Try[T]:
    return Try.of(value)
