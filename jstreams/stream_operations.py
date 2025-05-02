from typing import Iterable, Optional, TypeVar

from jstreams.stream import Stream
from jstreams.utils import is_not_none, require_non_null


T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


def extract_list(val: dict[K, Optional[T]], keys: Iterable[K]) -> list[Optional[T]]:
    """
    Extract the elements for the given keys iteration from a dictionary.
    If an element does not exist in the dictionary, None will be returned for that key.

    Args:
        val (dict[K, Optional[T]]): The dictionary from where the values will be extracted
        keys (Iterable[K]): The keys

    Returns:
        list[Optional[T]]: The list of extracted values
    """
    return Stream(keys).map(val.get).to_list()


def extract_non_null_list(val: dict[K, Optional[T]], keys: Iterable[K]) -> list[T]:
    """
    Extract the elements for the given keys iteration from a dictionary.
    If an element does not exist in the dictionary, a value will not be returned for that key.

    Args:
        val (dict[K, Optional[T]]): The dictionary from where the values will be extracted
        keys (Iterable[K]): The keys

    Returns:
        list[Optional[T]]: The list of extracted values
    """
    return (
        Stream(keys)
        .map(val.get)
        .filter(is_not_none)
        .map(lambda e: require_non_null(e))
        .to_list()
    )


def not_null_elements(iterable: Iterable[Optional[T]]) -> Iterable[T]:
    """
    Returns an iterable with all elements that are not None of the given iterable.

    Args:
        iterable (Iterable[Optional[T]]): The given iterable

    Returns:
        Iterable[T]: The iterable sans the None elements
    """
    return (
        Stream(iterable)
        .filter(is_not_none)
        .map(lambda e: require_non_null(e))
        .to_list()
    )
