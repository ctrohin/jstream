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
    Returns the same value. Meant to be used as a predicate for filtering.

    Args:
        var (bool): The value

    Returns:
        bool: The same value
    """
    return var


def is_false(var: bool) -> bool:
    """
    Returns the negated value.

    Args:
        var (bool): The value

    Returns:
        bool: the negated value
    """
    return not var


def is_none(val: Any) -> bool:
    """
    Equivalent to val is None. Meant to be used as a predicate.

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
        it (Iterable[Any]): The iterable to check within.

    Returns:
        Predicate[Any]: The predicate.
    """

    # Efficiency depends on the type of 'it' (set/dict is O(1), list/tuple is O(n))
    def wrap(elem: Any) -> bool:
        return elem in it

    return predicate_of(wrap)


def is_not_in(it: Iterable[Any]) -> Predicate[Any]:
    """
    Predicate to check if a value is not contained in an iterable.
    Usage: is_not_in(check_in_this_list)(find_this_item)
    Usage with Opt: Opt(val).filter(is_not_in(my_list))

    Args:
        it (Iterable[Any]): The iterable to check within.

    Returns:
        Predicate[Any]: The predicate.
    """
    # Reuses is_in and not_ for conciseness and correctness
    return not_(is_in(it))


def equals(obj: T) -> Predicate[T]:
    """
    Predicate to check if a value equals another value. Handles None correctly.
    Usage: equals(object_to_compare_to)(my_object)
    Usage with Opt: Opt(my_object).filter(equals(object_to_compare_to))

    Args:
        obj (T): The object to compare to.

    Returns:
        Predicate[T]: The predicate.
    """

    def wrap(other: T) -> bool:
        # Handles None comparison explicitly
        return (obj is None and other is None) or (obj == other)

    return predicate_of(wrap)


def not_equals(obj: Any) -> Predicate[Any]:
    """
    Predicate to check if a value does not equal another value.
    Usage: not_equals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(not_equals(objectToCompareTo))

    Args:
        obj (Any): The object to compare to.

    Returns:
        Predicate[Any]: The predicate.
    """
    # Reuses equals and not_
    return not_(equals(obj))


def is_blank(obj: Any) -> bool:
    """
    Checks if a value is blank. Returns True in the following conditions:
    - obj is None
    - obj is of type Sized and its len is 0

    Args:
        obj (Any): The object

    Returns:
        bool: True if is blank, False otherwise
    """
    if obj is None:
        return True
    # isinstance check is necessary before len()
    if isinstance(obj, Sized):
        return len(obj) == 0
    # If not None and not Sized, it's not considered blank
    return False


def is_not_blank(obj: Any) -> bool:
    """
    Checks if a value is not blank. Returns True in the following conditions:
    - obj is of type Sized and its len is greater than 0
    - if not of type Sized, object is not None

    Args:
        obj (Any): The object

    Returns:
        bool: True if is not blank, False otherwise
    """
    # Reuses is_blank and not_
    return not_(is_blank)(obj)


def default(default_val: T) -> Callable[[Optional[T]], T]:
    """
    Default value provider. Returns the default value if the input is None.
    Usage: default(defaultValue)(myValue)
    Usage with Opt: Opt(myValue).map(default(defaultValue))

    Args:
        default_val (T): The default value.

    Returns:
        Callable[[Optional[T]], T]: A function that returns the input or the default.
    """

    def wrap(val: Optional[T]) -> T:
        return default_val if val is None else val

    return wrap


def all_none(it: Iterable[Optional[Any]]) -> bool:
    """
    Checks if all elements in an iterable are None.

    Args:
        it (Iterable[Optional[Any]]): The iterable.

    Returns:
        bool: True if all values are None, False if at least one value is not None.
    """
    # Assumes Stream().all_match is efficient (potentially short-circuiting)
    return Stream(it).all_match(is_none)


def all_not_none(it: Iterable[Optional[Any]]) -> bool:
    """
    Checks if all elements in an iterable are not None.

    Args:
        it (Iterable[Optional[Any]]): The iterable.

    Returns:
        bool: True if all values differ from None, False if at least one None value is found.
    """
    # Assumes Stream().all_match is efficient (potentially short-circuiting)
    # Using not_(is_none) might be slightly less direct than `lambda e: e is not None`
    # but maintains consistency with using predicate functions.
    return Stream(it).all_match(not_(is_none))


def contains(value: Any) -> Predicate[Optional[Union[str, Iterable[Any]]]]:
    """
    Checks if the given value is contained in the call parameter (string or iterable).
    Usage:
    contains("test")("This is the test string") # Returns True
    contains(1)([1, 2, 3]) # Returns True
    Usage with Opt and Stream:
    Opt("This is a test string").filter(contains("test")).get() # Returns True
    Stream([1, 2, 3]).filter(contains(1)).to_list() # Results in [1]

    Args:
        value (Any): The value to check for containment.

    Returns:
        Predicate[Optional[Union[str, Iterable[Any]]]]: A predicate.
    """

    def wrap(val: Optional[Union[str, Iterable[Any]]]) -> bool:
        # Check for None before using 'in'
        return val is not None and value in val

    return predicate_of(wrap)


def str_contains(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the given string value is contained in the call parameter string.
    Usage: str_contains("test")("This is the test string") # Returns True
    Usage with Opt: Opt("test string").filter(str_contains("test"))

    Args:
        value (str): The substring to check for.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """
    # Correctly uses casting for type specificity
    return cast(Predicate[Optional[str]], contains(value))


