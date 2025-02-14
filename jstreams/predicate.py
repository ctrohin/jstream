import re
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
    Sized,
    TypeVar,
    Union,
    cast,
)

from jstreams.stream import Predicate, Stream, predicateOf

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
    return not_(isIn(it))


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


def notEquals(obj: Any) -> Callable[[Any], bool]:
    """
    Predicate to check if a value does not equal another value.
    Usage: notEquals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(notEquals(objectToCompareTo))

    Args:
        obj (Any): The object to compare to

    Returns:
        Callable[[Any], bool]: The predicate
    """
    return not_(equals(obj))


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


def isNotBlank(obj: Any) -> bool:
    """
    Checks if a value is not blank. Returns True in the following conditions:
    - obj is of type Sized and it's len greater than 0
    - if not of type Sized, object is not None

    Args:
        obj (Any): The object

    Returns:
        bool: True if is not blank, False otherwise
    """
    return not_(isBlank)(obj)


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


def contains(value: Any) -> Callable[[Optional[Union[str, Iterable[Any]]]], bool]:
    """
    Checks if the given value is contained in the call parameter
    Usage:
    contains("test")("This is the test string") # Returns True
    contains("other")("This is the test string") # Returns False
    contains(1)([1, 2, 3]) # Returns True
    contains(5)([1, 2, 3]) # Returns False
    Usage with Opt and Stream:
    Opt("This is a test string").map(contains("test")).get() # Returns True
    Stream(["test string", "other string"]).filter(contains("test")).toList() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (Any): The filter value

    Returns:
        Callable[[Optional[Union[str, Iterable[Any]]]], bool]: A predicate
    """

    def wrap(val: Optional[Union[str, Iterable[Any]]]) -> bool:
        return val is not None and value in val

    return wrap


def strContains(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the given value is contained in the call parameter
    Usage:
    strContains("test")("This is the test string") # Returns True
    strContains("other")("This is the test string") # Returns False
    Usage with Opt and Stream:
    Opt("This is a test string").map(strContains("test")).get() # Returns True
    Stream(["test string", "other string"]).filter(strContains("test")).toList() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (str): The filter value

    Returns:
        Callable[[Optional[str]], bool]: A predicate
    """

    return cast(Callable[[Optional[str]], bool], contains(value))


def strContainsIgnoreCase(value: str) -> Callable[[Optional[str]], bool]:
    """
    Same as strContains, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Callable[[Optional[str]], bool]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() in val.lower()

    return wrap


def strStartsWith(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the given call parameter starts with the given value
    Usage:
    strStartsWith("test")("test string") # Returns True
    strStartsWith("other")("test string") # Returns False
    Usage with Opt and Stream:
    Opt("test string").map(strStartsWith("test")).get() # Returns True
    Stream(["test string", "other string"]).filter(strStartsWith("test")).toList() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (str): The filter value

    Returns:
        Callable[[Optional[str]], bool]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.startswith(value)

    return wrap


def strStartsWithIgnoreCase(value: str) -> Callable[[Optional[str]], bool]:
    """
    Same as strStartsWith, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Callable[[Optional[str]], bool]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().startswith(value.lower())

    return wrap


def strEndsWith(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the given call parameter ends with the given value
    Usage:
    strEndsWith("string")("test string") # Returns True
    strEndsWith("other")("test string") # Returns False
    Usage with Opt and Stream:
    Opt("test string").map(strEndsWith("string")).get() # Returns True
    Stream(["test string", "other"]).filter(strEndsWith("string")).toList() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (str): The filter value

    Returns:
        Callable[[Optional[str]], bool]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.endswith(value)

    return wrap


def strEndsWithIgnoreCase(value: str) -> Callable[[Optional[str]], bool]:
    """
    Same as strEndsWith, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Callable[[Optional[str]], bool]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().endswith(value.lower())

    return wrap


def strMatches(value: str) -> Callable[[Optional[str]], bool]:
    def wrap(val: Optional[str]) -> bool:
        if val is None:
            return False
        match = re.match(value, val)
        return match is not None

    return wrap


def strNotMatches(value: str) -> Callable[[Optional[str]], bool]:
    return not_(strMatches(value))


def strLongerThan(value: int) -> Callable[[Optional[str]], bool]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) > value

    return wrap


def strShorterThan(value: int) -> Callable[[Optional[str]], bool]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) < value

    return wrap


def strLongerThanOrEqual(value: int) -> Callable[[Optional[str]], bool]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) >= value

    return wrap


def strShorterThanOrEqual(value: int) -> Callable[[Optional[str]], bool]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) <= value

    return wrap


def equalsIgnoreCase(value: str) -> Callable[[Optional[str]], bool]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() == val.lower()

    return wrap


def isEven(integer: Optional[int]) -> bool:
    return integer is not None and integer % 2 == 0


def isOdd(integer: Optional[int]) -> bool:
    return integer is not None and integer % 2 == 1


def isPositive(number: Optional[float]) -> bool:
    return number is not None and number > 0


def isNegative(number: Optional[float]) -> bool:
    return number is not None and number < 0


def isZero(number: Optional[float]) -> bool:
    return number is not None and number == 0


def isInt(number: Optional[float]) -> bool:
    return number is not None and number == int(number)


