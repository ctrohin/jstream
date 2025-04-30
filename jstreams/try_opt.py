import logging
from logging import Logger
from time import sleep
from typing import (
    Any,
    Callable,
    Final,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

from jstreams.noop import noop
from jstreams.stream import Opt
from jstreams.utils import require_non_null

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
EX_TYPE = TypeVar("EX_TYPE")

UNCAUGHT_EXCEPTION_LOGGER_NAME: Final[str] = "uncaught_exception_logger"

# Cache the default logger at the module level
_default_logger: Final[Logger] = logging.getLogger(UNCAUGHT_EXCEPTION_LOGGER_NAME)


class ErrorLog(Protocol):
    """Protocol for a minimal logger interface expecting an error method."""

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> Any:
        pass


ErrorLogger = Union[ErrorLog, Logger]


def _log_exception(
    exception: Exception,
    logger: Optional[ErrorLogger] = None,
    message: Optional[str] = None,
) -> None:
    """Helper function to log exceptions using the provided or default logger."""
    log_target = logger if logger is not None else _default_logger
    log_message = message if message is not None else "Uncaught exception"
    # Pass exception instance directly to exc_info for better traceback formatting
    log_target.error(log_message, exc_info=exception)


def catch(
    fn: Callable[[], T],
    logger: Optional[ErrorLogger] = None,
) -> Optional[T]:
    """
    Executes fn, catches any Exception, logs it using _log_exception,
    and returns None on failure.

    Args:
        fn: The function to execute.
        logger: Optional logger to use. Defaults to UNCAUGHT_EXCEPTION_LOGGER_NAME logger.

    Returns:
        The result of fn() or None if an exception occurred.
    """
    try:
        return fn()
    except Exception as e:
        _log_exception(e, logger)
        return None


def catch_with(
    with_val: K,
    fn: Callable[[K], V],
    logger: Optional[ErrorLogger] = None,
) -> Optional[V]:
    """
    Executes fn(with_val), catches any Exception, logs it using _log_exception,
    and returns None on failure.

    Args:
        with_val: The argument to pass to fn.
        fn: The function to execute.
        logger: Optional logger to use. Defaults to UNCAUGHT_EXCEPTION_LOGGER_NAME logger.

    Returns:
        The result of fn(with_val) or None if an exception occurred.
    """
    try:
        return fn(with_val)
    except Exception as e:
        _log_exception(e, logger)
        return None


class Try(Generic[T]):
    """
    A monadic container for operations that might fail.
    Provides mechanisms for chaining operations, handling failures, retrying,
    and final cleanup actions.
    """

    __slots__ = (
        "__fn",
        "__then_chain",
        "__on_failure_chain",
        "__error_log",
        "__error_message",
        "__has_failed",
        "__finally_chain",
        "__failure_exception_supplier",
        "__recovery_supplier",
        "__retries",
        "__retries_delay",
        "__is_resource",
        "__recovery_suppliers",
    )

    def __init__(self, fn: Callable[[], T], is_resource: bool = False) -> None:
        """
        Initializes a Try operation.

        Args:
            fn: The primary function to execute, which might raise an Exception.
        """
        self.__fn = fn
        self.__is_resource = is_resource
        self.__then_chain: list[Callable[[T], Any]] = []
        self.__finally_chain: list[Callable[[Optional[T]], Any]] = []
        self.__on_failure_chain: list[Callable[[Exception], Any]] = []
        self.__error_log: Optional[ErrorLogger] = None
        self.__error_message: Optional[str] = None
        self.__has_failed: bool = False
        self.__failure_exception_supplier: Optional[Callable[[], Exception]] = None
        self.__recovery_supplier: Optional[
            Callable[[Optional[Exception]], Optional[T]]
        ] = None
        self.__recovery_suppliers: dict[type, Callable[[Any], T]] = {}
        self.__retries: int = 0
        self.__retries_delay: float = 0.0

    def mute(self) -> "Try[T]":
        return self.with_logger(noop())

    def with_logger(self, logger: ErrorLogger) -> "Try[T]":
        """Sets a specific logger for handling errors within this Try block."""
        self.__error_log = logger
        return self

    def with_error_message(self, error_message: str) -> "Try[T]":
        """Sets a custom error message to be used when logging failures."""
        self.__error_message = error_message
        return self

    def retry(self, retries: int, delay_between: float = 0.0) -> "Try[T]":
        """
        Configures the operation to retry on failure.

        Args:
            retries: The number of times to retry after the initial failure.
            delay_between: The delay in seconds between retries. Defaults to 0.
        """
        if retries < 0:
            raise ValueError("Number of retries cannot be negative.")
        if delay_between < 0:
            raise ValueError("Delay between retries cannot be negative.")
        self.__retries = retries
        self.__retries_delay = delay_between
        return self

    def and_then(self, fn: Callable[[T], Any]) -> "Try[T]":
        """
        Adds a function to be executed sequentially if the primary operation succeeds.
        The function receives the result of the preceding successful operation.
        Failures in 'and_then' functions will propagate and cause the Try to fail.
        """
        self.__then_chain.append(fn)
        return self

    def on_failure(self, fn: Callable[[Exception], Any]) -> "Try[T]":
        """
        Adds a function to be executed if the operation fails (after all retries).
        The function receives the exception that caused the failure.
        Multiple failure handlers can be added. Exceptions in handlers are caught and logged.
        """
        self.__on_failure_chain.append(fn)
        return self

    def and_finally(self, fn: Callable[[Optional[T]], Any]) -> "Try[T]":
        """
        Adds a function to be executed after the operation completes, regardless of success or failure.
        The function receives the successful result (if any), otherwise None.
        Multiple finally handlers can be added. Exceptions in handlers are caught and logged.
        """
        self.__finally_chain.append(fn)
        return self

    def on_failure_log(self, message: str, error_log: ErrorLogger) -> "Try[T]":
        """Convenience method to set both an error message and a logger for failures."""
        return self.with_error_message(message).with_logger(error_log)

    def __handle_exception(self, e: Exception) -> None:
        """Internal method to handle exceptions after retries are exhausted."""
        self.__has_failed = True
        _log_exception(e, self.__error_log, self.__error_message)

        for fail_fn in self.__on_failure_chain:
            # Use catch_with to execute failure handlers safely
            catch_with(e, fail_fn, self.__error_log)

        if self.__failure_exception_supplier is not None:
            # If configured, raise a specific exception on failure
            raise self.__failure_exception_supplier()

    def __finally(self, val: Optional[T]) -> None:
        """Internal method to execute all finally handlers."""
        for finally_fn in self.__finally_chain:
            # Use catch_with to execute finally handlers safely
            # Pass None as the value to fn if val is None
            catch_with(val, finally_fn, self.__error_log)

    def get(self) -> Opt[T]:
        """
        Executes the Try operation, including retries and handlers.

        Returns:
            Opt[T]: An Opt containing the result on success or successful recovery,
                    or an empty Opt if the operation failed and could not recover.
        """
        self.__has_failed = False  # Reset failure flag for this execution attempt
        val: Optional[T] = None
        last_exception: Optional[Exception] = None

        # Loop for initial attempt + configured retries
        for attempt in range(self.__retries + 1):
            try:
                # Execute the primary function
                val = self.__fn()
                if self.__is_resource:
                    val = cast(T, val.__enter__())  # type: ignore[attr-defined]

                # Execute chained 'then' functions
                for then_fn in self.__then_chain:
                    # Exceptions in 'then' functions will be caught by the outer try-except
                    then_fn(val)

                last_exception = None  # Mark success for this attempt
                break  # Exit loop on success

            except Exception as e:
                last_exception = e
                if attempt < self.__retries:  # Check if more retries are available
                    if self.__retries_delay > 0:
                        sleep(self.__retries_delay)
                    # Continue to the next retry iteration
                else:
                    # No more retries left, handle the final exception
                    self.__handle_exception(e)
                    # Note: __handle_exception might raise if __failure_exception_supplier is set
            finally:
                if self.__is_resource and val is not None:
                    catch(val.__exit__, self.__error_log)  # type: ignore[attr-defined]

        # --- After the loop (either break on success or finish on failure) ---
        # Execute the finally chain once, passing the result if successful
        self.__finally(val if last_exception is None else None)

        if last_exception is None:
            # Operation succeeded
            return Opt(val)
        else:
            # Operation failed after retries
            return self.__recover(last_exception)

    def exec(self) -> None:
        """
        Executes the Try operation, including retries and handlers.
        Basically an alias of 'get' without the return result.
        """
        self.get()

    def __recover(self, last_exception: Exception) -> Opt[T]:
        # First try to recover for typed suppliers
        for ex_type, supplier in self.__recovery_suppliers.items():
            if isinstance(last_exception, ex_type):
                try:
                    return Opt(supplier(last_exception))
                except Exception as recovery_exception:
                    # Log the recovery failure
                    _log_exception(
                        recovery_exception,
                        self.__error_log,
                        "Exception during Try recovery",
                    )
                    # Recovery failed, return empty Opt
                    return Opt(None)

        if self.__recovery_supplier is not None:
            # Attempt recovery
            try:
                # The recovery function itself might fail
                recovered_val = self.__recovery_supplier(last_exception)
                # If recovery succeeds, __has_failed remains True (as the original op failed),
                # but we return the recovered value.
                return Opt(recovered_val)
            except Exception as recovery_exception:
                # Log the recovery failure
                _log_exception(
                    recovery_exception,
                    self.__error_log,
                    "Exception during Try recovery",
                )
                # Recovery failed, return empty Opt
                return Opt(None)
        return Opt(None)

    def on_failure_raise(self, exception_supplier: Callable[[], Exception]) -> "Try[T]":
        """
        Configures the Try operation to raise a specific exception on failure,
        supplied by the provided function. This overrides default failure handling.
        """
        self.__failure_exception_supplier = exception_supplier
        return self

    def recover(
        self, recovery_supplier: Callable[[Optional[Exception]], Optional[T]]
    ) -> "Try[T]":
        """
        Provides a function to generate a recovery value if the operation fails.
        The function receives the exception that caused the failure.
        If recovery succeeds, get() will return an Opt containing the recovered value.
        """
        self.__recovery_supplier = recovery_supplier
        return self

    def recover_from(
        self, exception_type: type[EX_TYPE], recovery_supplier: Callable[[EX_TYPE], T]
    ) -> "Try[T]":
        self.__recovery_suppliers[exception_type] = recovery_supplier
        return self

    def recover_from_these(
        self,
        exception_types: list[type],
        recovery_supplier: Callable[[BaseException], T],
    ) -> "Try[T]":
        for ex_type in exception_types:
            self.__recovery_suppliers[ex_type] = recovery_supplier
        return self

    def has_failed(self) -> bool:
        """
        Executes the Try operation (including retries, handlers) via self.get()
        and returns True if the original operation failed (i.e., `__handle_exception` was called),
        even if a recovery mechanism subsequently provided a value. Returns False if the
        original operation (including `and_then` steps) succeeded on any attempt.

        Note:
            - This method triggers the full execution defined by the Try object via `get()`.
            - It reflects whether the initial operation path encountered an unretried failure,
            not necessarily whether `get()` ultimately returned an empty `Opt`.
        """
        self.get()  # Trigger execution
        return self.__has_failed

    @staticmethod
    def of(val: Optional[K]) -> "Try[K]":
        """
        Creates a Try instance from an existing value.
        The operation will fail if the provided value is None.

        Args:
            val: The value to wrap in a Try.

        Returns:
            Try[K]: A Try instance that yields the value or fails if it's None.
        """
        # Use require_non_null to raise ValueError if val is None
        return Try(lambda: require_non_null(val))

    @staticmethod
    def with_resource(fn: Callable[[], T]) -> "Try[T]":
        return Try(fn, True)


def try_(fn: Callable[[], T]) -> Try[T]:
    """
    Factory function to create a Try instance from a callable.
    Syntactic sugar for `Try(fn)`.

    Args:
        fn: The function to wrap in a Try.

    Returns:
        Try[T]: A new Try instance.
    """
    return Try(fn)


def try_with_resource(fn: Callable[[], T]) -> Try[T]:
    """
    Factory function to create a Try instance from a callable producing a closeable resource.
    Syntactic sugar for `Try(fn, True)`.

    Args:
        fn: The function to wrap in a Try.

    Returns:
        Try[T]: A new Try instance.
    """
    return Try.with_resource(fn)


def try_of(value: Optional[T]) -> Try[T]:
    """
    Factory function to create a Try instance from an existing value.
    Syntactic sugar for `Try.of(value)`. The operation fails if value is None.

    Args:
        value: The value to wrap.

    Returns:
        Try[T]: A new Try instance.
    """
    return Try.of(value)
