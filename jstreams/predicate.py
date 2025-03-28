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

from jstreams.stream import Predicate, Stream, predicate_of

T = TypeVar("T")


def is_true(var: bool) -> bool:
    """
    Returns the same value. Meant to be used as a predicate for filtering

    Args:
        var (bool): The value

    Returns:
        bool: The same value
    """
    return var


def is_false(var: bool) -> bool:
    """
    Returns the negated value

    Args:
        var (bool): The value

    Returns:
        bool: the negated value
    """
    return not var


def is_none(val: Any) -> bool:
    """
    Equivalent to val is None. Meant to be used as a predicate

    Args:
        val (Any): The value

    Returns:
        bool: True if None, False otherwise
    """
    return val is None


def is_in(it: Iterable[Any]) -> Predicate[Any]:
    """
    Predicate to check if a value is contained in an iterable.
    Usage: is_in(check_in_this_list)(find_this_item)
    Usage with Opt: Opt(val).filter(is_in(my_list))

    Args:
        it (Iterable[Any]): The iterable

    Returns:
        Predicate[Any]: The predicate
    """

    def wrap(elem: Any) -> bool:
        return elem in it

    return predicate_of(wrap)


def is_not_in(it: Iterable[Any]) -> Predicate[Any]:
    """
    Predicate to check if a value is not contained in an iterable.
    Usage: is_not_in(check_in_this_list)(find_this_item)
    Usage with Opt: Opt(val).filter(is_not_in(my_list))

    Args:
        it (Iterable[Any]): The iterable

    Returns:
        Predicate[Any]: The predicate
    """
    return not_(is_in(it))


def equals(obj: T) -> Predicate[T]:
    """
    Predicate to check if a value equals another value.
    Usage: equals(object_to_compare_to)(my_object)
    Usage with Opt: Opt(my_object).filter(equals(object_to_compare_to))

    Args:
        obj (T): The object to compare to

    Returns:
        Predicate[T]: The predicate
    """

    def wrap(other: T) -> bool:
        return (obj is None and other is None) or (obj == other)

    return predicate_of(wrap)


def not_equals(obj: Any) -> Predicate[Any]:
    """
    Predicate to check if a value does not equal another value.
    Usage: not_equals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(not_equals(objectToCompareTo))

    Args:
        obj (Any): The object to compare to

    Returns:
        Callable[[Any], bool]: The predicate
    """
    return predicate_of(not_(equals(obj)))


def is_blank(obj: Any) -> bool:
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


def is_not_blank(obj: Any) -> bool:
    """
    Checks if a value is not blank. Returns True in the following conditions:
    - obj is of type Sized and it's len greater than 0
    - if not of type Sized, object is not None

    Args:
        obj (Any): The object

    Returns:
        bool: True if is not blank, False otherwise
    """
    return not_(is_blank)(obj)


def default(default_val: T) -> Callable[[Optional[T]], T]:
    """
    Default value predicate.
    Usage: default(defaultValue)(myValue)
    Usage with Opt: Opt(myValue).map(default(defaultValue))

    Args:
        default_val (T): The default value

    Returns:
        Callable[[Optional[T], T]]: The predicate
    """

    def wrap(val: Optional[T]) -> T:
        return default_val if val is None else val

    return wrap


def all_none(it: Iterable[Optional[T]]) -> bool:
    """
    Checks if all elements in an iterable are None

    Args:
        it (Iterable[Optional[T]]): The iterable

    Returns:
        bool: True if all values are None, False if at least one value is not None
    """
    return Stream(it).all_match(lambda e: e is None)


def all_not_none(it: Iterable[Optional[T]]) -> bool:
    """
    Checks if all elements in an iterable are not None

    Args:
        it (Iterable[Optional[T]]): The iterable

    Returns:
        bool: True if all values differ from None, False if at least one None value is found
    """
    return Stream(it).all_match(lambda e: e is not None)


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

    return predicate_of(wrap)


