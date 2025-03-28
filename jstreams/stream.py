from typing import (
    Callable,
    Iterable,
    Any,
    Iterator,
    Optional,
    TypeVar,
    Generic,
    cast,
    Union,
)
from abc import ABC, abstractmethod
from jstreams.utils import is_not_none, require_non_null, each, is_empty_or_none, sort

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")


class Predicate(ABC, Generic[T]):
    @abstractmethod
    def apply(self, value: T) -> bool:
        """
        Apply a condition to a given value.

        Args:
            value (T): The value

        Returns:
            bool: True if the value matches, False otherwise
        """

    def or_(self, other: Union[Callable[[T], bool], "Predicate[T]"]) -> "Predicate[T]":
        return predicate_of(lambda v: self.apply(v) or predicate_of(other).apply(v))

    def and_(self, other: Union[Callable[[T], bool], "Predicate[T]"]) -> "Predicate[T]":
        return predicate_of(lambda v: self.apply(v) and predicate_of(other).apply(v))

    def __call__(self, value: T) -> bool:
        return self.apply(value)


class PredicateWith(ABC, Generic[T, K]):
    @abstractmethod
    def apply(self, value: T, with_value: K) -> bool:
        """
        Apply a condition to two given values.

        Args:
            value (T): The value
            with_value (K): The second value

        Returns:
            bool: True if the values matche the predicate, False otherwise
        """

    def or_(self, other: "PredicateWith[T, K]") -> "PredicateWith[T, K]":
        return predicate_with_of(lambda v, k: self.apply(v, k) or other.apply(v, k))

    def and_(self, other: "PredicateWith[T, K]") -> "PredicateWith[T, K]":
        return predicate_with_of(lambda v, k: self.apply(v, k) and other.apply(v, k))

    def __call__(self, value: T, with_value: K) -> bool:
        return self.apply(value, with_value)


class _WrapPredicate(Predicate[T]):
    __slots__ = ["__predicate_fn"]

    def __init__(self, fn: Callable[[T], bool]) -> None:
        self.__predicate_fn = fn

    def apply(self, value: T) -> bool:
        return self.__predicate_fn(value)


class _WrapPredicateWith(PredicateWith[T, K]):
    __slots__ = ["__predicate_fn"]

    def __init__(self, fn: Callable[[T, K], bool]) -> None:
        self.__predicate_fn = fn

    def apply(self, value: T, withValue: K) -> bool:
        return self.__predicate_fn(value, withValue)


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


class _WrapReducer(Reducer[T]):
    __slots__ = ["__reducer"]

    def __init__(self, reducer: Callable[[T, T], T]) -> None:
        self.__reducer = reducer

    def reduce(self, a: T, b: T) -> T:
        return self.__reducer(a, b)


def reducer_of(reducer: Union[Reducer[T], Callable[[T, T], T]]) -> Reducer[T]:
    if isinstance(reducer, Reducer):
        return reducer
    return _WrapReducer(reducer)


def mapper_of(mapper: Union[Mapper[T, V], Callable[[T], V]]) -> Mapper[T, V]:
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
    if isinstance(mapper, MapperWith):
        return mapper
    return _WrapMapperWith(mapper)


def predicate_of(predicate: Union[Predicate[T], Callable[[T], bool]]) -> Predicate[T]:
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