def str_contains_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Case-insensitive version of str_contains.

    Args:
        value (str): The substring to check for.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # .lower() is the standard way, creates temporary strings.
    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() in val.lower()

    return predicate_of(wrap)


def str_starts_with(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string starts with the given value.
    Usage: str_starts_with("test")("test string") # Returns True

    Args:
        value (str): The prefix string.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # Uses efficient built-in str.startswith
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.startswith(value)

    return predicate_of(wrap)


def str_starts_with_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Case-insensitive version of str_starts_with.

    Args:
        value (str): The prefix string.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # .lower() is standard.
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().startswith(value.lower())

    return predicate_of(wrap)


def str_ends_with(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string ends with the given value.
    Usage: str_ends_with("string")("test string") # Returns True

    Args:
        value (str): The suffix string.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # Uses efficient built-in str.endswith
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.endswith(value)

    return predicate_of(wrap)


def str_ends_with_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Case-insensitive version of str_ends_with.

    Args:
        value (str): The suffix string.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # .lower() is standard.
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().endswith(value.lower())

    return predicate_of(wrap)


def str_matches(pattern: str) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string matches the given regex pattern *at the beginning*.
    Uses `re.match`.
    Usage: str_matches(r"\\d+")("123 abc") # Returns True
    Usage: str_matches(r"\\d+")("abc 123") # Returns False

    Args:
        pattern (str): The regular expression pattern.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # Compile regex for potential minor optimization if used repeatedly,
    # but re.match caches patterns anyway. Keeping it simple is fine.
    # compiled_pattern = re.compile(pattern) # Alternative
    def wrap(val: Optional[str]) -> bool:
        if val is None:
            return False
        # match = compiled_pattern.match(val) # Alternative
        match = re.match(pattern, val)
        return match is not None

    return predicate_of(wrap)


def str_not_matches(pattern: str) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string does *not* match the given regex pattern *at the beginning*.
    Uses `re.match`.

    Args:
        pattern (str): The regular expression pattern.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """
    # Reuses str_matches and not_
    return not_(str_matches(pattern))


def str_longer_than(length: int) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string's length is greater than the specified value.

    Args:
        length (int): The minimum exclusive length.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) > length

    return predicate_of(wrap)


def str_shorter_than(length: int) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string's length is less than the specified value.

    Args:
        length (int): The maximum exclusive length.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) < length

    return predicate_of(wrap)


def str_longer_than_or_eq(length: int) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string's length is greater than or equal to the specified value.

    Args:
        length (int): The minimum inclusive length.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) >= length

    return predicate_of(wrap)


def str_shorter_than_or_eq(length: int) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string's length is less than or equal to the specified value.

    Args:
        length (int): The maximum inclusive length.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) <= length

    return predicate_of(wrap)


def equals_ignore_case(value: str) -> Predicate[Optional[str]]:
    """
    Checks if the call parameter string equals the given value, ignoring case.

    Args:
        value (str): The string to compare against.

    Returns:
        Predicate[Optional[str]]: A predicate.
    """

    # .lower() is standard.
    def wrap(val: Optional[str]) -> bool:
        # Check both for None before comparing
        return val is not None and value.lower() == val.lower()

    return predicate_of(wrap)


# --- Numeric Predicates ---


def is_even(integer: Optional[int]) -> bool:
    """Checks if an integer is even."""
    return integer is not None and integer % 2 == 0


def is_odd(integer: Optional[int]) -> bool:
    """Checks if an integer is odd."""
    return (
        integer is not None and integer % 2 != 0
    )  # Changed from == 1 for robustness with negative numbers


def is_positive(number: Optional[float]) -> bool:
    """Checks if a number is positive (> 0)."""
    return number is not None and number > 0


def is_negative(number: Optional[float]) -> bool:
    """Checks if a number is negative (< 0)."""
    return number is not None and number < 0


def is_zero(number: Optional[float]) -> bool:
    """Checks if a number is zero (== 0)."""
    # Consider floating point precision issues if exact zero is critical
    return number is not None and number == 0


def is_int(number: Optional[float]) -> bool:
    """Checks if a float represents a whole number."""
    # Handles None check and potential float precision
    return number is not None and number == int(number)


def is_beween(interval_start: float, interval_end: float) -> Predicate[Optional[float]]:
    """Checks if a number is strictly between start and end (start < number < end)."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start < val < interval_end

    return predicate_of(wrap)


def is_beween_closed(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    """Checks if a number is between start and end inclusive (start <= number <= end)."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start <= val <= interval_end

    return predicate_of(wrap)


# Alias for clarity
is_in_interval = is_beween_closed
is_in_open_interval = is_beween


def is_beween_closed_start(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    """Checks if a number is between start (inclusive) and end (exclusive) (start <= number < end)."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start <= val < interval_end

    return predicate_of(wrap)


def is_beween_closed_end(
    interval_start: float, interval_end: float
) -> Predicate[Optional[float]]:
    """Checks if a number is between start (exclusive) and end (inclusive) (start < number <= end)."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start < val <= interval_end

    return predicate_of(wrap)


def is_higher_than(value: float) -> Predicate[Optional[float]]:
    """Checks if a number is strictly greater than the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > value

    return predicate_of(wrap)


def is_higher_than_or_eq(value: float) -> Predicate[Optional[float]]:
    """Checks if a number is greater than or equal to the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= value

    return predicate_of(wrap)


def is_less_than(value: float) -> Predicate[Optional[float]]:
    """Checks if a number is strictly less than the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val < value

    return predicate_of(wrap)


def is_less_than_or_eq(value: float) -> Predicate[Optional[float]]:
    """Checks if a number is less than or equal to the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val <= value

    return predicate_of(wrap)


# --- Higher-Order Predicates ---


def not_(
    predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
) -> Predicate[Optional[T]]:
    """
    Negates the result of the given predicate. Handles Optional input.
    Usage: not_(is_blank)("test") # Returns True

    Args:
        predicate: The predicate to negate.

    Returns:
        Predicate[Optional[T]]: The negated predicate.
    """
    # Uses predicate_of to handle both Predicate objects and raw callables
    wrapped_predicate = predicate_of(predicate)

    def wrap(val: Optional[T]) -> bool:
        return not wrapped_predicate.apply(val)

    return predicate_of(wrap)


def not_strict(
    predicate: Union[Predicate[T], Callable[[T], bool]],
) -> Predicate[T]:
    """
    Negates the result of the given predicate. Requires non-Optional input.
    Useful for maintaining stricter type checking in pipelines.

    Args:
        predicate: The predicate to negate (must accept non-Optional T).

    Returns:
        Predicate[T]: The negated predicate.
    """
    wrapped_predicate = predicate_of(predicate)

    def wrap(val: T) -> bool:
        return not wrapped_predicate.apply(val)

    return predicate_of(wrap)


def all_of(
    predicates: Iterable[Union[Predicate[T], Callable[[T], bool]]],
) -> Predicate[T]:
    """
    Produces a predicate that returns True if the input value matches *all* provided predicates.
    Short-circuits on the first False.

    Args:
        predicates: An iterable of predicates to check against.

    Returns:
        Predicate[T]: The combined predicate.
    """
    # Convert to list to avoid consuming iterator multiple times if stream doesn't cache
    predicate_list = [predicate_of(p) for p in predicates]

    def wrap(val: T) -> bool:
        return Stream(predicate_list).all_match(lambda p: p.apply(val))

    return predicate_of(wrap)


def any_of(
    predicates: Iterable[Union[Predicate[T], Callable[[T], bool]]],
) -> Predicate[T]:
    """
    Produces a predicate that returns True if the input value matches *any* of the provided predicates.
    Short-circuits on the first True.

    Args:
        predicates: An iterable of predicates to check against.

    Returns:
        Predicate[T]: The combined predicate.
    """
    predicate_list = [predicate_of(p) for p in predicates]

    def wrap(val: T) -> bool:
        return Stream(predicate_list).any_match(lambda p: p.apply(val))

    return predicate_of(wrap)


def none_of(
    predicates: Iterable[Union[Predicate[T], Callable[[T], bool]]],
) -> Predicate[T]:
    """
    Produces a predicate that returns True if the input value matches *none* of the provided predicates.

    Args:
        predicates: An iterable of predicates to check against.

    Returns:
        Predicate[T]: The combined predicate.
    """
    predicate_list = [predicate_of(p) for p in predicates]

    def wrap(val: T) -> bool:
        return Stream(predicate_list).none_match(lambda p: p.apply(val))

    return predicate_of(wrap)


# --- Mapping Predicates ---


def has_key(key: Any) -> Predicate[Optional[Mapping[Any, Any]]]:
    """
    Produces a predicate that checks if the argument mapping contains the given key.

    Args:
        key: The key to check for.

    Returns:
        Predicate[Optional[Mapping[Any, Any]]]: The resulting predicate.
    """

    # Using 'key in mapping' is generally preferred over 'key in mapping.keys()'
    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and key in dct

    return predicate_of(wrap)


def has_value(value: Any) -> Predicate[Optional[Mapping[Any, Any]]]:
    """
    Produces a predicate that checks if the argument mapping contains the given value.
    Note: This requires iterating through values (O(n)).

    Args:
        value: The value to check for.

    Returns:
        Predicate[Optional[Mapping[Any, Any]]]: The resulting predicate.
    """

    # 'value in mapping.values()' is the standard way
    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and value in dct.values()

    return predicate_of(wrap)


def is_key_in(mapping: Mapping[Any, Any]) -> Predicate[Any]:
    """
    Produces a predicate that checks if the argument key is present in the given mapping.

    Args:
        mapping: The mapping to check within.

    Returns:
        Predicate[Any]: The resulting predicate.
    """

    # Using 'key in mapping' is generally preferred
    def wrap(key: Any) -> bool:
        # Check key is not None if that's a requirement, depends on use case
        return key in mapping

    return predicate_of(wrap)


def is_value_in(mapping: Mapping[Any, Any]) -> Predicate[Any]:
    """
    Produces a predicate that checks if the argument value is present in the given mapping.
    Note: This requires iterating through values (O(n)).

    Args:
        mapping: The mapping to check within.

    Returns:
        Predicate[Any]: The resulting predicate.
    """

    def wrap(value: Any) -> bool:
        return value in mapping.values()

    return predicate_of(wrap)
