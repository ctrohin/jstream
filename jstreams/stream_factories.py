from typing import Generic, Iterable, Iterator, TypeVar

from jstreams.stream import Stream
from jstreams.tuples import Triplet


T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


class _TripletIterable(
    Generic[T, V, K], Iterator[Triplet[T, V, K]], Iterable[Triplet[T, V, K]]
):
    __slots__ = ["_it1", "_it2", "_it3", "_iter1", "_iter2", "_iter3"]

    def __init__(self, it1: Iterable[T], it2: Iterable[V], it3: Iterable[K]) -> None:
        self._it1 = it1
        self._it2 = it2
        self._it3 = it3
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()
        self._iter3 = self._it3.__iter__()

    def __iter__(self) -> Iterator[Triplet[T, V, K]]:
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()
        self._iter3 = self._it3.__iter__()
        return self

    def __next__(self) -> Triplet[T, V, K]:
        return Triplet(
            self._iter1.__next__(), self._iter2.__next__(), self._iter3.__next__()
        )


def triplet_stream(
    left: Iterable[T], middle: Iterable[V], right: Iterable[K]
) -> Stream[Triplet[T, V, K]]:
    """
    Create a triplet stream by zipping three iterables. The resulting stream will have the length
    of the shortest iterable.

    Args:
        left (Iterable[T]): The left iterable
        middle (Iterable[V]): The middle iterable
        right (Iterable[K]): The right iterable

    Returns:
        Stream[Triplet[T, V, K]]: The resulting pair stream
    """
    return Stream(_TripletIterable(left, middle, right))
