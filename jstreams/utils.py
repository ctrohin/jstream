import json
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")


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

def loadJson(s: Union[str, bytes, bytearray]) -> Optional[Union[list[Any], dict[Any, Any]]]:
    return loadJsonEx(s, None)
        

def loadJsonEx(s: Union[str, bytes, bytearray], handler: Optional[Callable[[Exception], Any]]) -> Optional[Union[list[Any], dict[Any, Any]]]:
    try:
        return json.loads(s) # type: ignore[no-any-return]
    except Exception as ex:
        if handler is not None:
            handler(ex)
    return None

__all__ = [
    "requireNotNull",
    "isNumber",
    "toInt",
    "toFloat",
    "asList",
    "keysAsList",
    "loadJson",
    "loadJsonEx",
]
