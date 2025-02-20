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
from abc import ABC, abstractmethod


T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")


class Predicate(ABC, Generic[T]):
    @abstractmethod
    def Apply(self, value: T) -> bool:
        """
        Apply a condition to a given value.

        Args:
            value (T): The value

        Returns:
            bool: True if the value matches, False otherwise
        """

    def Or(self, other: Union[Callable[[T], bool], "Predicate[T]"]) -> "Predicate[T]":
        return predicateOf(lambda v: self.Apply(v) or predicateOf(other).Apply(v))

    def And(self, other: Union[Callable[[T], bool], "Predicate[T]"]) -> "Predicate[T]":
        return predicateOf(lambda v: self.Apply(v) and predicateOf(other).Apply(v))

    def __call__(self, value: T) -> bool:
        return self.Apply(value)


class PredicateWith(ABC, Generic[T, K]):
    @abstractmethod
    def Apply(self, value: T, withValue: K) -> bool:
        """
        Apply a condition to two given values.

        Args:
            value (T): The value
            withValue (K): The second value

        Returns:
            bool: True if the values matche the predicate, False otherwise
        """

    def Or(self, other: "PredicateWith[T, K]") -> "PredicateWith[T, K]":
        return predicateWithOf(lambda v, k: self.Apply(v, k) or other.Apply(v, k))

    def And(self, other: "PredicateWith[T, K]") -> "PredicateWith[T, K]":
        return predicateWithOf(lambda v, k: self.Apply(v, k) and other.Apply(v, k))

    def __call__(self, value: T, withValue: K) -> bool:
        return self.Apply(value, withValue)


class _WrapPredicate(Predicate[T]):
    __slots__ = ["__predicateFn"]

    def __init__(self, fn: Callable[[T], bool]) -> None:
        self.__predicateFn = fn

    def Apply(self, value: T) -> bool:
        return self.__predicateFn(value)


class _WrapPredicateWith(PredicateWith[T, K]):
    __slots__ = ["__predicateFn"]

    def __init__(self, fn: Callable[[T, K], bool]) -> None:
        self.__predicateFn = fn

    def Apply(self, value: T, withValue: K) -> bool:
        return self.__predicateFn(value, withValue)


class Mapper(ABC, Generic[T, V]):
    @abstractmethod
    def Map(self, value: T) -> V:
        """
        Maps the given value, to a new value of maybe a different type.

        Args:
            value (T): The given value

        Returns:
            V: The produced value
        """

    def __call__(self, value: T) -> V:
        return self.Map(value)


class MapperWith(ABC, Generic[T, K, V]):
    @abstractmethod
    def Map(self, value: T, withValue: K) -> V:
        """
        Maps the given two values, to a new value.

        Args:
            value (T): The given value
            withValue (K): The scond value

        Returns:
            V: The produced value
        """

    def __call__(self, value: T, withValue: K) -> V:
        return self.Map(value, withValue)


class _WrapMapper(Mapper[T, V]):
    __slots__ = ["__mapper"]

    def __init__(self, mapper: Callable[[T], V]) -> None:
        self.__mapper = mapper

    def Map(self, value: T) -> V:
        return self.__mapper(value)


class _WrapMapperWith(MapperWith[T, K, V]):
    __slots__ = ["__mapper"]

    def __init__(self, mapper: Callable[[T, K], V]) -> None:
        self.__mapper = mapper

    def Map(self, value: T, withValue: K) -> V:
        return self.__mapper(value, withValue)


class Reducer(ABC, Generic[T]):
    @abstractmethod
    def Reduce(self, a: T, b: T) -> T:
        """
        Reduce two values to a single one.

        Args:
            a (T): The first value
            b (T): The second value

        Returns:
            T: The reduced value
        """

    def __call__(self, a: T, b: T) -> T:
        return self.Reduce(a, b)


class _WrapReducer(Reducer[T]):
    __slots__ = ["__reducer"]

    def __init__(self, reducer: Callable[[T, T], T]) -> None:
        self.__reducer = reducer

    def Reduce(self, a: T, b: T) -> T:
        return self.__reducer(a, b)