def predicate_with_of(
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


def find_first(
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
        if predicate_of(predicate).apply(el):
            return el
    return None


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
    mapper_obj = mapper_of(mapper)
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

    mapper_obj = mapper_of(mapper)

    for el in target:
        mapped = mapper_obj.map(el)
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

    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
            ret.append(el)
    return ret


def take_while(
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

    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
            ret.append(el)
        else:
            break
    return ret


def drop_while(
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

    pred = predicate_of(predicate)
    for el in target:
        if pred.apply(el):
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

    elem_list = list(target)
    if len(elem_list) == 0:
        return None

    result: T = elem_list[0]
    reducer_obj = reducer_of(reducer)
    for el in elem_list:
        result = reducer_obj.reduce(el, result)
    return result


class Opt(Generic[T]):
    __slots__ = ("__val",)
    __NONE: "Optional[Opt[Any]]" = None

    def __init__(self, val: Optional[T]) -> None:
        self.__val = val

    def __get_none(self) -> "Opt[T]":
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

    def get_actual(self) -> Optional[T]:
        """
        Returns the actual value of the Opt without raising any errors

        Returns:
            Optional[T]: The value
        """
        return self.__val

    def or_else(self, val: T) -> T:
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

    def or_else_opt(self, val: Optional[T]) -> Optional[T]:
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

    def or_else_get_opt(self, supplier: Callable[[], Optional[T]]) -> Optional[T]:
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

    def or_else_get(self, supplier: Callable[[], T]) -> T:
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

    def is_present(self) -> bool:
        """
        Returns whether the Opt is present

        Returns:
            bool: True if the Opt has a non null value, False otherwise
        """
        return self.__val is not None

    def is_empty(self) -> bool:
        """
        Returns whether the Opt is empty

        Returns:
            bool: True if the Opt value is None, False otherwise
        """
        return self.__val is None

    def if_present(self, action: Callable[[T], Any]) -> "Opt[T]":
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

    def if_present_with(self, with_val: K, action: Callable[[T, K], Any]) -> "Opt[T]":
        """
        Executes an action on the value of the Opt if the value is present, by providing
        the action an additional parameter

        Args:
            with_val (K): The additional parameter
            action (Callable[[T, K], Any]): The action
        Returns:
            Opt[T]: This optional
        """
        if self.__val is not None:
            action(self.__val, with_val)
        return self

    def if_not_present(self, action: Callable[[], Any]) -> "Opt[T]":
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

    def if_not_present_with(self, with_val: K, action: Callable[[K], Any]) -> "Opt[T]":
        """
        Executes an action on if the value is not present, by providing
        the action an additional parameter

        Args:
            with_val (K): The additional parameter
            action (Callable[[K], Any]): The action
        Returns:
            Opt[T]: This optional
        """
        if self.__val is None:
            action(with_val)
        return self

    def if_present_or_else(
        self, action: Callable[[T], Any], empty_action: Callable[[], Any]
    ) -> "Opt[T]":
        """
        Executes an action on the value of the Opt if the value is present, or executes
        the empty_action if the Opt is empty

        Args:
            action (Callable[[T], Any]): The action to be executed when present
            empty_action (Callable[[], Any]): The action to be executed when empty
        Returns:
            Opt[T]: This optional
        """
        if self.__val is not None:
            action(self.__val)
        else:
            empty_action()
        return self

    def if_present_or_else_with(
        self,
        with_val: K,
        action: Callable[[T, K], Any],
        empty_action: Callable[[K], Any],
    ) -> "Opt[T]":
        """
        Executes an action on the value of the Opt by providing the actions an additional parameter,
        if the value is present, or executes the empty_action if the Opt is empty

        Args:
            with_val (K): The additional parameter
            action (Callable[[T, K], Any]): The action to be executed when present
            empty_action (Callable[[K], Any]): The action to be executed when empty
        """
        if self.__val is not None:
            action(self.__val, with_val)
        else:
            empty_action(with_val)
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
        if predicate_of(predicate).apply(self.__val):
            return self
        return self.__get_none()

    def filter_with(
        self, with_val: K, predicate: Union[PredicateWith[T, K], Callable[[T, K], bool]]
    ) -> "Opt[T]":
        """
        Returns the filtered value of the Opt if it matches the given predicate, by
        providing the predicat with an additional value

        Args:
            with_val (K): the additional value
            predicate (Union[PredicateWith[T, K], Callable[[T, K], bool]]): The predicate

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.__val is None:
            return self
        if predicate_with_of(predicate).apply(self.__val, with_val):
            return self
        return self.__get_none()

    def map(self, mapper: Union[Mapper[T, V], Callable[[T], V]]) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return cast(Opt[V], self.__get_none())
        return Opt(mapper_of(mapper).map(self.__val))

    def map_with(
        self, with_val: K, mapper: Union[MapperWith[T, K, V], Callable[[T, K], V]]
    ) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function with an additional parameter

        Args:
            with_val (K): The additional parameter
            mapper (Callable[[T, K], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return cast(Opt[V], self.__get_none())
        return Opt(mapper_with_of(mapper).map(self.__val, with_val))

    def or_else_get_with(self, with_val: K, supplier: Callable[[K], T]) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result with
        the additional parameter

        Args:
            with_val (K): The additional parameter
            supplier (Callable[[K], T]): The supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        return self.or_else_get_with_opt(with_val, supplier)

    def or_else_get_with_opt(
        self, with_val: K, supplier: Callable[[K], Optional[T]]
    ) -> "Opt[T]":
        """
        Returns this Opt if present, otherwise will return the supplier result with
        the additional parameter

        Args:
            with_val (K): The additional parameter
            supplier (Callable[[K], Optional[T]]): The supplier

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.is_present():
            return self
        return Opt(supplier(with_val))

    def if_matches(
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
        if self.__val is not None and predicate_of(predicate).apply(self.__val):
            action(self.__val)
        return self

    def if_matches_opt(
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
        if predicate_of(predicate).apply(self.__val):
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

    def flat_stream(self) -> "Stream[T]":
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

    def or_else_raise(self) -> T:
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

    def or_else_raise_from(self, exception_supplier: Callable[[], BaseException]) -> T:
        """
        Returns the value of the Opt or raise an exeption provided by the exception supplier

        Args:
            exception_supplier (Callable[[], BaseException]): The exception supplier

        Raises:
            exception: The generated exception

        Returns:
            T: The value
        """
        if self.__val is not None:
            return self.__val
        raise exception_supplier()

    def if_present_map(
        self,
        is_present_mapper: Union[Mapper[T, V], Callable[[T], V]],
        or_else_supplier: Callable[[], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by is_present_mapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by or_else_supplier

        Args:
            is_present_mapper (Union[Mapper[T, V], Callable[[T], V]]): The presence mapper
            or_else_supplier (Callable[[], Optional[V]]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(or_else_supplier())
        return Opt(mapper_of(is_present_mapper).map(self.__val))

    def if_present_map_with(
        self,
        with_val: K,
        is_present_mapper: Union[MapperWith[T, K, V], Callable[[T, K], V]],
        or_else_supplier: Callable[[K], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by is_present_mapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by or_else_supplier.
        In addition to ifPresentMap, this method also passes the with_val param to the mapper and supplier

        Args:
            with_val (K): The additional mapper value
            is_present_mapper (Union[MapperWith[T, K, V],  Callable[[T, K], V]]): The presence mapper
            or_else_supplier (Callable[[K], V]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(or_else_supplier(with_val))
        return Opt(mapper_with_of(is_present_mapper).map(self.__val, with_val))

    def instance_of(self, class_type: type) -> "Opt[T]":
        """
        Equivalent of Opt.filter(lambda val: isinstance(val, classType))

        Args:
            class_type (type): The class type

        Returns:
            Opt[T]: An optional
        """
        if isinstance(self.__val, class_type):
            return self
        return self.__get_none()

    def cast(self, class_type: type[V]) -> "Opt[V]":
        """
        Equivalent of Opt.map(lambda val: cast(classType, val))

        Args:
            class_type (type[V]): The class type of the new optional

        Returns:
            Opt[V]: An optional
        """
        return Opt(cast(V, self.__val))

    def if_matches_map(
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
        if self.__val is not None and predicate_of(predicate).apply(self.__val):
            return Opt(mapper_of(mapper).map(self.__val))
        return cast(Opt[V], self.__get_none())

    def if_matches_map_with(
        self,
        with_val: K,
        predicate: Union[PredicateWith[T, K], Callable[[T, K], bool]],
        mapper: Union[MapperWith[T, K, Optional[V]], Callable[[T, K], Optional[V]]],
    ) -> "Opt[V]":
        """
        If the optional value is present and matches the given predicate, returns the value mapped by mapper wrapped in an Opt.
        If the optional value is not present, returns an empty Opt.
        In addition to ifMatchesMap, this method also passes the withVal param to the mapper and supplier

        Args:
            with_val (K): The additional mapper value
            predicate (Union[PredicateWith[T, K], Callable[[T, K], bool]]): The predicate
            mapper (Union[MapperWith[T, K, Optional[V]], Callable[[T, K], Optional[V]]]): The mapper

        Returns:
            Opt[V]: An optional
        """
        if self.__val is not None and predicate_with_of(predicate).apply(
            self.__val, with_val
        ):
            return Opt(mapper_with_of(mapper).map(self.__val, with_val))
        return cast(Opt[V], self.__get_none())


class ClassOps:
    __slots__ = ("__class_type",)

    def __init__(self, class_type: type) -> None:
        self.__class_type = class_type

    def instance_of(self, obj: Any) -> bool:
        return isinstance(obj, self.__class_type)

    def subclass_of(self, typ: type) -> bool:
        return issubclass(typ, self.__class_type)


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
            next_obj = self._iterator.__next__()
            if self.__predicate.apply(next_obj):
                return next_obj


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
        next_obj = self.__iterator.__next__()
        return cast(T, next_obj)


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
    __slots__ = ("__count", "__current_count")

    def __init__(self, it: Iterable[T], count: int) -> None:
        super().__init__(it)
        self.__count = count
        self.__current_count = 0

    def _prepare(self) -> None:
        self.__current_count = 0

    def __next__(self) -> T:
        if self.__current_count >= self.__count:
            raise StopIteration()

        obj = self._iterator.__next__()
        self.__current_count += 1
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
        if not self.__predicate.apply(obj):
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
            if not self.__predicate.apply(obj):
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
        return self.__mapper.map(self._iterator.__next__())


class Stream(Generic[T]):
    __slots__ = ("__arg",)

    def __init__(self, arg: Iterable[T]) -> None:
        self.__arg = arg

    @staticmethod
    def of(arg: Iterable[T]) -> "Stream[T]":
        return Stream(arg)

    @staticmethod
    def of_nullable(arg: Iterable[Optional[T]]) -> "Stream[T]":
        return Stream(arg).filter(is_not_none).map(lambda el: require_non_null(el))

    def map(self, mapper: Union[Mapper[T, V], Callable[[T], V]]) -> "Stream[V]":
        """
        Produces a new stream by mapping the stream elements using the given mapper function.
        Args:
            mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

        Returns:
            Stream[V]: The result stream
        """
        return Stream(_MapIterable(self.__arg, mapper_of(mapper)))

    def flat_map(
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
        return Stream(flat_map(self.__arg, mapper_of(mapper)))

    def flatten(self, typ: type[V]) -> "Stream[V]":
        """
        Flattens a stream of iterables.
        CAUTION: This method will actually iterate the entire iterable, so if you're using
        infinite generators, calling this method will block the execution of the program.
        Returns:
            Stream[T]: A flattened stream
        """
        return self.flat_map(
            lambda v: cast(Iterable[V], v) if isinstance(v, Iterable) else [cast(V, v)]
        )

    def first(self) -> Opt[T]:
        """
        Finds and returns the first element of the stream.

        Returns:
            Opt[T]: First element
        """
        return self.find_first(lambda e: True)

    def find_first(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> Opt[T]:
        """
        Finds and returns the first element matching the predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Opt[T]: The firs element found
        """
        return Opt(find_first(self.__arg, predicate_of(predicate)))

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

        return Stream(_FilterIterable(self.__arg, predicate_of(predicate)))

    def cast(self, cast_to: type[V]) -> "Stream[V]":
        """
        Returns a stream of objects casted to the given type. Useful when receiving untyped data lists
        and they need to be used in a typed context.

        Args:
            castTo (type[V]): The type all objects will be casted to

        Returns:
            Stream[V]: The stream of casted objects
        """
        return Stream(_CastIterable(self.__arg, cast_to))

    def any_match(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> bool:
        """
        Checks if any stream object matches the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            bool: True if any object matches, False otherwise
        """
        return self.filter(predicate_of(predicate)).is_not_empty()

    def none_match(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> bool:
        """
        Checks if none of the stream objects matches the given predicate. This is the inverse of 'any_match`
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            bool: True if no object matches, False otherwise
        """
        return self.filter(predicate_of(predicate)).is_empty()

    def all_match(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> bool:
        """
        Checks if all of the stream objects matche the given predicate.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            bool: True if all objects matche, False otherwise
        """
        return len(self.filter(predicate_of(predicate)).to_list()) == len(
            list(self.__arg)
        )

    def is_empty(self) -> bool:
        """
        Checks if the stream is empty
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            bool: True if the stream is empty, False otherwise
        """
        return is_empty_or_none(self.__arg)

    def is_not_empty(self) -> bool:
        """
        Checks if the stream is not empty
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            bool: True if the stream is not empty, False otherwise
        """
        return not is_empty_or_none(self.__arg)

    def collect(self) -> Iterable[T]:
        """
        Returns an iterable with the content of the stream

        Returns:
            Iterable[T]: The iterable
        """
        return self.__arg

    def collect_using(self, collector: Callable[[Iterable[T]], K]) -> K:
        """
        Returns a transformed version of the stream. The transformation is provided by the collector

        CAUTION: This method may actually iterate the entire stream, so if you're using
        infinite generators, calling this method may block the execution of the program.

        Args:
            collector (Callable[[Iterable[T]], K]): The collector

        Returns:
            K: The tranformed type
        """
        return collector(self.__arg)

    def to_list(self) -> list[T]:
        """
        Creates a list with the contents of the stream
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            list[T]: The list
        """
        return list(self.__arg)

    def to_set(self) -> set[T]:
        """
        Creates a set with the contents of the stream
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Returns:
            set[T]: The set
        """
        return set(self.__arg)

    def to_dict(
        self,
        key_mapper: Union[Mapper[T, V], Callable[[T], V]],
        value_mapper: Union[Mapper[T, K], Callable[[T], K]],
    ) -> dict[V, K]:
        """
        Creates a dictionary with the contents of the stream creating keys using
        the given key mapper and values using the value mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            key_mapper (Union[Mapper[T, V], Callable[[T], V]]): The key mapper
            value_mapper (Union[Mapper[T, K], Callable[[T], K]]): The value mapper

        Returns:
            dict[V, K]: The resulting dictionary
        """
        key_mapper_obj = mapper_of(key_mapper)
        value_mapper_obj = mapper_of(value_mapper)
        return {key_mapper_obj.map(v): value_mapper_obj.map(v) for v in self.__arg}

    def to_dict_as_values(
        self, key_mapper: Union[Mapper[T, V], Callable[[T], V]]
    ) -> dict[V, T]:
        """
        Creates a dictionary with the contents of the stream creating keys using
        the given key mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            key_mapper (Union[Mapper[T, V], Callable[[T], V]]): The key mapper

        Returns:
            dict[V, T]: The resulting dictionary
        """
        key_mapper_obj = mapper_of(key_mapper)
        return {key_mapper_obj.map(v): v for v in self.__arg}

    def to_dict_as_keys(
        self, value_mapper: Union[Mapper[T, V], Callable[[T], V]]
    ) -> dict[T, V]:
        """
        Creates a dictionary using the contents of the stream as keys and mapping
        the dictionary values using the given value mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            value_mapper (Union[Mapper[T, V], Callable[[T], V]]): The value mapper

        Returns:
            dict[V, T]: The resulting dictionary
        """
        value_mapper_obj = mapper_of(value_mapper)
        return {v: value_mapper_obj.map(v) for v in self.__arg}

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

    def of_type(self, the_type: type[V]) -> "Stream[V]":
        """
        Returns all items of the given type as a stream

        Args:
            the_type (type[V]): The given type

        Returns:
            Stream[V]: The result stream
        """
        return self.filter(ClassOps(the_type).instance_of).cast(the_type)

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

    def take_while(
        self, predicate: Union[Predicate[T], Callable[[T], bool]]
    ) -> "Stream[T]":
        """
        Returns a stream of elements until the first element that DOES NOT match the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_TakeWhileIterable(self.__arg, predicate_of(predicate)))

    def drop_while(
        self, predicate: Union[Predicate[T], Callable[[T], bool]]
    ) -> "Stream[T]":
        """
        Returns a stream of elements by dropping the first elements that match the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(_DropWhileIterable(self.__arg, predicate_of(predicate)))

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

    def non_null(self) -> "Stream[T]":
        """
        Returns a stream of non null objects from this stream

        Returns:
            Stream[T]: The result stream
        """
        return self.filter(is_not_none)

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

    def concat(self, new_stream: "Stream[T]") -> "Stream[T]":
        """
        Returns a stream concatenating the values from this stream with the ones
        from the given stream.

        Args:
            new_stream (Stream[T]): The stream to be concatenated with

        Returns:
            Stream[T]: The resulting stream
        """
        return Stream(_ConcatIterable(self.__arg, new_stream.__arg))


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


def extract_list(val: dict[K, Optional[T]], keys: Iterable[K]) -> list[Optional[T]]:
    """
    Extract the elements for the given keys iteration from a dictionary.
    If an element does not exist in the dictionary, None will be returned for that key.

    Args:
        val (dict[K, Optional[T]]): The dictionary from where the values will be extracted
        keys (Iterable[K]): The keys

    Returns:
        list[Optional[T]]: The list of extracted values
    """
    return Stream(keys).map(val.get).to_list()


def extract_non_null_list(val: dict[K, Optional[T]], keys: Iterable[K]) -> list[T]:
    """
    Extract the elements for the given keys iteration from a dictionary.
    If an element does not exist in the dictionary, a value will not be returned for that key.

    Args:
        val (dict[K, Optional[T]]): The dictionary from where the values will be extracted
        keys (Iterable[K]): The keys

    Returns:
        list[Optional[T]]: The list of extracted values
    """
    return (
        Stream(keys)
        .map(val.get)
        .filter(is_not_none)
        .map(lambda e: require_non_null(e))
        .to_list()
    )


def not_null_elements(iterable: Iterable[Optional[T]]) -> Iterable[T]:
    """
    Returns an iterable with all elements that are not None of the given iterable.

    Args:
        iterable (Iterable[Optional[T]]): The given iterable

    Returns:
        Iterable[T]: The iterable sans the None elements
    """
    return (
        Stream(iterable)
        .filter(is_not_none)
        .map(lambda e: require_non_null(e))
        .to_list()
    )
