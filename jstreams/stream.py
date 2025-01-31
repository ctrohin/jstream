from typing import (
    Callable,
    Iterable,
    Any,
    Iterator,
    Optional,
    Sized,
    TypeVar,
    Generic,
    cast,
    Union,
)
from abc import ABC

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")


def isEmptyOrNone(
    obj: Union[list[Any], dict[Any, Any], str, None, Any, Iterable[Any]],
) -> bool:
    if obj is None:
        return True

    if isinstance(obj, Iterable):
        for _ in obj:
            return False
        return True

    if isinstance(obj, Sized):
        return len(obj) == 0

    return False


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


def each(target: Optional[Iterable[T]], action: Callable[[T], Any]) -> None:
    """
    Executes an action on each element of the given iterable

    Args:
        target (Optional[Iterable[T]]): The target iterable
        action (Callable[[T], Any]): The action to be executed
    """
    if target is None:
        return

    for el in target:
        action(el)


def findFirst(
    target: Optional[Iterable[T]], predicate: Callable[[T], bool]
) -> Optional[T]:
    """
    Retrieves the first element of the given iterable that matches the given predicate

    Args:
        target (Optional[Iterable[T]]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        Optional[T]: The first matching element, or None if no element matches the predicate
    """
    if target is None:
        return None

    for el in target:
        if predicate(el):
            return el
    return None


def mapIt(target: Iterable[T], mapper: Callable[[T], V]) -> list[V]:
    """
    Maps each element of an iterable to a new object produced by the given mapper

    Args:
        target (Iterable[T]): The target iterable
        mapper (Callable[[T], V]): The mapper function

    Returns:
        list[V]: The mapped elements
    """
    if target is None:
        return []

    return [mapper(el) for el in target]


def flatMap(target: Iterable[T], mapper: Callable[[T], Iterable[V]]) -> list[V]:
    """
    Returns a flattened map. The mapper function is called for each element of the target
    iterable, then all elements are added to a result list.
    Ex: flatMap([1, 2], lambda x: [x, x + 1]) returns [1, 2, 2, 3]

    Args:
        target (Iterable[T]): The target iterable
        mapper (Callable[[T], Iterable[V]]): The mapper function

    Returns:
        list[V]: The resulting flattened map
    """
    ret: list[V] = []
    if target is None:
        return ret

    for el in target:
        mapped = mapper(el)
        each(mapped, ret.append)
    return ret


