import json
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")


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
