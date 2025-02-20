from typing import Any, Callable, Generic, TypeVar, Union

from jstreams.stream import Predicate, predicateOf

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


def leftMatches(
    predicateArg: Union[Predicate[T], Callable[[T], bool]],
) -> Predicate[Pair[Any, Any]]:
    """
    Produces a predicate that checks if the left value of a Pair/Triplet matches the given predicate

    Args:
        predicateArg (Union[Predicate[T], Callable[[T], bool]]): The left matching predicate

    Returns:
        Predicate[Pair[T, V]]: The produced predicate
    """

    def wrap(pairArg: Pair[T, V]) -> bool:
        return predicateOf(predicateArg)(pairArg.left())

    return predicateOf(wrap)


def rightMatches(
    predicateArg: Union[Predicate[V], Callable[[V], bool]],
) -> Predicate[Pair[Any, Any]]:
    """
    Produces a predicate that checks if the right value of a Pair/Triplet matches the given predicate

    Args:
        predicateArg (Union[Predicate[V], Callable[[V], bool]]): The right matching predicate

    Returns:
        Predicate[Pair[T, V]]: The produced predicate
    """

    def wrap(pairArg: Pair[T, V]) -> bool:
        return predicateOf(predicateArg)(pairArg.right())

    return predicateOf(wrap)


def middleMatches(
    predicateArg: Union[Predicate[V], Callable[[V], bool]],
) -> Predicate[Triplet[Any, Any, Any]]:
    """
    Produces a predicate that checks if the middle value of a Triplet matches the given predicate

    Args:
        predicateArg (Union[Predicate[V], Callable[[V], bool]]): The middle matching predicate

    Returns:
        Predicate[Triplet[T, V, K]]: The produced predicate
    """

    def wrap(tripletArg: Triplet[T, V, K]) -> bool:
        return predicateOf(predicateArg)(tripletArg.middle())

    return predicateOf(wrap)
