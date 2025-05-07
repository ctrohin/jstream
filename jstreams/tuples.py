from typing import Any, Callable, Generic, TypeVar, Union

from jstreams.predicate import Predicate, predicate_of

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

    def __hash__(self) -> int:
        return hash((self.__left, self.__right))

    def __str__(self) -> str:
        return f"left={self.__left}, right={self.__right}"

    def __repr__(self) -> str:
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

    def __hash__(self) -> int:
        return hash((self.__left, self.__middle, self.__right))

    def __str__(self) -> str:
        return f"left={self.__left}, middle={self.__middle}, right={self.__right}"

    def __repr__(self) -> str:
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
