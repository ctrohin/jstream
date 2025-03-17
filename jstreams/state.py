from threading import Lock, Thread
from typing import Any, Callable, Generic, Optional, TypeVar

from jstreams import each

T = TypeVar("T")
V = TypeVar("V")


class _State(Generic[T]):
    __slots__ = ("__value", "__onChangeList", "__onChangeAsyncList")

    def __init__(
        self,
        value: T,
    ) -> None:
        self.__value = value
        self.__onChangeList: list[Callable[[T, T], Any]] = []
        self.__onChangeAsyncList: list[Callable[[T, T], Any]] = []

    def setValue(self, value: T) -> None:
        oldValue = self.__value
        self.__value = value
        if len(self.__onChangeAsyncList) > 0:
            each(
                self.__onChangeList,
                lambda fn: Thread(target=lambda: fn(self.__value, oldValue)).start(),
            )
        if len(self.__onChangeList) > 0:
            each(self.__onChangeList, lambda fn: fn(self.__value, oldValue))

    def getValue(self) -> T:
        return self.__value

    def addOnChange(
        self, onChange: Optional[Callable[[T, T], Any]], asynchronous: bool
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
        self.__states: dict[str, _State[Any]] = {}

    def getState(
        self,
        key: str,
        value: T,
        onChange: Optional[Callable[[T, T], Any]],
        asynchronous: bool,
    ) -> _State[T]:
        if key in self.__states:
            currentState = self.__states[key]
            currentState.addOnChange(onChange, asynchronous)
            return self.__states[key]
        state = _State(value)
        state.addOnChange(onChange, asynchronous)
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


def defaultState(typ: type[T], value: Optional[T] = None) -> Optional[T]:
    return value


def nullState(typ: type[T]) -> Optional[T]:
    return None


def useState(
    key: str,
    defaultValue: T,
    onChange: Optional[Callable[[T, T], Any]] = None,
) -> tuple[Callable[[], T], Callable[[T], None]]:
    """
    Returns a state (getter,setter) tuple for a managed state.

    Args:
        key (str): The key of the state
        defaultValue (T): The default value of the state
        onChange (Optional[Callable[[T, T], Any]], optional): A function or method where the caller is notified about changes in the state.
            The first argument in this function will be the new state value, and the second will be the old state value.
            The on change will be called synchonously.
            Defaults to None.

    Returns:
        tuple[Callable[[], T], Callable[[T], None]]: The getter and setter
    """
    return _stateManager().getState(key, defaultValue, onChange, False).expand()


def useAsyncState(
    key: str,
    defaultValue: T,
    onChange: Optional[Callable[[T, T], Any]] = None,
) -> tuple[Callable[[], T], Callable[[T], None]]:
    """
    Returns a state (getter,setter) tuple for a managed state.

    Args:
        key (str): The key of the state
        defaultValue (T): The default value of the state
        onChange (Optional[Callable[[T, T], Any]], optional): A function or method where the caller is notified about changes in the state.
            The first argument in this function will be the new state value, and the second will be the old state value.
            The on change will be called asynchonously.
            Defaults to None.

    Returns:
        tuple[Callable[[], T], Callable[[T], None]]: The getter and setter
    """
    return _stateManager().getState(key, defaultValue, onChange, True).expand()
