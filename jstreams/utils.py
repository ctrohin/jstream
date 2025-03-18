import json
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    Sized,
    TypeVar,
    Union,
    cast,
)


T = TypeVar("T")
K = TypeVar("K")
C = TypeVar("C")
V = TypeVar("V")


def _f() -> None:
    pass


class _F:
    def mth(self) -> None:
        pass


FnType = type(_f)
MthType = type(_F().mth)


def isCallable(var: Any) -> bool:
    """
    Checks if the given argument is either a function or a method in a class.

    Args:
        var (Any): The argument to check

    Returns:
        bool: True if var is a function or method, False otherwise
    """
    varType = type(var)
    return varType is FnType or varType is MthType


def requireNotNull(obj: Optional[T]) -> T:
    """
    Returns a non null value of the object provided. If the provided value is null,
    the function raises a ValueError.

    Args:
        obj (Optional[T]): The object

    Raises:
        ValueError: Thrown when obj is None

    Returns:
        T: The non null value
    """
    if obj is None:
        raise ValueError("None object provided")
    return obj


def isNumber(anyVal: Any) -> bool:
    """Checks if the value provided is a number

    Args:
        anyVal (any): the value

    Returns:
        bool: True if anyVal is a number, False otherwise
    """
    try:
        _: float = float(anyVal) + 1
    except Exception:
        return False
    return True


def toInt(val: Any) -> int:
    """
    Returns an int representation of the given value.
    Raises a ValueError if the value cannot be represented as an int.

    Args:
        val (Any): The value

    Returns:
        int: The int representation
    """
    return int(str(val))


def toFloat(val: Any) -> float:
    """
    Returns a float representation of the given value.
    Raises a ValueError if the value cannot be represented as a float.

    Args:
        val (Any): The value

    Returns:
        float: The float representation
    """
    return float(str(val))


def asList(dct: dict[Any, T]) -> list[T]:
    """
    Returns the values in a dict as a list.

    Args:
        dct (dict[Any, T]): The dictionary

    Returns:
        list[T]: The list of values
    """
    return [v for _, v in dct.items()]


def keysAsList(dct: dict[T, Any]) -> list[T]:
    """
    Returns the keys in a dict as a list

    Args:
        dct (dict[T, Any]): The dictionary

    Returns:
        list[T]: The list of keys
    """
    return [k for k, _ in dct.items()]


def loadJson(
    s: Union[str, bytes, bytearray],
) -> Optional[Union[list[Any], dict[Any, Any]]]:
    return loadJsonEx(s, None)


def loadJsonEx(
    s: Union[str, bytes, bytearray], handler: Optional[Callable[[Exception], Any]]
) -> Optional[Union[list[Any], dict[Any, Any]]]:
    try:
        return json.loads(s)  # type: ignore[no-any-return]
    except Exception as ex:
        if handler is not None:
            handler(ex)
    return None


def identity(value: T) -> T:
    """
    Returns the same value.

    Args:
        value (T): The given value

    Returns:
        T: The same value
    """
    return value


def extract(
    typ: type[T], val: Any, keys: list[Any], defaultValue: Optional[T] = None
) -> Optional[T]:
    """
    Extract a property from a complex object

    Args:
        typ (type[T]): The property type
        val (Any): The object the property will be extracted from
        keys (list[Any]): The list of keys to be applied. For each key, a value will be extracted recursively
        defaultValue (Optional[T], optional): Default value if property is not found. Defaults to None.

    Returns:
        Optional[T]: The found property or the default value
    """
    if val is None:
        return defaultValue

    if len(keys) == 0:
        return cast(typ, val) if val is not None else defaultValue  # type: ignore[valid-type]

    if isinstance(val, list):
        if len(val) < keys[0]:
            return defaultValue
        return extract(typ, val[keys[0]], keys[1:], defaultValue)

    if isinstance(val, dict):
        return extract(typ, val.get(keys[0], None), keys[1:], defaultValue)

    if hasattr(val, keys[0]):
        return extract(typ, getattr(val, keys[0]), keys[:1], defaultValue)
    return defaultValue


def isNotNone(element: Optional[T]) -> bool:
    """
    Checks if the given element is not None. This function is meant to be used
    instead of lambdas for non null checks

    Args:
        element (Optional[T]): The given element

    Returns:
        bool: True if element is not None, False otherwise
    """
    return element is not None


def isEmptyOrNone(
    obj: Union[list[Any], dict[Any, Any], str, None, Any, Iterable[Any]],
) -> bool:
    """
    Checkes whether the given object is either None, or is empty.
    For str and Sized objects, besides the None check, the len(obj) == 0 is also applied

    Args:
        obj (Union[list[Any], dict[Any, Any], str, None, Any, Iterable[Any]]): The object

    Returns:
        bool: True if empty or None, False otherwise
    """
    if obj is None:
        return True

    if isinstance(obj, Iterable):
        for _ in obj:
            return False
        return True

    if isinstance(obj, Sized):
        return len(obj) == 0

    return False


def cmpToKey(mycmp: Callable[[C, C], int]) -> type:
    """Convert a cmp= function into a key= function"""

    class Key(Generic[C]):  # type: ignore[misc]
        __slots__ = ["obj"]

        def __init__(self, obj: C) -> None:
            self.obj = obj

        def __lt__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) >= 0

    return Key


def each(target: Optional[Iterable[T]], action: Callable[[T], Any]) -> None:
    """
    Executes an action on each element of the given iterable

    Args:
        target (Optional[Iterable[T]]): The target iterable
        action (Callable[[T], Any]): The action to be executed
    """
    if target is None:
        return

    for el in target:
        action(el)


def dictUpdate(target: dict[K, V], key: K, value: V) -> None:
    target[key] = value


def sort(target: list[T], comparator: Callable[[T, T], int]) -> list[T]:
    """
    Returns a list with the elements sorted according to the comparator function.
    CAUTION: This method will actually iterate the entire iterable, so if you're using
    infinite generators, calling this method will block the execution of the program.

    Args:
        comparator (Callable[[T, T], int]): The comparator function

    Returns:
        list[T]: The resulting list
    """

    return sorted(target, key=cmpToKey(comparator))
