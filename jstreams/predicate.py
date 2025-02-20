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


def isIn(it: Iterable[Any]) -> Predicate[Any]:
    """
    Predicate to check if a value is contained in an iterable.
    Usage: isIn(checkInThisList)(findThisItem)
    Usage with Opt: Opt(val).filter(isIn(myList))

    Args:
        it (Iterable[Any]): The iterable

    Returns:
        Predicate[Any]: The predicate
    """

    def wrap(elem: Any) -> bool:
        return elem in it

    return predicateOf(wrap)


def isNotIn(it: Iterable[Any]) -> Predicate[Any]:
    """
    Predicate to check if a value is not contained in an iterable.
    Usage: isNotIn(checkInThisList)(findThisItem)
    Usage with Opt: Opt(val).filter(isNotIn(myList))

    Args:
        it (Iterable[Any]): The iterable

    Returns:
        Predicate[Any]: The predicate
    """
    return not_(isIn(it))


def equals(obj: T) -> Predicate[T]:
    """
    Predicate to check if a value equals another value.
    Usage: equals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(equals(objectToCompareTo))

    Args:
        obj (T): The object to compare to

    Returns:
        Predicate[T]: The predicate
    """

    def wrap(other: T) -> bool:
        return (obj is None and other is None) or (obj == other)

    return predicateOf(wrap)


def notEquals(obj: Any) -> Predicate[Any]:
    """
    Predicate to check if a value does not equal another value.
    Usage: notEquals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(notEquals(objectToCompareTo))

    Args:
        obj (Any): The object to compare to

    Returns:
        Callable[[Any], bool]: The predicate
    """
    return predicateOf(not_(equals(obj)))


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


def contains(value: Any) -> Predicate[Optional[Union[str, Iterable[Any]]]]:
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
        Predicate[Optional[Union[str, Iterable[Any]]]]: A predicate
    """

    def wrap(val: Optional[Union[str, Iterable[Any]]]) -> bool:
        return val is not None and value in val

    return predicateOf(wrap)


def strContains(value: str) -> Predicate[Optional[str]]:
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
        Predicate[Optional[str]]: A predicate
    """

    return cast(Predicate[Optional[str]], contains(value))


def strContainsIgnoreCase(value: str) -> Predicate[Optional[str]]:
    """
    Same as strContains, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() in val.lower()

    return predicateOf(wrap)


def strStartsWith(value: str) -> Predicate[Optional[str]]:
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
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.startswith(value)

    return predicateOf(wrap)


def strStartsWithIgnoreCase(value: str) -> Predicate[Optional[str]]:
    """
    Same as strStartsWith, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().startswith(value.lower())

    return predicateOf(wrap)


def strEndsWith(value: str) -> Predicate[Optional[str]]:
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
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.endswith(value)

    return predicateOf(wrap)


