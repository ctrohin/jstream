from typing import Callable, Iterable, Optional, TypeVar, Union

from jstreams.predicate import Predicate, predicate_of
from jstreams.reducer import Reducer, reducer_of


T = TypeVar("T")


def find_first(
    target: Optional[Iterable[T]], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> Optional[T]:
    """
    Retrieves the first element of the given iterable that matches the given predicate

    Args:
        target (Optional[Iterable[T]]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Optional[T]: The first matching element, or None if no element matches the predicate
    """
    if target is None:
        return None

    for el in target:
        if predicate_of(predicate).apply(el):
            return el
    return None


def find_last(
    target: Optional[Iterable[T]], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> Optional[T]:
    """
    Retrieves the last element of the given iterable that matches the given predicate.
    Note: This function will iterate through the entire iterable.

    Args:
        target (Optional[Iterable[T]]): The target iterable.
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate.

    Returns:
        Optional[T]: The last matching element, or None if no element matches the predicate.
    """
    if target is None:
        return None

    last_match: Optional[T] = None
    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
            last_match = el
    return last_match


def matching(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns all elements of the target iterable that match the given predicate

    Args:
        target (Iterable[T]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        list[T]: The matching elements
    """
    ret: list[T] = []
    if target is None:
        return ret

    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
            ret.append(el)
    return ret


def take_while(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns the first batch of elements matching the predicate. Once an element
    that does not match the predicate is found, the function will return

    Args:
        target (Iterable[T]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
            ret.append(el)
        else:
            break
    return ret


def drop_while(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns the target iterable elements without the first elements that match the
    predicate. Once an element that does not match the predicate is found,
    the function will start adding the remaining elements to the result list

    Args:
        target (Iterable[T]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    index = 0

    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
            index += 1
        else:
            break
    return list(target)[index:]


def take_until(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns the first batch of elements until the predicate returns True.
    The element that satisfies the predicate IS included in the result.

    Args:
        target (Iterable[T]): The target iterable.
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate.

    Returns:
        list[T]: The result list including the element that matched the predicate.
    """
    ret: list[T] = []
    if target is None:
        return ret

    pred = predicate_of(predicate)
    for el in target:
        ret.append(el)  # Append the element first
        if pred.apply(el):  # Then check if the condition is met
            break  # Stop after including the element
    return ret


def drop_until(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns the target iterable elements starting from the first element that
    matches the predicate (inclusive). Elements before the first match are dropped.

    Args:
        target (Iterable[T]): The target iterable.
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate.

    Returns:
        list[T]: The result list starting from the first matching element.
                 Returns an empty list if the predicate never matches.
    """
    if target is None:
        return []

    index = 0
    found_match = False
    target_list = list(target)  # Convert once for slicing and indexing

    pred = predicate_of(predicate)
    for i, el in enumerate(target_list):
        if pred.apply(el):
            index = i  # Index of the first element matching the predicate
            found_match = True
            break  # Stop searching

    return target_list[index:] if found_match else []


def reduce(
    target: Iterable[T], reducer: Union[Reducer[T], Callable[[T, T], T]]
) -> Optional[T]:
    """
    Reduces an iterable to a single value. The reducer function takes two values and
    returns only one. This function can be used to find min or max from a stream of ints.

    Args:
        reducer (Union[Reducer[T], Callable[[T, T], T]]): The reducer

    Returns:
        Optional[T]: The resulting optional
    """

    if target is None:
        return None

    elem_list = list(target)
    if len(elem_list) == 0:
        return None

    result: T = elem_list[0]
    reducer_obj = reducer_of(reducer)
    for el in elem_list:
        result = reducer_obj.reduce(el, result)
    return result
