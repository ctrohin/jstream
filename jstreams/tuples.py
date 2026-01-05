from typing import Any, Generic, TypeVar
from collections.abc import Callable
from jstreams.predicate import Predicate, predicate_of

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")


class BasePair(Generic[T, V]):
    __slots__ = ("__left", "__right")

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


class Pair(BasePair[T, V]):
    def unpack(self) -> tuple[T, V]:
        return (self.left(), self.right())


class Triplet(Generic[T, V, K], BasePair[T, K]):
    __slots__ = ("__middle",)

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

    def unpack(self) -> tuple[T, V, K]:
        return (self.left(), self.middle(), self.right())


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
    predicate_arg: Callable[[T], bool],
) -> Predicate[BasePair[Any, Any]]:
    """
    Produces a predicate that checks if the left value of a Pair/Triplet matches the given predicate

    Args:
        predicate_arg (Callable[[T], bool]): The left matching predicate

    Returns:
        Predicate[BasePair[T, V]]: The produced predicate
    """

    def wrap(pair_arg: BasePair[T, V]) -> bool:
        return predicate_of(predicate_arg)(pair_arg.left())

    return predicate_of(wrap)


def right_matches(
    predicate_arg: Callable[[V], bool],
) -> Predicate[BasePair[Any, Any]]:
    """
    Produces a predicate that checks if the right value of a Pair/Triplet matches the given predicate

    Args:
        predicate_arg (Callable[[V], bool]): The right matching predicate

    Returns:
        Predicate[BasePair[T, V]]: The produced predicate
    """

    def wrap(pair_arg: BasePair[T, V]) -> bool:
        return predicate_arg(pair_arg.right())

    return predicate_of(wrap)


def middle_matches(
    predicate_arg: Callable[[V], bool],
) -> Predicate[Triplet[Any, Any, Any]]:
    """
    Produces a predicate that checks if the middle value of a Triplet matches the given predicate

    Args:
        predicate_arg (Callable[[V], bool]): The middle matching predicate

    Returns:
        Predicate[Triplet[T, V, K]]: The produced predicate
    """

    def wrap(triplet_arg: Triplet[T, V, K]) -> bool:
        return predicate_arg(triplet_arg.middle())

    return predicate_of(wrap)


class Tuple2(Generic[T, V], Pair[T, V]):
    pass


class Tuple3(Generic[T, V, K], Triplet[T, V, K]):
    pass


class Tuple4(Generic[T1, T2, T3, T4]):
    __slots__ = ("__value1", "__value2", "__value3", "__value4")

    def __init__(self, value1: T1, value2: T2, value3: T3, value4: T4) -> None:
        self.__value1: T1 = value1
        self.__value2: T2 = value2
        self.__value3: T3 = value3
        self.__value4: T4 = value4

    def val1(self) -> T1:
        return self.__value1

    def val2(self) -> T2:
        return self.__value2

    def val3(self) -> T3:
        return self.__value3

    def val4(self) -> T4:
        return self.__value4

    def __eq__(self, value: Any) -> bool:
        return (
            isinstance(value, Tuple4)
            and value.val1() == self.val1()
            and value.val2() == self.val2()
            and value.val3() == self.val3()
            and value.val4() == self.val4()
        )

    def __hash__(self) -> int:
        return hash((self.__value1, self.__value2, self.__value3, self.__value4))

    def __str__(self) -> str:
        return f"val1={self.__value1}, val2={self.__value2}, val3={self.__value3}, val4={self.__value4}"

    def __repr__(self) -> str:
        return f"val1={self.__value1}, val2={self.__value2}, val3={self.__value3}, val4={self.__value4}"

    def unpack(self) -> tuple[T1, T2, T3, T4]:
        return (self.val1(), self.val2(), self.val3(), self.val4())


def val1_matches(
    predicate_arg: Callable[[T1], bool],
) -> Predicate[Tuple4[Any, Any, Any, Any]]:
    """
    Produces a predicate that checks if the first value of a Tuple4 matches the given predicate

    Args:
        predicate_arg (Callable[[T1], bool]): The first value matching predicate

    Returns:
        Predicate[Tuple4[Any, Any, Any, Any]]: The produced predicate
    """

    def wrap(quadruplet_arg: Tuple4[T1, T2, T3, T4]) -> bool:
        return predicate_arg(quadruplet_arg.val1())

    return predicate_of(wrap)


def val2_matches(
    predicate_arg: Callable[[T2], bool],
) -> Predicate[Tuple4[Any, Any, Any, Any]]:
    """
    Produces a predicate that checks if the second value of a Tuple4 matches the given predicate

    Args:
        predicate_arg (Callable[[T2], bool]): The second value matching predicate

    Returns:
        Predicate[Tuple4[Any, Any, Any, Any]]: The produced predicate
    """

    def wrap(quadruplet_arg: Tuple4[T1, T2, T3, T4]) -> bool:
        return predicate_arg(quadruplet_arg.val2())

    return predicate_of(wrap)


def val3_matches(
    predicate_arg: Callable[[T3], bool],
) -> Predicate[Tuple4[Any, Any, Any, Any]]:
    """
    Produces a predicate that checks if the third value of a Tuple4 matches the given predicate

    Args:
        predicate_arg (Callable[[T3], bool]): The third value matching predicate

    Returns:
        Predicate[Tuple4[Any, Any, Any, Any]]: The produced predicate
    """

    def wrap(quadruplet_arg: Tuple4[T1, T2, T3, T4]) -> bool:
        return predicate_arg(quadruplet_arg.val3())

    return predicate_of(wrap)


def val4_matches(
    predicate_arg: Callable[[T4], bool],
) -> Predicate[Tuple4[Any, Any, Any, Any]]:
    """
    Produces a predicate that checks if the fourth value of a Tuple4 matches the given predicate

    Args:
        predicate_arg (Callable[[T4], bool]): The fourth value matching predicate

    Returns:
        Predicate[Tuple4[Any, Any, Any, Any]]: The produced predicate
    """

    def wrap(quadruplet_arg: Tuple4[T1, T2, T3, T4]) -> bool:
        return predicate_arg(quadruplet_arg.val4())

    return predicate_of(wrap)


def tuple4(val1: T1, val2: T2, val3: T3, val4: T4) -> Tuple4[T1, T2, T3, T4]:
    """
    Returns a Tuple4 object for the given values
    """
    return Tuple4(val1, val2, val3, val4)


def tuple4_of(values: tuple[T1, T2, T3, T4]) -> Tuple4[T1, T2, T3, T4]:
    """
    Produces a Tuple4 from a tuple
    """
    val1, val2, val3, val4 = values
    return tuple4(val1, val2, val3, val4)
