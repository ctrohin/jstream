from typing import TypeVar, Callable, Optional, Any, Generic, Protocol

from jstreams.stream import Opt

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class ErrorLog(Protocol):
    def error(self, msg: Any, *args: Any, **kwargs: Any) -> Any:
        pass


class Try(Generic[T]):
    __slots__ = (
        "__fn",
        "__then_chain",
        "__on_failure",
        "__error_log",
        "__error_message",
        "__has_failed",
        "__logger",
    )

    def __init__(self, fn: Callable[[], T]):
        self.__fn = fn
        self.__then_chain: list[Callable[[T], Any]] = []
        self.__on_failure: Optional[Callable[[BaseException], Any]] = None
        self.__error_log: Optional[ErrorLog] = None
        self.__error_message: Optional[str] = None
        self.__has_failed = False

    def with_logger(self, logger: ErrorLog) -> "Try[T]":
        self.__error_log = logger
        return self

    def with_error_message(self, error_message: str) -> "Try[T]":
        self.__error_message = error_message
        return self

    def and_then(self, fn: Callable[[T], Any]) -> "Try[T]":
        self.__then_chain.append(fn)
        return self

    def on_failure(self, fn: Callable[[BaseException], Any]) -> "Try[T]":
        self.__on_failure = fn
        return self

    def on_failure_log(self, message: str, error_log: ErrorLog) -> "Try[T]":
        return self.with_error_message(message).with_logger(error_log)

    def get(self) -> Opt[T]:
        try:
            val = self.__fn()
            for fn in self.__then_chain:
                fn(val)
            return Opt(val)
        except Exception as e:
            self.__has_failed = True
            if self.__on_failure is not None:
                self.__on_failure(e)
            if self.__error_log is not None:
                if self.__error_message is not None:
                    self.__error_log.error(self.__error_message)
                self.__error_log.error(e, exc_info=True)
        return Opt(None)

    def has_failed(self) -> bool:
        self.get()
        return self.__has_failed

    @staticmethod
    def of(val: K) -> "Try[K]":
        return Try(lambda: val)
