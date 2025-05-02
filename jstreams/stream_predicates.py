from typing import Any, Callable, Iterable, Optional, TypeVar, Union

from jstreams.predicate import Predicate, is_none, not_, predicate_of
from jstreams.stream import Stream


T = TypeVar("T")


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
