from abc import ABC, abstractmethod
import re
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
    cast,
    Generic,
    overload,
)
from collections.abc import Callable, Iterable, Mapping
from collections.abc import Sized

from jstreams.utils import require_non_null

T = TypeVar("T")
K = TypeVar("K")


class Predicate(ABC, Generic[T]):
    @abstractmethod
    def apply(self, value: T) -> bool:
        """
        Apply a condition to a given value.

        Args:
            value (T): The value

        Returns:
            bool: True if the value matches, False otherwise
        """

    def or_(self, other: Callable[[T], bool]) -> "Predicate[T]":
        return Predicate.of(lambda v: self.apply(v) or predicate_of(other).apply(v))

    def and_(self, other: Callable[[T], bool]) -> "Predicate[T]":
        return Predicate.of(lambda v: self.apply(v) and predicate_of(other).apply(v))

    def __call__(self, value: T) -> bool:
        return self.apply(value)

    @staticmethod
    def of(
        predicate: Callable[[T], bool],
    ) -> "Predicate[T]":
        """
        If the value passed is a predicate, it is returned without any changes.
        If a function is passed, it will be wrapped into a Predicate object.

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Predicate[T]: The produced predicate
        """
        if isinstance(predicate, Predicate):
            return predicate
        return _WrapPredicate(predicate)


class PredicateWith(ABC, Generic[T, K]):
    @abstractmethod
    def apply(self, value: T, with_value: K) -> bool:
        """
        Apply a condition to two given values.

        Args:
            value (T): The value
            with_value (K): The second value

        Returns:
            bool: True if the values matche the predicate, False otherwise
        """

    def or_(self, other: "PredicateWith[T, K]") -> "PredicateWith[T, K]":
        return predicate_with_of(lambda v, k: self.apply(v, k) or other.apply(v, k))

    def and_(self, other: "PredicateWith[T, K]") -> "PredicateWith[T, K]":
        return predicate_with_of(lambda v, k: self.apply(v, k) and other.apply(v, k))

    def __call__(self, value: T, with_value: K) -> bool:
        return self.apply(value, with_value)

    @staticmethod
    def of(
        predicate: Callable[[T, K], bool],
    ) -> "PredicateWith[T, K]":
        """
        If the value passed is a predicate, it is returned without any changes.
        If a function is passed, it will be wrapped into a Predicate object.

        Args:
            predicate (Callable[[T, K], bool]): The predicate

        Returns:
            PredicateWith[T, K]: The produced predicate
        """
        if isinstance(predicate, PredicateWith):
            return predicate
        return _WrapPredicateWith(predicate)


class _WrapPredicate(Predicate[T]):
    __slots__ = ("__predicate_fn",)

    def __init__(self, fn: Callable[[T], bool]) -> None:
        self.__predicate_fn = fn

    def apply(self, value: T) -> bool:
        return self.__predicate_fn(value)


class _WrapPredicateWith(PredicateWith[T, K]):
    __slots__ = ("__predicate_fn",)

    def __init__(self, fn: Callable[[T, K], bool]) -> None:
        self.__predicate_fn = fn

    def apply(self, value: T, with_value: K) -> bool:
        return self.__predicate_fn(value, with_value)


def predicate_of(predicate: Callable[[T], bool]) -> Predicate[T]:
    """
    If the value passed is a predicate, it is returned without any changes.
    If a function is passed, it will be wrapped into a Predicate object.

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        Predicate[T]: The produced predicate
    """
    return Predicate.of(predicate)


def predicate_with_of(
    predicate: Callable[[T, K], bool],
) -> PredicateWith[T, K]:
    """
    If the value passed is a predicate, it is returned without any changes.
    If a function is passed, it will be wrapped into a Predicate object.

    Args:
        predicate (Callable[[T, K], bool]): The predicate

    Returns:
        PredicateWith[T, K]: The produced predicate
    """
    return PredicateWith.of(predicate)


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


def is_in(it: Iterable[Any]) -> Callable[[Any], bool]:
    """
    Predicate to check if a value is contained in an iterable.
    Usage: is_in(check_in_this_list)(find_this_item)
    Usage with Opt: Opt(val).filter(is_in(my_list))

    Args:
        it (Iterable[Any]): The iterable to check within.

    Returns:
        Callable[[Any], bool]: The predicate.
    """
    # Convert to set for O(1) average lookup if 'it' is a list or tuple
    # and its elements are hashable. This optimizes repeated lookups.

    if isinstance(it, (list, tuple)):
        try:
            lookup_set = set(it)
            return lambda elem: elem in lookup_set
        except TypeError:  # Fallback if elements are not hashable
            return lambda elem: elem in it

    return lambda elem: elem in it


