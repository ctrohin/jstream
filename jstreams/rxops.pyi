import abc
from typing import Any, Callable, Generic, TypeVar

__all__ = [
    "Pipe",
    "Reduce",
    "Filter",
    "Map",
    "Take",
    "TakeWhile",
    "TakeUntil",
    "DropWhile",
    "DropUntil",
    "rxReduce",
    "rxFilter",
    "rxMap",
    "rxTake",
    "rxTakeWhile",
    "rxTakeUntil",
    "rxDropWhile",
    "rxDropUntil",
    "RxOperator",
    "BaseFilteringOperator",
    "BaseMappingOperator",
]

T = TypeVar("T")
V = TypeVar("V")

class RxOperator(abc.ABC, Generic[T, V]):
    def __init__(self) -> None: ...

class BaseFilteringOperator(RxOperator[T, T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None: ...
    def matches(self, val: T) -> bool: ...

class BaseMappingOperator(RxOperator[T, V]):
    def __init__(self, mapper: Callable[[T], V]) -> None: ...
    def transform(self, val: T) -> V: ...

class Reduce(BaseFilteringOperator[T]):
    def __init__(self, reducer: Callable[[T, T], T]) -> None: ...

def rxReduce(reducer: Callable[[T, T], T]) -> RxOperator[T, T]: ...

class Filter(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None: ...

def rxFilter(predicate: Callable[[T], bool]) -> RxOperator[T, T]: ...

class Map(BaseMappingOperator[T, V]):
    def __init__(self, mapper: Callable[[T], V]) -> None: ...

def rxMap(mapper: Callable[[T], V]) -> RxOperator[T, V]: ...

class Take(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None: ...

def rxTake(typ: type[T], count: int) -> RxOperator[T, T]: ...

class TakeWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None: ...

def rxTakeWhile(predicate: Callable[[T], bool]) -> RxOperator[T, T]: ...

class TakeUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None: ...

def rxTakeUntil(predicate: Callable[[T], bool]) -> RxOperator[T, T]: ...

class Drop(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None: ...

class DropWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None: ...

def rxDropWhile(predicate: Callable[[T], bool]) -> RxOperator[T, T]: ...

class DropUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None: ...

def rxDropUntil(predicate: Callable[[T], bool]) -> RxOperator[T, T]: ...

class Pipe(Generic[T, V]):
    def __init__(
        self, inputType: type[T], outputType: type[V], ops: list[RxOperator[Any, Any]]
    ) -> None: ...
    def apply(self, val: T) -> V | None: ...
