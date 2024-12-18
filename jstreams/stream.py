from typing import Callable, Iterable, Any, Optional, TypeVar, Generic, cast, Union

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")


def isEmptyOrNone(obj: Union[list[Any], dict[Any, Any], str, None, Any]) -> bool:
    if obj is None:
        return True
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


class Stream(Generic[T]):
    __slots__ = ("__arg",)

    def __init__(self, arg: Iterable[T]) -> None:
        self.__arg = arg

    @staticmethod
    def of(arg: Iterable[T]) -> "Stream[T]":
        return Stream(arg)

    def map(self, mapper: Callable[[T], V]) -> "Stream[V]":
        return Stream(mapIt(self.__arg, mapper))

    def flatMap(self, mapper: Callable[[T], Iterable[V]]) -> "Stream[V]":
        return Stream(flatMap(self.__arg, mapper))

    def first(self) -> Optional[T]:
        return findFirst(self.__arg, lambda e: True)

    def findFirst(self, predicate: Callable[[T], bool]) -> Opt[T]:
        return Opt(findFirst(self.__arg, predicate))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        return Stream(matching(self.__arg, predicate))

    def cast(self, castTo: type[V]) -> "Stream[V]":
        return self.map(lambda e: cast(castTo, e))  # type: ignore[valid-type]

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

    def each(self, action: Callable[[T], Any]) -> None:
        each(self.__arg, action)

    def ofType(self, theType: type[V]) -> "Stream[V]":
        return self.filter(ClassOps(theType).instanceOf).cast(theType)

    def skip(self, count: int) -> "Stream[T]":
        return Stream(list(self.__arg)[count:])

    def limit(self, count: int) -> "Stream[T]":
        return Stream(list(self.__arg)[:count])

    def takeWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        return Stream(takeWhile(self.__arg, predicate))

    def dropWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        return Stream(dropWhile(self.__arg, predicate))

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
        elSet: list[T] = []
        for el in self.__arg:
            if el not in elSet:
                elSet.append(el)
        return Stream(elSet)

    def concat(self, newStream: "Stream[T]") -> "Stream[T]":
        return Stream([*self.toList(), *newStream.toList()])


def stream(it: Iterable[T]) -> Stream[T]:
    return Stream(it)


def optional(val: Optional[T]) -> Opt[T]:
    return Opt(val)