def matching(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns all elements of the target iterable that match the given predicate

    Args:
        target (Iterable[T]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        list[T]: The matching elements
    """
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if predicate(el):
            ret.append(el)
    return ret


def takeWhile(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns the first batch of elements matching the predicate. Once an element
    that does not match the predicate is found, the function will return

    Args:
        target (Iterable[T]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if predicate(el):
            ret.append(el)
        else:
            break
    return ret


def dropWhile(target: Iterable[T], predicate: Callable[[T], bool]) -> list[T]:
    """
    Returns the target iterable elements without the first elements that match the
    predicate. Once an element that does not match the predicate is found,
    the function will start adding the remaining elements to the result list

    Args:
        target (Iterable[T]): The target iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    index = 0

    for el in target:
        if predicate(el):
            index += 1
        else:
            break
    return list(target)[index:]


def reduce(target: Iterable[T], reducer: Callable[[T, T], T]) -> Optional[T]:
    """
    Reduces an iterable to a single value. The reducer function takes two values and
    returns only one. This function can be used to find min or max from a stream of ints.

    Args:
        reducer (Callable[[T, T], T]): The reducer function

    Returns:
        Optional[T]: The resulting optional
    """

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
    """
    Checks if the given element is not None. This function is meant to be used
    instead of lambdas for non null checks

    Args:
        element (Optional[T]): The given element

    Returns:
        bool: True if element is not None, False otherwise
    """
    return element is not None


def dictUpdate(target: dict[K, V], key: K, value: V) -> None:
    target[key] = value


def sort(target: list[T], comparator: Callable[[T, T], int]) -> list[T]:
    """
    Returns a list with the elements sorted according to the comparator function.
    CAUTION: This method will actually iterate the entire iterable, so if you're using
    infinite generators, calling this method will block the execution of the program.

    Args:
        comparator (Callable[[T, T], int]): The comparator function

    Returns:
        list[T]: The resulting list
    """

    return sorted(target, key=cmpToKey(comparator))


class Opt(Generic[T]):
    __slots__ = ("__val",)

    def __init__(self, val: Optional[T]) -> None:
        self.__val = val

    def get(self) -> T:
        """
        Returns the value of the Opt object if present, otherwise will raise a ValueError

        Raises:
            ValueError: Error raised when the value is None

        Returns:
            T: The value
        """
        if self.__val is None:
            raise ValueError("Object is None")
        return self.__val

    def getActual(self) -> Optional[T]:
        """
        Returns the actual value of the Opt without raising any errors

        Returns:
            Optional[T]: The value
        """
        return self.__val

    def getOrElse(self, val: T) -> T:
        """
        Returns the value of the Opt if present, otherwise return the given parameter as a fallback.
        This functiona should be used when the given fallback is a constant or it does not require
        heavy computation

        Args:
            val (T): The fallback value

        Returns:
            T: The return value
        """
        return self.__val if self.__val is not None else val

    def getOrElseOpt(self, val: Optional[T]) -> Optional[T]:
        """
        Returns the value of the Opt if present, otherwise return the given parameter as a fallback.
        This functiona should be used when the given fallback is a constant or it does not require
        heavy computation

        Args:
            val (Optional[T]): The optional fallback value

        Returns:
            T: The return value
        """
        return self.__val if self.__val is not None else val

    def getOrElseGetOpt(self, supplier: Callable[[], Optional[T]]) -> Optional[T]:
        """
        Returns the value of the Opt if present, otherwise it will call the supplier
        function and return that value. This function is useful when the fallback value
        is compute heavy and should only be called when the value of the Opt is None

        Args:
            supplier (Callable[[], T]): The mandatory return supplier

        Returns:
            Optional[T]: The resulting value
        """
        return self.__val if self.__val is not None else supplier()


    def getOrElseGet(self, supplier: Callable[[], T]) -> T:
        """
        Returns the value of the Opt if present, otherwise it will call the supplier
        function and return that value. This function is useful when the fallback value
        is compute heavy and should only be called when the value of the Opt is None

        Args:
            supplier (Callable[[], T]): The mandatory value supplier

        Returns:
            Optional[T]: _description_
        """
        return self.__val if self.__val is not None else supplier()

    def isPresent(self) -> bool:
        """
        Returns whether the Opt is present

        Returns:
            bool: True if the Opt has a non null value, False otherwise
        """
        return self.__val is not None

    def isEmpty(self) -> bool:
        """
        Returns whether the Opt is empty

        Returns:
            bool: True if the Opt value is None, False otherwise
        """
        return self.__val is None

    def ifPresent(self, action: Callable[[T], Any]) -> "Opt[T]":
        """
        Executes an action on the value of the Opt if the value is present

        Args:
            action (Callable[[T], Any]): The action
        Returns:
            Opt[T]: This optional
        """
        if self.__val is not None:
            action(self.__val)
        return self

    def ifPresentWith(self, withVal: K, action: Callable[[T, K], Any]) -> "Opt[T]":
        """
        Executes an action on the value of the Opt if the value is present, by providing
        the action an additional parameter

        Args:
            withVal (K): The additional parameter
            action (Callable[[T, K], Any]): The action
        Returns:
            Opt[T]: This optional
        """
        if self.__val is not None:
            action(self.__val, withVal)
        return self

    def ifNotPresent(self, action: Callable[[], Any]) -> "Opt[T]":
        """
        Executes an action on if the value is not present

        Args:
            action (Callable[[], Any]): The action
        Returns:
            Opt[T]: This optional
        """
        if self.__val is None:
            action()
        return self

    def ifNotPresentWith(self, withVal: K, action: Callable[[K], Any]) -> "Opt[T]":
        """
        Executes an action on if the value is not present, by providing
        the action an additional parameter

        Args:
            withVal (K): The additional parameter
            action (Callable[[K], Any]): The action
        Returns:
            Opt[T]: This optional
        """
        if self.__val is None:
            action(withVal)
        return self


    def ifPresentOrElse(
        self, action: Callable[[T], Any], emptyAction: Callable[[], Any]
    ) -> "Opt[T]":
        """
        Executes an action on the value of the Opt if the value is present, or executes
        the emptyAction if the Opt is empty

        Args:
            action (Callable[[T], Any]): The action to be executed when present
            emptyAction (Callable[[], Any]): The action to be executed when empty
        Returns:
            Opt[T]: This optional
        """
        if self.__val is not None:
            action(self.__val)
        else:
            emptyAction()
        return self

    def ifPresentOrElseWith(
        self, withVal: K, action: Callable[[T, K], Any], emptyAction: Callable[[K], Any]
    ) -> "Opt[T]":
        """
        Executes an action on the value of the Opt by providing the actions an additional parameter,
        if the value is present, or executes the emptyAction if the Opt is empty

        Args:
            withVal (K): The additional parameter
            action (Callable[[T, K], Any]): The action to be executed when present
            emptyAction (Callable[[K], Any]): The action to be executed when empty
        """
        if self.__val is not None:
            action(self.__val, withVal)
        else:
            emptyAction(withVal)
        return self

    def filter(self, predicate: Callable[[T], bool]) -> "Opt[T]":
        """
        Returns the filtered value of the Opt if it matches the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.__val is None:
            return self
        if predicate(self.__val):
            return self
        return Opt(None)

    def filterWith(self, withVal: K, predicate: Callable[[T, K], bool]) -> "Opt[T]":
        """
        Returns the filtered value of the Opt if it matches the given predicate, by
        providing the predicat with an additional value

        Args:
            withVal (K): the additional value
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.__val is None:
            return self
        if predicate(self.__val, withVal):
            return self
        return Opt(None)

    def map(self, mapper: Callable[[T], V]) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return Opt(None)
        return Opt(mapper(self.__val))

    def mapWith(self, withVal: K, mapper: Callable[[T, K], V]) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function with an additional parameter

        Args:
            withVal (K): The additional parameter
            mapper (Callable[[T, K], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return Opt(None)
        return Opt(mapper(self.__val, withVal))

    def orElse(self, supplier: Callable[[], T]) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result

        Args:
            supplier (Callable[[], T]): The fallback supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        return self.orElseOpt(supplier)

    def orElseOpt(self, supplier: Callable[[], Optional[T]]) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result

        Args:
            supplier (Callable[[], Optional[T]]): The fallback supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.isPresent():
            return self
        return Opt(supplier())

    def orElseWith(self, withVal: K, supplier: Callable[[K], T]) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result with
        the additional parameter

        Args:
            withVal (K): The additional parameter
            supplier (Callable[[K], T]): The supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        return self.orElseWithOpt(withVal, supplier)

    def orElseWithOpt(self, withVal: K, supplier: Callable[[K], Optional[T]]) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result with
        the additional parameter

        Args:
            withVal (K): The additional parameter
            supplier (Callable[[K], Optional[T]]): The supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.isPresent():
            return self
        return Opt(supplier(withVal))

    def stream(self) -> "Stream[T]":
        """
        Returns a Stream containing the current Opt value

        Returns:
            Stream[T]: The resulting Stream
        """
        if self.__val is not None:
            return Stream([self.__val])
        return Stream([])

    def flatStream(self) -> "Stream[T]":
        """
        Returns a Stream containing the current Opt value if the value
        is not an Iterable, or a Stream containing all the values in
        the Opt if the Opt contains an iterable

        Returns:
            Stream[T]: The resulting Stream
        """
        if self.__val is not None:
            if isinstance(self.__val, Iterable):
                return Stream(self.__val)
            return Stream([self.__val])
        return Stream([])

    def orElseThrow(self) -> T:
        """
        Returns the value of the Opt or raise a value error

        Raises:
            ValueError: The value error

        Returns:
            T: The value
        """
        if self.__val is not None:
            return self.__val
        raise ValueError("Object is None")

    def orElseThrowFrom(self, exceptionSupplier: Callable[[], BaseException]) -> T:
        """
        Returns the value of the Opt or raise an exeption provided by the exception supplier

        Args:
            exceptionSupplier (Callable[[], BaseException]): The exception supplier

        Raises:
            exception: The generated exception

        Returns:
            T: The value
        """
        if self.__val is not None:
            return self.__val
        raise exceptionSupplier()

    def ifPresentMap(
        self,
        isPresentMapper: Callable[[T], V],
        orElseSupplier: Callable[[], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by isPresentMapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by orElseSupplier

        Args:
            isPresentMapper (Callable[[T], V]): The presence mapper
            orElseSupplier (Callable[[], V]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(orElseSupplier())
        return Opt(isPresentMapper(self.__val))

    def ifPresentMapWith(
        self,
        withVal: K,
        isPresentMapper: Callable[[T, K], V],
        orElseSupplier: Callable[[K], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by isPresentMapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by orElseSupplier.
        In addition to ifPresentMap, this method also passes the withVal param to the mapper and supplier

        Args:
            withVal (K): The additional mapper value
            isPresentMapper (Callable[[T, K], V]): The presence mapper
            orElseSupplier (Callable[[K], V]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(orElseSupplier(withVal))
        return Opt(isPresentMapper(self.__val, withVal))

    def instanceOf(self, classType: type) -> "Opt[T]":
        """
        Equivalent of Opt.filter(lambda val: isinstance(val, classType))

        Args:
            classType (type): The class type

        Returns:
            Opt[T]: An optional
        """
        if isinstance(self.__val, classType):
            return self
        return Opt(None)

    def cast(self, classType: type[V]) -> "Opt[V]":
        """
        Equivalent of Opt.map(lambda val: cast(classType, val))

        Args:
            classType (type[V]): The class type of the new optional

        Returns:
            Opt[V]: An optional
        """
        return Opt(cast(V, self.__val))

class ClassOps:
    __slots__ = ("__classType",)

    def __init__(self, classType: type) -> None:
        self.__classType = classType

    def instanceOf(self, obj: Any) -> bool:
        return isinstance(obj, self.__classType)

    def subClassOf(self, typ: type) -> bool:
        return issubclass(typ, self.__classType)


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

    def __next__(self) -> T:
        while True:
            nextObj = self._iterator.__next__()
            if self.__filterFn(nextObj):
                return nextObj


class _CastIterable(Generic[T, V], Iterator[T], Iterable[T]):
    __slots__ = ("__iterable", "__iterator", "__tp")

    def __init__(self, it: Iterable[V], typ: type[T]) -> None:
        self.__iterable = it
        self.__iterator = self.__iterable.__iter__()
        self.__tp = typ

    def __iter__(self) -> Iterator[T]:
        self.__iterator = self.__iterable.__iter__()
        return self

    def __next__(self) -> T:
        nextObj = self.__iterator.__next__()
        return cast(T, nextObj)


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

    def __next__(self) -> T:
        return self._iterator.__next__()


class _LimitIterable(_GenericIterable[T]):
    __slots__ = ("__count", "__currentCount")

    def __init__(self, it: Iterable[T], count: int) -> None:
        super().__init__(it)
        self.__count = count
        self.__currentCount = 0

    def _prepare(self) -> None:
        self.__currentCount = 0

    def __next__(self) -> T:
        if self.__currentCount >= self.__count:
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

    def __next__(self) -> T:
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

    def __next__(self) -> T:
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

    def __next__(self) -> T:
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
        self.__set: set[T] = set()

    def _prepare(self) -> None:
        self.__set = set()

    def __next__(self) -> T:
        obj = self._iterator.__next__()
        if obj not in self.__set:
            self.__set.add(obj)
            return obj
        return self.__next__()


class _MapIterable(Generic[T, V], Iterator[V], Iterable[V]):
    __slots__ = ("_iterable", "_iterator", "__fn")

    def __init__(self, it: Iterable[T], mapper: Callable[[T], V]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()
        self.__fn = mapper

    def _prepare(self) -> None:
        pass

    def __iter__(self) -> Iterator[V]:
        self._iterator = self._iterable.__iter__()
        self._prepare()
        return self

    def __next__(self) -> V:
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
        if isEmptyOrNone(self.__arg):
            return Stream([])
        return Stream(_MapIterable(self.__arg, mapper))

    def flatMap(self, mapper: Callable[[T], Iterable[V]]) -> "Stream[V]":
        """
        Produces a flat stream by mapping an element of this stream to an iterable, then concatenates
        the iterables into a single stream.
        Args:
            mapper (Callable[[T], Iterable[V]]): The mapper function

        Returns:
            Stream[V]: the result stream
        """
        if isEmptyOrNone(self.__arg):
            return Stream([])

        return Stream(flatMap(self.__arg, mapper))

    def first(self) -> Opt[T]:
        """
        Finds and returns the first element of the stream.

        Returns:
            Opt[T]: First element
        """
        return self.findFirst(lambda e: True)

    def findFirst(self, predicate: Callable[[T], bool]) -> Opt[T]:
        """
        Finds and returns the first element matching the predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Opt[T]: The firs element found
        """
        return Opt(findFirst(self.__arg, predicate))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Returns a stream of objects that match the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Stream[T]: The stream of filtered objects
        """
        if isEmptyOrNone(self.__arg):
            return Stream([])

        return Stream(_FilterIterable(self.__arg, predicate))

    def cast(self, castTo: type[V]) -> "Stream[V]":
        """
        Returns a stream of objects casted to the given type. Useful when receiving untyped data lists
        and they need to be used in a typed context.

        Args:
            castTo (type[V]): The type all objects will be casted to

        Returns:
            Stream[V]: The stream of casted objects
        """
        if isEmptyOrNone(self.__arg):
            return Stream([])
        return Stream(_CastIterable(self.__arg, castTo))

    def anyMatch(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks if any stream object matches the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            bool: True if any object matches, False otherwise
        """
        return self.filter(predicate).isNotEmpty()

    def noneMatch(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks if none of the stream objects matches the given predicate. This is the inverse of 'anyMatch`
        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            bool: True if no object matches, False otherwise
        """
        return self.filter(predicate).isEmpty()

    def allMatch(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks if all of the stream objects matche the given predicate.
        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            bool: True if all objects matche, False otherwise
        """
        return len(self.filter(predicate).toList()) == len(list(self.__arg))

    def isEmpty(self) -> bool:
        """
        Checks if the stream is empty

        Returns:
            bool: True if the stream is empty, False otherwise
        """
        return isEmptyOrNone(self.__arg)

    def isNotEmpty(self) -> bool:
        """
        Checks if the stream is not empty

        Returns:
            bool: True if the stream is not empty, False otherwise
        """
        return not isEmptyOrNone(self.__arg)

    def collect(self) -> Iterable[T]:
        """
        Returns an iterable with the content of the stream

        Returns:
            Iterable[T]: The iterable
        """
        return self.__arg

    def toList(self) -> list[T]:
        """
        Creates a list with the contents of the stream

        Returns:
            list[T]: The list
        """
        return list(self.__arg)

    def toSet(self) -> set[T]:
        """
        Creates a set witht he contents of the stream

        Returns:
            set[T]: The set
        """
        return set(self.__arg)

    def each(self, action: Callable[[T], Any]) -> None:
        """
        Executes the action callable for each of the stream's elements

        Args:
            action (Callable[[T], Any]): The action
        """
        each(self.__arg, action)

    def ofType(self, theType: type[V]) -> "Stream[V]":
        """
        Returns all items of the given type as a stream

        Args:
            theType (type[V]): The given type

        Returns:
            Stream[V]: The result stream
        """
        return self.filter(ClassOps(theType).instanceOf).cast(theType)

    def skip(self, count: int) -> "Stream[T]":
        """
        Returns a stream without the first number of items specified by 'count'

        Args:
            count (int): How many items should be skipped

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_SkipIterable(self.__arg, count))

    def limit(self, count: int) -> "Stream[T]":
        """
        Returns a stream limited to the first 'count' items of this stream

        Args:
            count (int): The max amount of items

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_LimitIterable(self.__arg, count))

    def takeWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Returns a stream of elements until the first element that DOES NOT match the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_TakeWhileIterable(self.__arg, predicate))

    def dropWhile(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Returns a stream of elements by dropping the first elements that match the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_DropWhileIterable(self.__arg, predicate))

    def reduce(self, reducer: Callable[[T, T], T]) -> Opt[T]:
        """
        Reduces a stream to a single value. The reducer function takes two values and
        returns only one. This function can be used to find min or max from a stream of ints.

        Args:
            reducer (Callable[[T, T], T]): The reducer function

        Returns:
            Opt[T]: The resulting optional
        """
        return Opt(reduce(self.__arg, reducer))

    def nonNull(self) -> "Stream[T]":
        """
        Returns a stream of non null objects from this stream

        Returns:
            Stream[T]: The result stream
        """
        return self.filter(isNotNone)

    def sort(self, comparator: Callable[[T, T], int]) -> "Stream[T]":
        """
        Returns a stream with the elements sorted according to the comparator function.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            comparator (Callable[[T, T], int]): The comparator function

        Returns:
            Stream[T]: The resulting stream
        """
        return Stream(sort(list(self.__arg), comparator))

    def reverse(self) -> "Stream[T]":
        """
        Returns a the reverted stream.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            Stream[T]: Thje resulting stream
        """
        elems = list(self.__arg)
        elems.reverse()
        return Stream(elems)

    def distinct(self) -> "Stream[T]":
        """
        Returns disting elements from the stream.
        CAUTION: Use this method on stream of items that have the __eq__ method implemented,
        otherwise the method will consider all values distinct

        Returns:
            Stream[T]: The resulting stream
        """
        if self.__arg is None:
            return self
        return Stream(_DistinctIterable(self.__arg))

    def concat(self, newStream: "Stream[T]") -> "Stream[T]":
        """
        Returns a stream concatenating the values from this stream with the ones
        from the given stream.

        Args:
            newStream (Stream[T]): The stream to be concatenated with

        Returns:
            Stream[T]: The resulting stream
        """
        return Stream(_ConcatIterable(self.__arg, newStream.__arg))


def stream(it: Iterable[T]) -> Stream[T]:
    """
    Helper method, equivalent to Stream(it)

    Args:
        it (Iterable[T]): The iterator

    Returns:
        Stream[T]: The stream
    """
    return Stream(it)


def optional(val: Optional[T]) -> Opt[T]:
    """
    Helper method, equivalent to Opt(val)

    Args:
        val (Optional[T]): The value

    Returns:
        Opt[T]: The optional
    """
    return Opt(val)
