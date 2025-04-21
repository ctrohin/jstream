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

from types import FunctionType, MethodType

T = TypeVar("T")
K = TypeVar("K")
C = TypeVar("C")
V = TypeVar("V")


def is_mth_or_fn(var: Any) -> bool:
    """
    Checks if the given argument is either a function or a method in a class.

    Args:
        var (Any): The argument to check

    Returns:
        bool: True if var is a function or method, False otherwise
    """
    var_type = type(var)
    return var_type is FunctionType or var_type is MethodType


def require_non_null(obj: Optional[T], message: Optional[str] = None) -> T:
    """
    Returns a non null value of the object provided. If the provided value is null,
    the function raises a ValueError.

    Args:
        obj (Optional[T]): The object
        message (Optional[str]): Error message

    Raises:
        ValueError: Thrown when obj is None

    Returns:
        T: The non null value
    """
    if obj is None:
        raise ValueError(message or "None object provided")
    return obj


def is_number(any_val: Any) -> bool:
    """Checks if the value provided is a float number or a string representing a valid float number
    Since int is a subset of float, all int numbers will pass the condition.

    Args:
        any_val (any): the value

    Returns:
        bool: True if anyVal is a float, False otherwise
    """
    try:
        float(any_val)
    except (ValueError, TypeError):
        return False
    return True


def to_int(val: Any) -> int:
    """
    Returns an int representation of the given value.
    Raises a ValueError if the value cannot be represented as an int.

    Args:
        val (Any): The value

    Returns:
        int: The int representation
    """
    return int(val)


def to_float(val: Any) -> float:
    """
    Returns a float representation of the given value.
    Raises a ValueError if the value cannot be represented as a float.

    Args:
        val (Any): The value

    Returns:
        float: The float representation
    """
    return float(val)


def as_list(dct: dict[Any, T]) -> list[T]:
    """
    Returns the values in a dict as a list.

    Args:
        dct (dict[Any, T]): The dictionary

    Returns:
        list[T]: The list of values
    """
    return list(dct.values())


def keys_as_list(dct: dict[T, Any]) -> list[T]:
    """
    Returns the keys in a dict as a list

    Args:
        dct (dict[T, Any]): The dictionary

    Returns:
        list[T]: The list of keys
    """
    return list(dct.keys())


def load_json(
    s: Union[str, bytes, bytearray],
) -> Optional[Union[list[Any], dict[Any, Any]]]:
    return load_json_ex(s, None)


def load_json_ex(
    s: Union[str, bytes, bytearray], handler: Optional[Callable[[Exception], Any]]
) -> Optional[Union[list[Any], dict[Any, Any]]]:
    try:
        return json.loads(s)  # type: ignore[no-any-return]
    except json.JSONDecodeError as ex:
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
    typ: type[T], val: Any, keys: list[Any], default_value: Optional[T] = None
) -> Optional[T]:
    """
    Extract a property from a complex object

    Args:
        typ (type[T]): The property type
        val (Any): The object the property will be extracted from
        keys (list[Any]): The list of keys to be applied. For each key, a value will be extracted recursively
        default_value (Optional[T], optional): Default value if property is not found. Defaults to None.

    Returns:
        Optional[T]: The found property or the default value
    """
    if val is None:
        return default_value

    if len(keys) == 0:
        return cast(T, val) if val is not None else default_value

    if isinstance(val, list):
        if len(val) < keys[0]:
            return default_value
        return extract(typ, val[keys[0]], keys[1:], default_value)

    if isinstance(val, dict):
        return extract(typ, val.get(keys[0], None), keys[1:], default_value)

    if hasattr(val, keys[0]):
        return extract(typ, getattr(val, keys[0]), keys[1:], default_value)
    return default_value


def is_not_none(element: Optional[T]) -> bool:
    """
    Checks if the given element is not None. This function is meant to be used
    instead of lambdas for non null checks

    Args:
        element (Optional[T]): The given element

    Returns:
        bool: True if element is not None, False otherwise
    """
    return element is not None


def is_empty_or_none(
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

    if isinstance(obj, Sized):
        return len(obj) == 0

    if isinstance(obj, Iterable):
        for _ in obj:
            return False
        return True

    return False


def cmp_to_key(mycmp: Callable[[C, C], int]) -> type:
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


def dict_update(target: dict[K, V], key: K, value: V) -> None:
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

    return sorted(target, key=cmp_to_key(comparator))


class Value(Generic[T]):
    __slots__ = ["__value"]

    def __init__(self, value: Optional[T]) -> None:
        self.__value = value

    def set(self, value: Optional[T]) -> None:
        self.__value = value

    def get(self) -> Optional[T]:
        return self.__value
