from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from jstreams.types import TReducer

T = TypeVar("T")


class Reducer(ABC, Generic[T]):
    @abstractmethod
    def reduce(self, a: T, b: T) -> T:
        """
        Reduce two values to a single one.

        Args:
            a (T): The first value
            b (T): The second value

        Returns:
            T: The reduced value
        """

    def __call__(self, a: T, b: T) -> T:
        return self.reduce(a, b)

    @staticmethod
    def of(reducer: TReducer[T]) -> "Reducer[T]":
        if isinstance(reducer, Reducer):
            return reducer
        return _WrapReducer(reducer)


class _WrapReducer(Reducer[T]):
    __slots__ = ("__reducer",)

    def __init__(self, reducer: TReducer[T]) -> None:
        self.__reducer = reducer

    def reduce(self, a: T, b: T) -> T:
        return self.__reducer(a, b)


def reducer_of(reducer: TReducer[T]) -> Reducer[T]:
    return Reducer.of(reducer)
