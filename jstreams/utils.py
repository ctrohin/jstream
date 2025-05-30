import json
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

from collections.abc import Sized

import itertools

from types import FunctionType, MethodType

from jstreams.annotations import locked

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
        __slots__ = ("obj",)

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
    __slots__ = ("__value",)

    def __init__(self, value: Optional[T]) -> None:
        self.__value = value

    def set(self, value: Optional[T]) -> None:
        self.__value = value

    def get(self) -> Optional[T]:
        return self.__value

    def __call__(self, value: Optional[T] = None) -> Optional[T]:
        if value is not None:
            self.__value = value
        return self.__value


@locked()
class SynchronizedValue(Value[T]):
    pass


def type_of(obj: T) -> type[T]:
    return type(obj)


def to_nullable(value: T) -> Optional[T]:
    """
    Converts the given value to a nullable type.
    This is a placeholder function that does not perform any actual conversion.
    It is meant to be used as a type hint for nullable values.
    This function is useful for type hinting and code readability.

    Args:
        value (T): The value to convert
    Returns:
        Optional[T]: The nullable value
    """
    return value


def chunk(data: Iterable[T], size: int) -> list[list[T]]:
    """
    Splits an iterable into chunks of a given size.
    The last chunk may be smaller if the iterable's length is not a multiple of size.

    Args:
        data (Iterable[T]): The iterable to chunk.
        size (int): The size of each chunk.

    Returns:
        list[list[T]]: A list of lists, where each inner list is a chunk.

    Raises:
        ValueError: If size is not positive.
    """
    if size <= 0:
        raise ValueError("Chunk size must be positive")

    it = iter(data)
    chunks: list[list[T]] = []
    while True:
        current_chunk = list(itertools.islice(it, size))
        if not current_chunk:
            break
        chunks.append(current_chunk)
    return chunks


def flatten(data: Iterable[Iterable[T]]) -> list[T]:
    """
    Flattens an iterable of iterables one level deep.

    Args:
        data (Iterable[Iterable[T]]): An iterable of iterables.

    Returns:
        list[T]: A new list with elements from the sub-iterables.
    """
    return [item for sublist in data for item in sublist]


def flatten_deep(data: Iterable[Any]) -> list[Any]:
    """
    Recursively flattens a nested iterable.

    Args:
        data (Iterable[Any]): The iterable to flatten.
                              Elements that are themselves iterable (but not strings, bytes, or bytearrays)
                              will be recursively flattened.

    Returns:
        list[Any]: A new list with all elements flattened.
    """
    result: list[Any] = []
    for item in data:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes, bytearray)):
            result.extend(flatten_deep(item))
        else:
            result.append(item)
    return result


def uniq(data: Iterable[T]) -> list[T]:
    """
    Creates a duplicate-free version of an iterable, preserving order.
    Only the first occurrence of each element is kept.
    Note: Elements in `data` must be hashable.

    Args:
        data (Iterable[T]): The input iterable. Elements must be hashable.

    Returns:
        list[T]: A new list with unique elements in their original order.
    """
    seen: set[T] = set()
    result: list[T] = []
    for item in data:
        if item not in seen:
            seen.add(item)  # Requires item to be hashable
            result.append(item)
    return result


def key_by(data: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, T]:
    """
    Creates a dictionary composed of keys generated from the results of running
    each element of iterable thru key_fn. The value for each key is the last
    element that generated that key.

    Args:
        data (Iterable[T]): The iterable to process.
        key_fn (Callable[[T], K]): A function to compute the key for each element.
                                   The key K must be hashable.

    Returns:
        dict[K, T]: A dictionary where keys are K and values are T.
    """
    result: dict[K, T] = {}
    for item in data:
        key = key_fn(item)
        result[key] = item
    return result


def pick(source_dict: dict[K, V], keys: Iterable[K]) -> dict[K, V]:
    """
    Creates a dictionary composed of the picked key-value pairs from source_dict.

    Args:
        source_dict (dict[K, V]): The source dictionary.
        keys (Iterable[K]): An iterable of keys to pick.

    Returns:
        dict[K, V]: A new dictionary with the picked key-value pairs.
    """
    keys_to_pick = set(keys)  # Efficient lookup for keys to include
    return {k: v for k, v in source_dict.items() if k in keys_to_pick}


def omit(source_dict: dict[K, V], keys_to_omit: Iterable[K]) -> dict[K, V]:
    """
    Creates a dictionary composed of the key-value pairs from source_dict
    that are not specified in keys_to_omit.

    Args:
        source_dict (dict[K, V]): The source dictionary.
        keys_to_omit (Iterable[K]): An iterable of keys to omit.

    Returns:
        dict[K, V]: A new dictionary without the omitted key-value pairs.
    """
    keys_to_skip = set(keys_to_omit)  # Efficient lookup for keys to exclude
    return {k: v for k, v in source_dict.items() if k not in keys_to_skip}


def head(data: Sequence[T]) -> Optional[T]:
    """
    Gets the first element of a sequence.

    Args:
        data (Sequence[T]): The input sequence.

    Returns:
        Optional[T]: The first element, or None if the sequence is empty.
    """
    return data[0] if data else None


def tail(data: Sequence[T]) -> list[T]:
    """
    Gets all but the first element of a sequence. (Similar to Lodash _.rest)

    Args:
        data (Sequence[T]): The input sequence.

    Returns:
        list[T]: A new list containing all elements of data except the first.
                 Returns an empty list if data has 0 or 1 element.
    """
    return list(data[1:]) if len(data) > 1 else []


def last(data: Sequence[T]) -> Optional[T]:
    """
    Gets the last element of a sequence.

    Args:
        data (Sequence[T]): The input sequence.

    Returns:
        Optional[T]: The last element, or None if the sequence is empty.
    """
    return data[-1] if data else None


def initial(data: Sequence[T]) -> list[T]:
    """
    Gets all but the last element of a sequence.

    Args:
        data (Sequence[T]): The input sequence.

    Returns:
        list[T]: A new list containing all elements of data except the last.
                 Returns an empty list if data has 0 or 1 element.
    """
    return list(data[:-1]) if len(data) > 1 else []


def repeat_value(value: T, n: int) -> Iterable[T]:
    """
    Creates an iterable that repeats a given value n times.
    """
    if n < 0:
        raise ValueError("Number of repetitions 'n' must be non-negative.")
    if n == 0:
        return []
    return [value] * n
