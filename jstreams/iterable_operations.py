from typing import Optional, TypeVar
from collections.abc import Callable, Iterable
import functools

T = TypeVar("T")


def find_first(
    target: Optional[Iterable[T]], predicate: Callable[[T], bool]
) -> Optional[T]:
    """
    Retrieves the first element of the given iterable that matches the given predicate

    Args:
        target (Optional[Iterable[T]]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        Optional[T]: The first matching element, or None if no element matches the predicate
    """
    if target is None:
        return None

    for el in target:
        if predicate(el):
            return el
    return None


def find_last(
    target: Optional[Iterable[T]], predicate: Callable[[T], bool]
) -> Optional[T]:
    """
    Retrieves the last element of the given iterable that matches the given predicate.
    Note: This function will iterate through the entire iterable.

    Args:
        target (Optional[Iterable[T]]): The target iterable.
        predicate (Callable[[T], bool]): The predicate.

    Returns:
        Optional[T]: The last matching element, or None if no element matches the predicate.
    """
    if target is None:
        return None

    last_match: Optional[T] = None
    for el in target:
        if predicate(el):
            last_match = el
    return last_match


def matching(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns all elements of the target iterable that match the given predicate

    Args:
        target (Iterable[T]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        list[T]: The matching elements
    """
    if target is None:
        return []

    return [el for el in target if predicate(el)]


def reduce(target: Iterable[T], reducer: Callable[[T, T], T]) -> Optional[T]:
    """
    Reduces an iterable to a single value. The reducer function takes two values and
    returns only one. This function can be used to find min or max from a stream of ints.

    Args:
        reducer (Callable[[T, T], T]): The reducer

    Returns:
        Optional[T]: The resulting optional
    """
    if target is None:
        return None

    iterator = iter(target)
    try:
        initial_value = next(iterator)
    except StopIteration:
        # Iterable is empty
        return None

    # functools.reduce will apply the reducer to the rest of the iterator
    # starting with the initial_value.
    return functools.reduce(reducer, iterator, initial_value)


def any_match(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """
    Checks if any iterable object matches the given predicate

    Args:
        iterable (Iterable[T]): The iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        bool: True if any object matches, False otherwise
    """
    if iterable is None:
        return False
    return any(predicate(el) for el in iterable)


def none_match(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """
    Checks if none of the iterable objects matches the given predicate. This is the inverse of 'any_match`

    Args:
        iterable (Iterable[T]): The iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        bool: True if no object matches, False otherwise
    """
    if iterable is None:
        return False

    return not any_match(iterable, predicate)


def all_match(iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """
    Checks if all of the iterable objects matche the given predicate.

    Args:
        iterable (Iterable[T]): The iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        bool: True if all objects matche, False otherwise
    """
    if iterable is None:
        return False
    return all(predicate(el) for el in iterable)
