from typing import Callable, Iterable, Any, Iterator, Optional, TypeVar, Generic, cast, Union
from abc import ABC

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")


def isEmptyOrNone(obj: Union[list[Any], dict[Any, Any], str, None, Any, Iterable[Any]]) -> bool:
    if obj is None:
        return True
    if isinstance(obj, Iterable):
        count = 0
        for _ in obj:
            count += 1
        return count == 0
        
    return len(obj) == 0


def cmpToKey(mycmp: Callable[[C, C], int]) -> type:
    """Convert a cmp= function into a key= function"""

    class Key(Generic[C]):  # type: ignore[misc]
        __slots__ = ["obj"]

        def __init__(self, obj: C) -> None:
            self.obj = obj

        def __lt__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other: "Key") -> bool:
            return mycmp(self.obj, other.obj) >= 0

    return Key


def each(target: Optional[Iterable[T]], fn: Callable[[T], Any]) -> None:
    if target is None:
        return
    for el in target:
        fn(el)


def findFirst(
    target: Optional[Iterable[T]], matches: Callable[[T], bool]
) -> Optional[T]:
    if target is None:
        return None
    for el in target:
        if matches(el):
            return el
    return None


def mapIt(target: Iterable[T], mapper: Callable[[T], V]) -> list[V]:
    return [mapper(el) for el in target]


def flatMap(target: Iterable[T], mapper: Callable[[T], Iterable[V]]) -> list[V]:
    ret: list[V] = []
    for el in target:
        mapped = mapper(el)
        each(mapped, ret.append)
    return ret


def matching(target: Iterable[T], matcher: Callable[[T], bool]) -> list[T]:
    ret: list[T] = []
    for el in target:
        if matcher(el):
            ret.append(el)
    return ret


def takeWhile(target: Iterable[T], matcher: Callable[[T], bool]) -> list[T]:
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if matcher(el):
            ret.append(el)
        else:
            break
    return ret


def dropWhile(target: Iterable[T], matcher: Callable[[T], bool]) -> list[T]:
    ret: list[T] = []
    if target is None:
        return ret

    index = 0

    for el in target:
        if matcher(el):
            index += 1
        else:
            break
    return list(target)[index:]


def reduce(target: Iterable[T], reducer: Callable[[T, T], T]) -> Optional[T]:
    if target is None:
        return None
    elemList = list(target)
    if len(elemList) == 0:
        return None

    result: T = elemList[0]
    for el in elemList:
        result = reducer(el, result)
    return result


def isNotNone(element: Optional[T]) -> bool:
    return element is not None


def dictUpdate(target: dict[K, V], key: K, value: V) -> None:
    target[key] = value


def sort(target: list[T], comparator: Callable[[T, T], int]) -> list[T]:
    return sorted(target, key=cmpToKey(comparator))


class Opt(Generic[T]):
    __slots__ = ("__val",)

    def __init__(self, val: Optional[T]) -> None:
        self.__val = val

    def get(self) -> T:
        if self.__val is None:
            raise ValueError("Object is None")
        return self.__val

    def getActual(self) -> Optional[T]:
        return self.__val

    def getOrElse(self, val: T) -> T:
        return self.__val if self.__val is not None else val

    def getOrElseGet(self, supplier: Callable[[], Optional[T]]) -> Optional[T]:
        return self.__val if self.__val is not None else supplier()

    def isPresent(self) -> bool:
        return self.__val is not None

    def isEmpty(self) -> bool:
        return self.__val is None

    def ifPresent(self, action: Callable[[T], Any]) -> None:
        if self.__val is not None:
            action(self.__val)

    def ifPresentWith(self, withVal: K, action: Callable[[T, K], Any]) -> None:
        if self.__val is not None:
            action(self.__val, withVal)

    def ifPresentOrElse(
        self, action: Callable[[T], Any], emptyAction: Callable[[], Any]
    ) -> None:
        if self.__val is not None:
            action(self.__val)
        else:
            emptyAction()

    def ifPresentOrElseWith(
        self, withVal: K, action: Callable[[T, K], Any], emptyAction: Callable[[K], Any]
    ) -> None:
        if self.__val is not None:
            action(self.__val, withVal)
        else:
            emptyAction(withVal)

    def filter(self, predicate: Callable[[T], bool]) -> "Opt[T]":
        if self.__val is None:
            return self
        if predicate(self.__val):
            return self
        return Opt(None)

    def filterWith(self, withVal: K, predicate: Callable[[T, K], bool]) -> "Opt[T]":
        if self.__val is None:
            return self
        if predicate(self.__val, withVal):
            return self
        return Opt(None)

    def map(self, mapper: Callable[[T], V]) -> "Opt[V]":
        if self.__val is None:
            return Opt(None)
        return Opt(mapper(self.__val))

    def mapWith(self, withVal: K, mapper: Callable[[T, K], V]) -> "Opt[V]":
        if self.__val is None:
            return Opt(None)
        return Opt(mapper(self.__val, withVal))

    def orElse(self, supplier: Callable[[], T]) -> "Opt[T]":
        if self.isPresent():
            return self
        return Opt(supplier())

    def orElseWith(self, withVal: K, supplier: Callable[[K], T]) -> "Opt[T]":
        if self.isPresent():
            return self
        return Opt(supplier(withVal))

    def stream(self) -> "Stream[T]":
        if self.__val is not None:
            return Stream([self.__val])
        return Stream([])

    def flatStream(self) -> "Stream[T]":
        if self.__val is not None:
            if isinstance(self.__val, Iterable):
                return Stream(self.__val)
            return Stream([self.__val])
        return Stream([])

    def orElseThrow(self) -> T:
        if self.__val is not None:
            return self.__val
        raise ValueError("Object is None")

    def orElseThrowFrom(self, exceptionSupplier: Callable[[], BaseException]) -> T:
        if self.__val is not None:
            return self.__val
        raise exceptionSupplier()