def isBeween(
    intervalStart: float, intervalEnd: float
) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > intervalStart and val < intervalEnd

    return wrap


def isBeweenClosed(
    intervalStart: float, intervalEnd: float
) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= intervalStart and val <= intervalEnd

    return wrap


def isInInterval(
    intervalStart: float, intervalEnd: float
) -> Callable[[Optional[float]], bool]:
    return isBeweenClosed(intervalStart, intervalEnd)


def isInOpenInterval(
    intervalStart: float, intervalEnd: float
) -> Callable[[Optional[float]], bool]:
    return isBeween(intervalStart, intervalEnd)


def isBeweenClosedStart(
    intervalStart: float, intervalEnd: float
) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= intervalStart and val < intervalEnd

    return wrap


def isBeweenClosedEnd(
    intervalStart: float, intervalEnd: float
) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > intervalStart and val <= intervalEnd

    return wrap


def isHigherThan(value: float) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > value

    return wrap


def isHigherThanOrEqual(value: float) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= value

    return wrap


def isLessThan(value: float) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val < value

    return wrap


def isLessThanOrEqual(value: float) -> Callable[[Optional[float]], bool]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val <= value

    return wrap


def Not(
    predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
) -> Callable[[Optional[T]], bool]:
    """
    Alias for not_

    Args:
        predicate (Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]]): The predicate

    Returns:
        Callable[[Optional[T]], bool]: The negated predicate
    """
    return not_(predicate)


def not_(
    predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
) -> Callable[[Optional[T]], bool]:
    """
    Negation predicate. Given a predicate, this predicate will map it to a negated value.
    Takes a predicate with optional as value, returning a negated predicate with an optional parameter as well.

    Usage: not_(isBlank)("test") # Returns True

    Args:
        predicate (Union[Predicate[T], Callable[[Optional[T]], bool]]): The predicate

    Returns:
        Callable[[Optional[T]], bool]: The negation predicate
    """

    def wrap(val: Optional[T]) -> bool:
        return not predicateOf(predicate).Apply(val)

    return wrap


def NotStrict(
    predicate: Union[Predicate[T], Callable[[T], bool]],
) -> Callable[[T], bool]:
    """
    Alias for notStrict

    Args:
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Callable[[T], bool]: The negated predicate
    """
    return notStrict(predicate)


def notStrict(
    predicate: Union[Predicate[T], Callable[[T], bool]],
) -> Callable[[T], bool]:
    """
    Negation predicate. Given a predicate, this predicate will map it to a negated value.
    Takes a predicate with a strict value, returning a negated predicate with an strict parameter as well.
    Very similar with not_, but will not break strict type checking when applied to strict typing predicates.

    Args:
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Callable[[Optional[T]], bool]: The negation predicate
    """

    def wrap(val: T) -> bool:
        return not predicateOf(predicate).Apply(val)

    return wrap


def allOf(
    predicates: list[Union[Predicate[T], Callable[[T], bool]]],
) -> Callable[[T], bool]:
    """
    Produces a predicate that checks the given value agains all predicates in the list

    Args:
        predicates (list[Union[Predicate[T], Callable[[T], bool]]]): The list of predicates

    Returns:
        Callable[[T], bool]: The resulting predicate
    """

    def wrap(val: T) -> bool:
        return Stream(predicates).map(predicateOf).allMatch(lambda p: p.Apply(val))

    return wrap


def anyOf(
    predicates: list[Union[Predicate[T], Callable[[T], bool]]],
) -> Callable[[T], bool]:
    """
    Produces a predicate that checks the given value agains any predicate in the list

    Args:
        predicates (list[Union[Predicate[T], Callable[[T], bool]]]): The list of predicates

    Returns:
        Callable[[T], bool]: The resulting predicate
    """

    def wrap(val: T) -> bool:
        return Stream(predicates).map(predicateOf).anyMatch(lambda p: p.Apply(val))

    return wrap


def noneOf(
    predicates: list[Union[Predicate[T], Callable[[T], bool]]],
) -> Callable[[T], bool]:
    """
    Produces a predicate that checks the given value agains all predicates in the list, resulting in a True
    response if the given value doesn't match any of them

    Args:
        predicates (list[Union[Predicate[T], Callable[[T], bool]]]): The list of predicates

    Returns:
        Callable[[T], bool]: The resulting predicate
    """

    def wrap(val: T) -> bool:
        return Stream(predicates).map(predicateOf).noneMatch(lambda p: p.Apply(val))

    return wrap


def hasKey(key: Any) -> Callable[[Optional[Mapping[Any, Any]]], bool]:
    """
    Produces a predicate that checks that the given value is present in the argument mapping as a key.

    Args:
        key (Any): The key to be checked

    Returns:
        Callable[[Optional[Mapping[Any, Any]]], bool]: The resulting predicate
    """

    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and key in dct.keys()

    return wrap


def hasValue(value: Any) -> Callable[[Optional[Mapping[Any, Any]]], bool]:
    """
    Produces a predicate that checks that the given value is present in the argument mapping as a value.

    Args:
        value (Any): The value to be checked

    Returns:
        Callable[[Optional[Mapping[Any, Any]]], bool]: The resulting predicate
    """

    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and value in dct.values()

    return wrap
