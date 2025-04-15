from typing import Any, Callable, Generic, Iterable, Iterator, TypeVar, Union

from jstreams.stream import Predicate, Stream, predicate_of

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


class Pair(Generic[T, V]):
    __slots__ = ["__left", "__right"]

    def __init__(self, left: T, right: V) -> None:
        """
        Pair constructor. The pair class is an object oriented replacement for a two value Python tuple.

        Args:
            left (T): The left value of the Pair
            right (V): The right value of the Pair
        """
        self.__left = left
        self.__right = right

    def left(self) -> T:
        return self.__left

    def right(self) -> V:
        return self.__right

    def __eq__(self, value: Any) -> bool:
        return (
            isinstance(value, Pair)
            and value.left() == self.left()
            and value.right() == self.right()
        )

    def __str__(self) -> str:
        return f"left={self.__left}, right={self.__right}"


class Triplet(Generic[T, V, K], Pair[T, K]):
    __slots__ = ["__middle"]

    def __init__(self, left: T, middle: V, right: K) -> None:
        """
        Triplet constructor. The triplet class is an object oriented replacement for a three value Python tuple.

        Args:
            left (T): The left value of the Triplet
            middle (V): The middle value of the Triplet
            right (K): The right value of the Triplet
        """
        super().__init__(left, right)
        self.__middle = middle

    def middle(self) -> V:
        return self.__middle

    def __eq__(self, value: Any) -> bool:
        return (
            isinstance(value, Triplet)
            and value.left() == self.left()
            and value.right() == self.right()
            and value.middle() == self.middle()
        )

    def __str__(self) -> str:
        return f"left={self.__left}, middle={self.__middle}, right={self.__right}"


def pair(left: T, right: V) -> Pair[T, V]:
    """
    Returns a Pair object for the given values

    Args:
        left (T): The left value of the Pair
        right (V): The right value of the Pair

    Returns:
        Pair[T, V]: The Pair
    """
    return Pair(left, right)


def triplet(left: T, middle: V, right: K) -> Triplet[T, V, K]:
    """
    Returns a Triplet object for the given values

    Args:
        left (T): The left value of the Triplet
        middle (V): The middle value of the Triplet
        right (K): The right value of the Triplet

    Returns:
        Triplet[T, V, K]: The Triplet
    """
    return Triplet(left, middle, right)


def pair_of(values: tuple[T, V]) -> Pair[T, V]:
    """
    Produces a pair from a tuple
    """
    t_val, v_val = values
    return pair(t_val, v_val)


def triplet_of(values: tuple[T, V, K]) -> Triplet[T, V, K]:
    """
    Produces a triplet from a tuple
    """
    t_val, v_val, k_val = values
    return triplet(t_val, v_val, k_val)


def left_matches(
    predicate_arg: Union[Predicate[T], Callable[[T], bool]],
) -> Predicate[Pair[Any, Any]]:
    """
    Produces a predicate that checks if the left value of a Pair/Triplet matches the given predicate

    Args:
        predicate_arg (Union[Predicate[T], Callable[[T], bool]]): The left matching predicate

    Returns:
        Predicate[Pair[T, V]]: The produced predicate
    """

    def wrap(pair_arg: Pair[T, V]) -> bool:
        return predicate_of(predicate_arg)(pair_arg.left())

    return predicate_of(wrap)


def right_matches(
    predicate_arg: Union[Predicate[V], Callable[[V], bool]],
) -> Predicate[Pair[Any, Any]]:
    """
    Produces a predicate that checks if the right value of a Pair/Triplet matches the given predicate

    Args:
        predicate_arg (Union[Predicate[V], Callable[[V], bool]]): The right matching predicate

    Returns:
        Predicate[Pair[T, V]]: The produced predicate
    """

    def wrap(pair_arg: Pair[T, V]) -> bool:
        return predicate_of(predicate_arg)(pair_arg.right())

    return predicate_of(wrap)


def middle_matches(
    predicate_arg: Union[Predicate[V], Callable[[V], bool]],
) -> Predicate[Triplet[Any, Any, Any]]:
    """
    Produces a predicate that checks if the middle value of a Triplet matches the given predicate

    Args:
        predicate_arg (Union[Predicate[V], Callable[[V], bool]]): The middle matching predicate

    Returns:
        Predicate[Triplet[T, V, K]]: The produced predicate
    """

    def wrap(triplet_arg: Triplet[T, V, K]) -> bool:
        return predicate_of(predicate_arg)(triplet_arg.middle())

    return predicate_of(wrap)


class _PairIterable(Generic[T, V], Iterator[Pair[T, V]], Iterable[Pair[T, V]]):
    __slots__ = ["_it1", "_it2", "_iter1", "_iter2"]

    def __init__(self, it1: Iterable[T], it2: Iterable[V]) -> None:
        self._it1 = it1
        self._it2 = it2
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()

    def __iter__(self) -> Iterator[Pair[T, V]]:
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()
        return self

    def __next__(self) -> Pair[T, V]:
        return Pair(self._iter1.__next__(), self._iter2.__next__())


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


def pair_stream(left: Iterable[T], right: Iterable[V]) -> Stream[Pair[T, V]]:
    """
    Create a pair stream by zipping two iterables. The resulting stream will have the length
    of the shortest iterable.

    Args:
        left (Iterable[T]): The left iterable
        right (Iterable[V]): The right iterable

    Returns:
        Stream[Pair[T, V]]: The resulting pair stream
    """
    return Stream(_PairIterable(left, right))


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