def reducerOf(reducer: Union[Reducer[T], Callable[[T, T], T]]) -> Reducer[T]:
    if isinstance(reducer, Reducer):
        return reducer
    return _WrapReducer(reducer)


def mapperOf(mapper: Union[Mapper[T, V], Callable[[T], V]]) -> Mapper[T, V]:
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


def mapperWithOf(
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
    if isinstance(mapper, MapperWith):
        return mapper
    return _WrapMapperWith(mapper)


def predicateOf(predicate: Union[Predicate[T], Callable[[T], bool]]) -> Predicate[T]:
    """
    If the value passed is a predicate, it is returned without any changes.
    If a function is passed, it will be wrapped into a Predicate object.

    Args:
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Predicate[T]: The produced predicate
    """
    if isinstance(predicate, Predicate):
        return predicate
    return _WrapPredicate(predicate)


def predicateWithOf(
    predicate: Union[PredicateWith[T, K], Callable[[T, K], bool]],
) -> PredicateWith[T, K]:
    """
    If the value passed is a predicate, it is returned without any changes.
    If a function is passed, it will be wrapped into a Predicate object.

    Args:
        predicate (Union[PredicateWith[T, K], Callable[[T, K], bool]]): The predicate

    Returns:
        PredicateWith[T, K]: The produced predicate
    """
    if isinstance(predicate, PredicateWith):
        return predicate
    return _WrapPredicateWith(predicate)


def isEmptyOrNone(
    obj: Union[list[Any], dict[Any, Any], str, None, Any, Iterable[Any]],
) -> bool:
    """
    Checkes whether the given object is either None, or is empty.
    For str and Sized objects, besides the None check, the len(obj) == 0 is also applied

    Args:
        obj (Union[list[Any], dict[Any, Any], str, None, Any, Iterable[Any]]): The object

    Returns:
        bool: True if empty or None, False otherwise
    """
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
    target: Optional[Iterable[T]], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> Optional[T]:
    """
    Retrieves the first element of the given iterable that matches the given predicate

    Args:
        target (Optional[Iterable[T]]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        Optional[T]: The first matching element, or None if no element matches the predicate
    """
    if target is None:
        return None

    for el in target:
        if predicateOf(predicate).Apply(el):
            return el
    return None


def mapIt(
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
    mapperObj = mapperOf(mapper)
    return [mapperObj.Map(el) for el in target]


def flatMap(
    target: Iterable[T],
    mapper: Union[Mapper[T, Iterable[V]], Callable[[T], Iterable[V]]],
) -> list[V]:
    """
    Returns a flattened map. The mapper function is called for each element of the target
    iterable, then all elements are added to a result list.
    Ex: flatMap([1, 2], lambda x: [x, x + 1]) returns [1, 2, 2, 3]

    Args:
        target (Iterable[T]): The target iterable
        mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

    Returns:
        list[V]: The resulting flattened map
    """
    ret: list[V] = []
    if target is None:
        return ret

    mapperObj = mapperOf(mapper)

    for el in target:
        mapped = mapperObj.Map(el)
        each(mapped, ret.append)
    return ret


def matching(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns all elements of the target iterable that match the given predicate

    Args:
        target (Iterable[T]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        list[T]: The matching elements
    """
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if predicateOf(predicate).Apply(el):
            ret.append(el)
    return ret


def takeWhile(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns the first batch of elements matching the predicate. Once an element
    that does not match the predicate is found, the function will return

    Args:
        target (Iterable[T]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    for el in target:
        if predicateOf(predicate).Apply(el):
            ret.append(el)
        else:
            break
    return ret


def dropWhile(
    target: Iterable[T], predicate: Union[Predicate[T], Callable[[T], bool]]
) -> list[T]:
    """
    Returns the target iterable elements without the first elements that match the
    predicate. Once an element that does not match the predicate is found,
    the function will start adding the remaining elements to the result list

    Args:
        target (Iterable[T]): The target iterable
        predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

    Returns:
        list[T]: The result list
    """
    ret: list[T] = []
    if target is None:
        return ret

    index = 0

    for el in target:
        if predicateOf(predicate).Apply(el):
            index += 1
        else:
            break
    return list(target)[index:]


def reduce(
    target: Iterable[T], reducer: Union[Reducer[T], Callable[[T, T], T]]
) -> Optional[T]:
    """
    Reduces an iterable to a single value. The reducer function takes two values and
    returns only one. This function can be used to find min or max from a stream of ints.

    Args:
        reducer (Union[Reducer[T], Callable[[T, T], T]]): The reducer

    Returns:
        Optional[T]: The resulting optional
    """

    if target is None:
        return None

    elemList = list(target)
    if len(elemList) == 0:
        return None

    result: T = elemList[0]
    reducerObj = reducerOf(reducer)
    for el in elemList:
        result = reducerObj.Reduce(el, result)
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
    __NONE: "Optional[Opt[Any]]" = None

    def __init__(self, val: Optional[T]) -> None:
        self.__val = val

    def __getNone(self) -> "Opt[T]":
        if Opt.__NONE is None:
            Opt.__NONE = Opt(None)
        return cast(Opt[T], Opt.__NONE)

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

    def orElse(self, val: T) -> T:
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

    def orElseOpt(self, val: Optional[T]) -> Optional[T]:
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

    def orElseGetOpt(self, supplier: Callable[[], Optional[T]]) -> Optional[T]:
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

    def orElseGet(self, supplier: Callable[[], T]) -> T:
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

    def filter(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> "Opt[T]":
        """
        Returns the filtered value of the Opt if it matches the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.__val is None:
            return self
        if predicateOf(predicate).Apply(self.__val):
            return self
        return self.__getNone()

    def filterWith(
        self, withVal: K, predicate: Union[PredicateWith[T, K], Callable[[T, K], bool]]
    ) -> "Opt[T]":
        """
        Returns the filtered value of the Opt if it matches the given predicate, by
        providing the predicat with an additional value

        Args:
            withVal (K): the additional value
            predicate (Union[PredicateWith[T, K], Callable[[T, K], bool]]): The predicate

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.__val is None:
            return self
        if predicateWithOf(predicate).Apply(self.__val, withVal):
            return self
        return self.__getNone()

    def map(self, mapper: Union[Mapper[T, V], Callable[[T], V]]) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return cast(Opt[V], self.__getNone())
        return Opt(mapperOf(mapper).Map(self.__val))

    def mapWith(
        self, withVal: K, mapper: Union[MapperWith[T, K, V], Callable[[T, K], V]]
    ) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function with an additional parameter

        Args:
            withVal (K): The additional parameter
            mapper (Callable[[T, K], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return cast(Opt[V], self.__getNone())
        return Opt(mapperWithOf(mapper).Map(self.__val, withVal))

    def orElseGetWith(self, withVal: K, supplier: Callable[[K], T]) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result with
        the additional parameter

        Args:
            withVal (K): The additional parameter
            supplier (Callable[[K], T]): The supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        return self.orElseGetWithOpt(withVal, supplier)

    def orElseGetWithOpt(
        self, withVal: K, supplier: Callable[[K], Optional[T]]
    ) -> "Opt[T]":
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

    def ifMatches(
        self,
        predicate: Union[Predicate[T], Callable[[T], bool]],
        action: Callable[[T], Any],
    ) -> "Opt[T]":
        """
        Executes the given action on the value of this Opt, if the value is present and
        matches the given predicate. Returns the same Opt

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate
            action (Callable[[T], Any]): The action to be executed

        Returns:
            Opt[T]: The same Opt
        """
        if self.__val is not None and predicateOf(predicate).Apply(self.__val):
            action(self.__val)
        return self

    def ifMatchesOpt(
        self,
        predicate: Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]],
        action: Callable[[Optional[T]], Any],
    ) -> "Opt[T]":
        """
        Executes the given action on the value of this Opt, regardless of whether the value
        is present, if the value matches the given predicate. Returns the same Opt

        Args:
            predicate (Union[Predicate[Optional[T]], Callable[[Optional[T]], bool]]): The predicate
            action (Callable[[Optional[T]], Any]): The action to be executed

        Returns:
            Opt[T]: The same Opt
        """
        if predicateOf(predicate).Apply(self.__val):
            action(self.__val)
        return self

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
        isPresentMapper: Union[Mapper[T, V], Callable[[T], V]],
        orElseSupplier: Callable[[], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by isPresentMapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by orElseSupplier

        Args:
            isPresentMapper (Union[Mapper[T, V], Callable[[T], V]]): The presence mapper
            orElseSupplier (Callable[[], Optional[V]]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(orElseSupplier())
        return Opt(mapperOf(isPresentMapper).Map(self.__val))

    def ifPresentMapWith(
        self,
        withVal: K,
        isPresentMapper: Union[MapperWith[T, K, V], Callable[[T, K], V]],
        orElseSupplier: Callable[[K], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by isPresentMapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by orElseSupplier.
        In addition to ifPresentMap, this method also passes the withVal param to the mapper and supplier

        Args:
            withVal (K): The additional mapper value
            isPresentMapper (Union[MapperWith[T, K, V],  Callable[[T, K], V]]): The presence mapper
            orElseSupplier (Callable[[K], V]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(orElseSupplier(withVal))
        return Opt(mapperWithOf(isPresentMapper).Map(self.__val, withVal))

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
        return self.__getNone()

    def cast(self, classType: type[V]) -> "Opt[V]":
        """
        Equivalent of Opt.map(lambda val: cast(classType, val))

        Args:
            classType (type[V]): The class type of the new optional

        Returns:
            Opt[V]: An optional
        """
        return Opt(cast(V, self.__val))

    def ifMatchesMap(
        self,
        predicate: Union[Predicate[T], Callable[[T], bool]],
        mapper: Union[Mapper[T, Optional[V]], Callable[[T], Optional[V]]],
    ) -> "Opt[V]":
        """
        If the optional value is present and matches the given predicate, returns the value mapped
        by mapper wrapped in an Opt.
        If the optional value is not present, returns an empty Opt.

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate
            mapper (Union[Mapper[T, V], Callable[[T], Optional[V]]]): The the mapper

        Returns:
            Opt[V]: An optional
        """
        if self.__val is not None and predicateOf(predicate).Apply(self.__val):
            return Opt(mapperOf(mapper).Map(self.__val))
        return cast(Opt[V], self.__getNone())

    def ifMatchesMapWith(
        self,
        withVal: K,
        predicate: Union[PredicateWith[T, K], Callable[[T, K], bool]],
        mapper: Union[MapperWith[T, K, Optional[V]], Callable[[T, K], Optional[V]]],
    ) -> "Opt[V]":
        """
        If the optional value is present and matches the given predicate, returns the value mapped by mapper wrapped in an Opt.
        If the optional value is not present, returns an empty Opt.
        In addition to ifMatchesMap, this method also passes the withVal param to the mapper and supplier

        Args:
            withVal (K): The additional mapper value
            predicate (Union[PredicateWith[T, K], Callable[[T, K], bool]]): The predicate
            mapper (Union[MapperWith[T, K, Optional[V]], Callable[[T, K], Optional[V]]]): The mapper

        Returns:
            Opt[V]: An optional
        """
        if self.__val is not None and predicateWithOf(predicate).Apply(
            self.__val, withVal
        ):
            return Opt(mapperWithOf(mapper).Map(self.__val, withVal))
        return cast(Opt[V], self.__getNone())


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
    __slots__ = ("__predicate",)

    def __init__(self, it: Iterable[T], predicate: Predicate[T]) -> None:
        super().__init__(it)
        self.__predicate = predicate

    def __next__(self) -> T:
        while True:
            nextObj = self._iterator.__next__()
            if self.__predicate.Apply(nextObj):
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
    __slots__ = ("__predicate", "__done")

    def __init__(self, it: Iterable[T], predicate: Predicate[T]) -> None:
        super().__init__(it)
        self.__done = False
        self.__predicate = predicate

    def _prepare(self) -> None:
        self.__done = False

    def __next__(self) -> T:
        if self.__done:
            raise StopIteration()

        obj = self._iterator.__next__()
        if not self.__predicate.Apply(obj):
            self.__done = True
            raise StopIteration()

        return obj


class _DropWhileIterable(_GenericIterable[T]):
    __slots__ = ("__predicate", "__done")

    def __init__(self, it: Iterable[T], predicate: Predicate[T]) -> None:
        super().__init__(it)
        self.__done = False
        self.__predicate = predicate

    def _prepare(self) -> None:
        self.__done = False

    def __next__(self) -> T:
        if self.__done:
            return self._iterator.__next__()
        while not self.__done:
            obj = self._iterator.__next__()
            if not self.__predicate.Apply(obj):
                self.__done = True
                return obj
        raise StopIteration()


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
    __slots__ = ("_iterable", "_iterator", "__mapper")

    def __init__(self, it: Iterable[T], mapper: Mapper[T, V]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()
        self.__mapper = mapper

    def _prepare(self) -> None:
        pass

    def __iter__(self) -> Iterator[V]:
        self._iterator = self._iterable.__iter__()
        self._prepare()
        return self

    def __next__(self) -> V:
        return self.__mapper.Map(self._iterator.__next__())


class Stream(Generic[T]):
    __slots__ = ("__arg",)

    def __init__(self, arg: Iterable[T]) -> None:
        self.__arg = arg

    @staticmethod
    def of(arg: Iterable[T]) -> "Stream[T]":
        return Stream(arg)

    def map(self, mapper: Union[Mapper[T, V], Callable[[T], V]]) -> "Stream[V]":
        """
        Produces a new stream by mapping the stream elements using the given mapper function.
        Args:
            mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

        Returns:
            Stream[V]: The result stream
        """
        return Stream(_MapIterable(self.__arg, mapperOf(mapper)))

    def flatMap(
        self, mapper: Union[Mapper[T, Iterable[V]], Callable[[T], Iterable[V]]]
    ) -> "Stream[V]":
        """
        Produces a flat stream by mapping an element of this stream to an iterable, then concatenates
        the iterables into a single stream.
        Args:
            mapper (Union[Mapper[T, Iterable[V]], Callable[[T], Iterable[V]]]): The mapper

        Returns:
            Stream[V]: the result stream
        """
        return Stream(flatMap(self.__arg, mapperOf(mapper)))

    def flatten(self, typ: type[V]) -> "Stream[V]":
        """
        Flattens a stream of iterables.
        CAUTION: This method will actually iterate the entire iterable, so if you're using
        infinite generators, calling this method will block the execution of the program.
        Returns:
            Stream[T]: A flattened stream
        """
        return self.flatMap(
            lambda v: cast(Iterable[V], v) if isinstance(v, Iterable) else [cast(V, v)]
        )

    def first(self) -> Opt[T]:
        """
        Finds and returns the first element of the stream.

        Returns:
            Opt[T]: First element
        """
        return self.findFirst(lambda e: True)

    def findFirst(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> Opt[T]:
        """
        Finds and returns the first element matching the predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Opt[T]: The firs element found
        """
        return Opt(findFirst(self.__arg, predicateOf(predicate)))

    def filter(
        self, predicate: Union[Predicate[T], Callable[[T], bool]]
    ) -> "Stream[T]":
        """
        Returns a stream of objects that match the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Stream[T]: The stream of filtered objects
        """

        return Stream(_FilterIterable(self.__arg, predicateOf(predicate)))

    def cast(self, castTo: type[V]) -> "Stream[V]":
        """
        Returns a stream of objects casted to the given type. Useful when receiving untyped data lists
        and they need to be used in a typed context.

        Args:
            castTo (type[V]): The type all objects will be casted to

        Returns:
            Stream[V]: The stream of casted objects
        """
        return Stream(_CastIterable(self.__arg, castTo))

    def anyMatch(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> bool:
        """
        Checks if any stream object matches the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            bool: True if any object matches, False otherwise
        """
        return self.filter(predicateOf(predicate)).isNotEmpty()

    def noneMatch(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> bool:
        """
        Checks if none of the stream objects matches the given predicate. This is the inverse of 'anyMatch`
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            bool: True if no object matches, False otherwise
        """
        return self.filter(predicateOf(predicate)).isEmpty()

    def allMatch(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> bool:
        """
        Checks if all of the stream objects matche the given predicate.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            bool: True if all objects matche, False otherwise
        """
        return len(self.filter(predicateOf(predicate)).toList()) == len(
            list(self.__arg)
        )

    def isEmpty(self) -> bool:
        """
        Checks if the stream is empty
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            bool: True if the stream is empty, False otherwise
        """
        return isEmptyOrNone(self.__arg)

    def isNotEmpty(self) -> bool:
        """
        Checks if the stream is not empty
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

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
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            list[T]: The list
        """
        return list(self.__arg)

    def toSet(self) -> set[T]:
        """
        Creates a set with the contents of the stream
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            set[T]: The set
        """
        return set(self.__arg)

    def toDict(
        self,
        keyMapper: Union[Mapper[T, V], Callable[[T], V]],
        valueMapper: Union[Mapper[T, K], Callable[[T], K]],
    ) -> dict[V, K]:
        """
        Creates a dictionary with the contents of the stream creating keys using
        the given key mapper and values using the value mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            keyMapper (Union[Mapper[T, V], Callable[[T], V]]): The key mapper
            valueMapper (Union[Mapper[T, K], Callable[[T], K]]): The value mapper

        Returns:
            dict[V, K]: The resulting dictionary
        """
        keyMapperObj = mapperOf(keyMapper)
        valueMapperObj = mapperOf(valueMapper)
        return {keyMapperObj.Map(v): valueMapperObj.Map(v) for v in self.__arg}

    def toDictAsValues(
        self, keyMapper: Union[Mapper[T, V], Callable[[T], V]]
    ) -> dict[V, T]:
        """
        Creates a dictionary with the contents of the stream creating keys using
        the given key mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            keyMapper (Union[Mapper[T, V], Callable[[T], V]]): The key mapper

        Returns:
            dict[V, T]: The resulting dictionary
        """
        keyMapperObj = mapperOf(keyMapper)
        return {keyMapperObj.Map(v): v for v in self.__arg}

    def toDictAsKeys(
        self, valueMapper: Union[Mapper[T, V], Callable[[T], V]]
    ) -> dict[T, V]:
        """
        Creates a dictionary using the contents of the stream as keys and mapping
        the dictionary values using the given value mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            keyMapper (Union[Mapper[T, V], Callable[[T], V]]): The value mapper

        Returns:
            dict[V, T]: The resulting dictionary
        """
        valueMapperObj = mapperOf(valueMapper)
        return {v: valueMapperObj.Map(v) for v in self.__arg}

    def each(self, action: Callable[[T], Any]) -> "Stream[T]":
        """
        Executes the action callable for each of the stream's elements.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            action (Callable[[T], Any]): The action
        """
        each(self.__arg, action)
        return self

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

    def takeWhile(
        self, predicate: Union[Predicate[T], Callable[[T], bool]]
    ) -> "Stream[T]":
        """
        Returns a stream of elements until the first element that DOES NOT match the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_TakeWhileIterable(self.__arg, predicateOf(predicate)))

    def dropWhile(
        self, predicate: Union[Predicate[T], Callable[[T], bool]]
    ) -> "Stream[T]":
        """
        Returns a stream of elements by dropping the first elements that match the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_DropWhileIterable(self.__arg, predicateOf(predicate)))

    def reduce(self, reducer: Union[Reducer[T], Callable[[T, T], T]]) -> Opt[T]:
        """
        Reduces a stream to a single value. The reducer takes two values and
        returns only one. This function can be used to find min or max from a stream of ints.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            reducer (Union[Reducer[T], Callable[[T, T], T]]): The reducer

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
