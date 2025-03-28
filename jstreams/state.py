from threading import Lock, Thread
from typing import Any, Callable, Generic, Optional, TypeVar

from jstreams.utils import each

T = TypeVar("T")
V = TypeVar("V")


class _State(Generic[T]):
    __slots__ = ("__value", "__on_change_list", "__on_change_async_list")

    def __init__(
        self,
        value: T,
    ) -> None:
        self.__value = value
        self.__on_change_list: list[Callable[[T, T], Any]] = []
        self.__on_change_async_list: list[Callable[[T, T], Any]] = []

    def set_value(self, value: T) -> None:
        old_value = self.__value
        self.__value = value
        if len(self.__on_change_async_list) > 0:
            each(
                self.__on_change_list,
                lambda fn: Thread(target=lambda: fn(self.__value, old_value)).start(),
            )
        if len(self.__on_change_list) > 0:
            each(self.__on_change_list, lambda fn: fn(self.__value, old_value))

    def get_value(self) -> T:
        return self.__value

    def add_on_change(
        self, on_change: Optional[Callable[[T, T], Any]], asynchronous: bool
    ) -> None:
        if on_change is not None:
            if asynchronous:
                self.__on_change_async_list.append(on_change)
            else:
                self.__on_change_list.append(on_change)

    def expand(self) -> tuple[Callable[[], T], Callable[[T], None]]:
        return self.get_value, self.set_value


class _StateManager:
    instance: Optional["_StateManager"] = None
    instance_lock = Lock()

    def __init__(self) -> None:
        self.__states: dict[str, _State[Any]] = {}

    def get_state(
        self,
        key: str,
        value: T,
        on_change: Optional[Callable[[T, T], Any]],
        asynchronous: bool,
    ) -> _State[T]:
        if key in self.__states:
            current_state = self.__states[key]
            current_state.add_on_change(on_change, asynchronous)
            return self.__states[key]
        state = _State(value)
        state.add_on_change(on_change, asynchronous)
        self.__states[key] = state
        return state


def _state_manager() -> _StateManager:
    if _StateManager.instance is None:
        with _StateManager.instance_lock:
            if _StateManager.instance is None:
                _StateManager.instance = _StateManager()
                return _StateManager.instance
            return _StateManager.instance
    return _StateManager.instance


def default_state(typ: type[T], value: Optional[T] = None) -> Optional[T]:
    return value


def null_state(typ: type[T]) -> Optional[T]:
    return None


def use_state(
    key: str,
    default_value: T,
    on_change: Optional[Callable[[T, T], Any]] = None,
) -> tuple[Callable[[], T], Callable[[T], None]]:
    """
    Returns a state (getter,setter) tuple for a managed state.

    Args:
        key (str): The key of the state
        default_value (T): The default value of the state
        on_change (Optional[Callable[[T, T], Any]], optional): A function or method where the caller is notified about changes in the state.
            The first argument in this function will be the new state value, and the second will be the old state value.
            The on change will be called synchonously.
            Defaults to None.

    Returns:
        tuple[Callable[[], T], Callable[[T], None]]: The getter and setter
    """
    return _state_manager().get_state(key, default_value, on_change, False).expand()


def use_async_state(
    key: str,
    default_value: T,
    on_change: Optional[Callable[[T, T], Any]] = None,
) -> tuple[Callable[[], T], Callable[[T], None]]:
    """
    Returns a state (getter,setter) tuple for a managed state.

    Args:
        key (str): The key of the state
        default_value (T): The default value of the state
        on_change (Optional[Callable[[T, T], Any]], optional): A function or method where the caller is notified about changes in the state.
            The first argument in this function will be the new state value, and the second will be the old state value.
            The on change will be called asynchonously.
            Defaults to None.

    Returns:
        tuple[Callable[[], T], Callable[[T], None]]: The getter and setter
    """
    return _state_manager().get_state(key, default_value, on_change, True).expand()