class ClassOps:
    __slots__ = ("__classType",)

    def __init__(self, classType: type) -> None:
        self.__classType = classType

    def instanceOf(self, obj: Any) -> bool:
        return isinstance(obj, self.__classType)

class _GenericIterable(ABC, Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("_iterable", "_iterator")
    def __init__(self, it: Iterable[T]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()

    def _prepare(self) -> None:
        pass
    
    def __iter__(self) -> Iterator[T]:
        self._iterator = self._iterable.__iter__()
        self._prepare()
        return self

class _FilterIterable(_GenericIterable[T]):
    __slots__ = ("__filterFn",)
    def __init__(self, it: Iterable[T], fn: Callable[[T], bool]) -> None:
        super().__init__(it)
        self.__filterFn = fn
    
    def __next__(self) -> Optional[T]:
        while True:
            nextObj = self._iterator.__next__()
            if self.__filterFn(nextObj):
                return nextObj

class _CastIterable(Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("__iterable", "__iterator", "__type")
    def __init__(self, it: Iterable[V], typ: type[T]) -> None:
        self.__iterable = it
        self.__iterator = self.__iterable.__iter__()
        self.__type = typ

    def __iter__(self) -> Iterator[T]:
        self.__iterator = self.__iterable.__iter__()
        return self

    def __next__(self) -> Optional[T]:
        nextObj = self.__iterator.__next__()
        return cast(self.__type, nextObj) # type: ignore[valid-type]

class _SkipIterable(_GenericIterable[T]):
    __slots__ = ("__count",)
    def __init__(self, it: Iterable[T], count: int) -> None:
        super().__init__(it)
        self.__count = count

    def _prepare(self) -> None:
        try:
            count = 0
            while count < self.__count:
                self._iterator.__next__()
                count += 1
        except StopIteration:
            pass
        
    def __next__(self) -> Optional[T]:
        return self._iterator.__next__()

class _LimitIterable(_GenericIterable[T]):
    __slots__ = ("__count", "__currentCount")
    def __init__(self, it: Iterable[T], count: int) -> None:
        super().__init__(it)
        self.__count = count
        self.__currentCount = 0

    def _prepare(self) -> None:
        self.__currentCount = 0
        
    def __next__(self) -> Optional[T]:
        if  self.__currentCount >= self.__count:
            raise StopIteration()
        
        obj = self._iterator.__next__()
        self.__currentCount += 1
        return obj

class _TakeWhileIterable(_GenericIterable[T]):
    __slots__ = ("__fn", "__done")
    def __init__(self, it: Iterable[T], fn: Callable[[T], bool]) -> None:
        super().__init__(it)
        self.__done = False
        self.__fn = fn
        
    def _prepare(self) -> None:
        self.__done = False
        
    def __next__(self) -> Optional[T]:
        if self.__done:
            raise StopIteration()
        
        obj = self._iterator.__next__()
        if not self.__fn(obj):
            self.__done = True
            raise StopIteration()
        
        return obj

class _DropWhileIterable(_GenericIterable[T]):
    __slots__ = ("__fn", "__done")
    def __init__(self, it: Iterable[T], fn: Callable[[T], bool]) -> None:
        super().__init__(it)
        self.__done = False
        self.__fn = fn
        
    def _prepare(self) -> None:
        self.__done = False
        
    def __next__(self) -> Optional[T]:
        if self.__done:
            return self._iterator.__next__()
        while not self.__done:
            obj = self._iterator.__next__()
            if not self.__fn(obj):
                self.__done = True
                return obj

class _ConcatIterable(_GenericIterable[T]):
    __slots__ = ("__iterable2", "__iterator2", "__done")
    def __init__(self, it1: Iterable[T], it2: Iterable[T]) -> None:
        super().__init__(it1)
        self.__done = False
        self.__iterable2 = it2
        self.__iterator2 = self.__iterable2.__iter__()
        
    def _prepare(self) -> None:
        self.__done = False
        self.__iterator2 = self.__iterable2.__iter__()
        
    def __next__(self) -> Optional[T]:
        if self.__done:
            return self.__iterator2.__next__()
        else:
            try:
                return self._iterator.__next__()
            except StopIteration:
                self.__done = True
                return self.__next__()
            
class _DistinctIterable(_GenericIterable[T]):
    __slots__ = ("__set",)
    def __init__(self, it: Iterable[T]) -> None:
        super().__init__(it)
        self.__set = set()
        
    def _prepare(self) -> None:
        self.__set = set()

    def __next__(self) -> Optional[T]:
        obj = self._iterator.__next__()
        if obj not in self.__set:
            self.__set.add(obj)
            return obj
        return self.__next__()

class _MapIterable(_GenericIterable[T]):
    __slots__ = ("__fn",)
    def __init__(self, it: Iterable[T], mapper: Callable[[T], V]) -> None:
        super().__init__(it)
        self.__fn = mapper
        
    def __next__(self) -> Optional[V]:
        return self.__fn(self._iterator.__next__())

class Stream(Generic[T]):
    __slots__ = ("__arg",)

    def __init__(self, arg: Iterable[T]) -> None:
        self.__arg = arg

    @staticmethod
    def of(arg: Iterable[T]) -> "Stream[T]":
        return Stream(arg)

    def map(self, mapper: Callable[[T], V]) -> "Stream[V]":
        """
        Produces a new stream by mapping the stream elements using the given mapper function.
        Args:
            mapper (Callable[[T], V]): The mapper function

        Returns:
            Stream[V]: The result stream
        """
        return Stream(_MapIterable(self.__arg, mapper))

    def flatMap(self, mapper: Callable[[T], Iterable[V]]) -> "Stream[V]":
        return Stream(flatMap(self.__arg, mapper))

    def first(self) -> Optional[T]:
        return findFirst(self.__arg, lambda e: True)

    def findFirst(self, predicate: Callable[[T], bool]) -> Opt[T]:
        return Opt(findFirst(self.__arg, predicate))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        return Stream(_FilterIterable(self.__arg, predicate))

    def cast(self, castTo: type[V]) -> "Stream[V]":
        return Stream(_CastIterable(self.__arg, castTo))

    def anyMatch(self, predicate: Callable[[T], bool]) -> bool:
        return self.filter(predicate).isNotEmpty()

    def noneMatch(self, predicate: Callable[[T], bool]) -> bool:
        return self.filter(predicate).isEmpty()

    def allMatch(self, predicate: Callable[[T], bool]) -> bool:
        return len(self.filter(predicate).toList()) == len(list(self.__arg))

    def isEmpty(self) -> bool:
        return isEmptyOrNone(self.__arg)

    def isNotEmpty(self) -> bool:
        return not isEmptyOrNone(self.__arg)

    def collect(self) -> Iterable[T]:
        return self.__arg

    def toList(self) -> list[T]:
        return list(self.__arg)
    
    def toSet(self) -> set[T]:
        return set(self.__arg)

    def each(self, action: Callable[[T], Any]) -> None:
        each(self.__arg, action)

    def ofType(self, theType: type[V]) -> "Stream[V]":
        return self.filter(ClassOps(theType).instanceOf).cast(theType)

    def skip(self, count: int) -> "Stream[T]":
        return Stream(_SkipIterable(self.__arg, count))

    def limit(self, count: int) -> "Stream[T]":
        return Stream(_LimitIterable(self.__arg, count))

    def takeWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        return Stream(_TakeWhileIterable(self.__arg, predicate))

    def dropWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        return Stream(_DropWhileIterable(self.__arg, predicate))

    def reduce(self, reducer: Callable[[T, T], T]) -> Opt[T]:
        return Opt(reduce(self.__arg, reducer))

    def nonNull(self) -> "Stream[T]":
        return self.filter(isNotNone)

    def sort(self, comparator: Callable[[T, T], int]) -> "Stream[T]":
        return Stream(sort(list(self.__arg), comparator))

    def reverse(self) -> "Stream[T]":
        elems = list(self.__arg)
        elems.reverse()
        return Stream(elems)

    def distinct(self) -> "Stream[T]":
        if self.__arg is None:
            return self
        return Stream(_DistinctIterable(self.__arg))

    def concat(self, newStream: "Stream[T]") -> "Stream[T]":
        return Stream(_ConcatIterable(self.__arg, newStream.__arg))


def stream(it: Iterable[T]) -> Stream[T]:
    return Stream(it)


def optional(val: Optional[T]) -> Opt[T]:
    return Opt(val)
