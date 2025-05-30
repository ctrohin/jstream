from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Iterable, TypeVar

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
    def of(mapper: Callable[[T], V]) -> "Mapper[T, V]":
        """
        If the value passed is a mapper, it is returned without changes.
        If a function is passed, it will be wrapped into a Mapper object.

        Args:
            mapper (Callable[[T], V]): The mapper

        Returns:
            Mapper[T, V]: The produced mapper
        """
        if isinstance(mapper, Mapper):
            return mapper
        return _WrapMapper(mapper)

    @staticmethod
    def constant(value: K) -> "Mapper[Any, K]":
        """
        Returns a mapper that always returns the given constant value.

        Args:
            value (K): The constant value to be returned by the mapper.

        Returns:
            Mapper[Any, K]: A mapper that returns the constant value.
        """
        return _WrapMapper(lambda _: value)


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
        mapper: Callable[[T, K], V],
    ) -> "MapperWith[T, K, V]":
        """
        If the value passed is a mapper, it is returned without changes.
        If a function is passed, it will be wrapped into a Mapper object.


        Args:
            mapper (Callable[[T, K], V]): The mapper

        Returns:
            MapperWith[T, K, V]: The produced mapper
        """
        if isinstance(mapper, MapperWith):
            return mapper
        return _WrapMapperWith(mapper)


class _WrapMapper(Mapper[T, V]):
    __slots__ = ("__mapper",)

    def __init__(self, mapper: Callable[[T], V]) -> None:
        self.__mapper = mapper

    def map(self, value: T) -> V:
        return self.__mapper(value)

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, _WrapMapper):
            return False
        return self.__mapper == value.__mapper


class _WrapMapperWith(MapperWith[T, K, V]):
    __slots__ = ("__mapper",)

    def __init__(self, mapper: Callable[[T, K], V]) -> None:
        self.__mapper = mapper

    def map(self, value: T, with_value: K) -> V:
        return self.__mapper(value, with_value)

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, _WrapMapperWith):
            return False
        return self.__mapper == value.__mapper


def mapper_of(mapper: Callable[[T], V]) -> Mapper[T, V]:
    """
    If the value passed is a mapper, it is returned without changes.
    If a function is passed, it will be wrapped into a Mapper object.

    Args:
        mapper (Callable[[T], V]): The mapper

    Returns:
        Mapper[T, V]: The produced mapper
    """
    return Mapper.of(mapper)


def mapper_with_of(
    mapper: Callable[[T, K], V],
) -> MapperWith[T, K, V]:
    """
    If the value passed is a mapper, it is returned without changes.
    If a function is passed, it will be wrapped into a Mapper object.


    Args:
        mapper (Callable[[T, K], V]): The mapper

    Returns:
        MapperWith[T, K, V]: The produced mapper
    """
    return MapperWith.of(mapper)


def map_it(target: Iterable[T], mapper: Callable[[T], V]) -> list[V]:
    """
    Maps each element of an iterable to a new object produced by the given mapper

    Args:
        target (Iterable[T]): The target iterable
        mapper (Callable[[T], V]): The mapper

    Returns:
        list[V]: The mapped elements
    """
    if target is None:
        return []
    mapper_obj = Mapper.of(mapper)
    return [mapper_obj.map(el) for el in target]


def flat_map(
    target: Iterable[T],
    mapper: Callable[[T], Iterable[V]],
) -> list[V]:
    """
    Returns a flattened map. The mapper function is called for each element of the target
    iterable, then all elements are added to a result list.
    Ex: flat_map([1, 2], lambda x: [x, x + 1]) returns [1, 2, 2, 3]

    Args:
        target (Iterable[T]): The target iterable
        mapper (Callable[[T], Iterable[V]]): The mapper

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
