from threading import Lock, Thread
from typing import Any, Callable, Generic, Optional, TypeVar

from jstreams import each

T = TypeVar("T")
V = TypeVar("V")


class State(Generic[T]):
    __slots__ = ("__value", "__onChangeList", "__onChangeAsyncList")

    def __init__(
        self,
        value: T,
    ) -> None:
        self.__value = value
        self.__onChangeList: list[Callable[[T], Any]] = []
        self.__onChangeAsyncList: list[Callable[[T], Any]] = []

    def setValue(self, value: T) -> None:
        self.__value = value
        if len(self.__onChangeAsyncList) > 0:
            Thread(
                target=lambda: each(
                    self.__onChangeAsyncList, lambda fn: fn(self.__value)
                )
            )
        if len(self.__onChangeList) > 0:
            each(self.__onChangeList, lambda fn: fn(self.__value))

    def getValue(self) -> T:
        return self.__value

    def addOnChange(
        self, onChange: Optional[Callable[[T], Any]], asynchronous: bool
    ) -> None:
        if onChange is not None:
            if asynchronous:
                self.__onChangeAsyncList.append(onChange)
            else:
                self.__onChangeList.append(onChange)

    def expand(self) -> tuple[Callable[[], T], Callable[[T], None]]:
        return self.getValue, self.setValue


class _StateManager:
    instance: Optional["_StateManager"] = None
    instanceLock = Lock()

    def __init__(self) -> None:
        self.__states: dict[str, State[Any]] = {}

    def getState(
        self,
        key: str,
        value: T,
        onChange: Optional[Callable[[T], Any]],
        asyncronous: bool,
    ) -> State[T]:
        if key in self.__states:
            currentState = self.__states[key]
            currentState.addOnChange(onChange, asyncronous)
            return self.__states[key]
        state = State(value)
        state.addOnChange(onChange, asyncronous)
        self.__states[key] = state
        return state


def _stateManager() -> _StateManager:
    if _StateManager.instance is None:
        with _StateManager.instanceLock:
            if _StateManager.instance is None:
                _StateManager.instance = _StateManager()
                return _StateManager.instance
            return _StateManager.instance
    return _StateManager.instance


def defaultState(typ: type[T], value: Optional[T]) -> Optional[T]:
    return value


def useState(
    key: str,
    defaultValue: T,
    onChange: Optional[Callable[[T], Any]] = None,
) -> tuple[Callable[[], T], Callable[[T], None]]:
    return _stateManager().getState(key, defaultValue, onChange, False).expand()


def useAsyncState(
    key: str,
    defaultValue: T,
    onChange: Optional[Callable[[T], Any]] = None,
) -> tuple[Callable[[], T], Callable[[T], None]]:
    return _stateManager().getState(key, defaultValue, onChange, True).expand()
