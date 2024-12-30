import abc
from abc import ABC
from typing import Any, Callable, Generic, Iterable, Iterator, TypeVar

T = TypeVar('T')
V = TypeVar('V')
K = TypeVar('K')
C = TypeVar('C')

def isEmptyOrNone(obj: list[Any] | dict[Any, Any] | str | None | Any | Iterable[Any]) -> bool: ...
def cmpToKey(mycmp: Callable[[C, C], int]) -> type: ...
def each(target: Iterable[T] | None, fn: Callable[[T], Any]) -> None: ...
def findFirst(target: Iterable[T] | None, matches: Callable[[T], bool]) -> T | None: ...
def mapIt(target: Iterable[T], mapper: Callable[[T], V]) -> list[V]: ...
def flatMap(target: Iterable[T], mapper: Callable[[T], Iterable[V]]) -> list[V]: ...
def matching(target: Iterable[T], matcher: Callable[[T], bool]) -> list[T]: ...
def takeWhile(target: Iterable[T], matcher: Callable[[T], bool]) -> list[T]: ...
def dropWhile(target: Iterable[T], matcher: Callable[[T], bool]) -> list[T]: ...
def reduce(target: Iterable[T], reducer: Callable[[T, T], T]) -> T | None: ...
def isNotNone(element: T | None) -> bool: ...
def dictUpdate(target: dict[K, V], key: K, value: V) -> None: ...
def sort(target: list[T], comparator: Callable[[T, T], int]) -> list[T]: ...

class Opt(Generic[T]):
    def __init__(self, val: T | None) -> None: ...
    def get(self) -> T: ...
    def getActual(self) -> T | None: ...
    def getOrElse(self, val: T) -> T: ...
    def getOrElseGet(self, supplier: Callable[[], T | None]) -> T | None: ...
    def isPresent(self) -> bool: ...
    def isEmpty(self) -> bool: ...
    def ifPresent(self, action: Callable[[T], Any]) -> None: ...
    def ifPresentWith(self, withVal: K, action: Callable[[T, K], Any]) -> None: ...
    def ifPresentOrElse(self, action: Callable[[T], Any], emptyAction: Callable[[], Any]) -> None: ...
    def ifPresentOrElseWith(self, withVal: K, action: Callable[[T, K], Any], emptyAction: Callable[[K], Any]) -> None: ...
    def filter(self, predicate: Callable[[T], bool]) -> Opt[T]: ...
    def filterWith(self, withVal: K, predicate: Callable[[T, K], bool]) -> Opt[T]: ...
    def map(self, mapper: Callable[[T], V]) -> Opt[V]: ...
    def mapWith(self, withVal: K, mapper: Callable[[T, K], V]) -> Opt[V]: ...
    def orElse(self, supplier: Callable[[], T]) -> Opt[T]: ...
    def orElseWith(self, withVal: K, supplier: Callable[[K], T]) -> Opt[T]: ...
    def stream(self) -> Stream[T]: ...
    def flatStream(self) -> Stream[T]: ...
    def orElseThrow(self) -> T: ...
    def orElseThrowFrom(self, exceptionSupplier: Callable[[], BaseException]) -> T: ...

class ClassOps:
    def __init__(self, classType: type) -> None: ...
    def instanceOf(self, obj: Any) -> bool: ...

class _GenericIterable(ABC, Iterator[T], Iterable[T], Generic[T], metaclass=abc.ABCMeta):
    def __init__(self, it: Iterable[T]) -> None: ...
    def __iter__(self) -> Iterator[T]: ...

class _FilterIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T], fn: Callable[[T], bool]) -> None: ...
    def __next__(self) -> T | None: ...

class _CastIterable(Iterator[T], Iterable[T], Generic[T]):
    def __init__(self, it: Iterable[V], typ: type[T]) -> None: ...
    def __iter__(self) -> Iterator[T]: ...
    def __next__(self) -> T | None: ...

class _SkipIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T], count: int) -> None: ...
    def __next__(self) -> T | None: ...

class _LimitIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T], count: int) -> None: ...
    def __next__(self) -> T | None: ...

class _TakeWhileIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T], fn: Callable[[T], bool]) -> None: ...
    def __next__(self) -> T | None: ...

class _DropWhileIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T], fn: Callable[[T], bool]) -> None: ...
    def __next__(self) -> T | None: ...

class _ConcatIterable(_GenericIterable[T]):
    def __init__(self, it1: Iterable[T], it2: Iterable[T]) -> None: ...
    def __next__(self) -> T | None: ...

class _DistinctIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T]) -> None: ...
    def __next__(self) -> T | None: ...

class _MapIterable(_GenericIterable[T]):
    def __init__(self, it: Iterable[T], mapper: Callable[[T], V]) -> None: ...
    def __next__(self) -> V | None: ...

class Stream(Generic[T]):
    def __init__(self, arg: Iterable[T]) -> None: ...
    @staticmethod
    def of(arg: Iterable[T]) -> Stream[T]: ...
    def map(self, mapper: Callable[[T], V]) -> Stream[V]: ...
    def flatMap(self, mapper: Callable[[T], Iterable[V]]) -> Stream[V]: ...
    def first(self) -> T | None: ...
    def findFirst(self, predicate: Callable[[T], bool]) -> Opt[T]: ...
    def filter(self, predicate: Callable[[T], bool]) -> Stream[T]: ...
    def cast(self, castTo: type[V]) -> Stream[V]: ...
    def anyMatch(self, predicate: Callable[[T], bool]) -> bool: ...
    def noneMatch(self, predicate: Callable[[T], bool]) -> bool: ...
    def allMatch(self, predicate: Callable[[T], bool]) -> bool: ...
    def isEmpty(self) -> bool: ...
    def isNotEmpty(self) -> bool: ...
    def collect(self) -> Iterable[T]: ...
    def toList(self) -> list[T]: ...
    def toSet(self) -> set[T]: ...
    def each(self, action: Callable[[T], Any]) -> None: ...
    def ofType(self, theType: type[V]) -> Stream[V]: ...
    def skip(self, count: int) -> Stream[T]: ...
    def limit(self, count: int) -> Stream[T]: ...
    def takeWhile(self, predicate: Callable[[T], bool]) -> Stream[T]: ...
    def dropWhile(self, predicate: Callable[[T], bool]) -> Stream[T]: ...
    def reduce(self, reducer: Callable[[T, T], T]) -> Opt[T]: ...
    def nonNull(self) -> Stream[T]: ...
    def sort(self, comparator: Callable[[T, T], int]) -> Stream[T]: ...
    def reverse(self) -> Stream[T]: ...
    def distinct(self) -> Stream[T]: ...
    def concat(self, newStream: Stream[T]) -> Stream[T]: ...

def stream(it: Iterable[T]) -> Stream[T]: ...
def optional(val: T | None) -> Opt[T]: ...
