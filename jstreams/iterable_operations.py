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
