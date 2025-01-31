from typing import Any, Callable, Iterable, Optional, Sized, TypeVar

from jstreams.stream import Stream

T = TypeVar("T")

def isTrue(var: bool) -> bool:
    """
    Returns the same value. Meant to be used as a predicate for filtering

    Args:
        var (bool): The value

    Returns:
        bool: The same value
    """
    return var


def isFalse(var: bool) -> bool:
    """
    Returns the negated value

    Args:
        var (bool): The value

    Returns:
        bool: the negated value
    """
    return not var

def isNone(val: Any) -> bool:
    """
    Equivalent to val is None. Meant to be used as a predicate

    Args:
        val (Any): The value

    Returns:
        bool: True if None, False otherwise
    """
    return val is None


def isIn(it: Iterable[Optional[T]]) -> Callable[[Optional[T]], bool]:
    """
    Predicate to check if a value is contained in an iterable. 
    Usage: isIn(checkInThisList)(findThisItem)
    Usage with Opt: Opt(val).filter(isIn(myList))

    Args:
        it (Iterable[Optional[T]]): The iterable

    Returns:
        Callable[[Optional[T]], bool]: The predicate
    """
    def wrap(elem: Optional[T]) -> bool:
        return elem in it
    return wrap


def isNotIn(it: Iterable[Optional[T]]) -> Callable[[Optional[T]], bool]:
    """
    Predicate to check if a value is not contained in an iterable. 
    Usage: isNotIn(checkInThisList)(findThisItem)
    Usage with Opt: Opt(val).filter(isNotIn(myList))    

    Args:
        it (Iterable[Optional[T]]): The iterable

    Returns:
        Callable[[Optional[T]], bool]: The predicate
    """
    def wrap(elem: Optional[T]) -> bool:
        return elem not in it
    return wrap


def equals(obj: Any) -> Callable[[Any], bool]:
    """
    Predicate to check if a value equals another value.
    Usage: equals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(equals(objectToCompareTo))

    Args:
        obj (Any): The object to compare to

    Returns:
        Callable[[Any], bool]: The predicate
    """
    def wrap(other: Any) -> bool:
        return (obj is None and other is None) or (obj == other)
    return wrap

def isBlank(obj: Any) -> bool:
    """
    Checks if a value is blank. Returns True in the following conditions:
    - obj is None
    - obj is of type Sized and it's len is 0

    Args:
        obj (Any): The object

    Returns:
        bool: True if is blank, False otherwise
    """
    if obj is None:
        return True
    if isinstance(obj, Sized):
        return len(obj) == 0
    return False

def default(defaultVal: T) -> Callable[[Optional[T]], T]:
    """
    Default value predicate.
    Usage: default(defaultValue)(myValue)
    Usage with Opt: Opt(myValue).map(default(defaultValue))

    Args:
        defaultVal (T): The default value

    Returns:
        Callable[[Optional[T], T]]: The predicate
    """
    def wrap(val: Optional[T]) -> T:
        return defaultVal if val is None else val
    return wrap

def allNone(it: Iterable[Optional[T]]) -> bool:
    """
    Checks if all elements in an iterable are None

    Args:
        it (Iterable[Optional[T]]): The iterable

    Returns:
        bool: True if all values are None, False if at least one value is not None
    """
    return Stream(it).allMatch(lambda e: e is None)

def allNotNone(it: Iterable[Optional[T]]) -> bool:
    """
    Checks if all elements in an iterable are not None

    Args:
        it (Iterable[Optional[T]]): The iterable

    Returns:
        bool: True if all values differ from None, False if at least one None value is found
    """
    return Stream(it).allMatch(lambda e: e is not None)

__all__ = [
    "isTrue",
    "isFalse",
    "isNone",
    "isNotNone",
    "isIn",
    "isNotIn",
    "equals",
    "isBlank",
    "default",
    "allNone",
    "allNotNone",
]