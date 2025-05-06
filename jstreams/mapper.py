from abc import ABC, abstractmethod
from typing import Callable, Generic, Iterable, TypeVar, Union

from jstreams.utils import each

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


class Mapper(ABC, Generic[T, V]):
    @abstractmethod
    def map(self, value: T) -> V:
        """
        Maps the given value, to a new value of maybe a different type.

        Args:
            value (T): The given value

        Returns:
            V: The produced value
        """

    def __call__(self, value: T) -> V:
        return self.map(value)

    @staticmethod
    def of(mapper: "Union[Mapper[T, V], Callable[[T], V]]") -> "Mapper[T, V]":
        """
        If the value passed is a mapper, it is returned without changes.
        If a function is passed, it will be wrapped into a Mapper object.

        Args:
            mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

        Returns:
            Mapper[T, V]: The produced mapper
        """
        if isinstance(mapper, Mapper):
            return mapper
        return _WrapMapper(mapper)


class MapperWith(ABC, Generic[T, K, V]):
    @abstractmethod
    def map(self, value: T, with_value: K) -> V:
        """
        Maps the given two values, to a new value.

        Args:
            value (T): The given value
            with_value (K): The scond value

        Returns:
            V: The produced value
        """

    def __call__(self, value: T, with_value: K) -> V:
        return self.map(value, with_value)

    @staticmethod
    def of(
        mapper: "Union[MapperWith[T, K, V], Callable[[T, K], V]]",
    ) -> "MapperWith[T, K, V]":
        """
        If the value passed is a mapper, it is returned without changes.
        If a function is passed, it will be wrapped into a Mapper object.


        Args:
            mapper (Union[MapperWith[T, K, V], Callable[[T, K], V]]): The mapper

        Returns:
            MapperWith[T, K, V]: The produced mapper
        """
        if isinstance(mapper, MapperWith):
            return mapper
        return _WrapMapperWith(mapper)


class _WrapMapper(Mapper[T, V]):
    __slots__ = ["__mapper"]

    def __init__(self, mapper: Callable[[T], V]) -> None:
        self.__mapper = mapper

    def map(self, value: T) -> V:
        return self.__mapper(value)


class _WrapMapperWith(MapperWith[T, K, V]):
    __slots__ = ["__mapper"]

    def __init__(self, mapper: Callable[[T, K], V]) -> None:
        self.__mapper = mapper

    def map(self, value: T, withValue: K) -> V:
        return self.__mapper(value, withValue)


def mapper_of(mapper: Union[Mapper[T, V], Callable[[T], V]]) -> Mapper[T, V]:
    """
    If the value passed is a mapper, it is returned without changes.
    If a function is passed, it will be wrapped into a Mapper object.

    Args:
        mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

    Returns:
        Mapper[T, V]: The produced mapper
    """
    return Mapper.of(mapper)


def mapper_with_of(
    mapper: Union[MapperWith[T, K, V], Callable[[T, K], V]],
) -> MapperWith[T, K, V]:
    """
    If the value passed is a mapper, it is returned without changes.
    If a function is passed, it will be wrapped into a Mapper object.


    Args:
        mapper (Union[MapperWith[T, K, V], Callable[[T, K], V]]): The mapper

    Returns:
        MapperWith[T, K, V]: The produced mapper
    """
    return MapperWith.of(mapper)


def map_it(
    target: Iterable[T], mapper: Union[Mapper[T, V], Callable[[T], V]]
) -> list[V]:
    """
    Maps each element of an iterable to a new object produced by the given mapper

    Args:
        target (Iterable[T]): The target iterable
        mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

    Returns:
        list[V]: The mapped elements
    """
    if target is None:
        return []
    mapper_obj = Mapper.of(mapper)
    return [mapper_obj.map(el) for el in target]


def flat_map(
    target: Iterable[T],
    mapper: Union[Mapper[T, Iterable[V]], Callable[[T], Iterable[V]]],
) -> list[V]:
    """
    Returns a flattened map. The mapper function is called for each element of the target
    iterable, then all elements are added to a result list.
    Ex: flat_map([1, 2], lambda x: [x, x + 1]) returns [1, 2, 2, 3]

    Args:
        target (Iterable[T]): The target iterable
        mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

    Returns:
        list[V]: The resulting flattened map
    """
    ret: list[V] = []
    if target is None:
        return ret

    mapper_obj = Mapper.of(mapper)

    for el in target:
        mapped = mapper_obj.map(el)
        each(mapped, ret.append)
    return ret