def str_contains(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the given value is contained in the call parameter
    Usage:
    str_contains("test")("This is the test string") # Returns True
    str_contains("other")("This is the test string") # Returns False
    Usage with Opt and Stream:
    Opt("This is a test string").map(str_contains("test")).get() # Returns True
    Stream(["test string", "other string"]).filter(str_contains("test")).to_list() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    return cast(Predicate[Optional[str]], contains(value))


def str_contains_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Same as str_contains, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() in val.lower()

    return predicate_of(wrap)


def str_starts_with(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the given call parameter starts with the given value
    Usage:
    str_starts_with("test")("test string") # Returns True
    str_starts_with("other")("test string") # Returns False
    Usage with Opt and Stream:
    Opt("test string").map(str_starts_with("test")).get() # Returns True
    Stream(["test string", "other string"]).filter(str_starts_with("test")).to_list() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.startswith(value)

    return predicate_of(wrap)


def str_starts_with_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Same as str_starts_with, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().startswith(value.lower())

    return predicate_of(wrap)


def str_ends_with(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the given call parameter ends with the given value
    Usage:
    str_ends_with("string")("test string") # Returns True
    str_ends_with("other")("test string") # Returns False
    Usage with Opt and Stream:
    Opt("test string").map(str_ends_with("string")).get() # Returns True
    Stream(["test string", "other"]).filter(str_ends_with("string")).to_list() # Results in ["test string"], filtering out the non matching elements

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.endswith(value)

    return predicate_of(wrap)


def str_ends_with_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Same as str_ends_with, but using case insensitive comparison.

    Args:
        value (str): The filter value

    Returns:
        Predicate[Optional[str]]: A predicate
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().endswith(value.lower())

    return predicate_of(wrap)


def str_matches(value: str) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        if val is None:
            return False
        match = re.match(value, val)
        return match is not None

    return predicate_of(wrap)


def str_not_matches(value: str) -> Predicate[Optional[str]]:
    return not_(str_matches(value))


def str_longer_than(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) > value

    return predicate_of(wrap)


def str_shorter_than(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) < value

    return predicate_of(wrap)


def str_longer_than_or_eq(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) >= value

    return predicate_of(wrap)


def str_shorter_than_or_eq(value: int) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) <= value

    return predicate_of(wrap)


def equals_ignore_case(value: str) -> Predicate[Optional[str]]:
    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() == val.lower()

    return predicate_of(wrap)


def is_even(integer: Optional[int]) -> bool:
    return integer is not None and integer % 2 == 0


def is_odd(integer: Optional[int]) -> bool:
    return integer is not None and integer % 2 == 1


def is_positive(number: Optional[float]) -> bool:
    return number is not None and number > 0


def is_negative(number: Optional[float]) -> bool:
    return number is not None and number < 0


def is_zero(number: Optional[float]) -> bool:
    return number is not None and number == 0


def is_int(number: Optional[float]) -> bool:
    return number is not None and number == int(number)


def is_beween(interval_start: float, interval_end: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start < val < interval_end

    return predicate_of(wrap)


def is_beween_closed(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start <= val <= interval_end

    return predicate_of(wrap)


def is_in_interval(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    return is_beween_closed(interval_start, interval_end)


def is_in_open_interval(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    return is_beween(interval_start, interval_end)


def is_beween_closed_start(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start <= val < interval_end

    return predicate_of(wrap)


def is_beween_closed_end(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start < val <= interval_end

    return predicate_of(wrap)


def is_higher_than(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > value

    return predicate_of(wrap)


def is_higher_than_or_eq(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= value

    return predicate_of(wrap)


def is_less_than(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val < value

    return predicate_of(wrap)


def is_less_than_or_eq(value: float) -> Predicate[Optional[float]]:
    def wrap(val: Optional[float]) -> bool:
        return val is not None and val <= value

    return predicate_of(wrap)


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
        return not predicate_of(predicate).apply(val)

    return predicate_of(wrap)


def not_strict(
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
        return not predicate_of(predicate).apply(val)

    return predicate_of(wrap)


def all_of(
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
        return Stream(predicates).map(predicate_of).all_match(lambda p: p.apply(val))

    return predicate_of(wrap)


def any_of(
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
        return Stream(predicates).map(predicate_of).any_match(lambda p: p.apply(val))

    return predicate_of(wrap)


def none_of(
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
        return Stream(predicates).map(predicate_of).none_match(lambda p: p.apply(val))

    return predicate_of(wrap)


def has_key(key: Any) -> Predicate[Optional[Mapping[Any, Any]]]:
    """
    Produces a predicate that checks that the given value is present in the argument mapping as a key.

    Args:
        key (Any): The key to be checked

    Returns:
        Predicate[Optional[Mapping[Any, Any]]]: The resulting predicate
    """

    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and key in dct.keys()

    return predicate_of(wrap)


def has_value(value: Any) -> Predicate[Optional[Mapping[Any, Any]]]:
    """
    Produces a predicate that checks that the given value is present in the argument mapping as a value.

    Args:
        value (Any): The value to be checked

    Returns:
        Predicate[Optional[Mapping[Any, Any]]]: The resulting predicate
    """

    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and value in dct.values()

    return predicate_of(wrap)


def is_key_in(mapping: Mapping[Any, Any]) -> Predicate[Any]:
    """
    Produces a predicate that checks that the given mapping contains the argument key.

    Args:
        mapping (Mapping[Any, Any]): The mapping to be checked

    Returns:
        Predicate[Any]: The resulting predicate
    """

    def wrap(key: Any) -> bool:
        return key is not None and key in mapping.keys()

    return predicate_of(wrap)


def is_value_in(mapping: Mapping[Any, Any]) -> Predicate[Any]:
    """
    Produces a predicate that checks that the given mapping contains the argument value.

    Args:
        mapping (Mapping[Any, Any]): The mapping to be checked

    Returns:
        Predicate[Any]: The resulting predicate
    """

    def wrap(value: Any) -> bool:
        return value is not None and value in mapping.values()

    return predicate_of(wrap)
