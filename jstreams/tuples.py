from typing import Callable, Generic, TypeVar, Union

from jstreams.stream import Predicate, predicateOf

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


class Pair(Generic[T, V]):
    __slots__ = ["__left", "__right"]

    def __init__(self, left: T, right: V) -> None:
        self.__left = left
        self.__right = right

    def left(self) -> T:
        return self.__left

    def right(self) -> V:
        return self.__right


class Triplet(Generic[T, V, K], Pair[T, K]):
    __slots__ = ["__middle"]

    def __init__(self, left: T, middle: V, right: K) -> None:
        super().__init__(left, right)
        self.__middle = middle

    def middle(self) -> V:
        return self.__middle


def pair(left: T, right: V) -> Pair[T, V]:
    return Pair(left, right)


def triplet(left: T, middle: V, right: K) -> Triplet[T, V, K]:
    return Triplet(left, middle, right)


def leftMatches(
    predicate: Union[Predicate[T], Callable[[T], bool]],
) -> Predicate[Pair[T, V]]:
    def wrap(pair: Pair[T, V]) -> bool:
        return predicateOf(predicate)(pair.left())

    return predicateOf(wrap)


def rightMatches(
    predicate: Union[Predicate[V], Callable[[V], bool]],
) -> Predicate[Pair[T, V]]:
    def wrap(pair: Pair[T, V]) -> bool:
        return predicateOf(predicate)(pair.right())

    return predicateOf(wrap)


def middleMatches(
    predicate: Union[Predicate[V], Callable[[V], bool]],
) -> Predicate[Triplet[T, V, K]]:
    def wrap(triplet: Triplet[T, V, K]) -> bool:
        return predicateOf(predicate)(triplet.middle())

    return predicateOf(wrap)