def is_not_in(it: Iterable[Any]) -> Callable[[Any], bool]:
    """
    Predicate to check if a value is not contained in an iterable.
    Usage: is_not_in(check_in_this_list)(find_this_item)
    Usage with Opt: Opt(val).filter(is_not_in(my_list))

    Args:
        it (Iterable[Any]): The iterable to check within.

    Returns:
        Callable[[Any], bool]: The predicate.
    """
    # Reuses is_in and not_ for conciseness and correctness
    return not_(is_in(it))


def equals(obj: T) -> Callable[[T], bool]:
    """
    Predicate to check if a value equals another value. Handles None correctly.
    Usage: equals(object_to_compare_to)(my_object)
    Usage with Opt: Opt(my_object).filter(equals(object_to_compare_to))

    Args:
        obj (T): The object to compare to.

    Returns:
        Callable[[T], bool]: The predicate.
    """

    def wrap(other: T) -> bool:
        # Handles None comparison explicitly
        return (obj is None and other is None) or (obj == other)

    return wrap


def not_equals(obj: Any) -> Callable[[Any], bool]:
    """
    Predicate to check if a value does not equal another value.
    Usage: not_equals(objectToCompareTo)(myObject)
    Usage with Opt: Opt(myObject).filter(not_equals(objectToCompareTo))

    Args:
        obj (Any): The object to compare to.

    Returns:
        Callable[[Any], bool]: The predicate.
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

    require_non_null(default_val, "Default value cannot be None")

    def wrap(val: Optional[T]) -> T:
        return default_val if val is None else val

    return wrap


def contains(value: Any) -> Callable[[Optional[Union[str, Iterable[Any]]]], bool]:
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
        Callable[[Optional[Union[str, Iterable[Any]]]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    def wrap(val: Optional[Union[str, Iterable[Any]]]) -> bool:
        # Check for None before using 'in'
        return val is not None and value in val

    return wrap


def str_contains(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the given string value is contained in the call parameter string.
    Usage: str_contains("test")("This is the test string") # Returns True
    Usage with Opt: Opt("test string").filter(str_contains("test"))

    Args:
        value (str): The substring to check for.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")
    # Correctly uses casting for type specificity
    return cast(Callable[[Optional[str]], bool], contains(value))


def str_contains_ignore_case(value: str) -> Callable[[Optional[str]], bool]:
    """
    Case-insensitive version of str_contains.

    Args:
        value (str): The substring to check for.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    # .lower() is the standard way, creates temporary strings.
    def wrap(val: Optional[str]) -> bool:
        return val is not None and value.lower() in val.lower()

    return wrap


