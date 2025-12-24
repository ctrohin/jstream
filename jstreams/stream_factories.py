from typing import Generic, TypeVar
from collections.abc import Iterable, Iterator
from jstreams.stream import Stream
from jstreams.tuples import Triplet, Tuple4


T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")


class _TripletIterable(
    Generic[T, V, K], Iterator[Triplet[T, V, K]], Iterable[Triplet[T, V, K]]
):
    __slots__ = ("_it1", "_it2", "_it3", "_iter1", "_iter2", "_iter3")

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
        Stream[Triplet[T, V, K]]: The resulting triplet stream
    """
    return Stream(_TripletIterable(left, middle, right))


class _Tuple4Iterable(
    Generic[T1, T2, T3, T4],
    Iterator[Tuple4[T1, T2, T3, T4]],
    Iterable[Tuple4[T1, T2, T3, T4]],
):
    __slots__ = ("_it1", "_it2", "_it3", "_it4", "_iter1", "_iter2", "_iter3", "_iter4")

    def __init__(
        self, it1: Iterable[T1], it2: Iterable[T2], it3: Iterable[T3], it4: Iterable[T4]
    ) -> None:
        self._it1 = it1
        self._it2 = it2
        self._it3 = it3
        self._it4 = it4
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()
        self._iter3 = self._it3.__iter__()
        self._iter4 = self._it4.__iter__()

    def __iter__(self) -> Iterator[Tuple4[T1, T2, T3, T4]]:
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()
        self._iter3 = self._it3.__iter__()
        self._iter4 = self._it4.__iter__()
        return self

    def __next__(self) -> Tuple4[T1, T2, T3, T4]:
        return Tuple4(
            self._iter1.__next__(),
            self._iter2.__next__(),
            self._iter3.__next__(),
            self._iter4.__next__(),
        )


def tuple4_stream(
    first: Iterable[T1], second: Iterable[T2], third: Iterable[T3], fourth: Iterable[T4]
) -> Stream[Tuple4[T1, T2, T3, T4]]:
    """
    Create a tuple4 stream by zipping four iterables. The resulting stream will have the length
    of the shortest iterable.

    Args:
        first (Iterable[T]): The first iterable
        second (Iterable[V]): The second iterable
        third (Iterable[K]): The third iterable
        fourth (Iterable[K]): The fourth iterable

    Returns:
        Stream[Tuple4[T1, T2, T3, T4]]: The resulting tuple4 stream
    """
    return Stream(_Tuple4Iterable(first, second, third, fourth))