def strEndsWithIgnoreCase(value: str) -> Predicate[Optional[str]]:
    """
    Same as strEndsWith, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().endswith(value.lower())

    return predicateOf(wrap)


def strMatches(value: str) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        if val is None:
            return False
        match = re.match(value, val)
        return match is not None

    return predicateOf(wrap)


def strNotMatches(value: str) -> Predicate[Optional[str]]:
    return not_(strMatches(value))


def strLongerThan(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) > value

    return predicateOf(wrap)


def strShorterThan(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) < value

    return predicateOf(wrap)


def strLongerThanOrEqual(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) >= value

    return predicateOf(wrap)


def strShorterThanOrEqual(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) <= value

    return predicateOf(wrap)


def equalsIgnoreCase(value: str) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() == val.lower()

    return predicateOf(wrap)


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


def isBeween(intervalStart: float, intervalEnd: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and intervalStart < val < intervalEnd

    return predicateOf(wrap)


def isBeweenClosed(
    intervalStart: float, intervalEnd: float
) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and intervalStart <= val <= intervalEnd

    return predicateOf(wrap)


def isInInterval(
    intervalStart: float, intervalEnd: float
) -> Predicate[Optional[float]]:
    return isBeweenClosed(intervalStart, intervalEnd)


def isInOpenInterval(
    intervalStart: float, intervalEnd: float
) -> Predicate[Optional[float]]:
    return isBeween(intervalStart, intervalEnd)


def isBeweenClosedStart(
    intervalStart: float, intervalEnd: float
) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and intervalStart <= val < intervalEnd

    return predicateOf(wrap)


def isBeweenClosedEnd(
    intervalStart: float, intervalEnd: float
) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and intervalStart < val <= intervalEnd

    return predicateOf(wrap)


def isHigherThan(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > value

    return predicateOf(wrap)


def isHigherThanOrEqual(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= value

    return predicateOf(wrap)


def isLessThan(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val < value

    return predicateOf(wrap)


def isLessThanOrEqual(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val <= value

    return predicateOf(wrap)


def Not(
    predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
) -> Predicate[Optional[T]]:
    """
    Alias for not_

    Args:
        predicate (Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]]): The predicate

    Returns:
        Predicate[Optional[T]]: The negated predicate
    """
    return not_(predicate)


def not_(
    predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
) -> Predicate[Optional[T]]:
    """
    Negation predicate. Given a predicate, this predicate will map it to a negated value.
    Takes a predicate with optional as value, returning a negated predicate with an optional parameter as well.

    Usage: not_(isBlank)("test") # Returns True

    Args:
        predicate (Union[Predicate[T], Callable[[Optional[T]], bool]]): The predicate

    Returns:
        Predicate[Optional[T]]: The negation predicate
    """

    def wrap(val: Optional[T]) -> bool:
        return not predicateOf(predicate).Apply(val)

    return predicateOf(wrap)


def NotStrict(
    predicate: Union[Predicate[T], Callable[[T], bool]],
) -> Predicate[T]:
    """
    Alias for notStrict

    Args:
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Predicate[T]: The negated predicate
    """
    return notStrict(predicate)


def notStrict(
    predicate: Union[Predicate[T], Callable[[T], bool]],
) -> Predicate[T]:
    """
    Negation predicate. Given a predicate, this predicate will map it to a negated value.
    Takes a predicate with a strict value, returning a negated predicate with an strict parameter as well.
    Very similar with not_, but will not break strict type checking when applied to strict typing predicates.

    Args:
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Predicate[T]: The negation predicate
    """

    def wrap(val: T) -> bool:
        return not predicateOf(predicate).Apply(val)

    return predicateOf(wrap)


def allOf(
    predicates: list[Union[Predicate[T], Callable[[T], bool]]],
) -> Predicate[T]:
    """
    Produces a predicate that checks the given value agains all predicates in the list

    Args:
        predicates (list[Union[Predicate[T], Callable[[T], bool]]]): The list of predicates

    Returns:
        Predicate[T]: The resulting predicate
    """

    def wrap(val: T) -> bool:
        return Stream(predicates).map(predicateOf).allMatch(lambda p: p.Apply(val))

    return predicateOf(wrap)


def anyOf(
    predicates: list[Union[Predicate[T], Callable[[T], bool]]],
) -> Predicate[T]:
    """
    Produces a predicate that checks the given value agains any predicate in the list

    Args:
        predicates (list[Union[Predicate[T], Callable[[T], bool]]]): The list of predicates

    Returns:
        Predicate[T]: The resulting predicate
    """

    def wrap(val: T) -> bool:
        return Stream(predicates).map(predicateOf).anyMatch(lambda p: p.Apply(val))

    return predicateOf(wrap)


def noneOf(
    predicates: list[Union[Predicate[T], Callable[[T], bool]]],
) -> Predicate[T]:
    """
    Produces a predicate that checks the given value agains all predicates in the list, resulting in a True
    response if the given value doesn't match any of them

    Args:
        predicates (list[Union[Predicate[T], Callable[[T], bool]]]): The list of predicates

    Returns:
        Predicate[T]: The resulting predicate
    """

    def wrap(val: T) -> bool:
        return Stream(predicates).map(predicateOf).noneMatch(lambda p: p.Apply(val))

    return predicateOf(wrap)


def hasKey(key: Any) -> Predicate[Optional[Mapping[Any, Any]]]:
    """
    Produces a predicate that checks that the given value is present in the argument mapping as a key.

    Args:
        key (Any): The key to be checked

    Returns:
        Predicate[Optional[Mapping[Any, Any]]]: The resulting predicate
    """

    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and key in dct.keys()

    return predicateOf(wrap)


def hasValue(value: Any) -> Predicate[Optional[Mapping[Any, Any]]]:
    """
    Produces a predicate that checks that the given value is present in the argument mapping as a value.

    Args:
        value (Any): The value to be checked

    Returns:
        Predicate[Optional[Mapping[Any, Any]]]: The resulting predicate
    """

    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and value in dct.values()

    return predicateOf(wrap)


def isKeyIn(mapping: Mapping[Any, Any]) -> Predicate[Any]:
    """
    Produces a predicate that checks that the given mapping contains the argument key.

    Args:
        mapping (Mapping[Any, Any]): The mapping to be checked

    Returns:
        Predicate[Any]: The resulting predicate
    """

    def wrap(key: Any) -> bool:
        return key is not None and key in mapping.keys()

    return predicateOf(wrap)


def isValueIn(mapping: Mapping[Any, Any]) -> Predicate[Any]:
    """
    Produces a predicate that checks that the given mapping contains the argument value.

    Args:
        mapping (Mapping[Any, Any]): The mapping to be checked

    Returns:
        Predicate[Any]: The resulting predicate
    """

    def wrap(value: Any) -> bool:
        return value is not None and value in mapping.values()

    return predicateOf(wrap)