def str_starts_with(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string starts with the given value.
    Usage: str_starts_with("test")("test string") # Returns True

    Args:
        value (str): The prefix string.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    # Uses efficient built-in str.startswith
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.startswith(value)

    return wrap


def str_starts_with_ignore_case(value: str) -> Callable[[Optional[str]], bool]:
    """
    Case-insensitive version of str_starts_with.

    Args:
        value (str): The prefix string.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    # .lower() is standard.
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().startswith(value.lower())

    return wrap


def str_ends_with(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string ends with the given value.
    Usage: str_ends_with("string")("test string") # Returns True

    Args:
        value (str): The suffix string.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    # Uses efficient built-in str.endswith
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.endswith(value)

    return wrap


def str_ends_with_ignore_case(value: str) -> Callable[[Optional[str]], bool]:
    """
    Case-insensitive version of str_ends_with.

    Args:
        value (str): The suffix string.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    # .lower() is standard.
    def wrap(val: Optional[str]) -> bool:
        return val is not None and val.lower().endswith(value.lower())

    return wrap


def str_matches(pattern: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string matches the given regex pattern *at the beginning*.
    Uses `re.match`.
    Usage: str_matches(r"\\d+")("123 abc") # Returns True
    Usage: str_matches(r"\\d+")("abc 123") # Returns False

    Args:
        pattern (str): The regular expression pattern.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(pattern, "Pattern cannot be None")

    # Compile regex for potential minor optimization if used repeatedly,
    # but re.match caches patterns anyway. Keeping it simple is fine.
    # compiled_pattern = re.compile(pattern) # Alternative
    def wrap(val: Optional[str]) -> bool:
        if val is None:
            return False
        # match = compiled_pattern.match(val) # Alternative
        match = re.match(pattern, val)
        return match is not None

    return wrap


def str_not_matches(pattern: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string does *not* match the given regex pattern *at the beginning*.
    Uses `re.match`.

    Args:
        pattern (str): The regular expression pattern.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    # Reuses str_matches and not_
    require_non_null(pattern, "Pattern cannot be None")
    return not_(str_matches(pattern))


def str_longer_than(length: int) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string's length is greater than the specified value.

    Args:
        length (int): The minimum exclusive length.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    if length < 0:
        raise ValueError("Length cannot be negative")

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) > length

    return wrap


def str_shorter_than(length: int) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string's length is less than the specified value.

    Args:
        length (int): The maximum exclusive length.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    if length < 0:
        raise ValueError("Length cannot be negative")

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) < length

    return wrap


def str_longer_than_or_eq(length: int) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string's length is greater than or equal to the specified value.

    Args:
        length (int): The minimum inclusive length.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """

    if length < 0:
        raise ValueError("Length cannot be negative")

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) >= length

    return wrap


def str_shorter_than_or_eq(length: int) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string's length is less than or equal to the specified value.

    Args:
        length (int): The maximum inclusive length.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """

    if length < 0:
        raise ValueError("Length cannot be negative")

    def wrap(val: Optional[str]) -> bool:
        return val is not None and len(val) <= length

    return wrap


def equals_ignore_case(value: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the call parameter string equals the given value, ignoring case.

    Args:
        value (str): The string to compare against.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """
    require_non_null(value, "Value cannot be None")

    # .lower() is standard.
    def wrap(val: Optional[str]) -> bool:
        # Check both for None before comparing
        return val is not None and value.lower() == val.lower()

    return wrap


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


def is_between_closed(
    interval_start: float, interval_end: float
) -> Callable[[Optional[float]], bool]:
    """Checks if a number is between start and end inclusive (start <= number <= end)."""
    if interval_end < interval_start:
        raise ValueError("End cannot be less than start")

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start <= val <= interval_end

    return wrap


def is_in_interval(
    interval_start: float, interval_end: float
) -> Callable[[Optional[float]], bool]:
    """Checks if a number is between start and end inclusive (start <= number <= end)."""
    return is_between_closed(interval_start, interval_end)


def is_between(
    interval_start: float, interval_end: float
) -> Callable[[Optional[float]], bool]:
    """Checks if a number is strictly between start and end (start < number < end)."""
    if interval_end < interval_start:
        raise ValueError("End cannot be less than start")

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start < val < interval_end

    return wrap


def is_in_open_interval(
    interval_start: float, interval_end: float
) -> Callable[[Optional[float]], bool]:
    """Checks if a number is strictly between start and end (start < number < end)."""
    return is_between(interval_start, interval_end)


def is_between_closed_start(
    interval_start: float, interval_end: float
) -> Callable[[Optional[float]], bool]:
    """Checks if a number is between start (inclusive) and end (exclusive) (start <= number < end)."""

    if interval_end < interval_start:
        raise ValueError("End cannot be less than start")

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start <= val < interval_end

    return wrap


def is_between_closed_end(
    interval_start: float, interval_end: float
) -> Callable[[Optional[float]], bool]:
    """Checks if a number is between start (exclusive) and end (inclusive) (start < number <= end)."""

    if interval_end < interval_start:
        raise ValueError("End cannot be less than start")

    def wrap(val: Optional[float]) -> bool:
        return val is not None and interval_start < val <= interval_end

    return wrap


def is_higher_than(value: float) -> Callable[[Optional[float]], bool]:
    """Checks if a number is strictly greater than the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val > value

    return wrap


def is_higher_than_or_eq(value: float) -> Callable[[Optional[float]], bool]:
    """Checks if a number is greater than or equal to the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val >= value

    return wrap


def is_less_than(value: float) -> Callable[[Optional[float]], bool]:
    """Checks if a number is strictly less than the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val < value

    return wrap


def is_less_than_or_eq(value: float) -> Callable[[Optional[float]], bool]:
    """Checks if a number is less than or equal to the specified value."""

    def wrap(val: Optional[float]) -> bool:
        return val is not None and val <= value

    return wrap


# --- Higher-Order Predicates ---


def not_(
    predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
) -> Callable[[T], bool]:
    """
    Negates the result of the given predicate. Handles Optional input.
    Usage: not_(is_blank)("test") # Returns True

    Args:
        predicate: The predicate to negate.

    Returns:
        Predicate[Optional[T]]: The negated predicate.
    """

    return not_strict(predicate)


def not_strict(
    predicate: Callable[[T], bool],
) -> Callable[[T], bool]:
    """
    Negates the result of the given predicate. Requires non-Optional input.
    Useful for maintaining stricter type checking in pipelines.

    Args:
        predicate: The predicate to negate (must accept non-Optional T).

    Returns:
        Callable[[T], bool]: The negated predicate.
    """

    return lambda x: not predicate(x)


# --- Mapping Predicates ---


def has_key(key: Any) -> Callable[[Optional[Mapping[Any, Any]]], bool]:
    """
    Produces a predicate that checks if the argument mapping contains the given key.

    Args:
        key: The key to check for.

    Returns:
        Callable[[Optional[Mapping[Any, Any]]], bool]: The resulting predicate.
    """

    # Using 'key in mapping' is generally preferred over 'key in mapping.keys()'
    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and key in dct

    return wrap


def has_value(value: Any) -> Callable[[Optional[Mapping[Any, Any]]], bool]:
    """
    Produces a predicate that checks if the argument mapping contains the given value.
    Note: This requires iterating through values (O(n)).

    Args:
        value: The value to check for.

    Returns:
        Callable[[Optional[Mapping[Any, Any]]], bool]: The resulting predicate.
    """

    # 'value in mapping.values()' is the standard way
    def wrap(dct: Optional[Mapping[Any, Any]]) -> bool:
        return dct is not None and value in dct.values()

    return wrap


def is_key_in(mapping: Mapping[Any, Any]) -> Callable[[Any], bool]:
    """
    Produces a predicate that checks if the argument key is present in the given mapping.

    Args:
        mapping: The mapping to check within.

    Returns:
        Callable[[Any], bool]: The resulting predicate.
    """

    # Using 'key in mapping' is generally preferred
    def wrap(key: Any) -> bool:
        # Check key is not None if that's a requirement, depends on use case
        return key in mapping

    return wrap


def is_value_in(mapping: Mapping[Any, Any]) -> Callable[[Any], bool]:
    """
    Produces a predicate that checks if the argument value is present in the given mapping.
    Note: This requires iterating through values (O(n)).

    Args:
        mapping: The mapping to check within.

    Returns:
        Callable[[Any], bool]: The resulting predicate.
    """

    # Convert values to set for O(1) average lookup if possible
    # and elements are hashable. This optimizes repeated lookups.
    if isinstance(mapping, dict):  # Check for dict specifically as .values() is a view
        try:
            lookup_set = set(mapping.values())

            return lambda value: value in lookup_set

        except TypeError:  # Fallback if elements are not hashable
            return lambda value: value in mapping.values()

    return lambda value: value in mapping.values()


def is_truthy(val: Any) -> bool:
    """Checks if a value is considered True in a boolean context."""
    return bool(val)


def is_falsy(val: Any) -> bool:
    """Checks if a value is considered False in a boolean context."""
    return not bool(val)


def is_identity(other: Any) -> Callable[[Any], bool]:
    """Checks if a value is the same object as 'other' (using 'is')."""

    def wrap(val: Any) -> bool:
        return val is other

    return wrap


def has_length(length: int) -> Callable[[Optional[Sized]], bool]:
    """Checks if a Sized object has the specified length."""

    def wrap(val: Optional[Sized]) -> bool:
        # is_blank already checks for None
        return not is_blank(val) and len(val) == length  # type: ignore

    return wrap


def is_instance(cls: type) -> Callable[[Any], bool]:
    """Checks if a value is an instance of the given class."""

    def wrap(val: Any) -> bool:
        return isinstance(val, cls)

    return wrap


def str_fullmatch(pattern: str) -> Callable[[Optional[str]], bool]:
    """
    Checks if the *entire* string matches the given regex pattern (uses re.fullmatch).
    Complements `str_matches` which only checks from the beginning (`re.match`).

    Args:
        pattern (str): The regular expression pattern.

    Returns:
        Callable[[Optional[str]], bool]: A predicate.
    """

    require_non_null(pattern, "Pattern cannot be None")

    compiled_pattern = re.compile(pattern)

    def wrap(val: Optional[str]) -> bool:
        if val is None:
            return False
        match = compiled_pattern.fullmatch(val)
        return match is not None

    return wrap


def str_is_alpha(val: Optional[str]) -> bool:
    """Checks if a string is not None and all characters are alphabetic."""
    return val is not None and val.isalpha()


def str_is_digit(val: Optional[str]) -> bool:
    """Checks if a string is not None and all characters are digits."""
    return val is not None and val.isdigit()


def str_is_alnum(val: Optional[str]) -> bool:
    """Checks if a string is not None and all characters are alphanumeric."""
    return val is not None and val.isalnum()


def str_is_lower(val: Optional[str]) -> bool:
    """Checks if a string is not None and all cased characters are lowercase."""
    return val is not None and val.islower()


def str_is_upper(val: Optional[str]) -> bool:
    """Checks if a string is not None and all cased characters are uppercase."""
    return val is not None and val.isupper()


def str_is_space(val: Optional[str]) -> bool:
    """Checks if a string is not None and all characters are whitespace."""
    return val is not None and val.isspace()


def str_is_title(val: Optional[str]) -> bool:
    """Checks if a string is not None and is titlecased."""
    return val is not None and val.istitle()


def _extract_predicate_fn(predicate: Callable[[T], bool]) -> Callable[[T], bool]:
    if isinstance(predicate, Predicate):
        return predicate.apply
    return predicate


@overload
def and_(
    predicate1: Callable[[T], bool], predicate2: Callable[[T], bool]
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
    predicate15: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
    predicate15: Optional[Callable[[T], bool]] = None,
    predicate16: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


def and_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
    predicate15: Optional[Callable[[T], bool]] = None,
    predicate16: Optional[Callable[[T], bool]] = None,
    predicate17: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]:
    """
    Produces a predicate that returns True if all of the provided predicates returns True.

    Args:
        predicate1 (Callable[[T], bool]): Predicate
        predicate2 (Callable[[T], bool]): Predicate
        predicate3 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate4 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate5 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate6 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate7 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate8 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate9 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate10 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate11 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate12 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate13 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate14 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate15 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate16 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate17 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.

    Returns:
        Callable[[T], bool]: The AND predicate
    """

    predicates: list[Callable[[T], bool]] = filter(  # type: ignore[assignment]
        lambda p: p is not None,
        [
            predicate1,
            predicate2,
            predicate3,
            predicate4,
            predicate5,
            predicate6,
            predicate7,
            predicate8,
            predicate9,
            predicate10,
            predicate11,
            predicate12,
            predicate13,
            predicate14,
            predicate15,
            predicate16,
            predicate17,
        ],
    )
    return lambda el: all(pred(el) for pred in predicates)


@overload
def or_(
    predicate1: Callable[[T], bool], predicate2: Callable[[T], bool]
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
    predicate15: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


@overload
def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
    predicate15: Optional[Callable[[T], bool]] = None,
    predicate16: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]: ...


def or_(
    predicate1: Callable[[T], bool],
    predicate2: Callable[[T], bool],
    predicate3: Optional[Callable[[T], bool]] = None,
    predicate4: Optional[Callable[[T], bool]] = None,
    predicate5: Optional[Callable[[T], bool]] = None,
    predicate6: Optional[Callable[[T], bool]] = None,
    predicate7: Optional[Callable[[T], bool]] = None,
    predicate8: Optional[Callable[[T], bool]] = None,
    predicate9: Optional[Callable[[T], bool]] = None,
    predicate10: Optional[Callable[[T], bool]] = None,
    predicate11: Optional[Callable[[T], bool]] = None,
    predicate12: Optional[Callable[[T], bool]] = None,
    predicate13: Optional[Callable[[T], bool]] = None,
    predicate14: Optional[Callable[[T], bool]] = None,
    predicate15: Optional[Callable[[T], bool]] = None,
    predicate16: Optional[Callable[[T], bool]] = None,
    predicate17: Optional[Callable[[T], bool]] = None,
) -> Callable[[T], bool]:
    """
    Produces a predicate that returns True if all of the provided predicates returns True.

    Args:
        predicate1 (Callable[[T], bool]): Predicate
        predicate2 (Callable[[T], bool]): Predicate
        predicate3 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate4 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate5 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate6 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate7 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate8 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate9 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate10 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate11 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate12 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate13 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate14 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate15 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate16 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.
        predicate17 (Optional[Callable[[T], bool]], optional): Predicate. Defaults to None.

    Returns:
        Callable[[T], bool]: The AND predicate
    """

    predicates: list[Callable[[T], bool]] = filter(  # type: ignore[assignment]
        lambda p: p is not None,
        [
            predicate1,
            predicate2,
            predicate3,
            predicate4,
            predicate5,
            predicate6,
            predicate7,
            predicate8,
            predicate9,
            predicate10,
            predicate11,
            predicate12,
            predicate13,
            predicate14,
            predicate15,
            predicate16,
            predicate17,
        ],
    )
    return lambda el: any(pred(el) for pred in predicates)
