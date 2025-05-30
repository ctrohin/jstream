from typing import Callable, Iterable, Optional, TypeVar
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


def take_while(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns the first batch of elements matching the predicate. Once an element
    that does not match the predicate is found, the function will return

    Args:
        target (Iterable[T]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if predicate(el):
            ret.append(el)
        else:
            break
    return ret


def drop_while(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns the target iterable elements without the first elements that match the
    predicate. Once an element that does not match the predicate is found,
    the function will start adding the remaining elements to the result list

    Args:
        target (Iterable[T]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    index = 0
    start_adding = False
    for el in target:
        if start_adding:
            ret.append(el)
            continue
        if predicate(el):
            index += 1
        else:
            start_adding = True
            ret.append(el)

    return ret


def take_until(
    target: Iterable[T],
    predicate: Callable[[T], bool],
    include_stop_value: bool = False,
) -> list[T]:
    """
    Returns the first batch of elements until the predicate returns True.
    The element that satisfies the predicate IS included in the result.

    Args:
        target (Iterable[T]): The target iterable.
        predicate (Callable[[T], bool]): The predicate.

    Returns:
        list[T]: The result list including the element that matched the predicate.
    """
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if predicate(el):  # Then check if the condition is met
            if include_stop_value:
                ret.append(el)  # Append the if it needs to be included
            break  # Stop after including the element
        ret.append(el)
    return ret


def drop_until(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns the target iterable elements starting from the first element that
    matches the predicate (inclusive). Elements before the first match are dropped.

    Args:
        target (Iterable[T]): The target iterable.
        predicate (Callable[[T], bool]): The predicate.

    Returns:
        list[T]: The result list starting from the first matching element.
                 Returns an empty list if the predicate never matches.
    """
    if target is None:
        return []

    index = 0
    target_list = list(target)  # Convert once for slicing and indexing

    for el in target_list:
        if predicate(el):
            break  # Stop searching
        index += 1

    return target_list[index:]


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
