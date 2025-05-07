from collections import deque
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
from abc import ABC

from jstreams.class_operations import ClassOps
from jstreams.iterable_operations import find_first, reduce
from jstreams.mapper import Mapper, MapperWith, flat_map, mapper_of, mapper_with_of
from jstreams.reducer import Reducer
from jstreams.predicate import (
    Predicate,
    PredicateWith,
    is_none,
    predicate_of,
    predicate_with_of,
)
from jstreams.tuples import Pair, pair_of
from jstreams.utils import is_not_none, require_non_null, each, is_empty_or_none, sort

A = TypeVar("A")
B = TypeVar("B")

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")
S = TypeVar("S")
U = TypeVar("U")


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

    def flatten(self: "Opt[Opt[U]]") -> "Opt[U]":
        """
        Flattens a nested Opt[Opt[U]] into Opt[U].
        If the outer Opt is empty, or the inner Opt is empty, returns an empty Opt.

        Returns:
            Opt[U]: The flattened Opt.
        """
        if self.is_present():
            inner_opt = self.__val  # self.__val is Opt[U] here
            if isinstance(inner_opt, Opt):
                return inner_opt  # Return the inner Opt[U]
            else:
                # This case shouldn't happen if type hints are correct,
                # but defensively return empty if the contained value isn't an Opt.
                # Or perhaps raise a TypeError? Returning empty seems safer.
                return cast(Opt[U], self.__get_none())
        else:
            return cast(Opt[U], self.__get_none())  # Outer Opt was empty

    def flat_map(self, mapper: Callable[[T], "Opt[V]"]) -> "Opt[V]":
        """
        If a value is present, applies the provided mapping function to it,
        returning the Opt result of the function. Otherwise returns an empty Opt.
        This is useful for chaining operations that return Opt.

        Args:
            mapper: A function that takes the value T and returns an Opt[V].

        Returns:
            Opt[V]: The result of the mapping function if the value was present,
                    otherwise an empty Opt.
        """
        if self.is_empty():
            return cast(Opt[V], self.__get_none())
        else:
            # Type checker knows self.__val is T here
            return mapper(require_non_null(self.__val))

    def zip(self, other: "Opt[V]") -> "Opt[Pair[T, V]]":
        """
        Combines this Opt with another Opt. If both contain a value, returns an
        Opt containing a Pair of the two values. Otherwise, returns an empty Opt.

        Args:
            other: The other Opt instance to zip with.

        Returns:
            Opt[Pair[T, V]]: An Opt containing the pair if both were present, else empty.
        """
        if self.is_present() and other.is_present():
            # Type checker knows self.__val is T and other.__val is V
            return Opt(
                Pair(require_non_null(self.__val), require_non_null(other.__val))
            )
        else:
            return cast(Opt[Pair[T, V]], self.__get_none())

    def zip_with(self, other: "Opt[V]", zipper: Callable[[T, V], K]) -> "Opt[K]":
        """
        Combines this Opt with another Opt using a zipper function. If both contain
        a value, applies the zipper function to them and returns an Opt containing
        the result. Otherwise, returns an empty Opt.

        Args:
            other: The other Opt instance to zip with.
            zipper: A function that takes values T and V and returns K.

        Returns:
            Opt[K]: An Opt containing the result of the zipper function if both
                    were present, else empty.
        """
        if self.is_present() and other.is_present():
            # Type checker knows self.__val is T and other.__val is V
            return Opt(
                zipper(require_non_null(self.__val), require_non_null(other.__val))
            )
        else:
            return cast(Opt[K], self.__get_none())

    def or_opt(self, other: "Opt[T]") -> "Opt[T]":
        """
        Returns this Opt if it contains a value, otherwise returns the other Opt.
        Useful for providing an alternative Opt as a fallback.

        Args:
            other: The alternative Opt to return if this one is empty.

        Returns:
            Opt[T]: This Opt if present, otherwise the other Opt.
        """
        return self if self.is_present() else other

    def peek(self, action: Callable[[T], Any]) -> "Opt[T]":
        return self.if_present(action)

    def unzip(self: "Opt[Pair[A, B]]") -> "Pair[Opt[A], Opt[B]]":
        """
        Transforms an Opt[Pair[A, B]] into a Pair[Opt[A], Opt[B]].
        If the original Opt is empty, returns a Pair of two empty Opts.

        Returns:
            Pair[Opt[A], Opt[B]]: The resulting pair of Opts.
        """
        if self.is_present():
            pair_val = self.__val  # Type is Pair[A, B]
            if isinstance(pair_val, Pair):
                return Pair(Opt(pair_val.left()), Opt(pair_val.right()))
            else:
                # Should not happen with correct types, return pair of empty
                return Pair(
                    cast(Opt[A], self.__get_none()), cast(Opt[B], self.__get_none())
                )
        else:
            return Pair(
                cast(Opt[A], self.__get_none()), cast(Opt[B], self.__get_none())
            )

    @staticmethod
    def of(value: T) -> "Opt[T]":
        """
        Creates an Opt instance containing the given value. If the value is None, it raises a value error.
        This method is useful for creating an Opt from a non-null value. This helps to ensure that the value
        is not null when creating the Opt. In some cases, you might not expect a null value, and this method
        can help catch that error early.

        Args:
            value (T): The given value

        Returns:
            Opt[T]: The optional object
        """
        return Opt(require_non_null(value))

    @staticmethod
    def of_nullable(value: Optional[T]) -> "Opt[T]":
        """
        Creates an Opt instance containing the given value. If the value is None, it returns an empty Opt.

        Args:
            value (Optional[T]): The given value

        Returns:
            Opt[T]: The optional object
        """
        return Opt(value)

    @staticmethod
    def empty() -> "Opt[T]":
        """
        Returns a cached empty Opt instance.

        Returns:
            Opt[T]: An empty Opt. The type T is inferred from context.
        """
        if Opt.__NONE is None:
            Opt.__NONE = Opt(None)
        return cast(Opt[T], Opt.__NONE)

    @staticmethod
    def when(condition: bool, value: T) -> "Opt[T]":
        """
        Creates an Opt containing the given value if the condition is true,
        otherwise returns an empty Opt.

        Args:
            condition (bool): The condition to evaluate.
            value (T): The value to wrap in an Opt if the condition is true.

        Returns:
            Opt[T]: An Opt containing the value if the condition is true, else an empty Opt.
        """
        return Opt(value) if condition else Opt.empty()

    @staticmethod
    def when_supplied(condition: bool, supplier: Callable[[], T]) -> "Opt[T]":
        """
        If the condition is true, calls the supplier and returns an Opt
        containing the supplied value. Otherwise, returns an empty Opt.
        The supplier is only called if the condition is true.

        Args:
            condition (bool): The condition to evaluate.
            supplier (Callable[[], T]): A function that supplies the value if the condition is true.

        Returns:
            Opt[T]: An Opt containing the supplied value if the condition is true, else an empty Opt.
        """
        return Opt(supplier()) if condition else Opt.empty()

    @staticmethod
    def try_or_empty(
        callable_fn: Callable[[], T], *catch_exceptions: type[BaseException]
    ) -> "Opt[T]":
        """
        Executes the given callable. If it succeeds, returns an Opt containing its result.
        If any of the specified exceptions (or `Exception` by default if none are specified)
        are raised during execution, returns an empty Opt.

        Args:
            callable_fn (Callable[[], T]): The function to call.
            *catch_exceptions (type[BaseException]): Specific exception types to catch.
                If not provided, defaults to `(Exception,)`.

        Returns:
            Opt[T]: An Opt containing the result of the callable, or an empty Opt if an exception occurred.
        """
        exceptions_to_catch = catch_exceptions if catch_exceptions else (Exception,)
        try:
            return Opt(callable_fn())
        except exceptions_to_catch:
            return Opt.empty()

    @staticmethod
    def first_present(*opts: "Opt[T]") -> "Opt[T]":
        """
        Returns the first Opt in the given sequence that is present (non-empty).
        If all Opts are empty or no Opts are provided, returns an empty Opt.
        """
        return Stream(opts).find_first(Opt.is_present).flat_map(lambda x: x)


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
    __slots__ = ("__predicate", "__done", "__include_stop_value")

    def __init__(
        self, it: Iterable[T], predicate: Predicate[T], include_stop_value: bool
    ) -> None:
        super().__init__(it)
        self.__done = False
        self.__predicate = predicate
        self.__include_stop_value = include_stop_value

    def _prepare(self) -> None:
        self.__done = False

    def __next__(self) -> T:
        if self.__done:
            raise StopIteration()

        obj = self._iterator.__next__()
        if not self.__predicate.apply(obj):
            self.__done = True
            if not self.__include_stop_value:
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


# Modify _DistinctIterable to accept key_func
class _DistinctIterable(_GenericIterable[T]):
    __slots__ = ("__seen", "__key_func")  # Use __seen instead of __set for clarity

    def __init__(
        self, it: Iterable[T], key_func: Optional[Callable[[T], Any]] = None
    ) -> None:
        super().__init__(it)
        self.__seen: set[Any] = (
            set()
        )  # Stores keys if key_func is provided, else elements
        self.__key_func = key_func

    def _prepare(self) -> None:
        self.__seen = set()

    def __next__(self) -> T:
        while True:  # Keep trying until a distinct element is found or iterator ends
            obj = self._iterator.__next__()
            key_to_check = self.__key_func(obj) if self.__key_func else obj
            if key_to_check not in self.__seen:
                self.__seen.add(key_to_check)
                return obj


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


class _PeekIterable(_GenericIterable[T]):
    __slots__ = ("__action", "__logger")

    def __init__(
        self,
        it: Iterable[T],
        action: Callable[[T], Any],
        logger: Optional[Callable[[Exception], Any]] = None,
    ) -> None:
        super().__init__(it)
        self.__action = action
        self.__logger = logger

    def _prepare(self) -> None:
        pass

    def __next__(self) -> T:
        obj = self._iterator.__next__()
        try:
            self.__action(obj)  # Perform the side-effect
        except Exception as e:
            print(
                f"Exception during Stream.peek: {e}"
            ) if self.__logger is None else self.__logger(e)
        return obj  # Return the original object


class _IndexedIterable(Generic[T], Iterator[Pair[int, T]], Iterable[Pair[int, T]]):
    __slots__ = ("_iterable", "_iterator", "_index")

    def __init__(self, it: Iterable[T]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()
        self._index = 0

    def __iter__(self) -> Iterator[Pair[int, T]]:
        self._iterator = self._iterable.__iter__()
        self._index = 0  # Reset index for new iteration
        return self

    def __next__(self) -> Pair[int, T]:
        obj = self._iterator.__next__()  # Raises StopIteration when done
        current_index = self._index
        self._index += 1
        return Pair(current_index, obj)


# In stream.py, add a new Iterable class
class _ChunkedIterable(Generic[T], Iterator[list[T]], Iterable[list[T]]):
    __slots__ = ("_iterator", "_size")

    def __init__(self, it: Iterable[T], size: int) -> None:
        if size <= 0:
            raise ValueError("Chunk size must be positive")
        # Store the original iterator directly
        self._iterator = iter(it)
        self._size = size

    def __iter__(self) -> Iterator[list[T]]:
        # Resetting isn't straightforward without consuming the original iterable again.
        # This implementation assumes the stream is consumed once.
        # If re-iteration is needed, the original iterable must support it.
        # Or, store the original iterable and get a new iterator here.
        # self._iterator = iter(self._iterable) # If storing _iterable instead
        return self

    def __next__(self) -> list[T]:
        chunk = []
        try:
            for _ in range(self._size):
                chunk.append(next(self._iterator))
        except StopIteration:
            # Reached the end of the underlying iterator
            pass  # Allow the loop to finish

        if not chunk:  # If no elements were added (end of iteration)
            raise StopIteration
        return chunk


class _TakeUntilIterable(_GenericIterable[T]):
    __slots__ = ("__predicate", "__done", "__include_stop_value")

    def __init__(
        self, it: Iterable[T], predicate: Predicate[T], include_stop_value: bool
    ) -> None:
        super().__init__(it)
        self.__predicate = predicate
        self.__done = False
        self.__include_stop_value = include_stop_value

    def _prepare(self) -> None:
        self.__done = False

    def __next__(self) -> T:
        if self.__done:
            raise StopIteration()

        obj = self._iterator.__next__()
        if self.__predicate.apply(obj):
            self.__done = True  # Stop after yielding this one
            if not self.__include_stop_value:
                raise StopIteration()

        return obj


class _DropUntilIterable(_GenericIterable[T]):
    __slots__ = ("__predicate", "__dropping")

    def __init__(self, it: Iterable[T], predicate: Predicate[T]) -> None:
        super().__init__(it)
        self.__predicate = predicate
        self.__dropping = True  # Start in dropping mode

    def _prepare(self) -> None:
        self.__dropping = True

    def __next__(self) -> T:
        while self.__dropping:
            obj = self._iterator.__next__()  # Consume elements
            if self.__predicate.apply(obj):
                self.__dropping = False  # Stop dropping
                return obj  # Return the first matching element
        # Once dropping stops, just yield remaining elements
        return self._iterator.__next__()


class _ScanIterable(Generic[T, V], Iterator[V], Iterable[V]):
    __slots__ = (
        "_iterator",
        "_accumulator",
        "_current_value",
        "_first",
        "_iterable",
        "_initial_value",
    )

    def __init__(
        self, it: Iterable[T], accumulator: Callable[[V, T], V], initial_value: V
    ) -> None:
        # Store original iterable to allow re-iteration if needed
        self._iterable = it
        self._iterator = iter(self._iterable)
        self._accumulator = accumulator
        self._initial_value = initial_value
        # State for iteration
        self._current_value = self._initial_value
        self._first = True  # Flag to yield initial value first

    def __iter__(self) -> Iterator[V]:
        # Reset state for new iteration
        self._iterator = iter(self._iterable)
        self._current_value = self._initial_value
        self._first = True
        return self

    def __next__(self) -> V:
        if self._first:
            self._first = False
            return self._current_value  # Yield initial value first

        next_element = next(self._iterator)  # Get next element from source
        self._current_value = self._accumulator(self._current_value, next_element)
        return self._current_value


class _PairIterable(Generic[T, V], Iterator[Pair[T, V]], Iterable[Pair[T, V]]):
    __slots__ = ["_it1", "_it2", "_iter1", "_iter2"]

    def __init__(self, it1: Iterable[T], it2: Iterable[V]) -> None:
        self._it1 = it1
        self._it2 = it2
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()

    def __iter__(self) -> Iterator[Pair[T, V]]:
        self._iter1 = self._it1.__iter__()
        self._iter2 = self._it2.__iter__()
        return self

    def __next__(self) -> Pair[T, V]:
        return Pair(self._iter1.__next__(), self._iter2.__next__())


class _MultiConcatIterable(Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("_iterables", "_current_iterator", "_iterable_index")

    def __init__(self, iterables: tuple[Iterable[T], ...]) -> None:
        self._iterables = iterables
        self._iterable_index = 0
        self._current_iterator: Optional[Iterator[T]] = None
        self._advance_iterator()  # Initialize the first iterator

    def _advance_iterator(self) -> None:
        """Moves to the next iterator in the sequence."""
        if self._iterable_index < len(self._iterables):
            self._current_iterator = iter(self._iterables[self._iterable_index])
            self._iterable_index += 1
        else:
            self._current_iterator = None  # No more iterables

    def __iter__(self) -> Iterator[T]:
        # Reset state for new iteration
        self._iterable_index = 0
        self._advance_iterator()
        return self

    def __next__(self) -> T:
        while self._current_iterator is not None:
            try:
                return next(self._current_iterator)
            except StopIteration:
                # Current iterator is exhausted, move to the next one
                self._advance_iterator()
        # If _current_iterator becomes None, all iterables are exhausted
        raise StopIteration


class _PairwiseIterable(Generic[T], Iterator[Pair[T, T]], Iterable[Pair[T, T]]):
    __slots__ = ("_iterator", "_previous", "_first_element_consumed", "_iterable")

    def __init__(self, it: Iterable[T]) -> None:
        self._iterable = it  # Store original iterable if re-iteration needed
        self._iterator = iter(self._iterable)
        self._previous: Optional[T] = None
        self._first_element_consumed = False

    def __iter__(self) -> Iterator[Pair[T, T]]:
        self._iterator = iter(self._iterable)  # Reset iterator
        self._previous = None
        self._first_element_consumed = False
        return self

    def __next__(self) -> Pair[T, T]:
        if not self._first_element_consumed:
            # Consume the very first element to establish the initial 'previous'
            try:
                self._previous = next(self._iterator)
                self._first_element_consumed = True
            except StopIteration:
                # Stream had 0 or 1 element, so no pairs can be formed
                raise StopIteration

        # Get the next element to form a pair with the previous one
        current = next(self._iterator)  # Raises StopIteration when done
        pair_to_yield = Pair(
            require_non_null(self._previous), current
        )  # require_non_null is safe here
        self._previous = current  # Update previous for the next iteration
        return pair_to_yield


class _SlidingWindowIterable(Generic[T], Iterator[list[T]], Iterable[list[T]]):
    __slots__ = ("_iterator", "_size", "_step", "_window", "_buffer")

    def __init__(self, it: Iterable[T], size: int, step: int) -> None:
        if size <= 0 or step <= 0:
            raise ValueError("Size and step must be positive")
        self._iterator = iter(it)
        self._size = size
        if step <= 0:
            raise ValueError("Step must be positive")
        self._step = step
        # Use deque for efficient additions/removals from both ends
        self._window: deque[T] = deque(maxlen=size)

    def __iter__(self) -> Iterator[list[T]]:
        # Resetting requires re-iterating the source
        # self._iterator = iter(self._iterable) # If storing original iterable
        self._window.clear()
        return self

    def __next__(self) -> list[T]:
        while len(self._window) < self._size:
            try:
                element = next(self._iterator)
                self._window.append(element)

            except StopIteration:
                # Not enough elements to form a full window initially or remaining
                if len(self._window) > 0 and len(self._window) < self._size:
                    # Option: yield partial window at the end? Or require full windows?
                    # Current StopIteration implies only full windows.
                    pass  # Let StopIteration be raised below if window is empty
                raise StopIteration

        # Yield the current full window
        result = list(self._window)  # Create list copy

        # Prepare for the next window by sliding
        for _ in range(self._step):
            if not self._window:
                break  # Should not happen if size > 0
            self._window.popleft()  # Remove element(s) from the left

        return result  # Return the window captured before sliding


class _RepeatIterable(Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("_buffered_elements", "_n", "_current_n", "_iterator")

    def __init__(self, it: Iterable[T], n: Optional[int]) -> None:
        # Buffer the original iterable ONCE
        self._buffered_elements = list(it)
        self._n = n  # None means infinite
        self._current_n = 0
        self._iterator = iter(self._buffered_elements)

    def __iter__(self) -> Iterator[T]:
        # Reset for new iteration
        self._current_n = 0
        self._iterator = iter(self._buffered_elements)
        return self

    def __next__(self) -> T:
        try:
            return next(self._iterator)
        except StopIteration:
            # End of current cycle reached
            if self._n is not None:  # Finite repetitions
                self._current_n += 1
                if self._current_n >= self._n:
                    raise StopIteration  # Max repetitions reached
            # Start next cycle
            if not self._buffered_elements:  # Handle empty source
                raise StopIteration
            self._iterator = iter(self._buffered_elements)
            return next(self._iterator)  # Get first element of next cycle


class _IntersperseIterable(Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("_iterator", "_separator", "_needs_separator", "_iterable")

    def __init__(self, it: Iterable[T], separator: T) -> None:
        self._iterable = it  # Store original if re-iteration needed
        self._iterator = iter(self._iterable)
        self._separator = separator
        self._needs_separator = False  # Don't insert before the first element

    def __iter__(self) -> Iterator[T]:
        self._iterator = iter(self._iterable)  # Reset
        self._needs_separator = False
        return self

    def __next__(self) -> T:
        if self._needs_separator:
            self._needs_separator = False  # Reset flag after yielding separator
            return self._separator
        else:
            # Get the next actual element from the source
            next_element = next(
                self._iterator
            )  # Raises StopIteration when source is done
            # Set flag to insert separator *before* the *next* element
            self._needs_separator = True
            return next_element


class _UnfoldIterable(Generic[T, S], Iterator[T], Iterable[T]):
    __slots__ = ("_initial_seed", "_generator", "_current_seed", "_next_pair")

    def __init__(self, seed: S, generator: Callable[[S], Optional[Pair[T, S]]]) -> None:
        self._initial_seed = seed
        self._generator = generator
        # State for iteration
        self._current_seed = self._initial_seed
        self._next_pair: Optional[Pair[T, S]] = self._generator(
            self._current_seed
        )  # Compute first pair

    def __iter__(self) -> Iterator[T]:
        # Reset state for new iteration
        self._current_seed = self._initial_seed
        self._next_pair = self._generator(self._current_seed)
        return self

    def __next__(self) -> T:
        if self._next_pair is None:
            raise StopIteration  # Generator signaled end

        # Get current element and next seed from the pair
        current_element = self._next_pair.left()
        next_seed = self._next_pair.right()

        # Update state for the *next* call to __next__
        self._current_seed = next_seed
        self._next_pair = self._generator(self._current_seed)

        return current_element  # Return the element generated in the previous step


class _ZipLongestIterable(
    Generic[T, V],
    Iterator[Pair[Optional[T], Optional[V]]],
    Iterable[Pair[Optional[T], Optional[V]]],
):
    __slots__ = ("_it1", "_it2", "_iter1", "_iter2", "_fillvalue", "_done1", "_done2")

    def __init__(
        self, it1: Iterable[T], it2: Iterable[V], fillvalue: Any = None
    ) -> None:
        self._it1 = it1
        self._it2 = it2
        self._fillvalue = fillvalue
        self._iter1 = iter(self._it1)
        self._iter2 = iter(self._it2)
        self._done1 = False
        self._done2 = False

    def __iter__(self) -> Iterator[Pair[Optional[T], Optional[V]]]:
        self._iter1 = iter(self._it1)
        self._iter2 = iter(self._it2)
        self._done1 = False
        self._done2 = False
        return self

    def __next__(self) -> Pair[Optional[T], Optional[V]]:
        val1: Optional[T] = self._fillvalue
        val2: Optional[V] = self._fillvalue

        if not self._done1:
            try:
                val1 = next(self._iter1)
            except StopIteration:
                self._done1 = True

        if not self._done2:
            try:
                val2 = next(self._iter2)
            except StopIteration:
                self._done2 = True

        if self._done1 and self._done2:
            raise StopIteration

        return Pair(val1, val2)


class _CycleIterable(Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("_elements", "_n", "_current_n", "_iterator")

    def __init__(self, it: Iterable[T], n: Optional[int]) -> None:
        self._n: Optional[int] = n
        self._elements = list(it)  # Buffer elements
        if not self._elements and n is not None and n > 0:
            # Cannot cycle an empty iterable a fixed number of times > 0
            # If n is None (infinite) or n is 0, an empty iterable source is fine (results in empty stream).
            self._elements = []  # Ensure it's empty and will stop immediately
            self._n = 0  # Force stop
        else:
            self._n = n
        self._current_n = 0
        self._iterator = iter(self._elements)

    def __iter__(self) -> Iterator[T]:
        self._current_n = 0
        if not self._elements:  # Handle empty iterable source
            self._iterator = iter([])  # Empty iterator
        else:
            self._iterator = iter(self._elements)
        return self

    def __next__(self) -> T:
        if not self._elements:  # If original iterable was empty
            raise StopIteration

        try:
            return next(self._iterator)
        except StopIteration:
            if self._n is not None:
                self._current_n += 1
                if self._current_n >= self._n:
                    raise StopIteration
            # Reset for next cycle (will raise StopIteration if _elements is empty,
            # but we've guarded against that if n > 0)
            self._iterator = iter(self._elements)
            return next(self._iterator)


class _DeferIterable(Generic[T], Iterator[T], Iterable[T]):
    __slots__ = ("_supplier", "_current_iterator")

    def __init__(self, supplier: Callable[[], Iterable[T]]) -> None:
        self._supplier = supplier
        self._current_iterator: Optional[Iterator[T]] = None  # Initialized in __iter__

    def __iter__(self) -> Iterator[T]:
        self._current_iterator = iter(
            self._supplier()
        )  # Call supplier and get iterator
        return self

    def __next__(self) -> T:
        if self._current_iterator is None:
            raise RuntimeError(
                "Iterator not initialized. __iter__ must be called first."
            )
        return next(self._current_iterator)


class Stream(Generic[T]):
    __slots__ = ("__arg",)

    def __init__(self, arg: Iterable[T]) -> None:
        self.__arg = require_non_null(arg)

    @staticmethod
    def of(arg: Iterable[T]) -> "Stream[T]":
        """
        Creates a stream from an iterable. Much in the same way as when calling the Stream constructor, the
        type of the stream is inferred from the type of the iterable.
        This method is useful when you want to create a stream from an iterable without explicitly specifying
        the type of the stream. It allows for more concise code and can be used in situations where the type
        of the iterable is known but the type of the stream is not.

        Args:
            arg (Iterable[T]): The iterable to create the stream from
        Returns:
            Stream[T]: The stream
        """
        return Stream(arg)

    @staticmethod
    def of_nullable(arg: Iterable[Optional[T]]) -> "Stream[T]":
        """
        Creates a stream from an iterable of optional values, filtering out None values.
        This method is useful when you want to create a stream from an iterable that may contain None values,
        and you want to filter them out. It allows for more concise code and can be used in situations where
        the type of the iterable is known to be optional, but the resulting stream needs to be of non-null elements.

        Args:
            arg (Iterable[Optional[T]]): The iterable of optional values
        Returns:
            Stream[T]: The stream of non-null values
        """
        return Stream(arg).filter(is_not_none).map(lambda el: require_non_null(el))

    @staticmethod
    def cycle(iterable: Iterable[T], n: Optional[int] = None) -> "Stream[T]":
        """
        Creates a stream that cycles over the elements of an iterable.

        The elements of the input iterable are buffered. The stream will then
        repeat these buffered elements.

        Args:
            iterable (Iterable[T]): The iterable whose elements are to be cycled.
            n (Optional[int]): The number of times to cycle through the iterable.
                If None (default), cycles indefinitely.
                If 0, results in an empty stream.
                If the input iterable is empty and n > 0, an empty stream is also produced.

        Returns:
            Stream[T]: A stream that cycles through the elements of the iterable.

        Raises:
            ValueError: If n is specified and is negative.
        """
        if n is not None and n < 0:
            raise ValueError("Number of repetitions 'n' must be non-negative.")
        if n == 0:
            return Stream.empty()
        return Stream(_CycleIterable(iterable, n))

    @staticmethod
    def of_dict_keys(dictionary: dict[K, Any]) -> "Stream[K]":
        """
        Creates a stream from the keys of the given dictionary.
        """
        return Stream(dictionary.keys())

    @staticmethod
    def of_dict_values(dictionary: dict[Any, V]) -> "Stream[V]":
        """
        Creates a stream from the values of the given dictionary.
        """
        return Stream(dictionary.values())

    @staticmethod
    def of_dict_items(dictionary: dict[K, V]) -> "Stream[Pair[K, V]]":
        """
        Creates a stream of Pair(key, value) from the items of the given dictionary.
        """
        return Stream(dictionary.items()).map(pair_of)

    @staticmethod
    def defer(supplier: Callable[[], Iterable[T]]) -> "Stream[T]":
        """
        Creates a stream whose underlying iterable is obtained by calling the
        supplier function only when the stream is iterated.
        """
        return Stream(_DeferIterable(supplier))

    def map(self, mapper: Union[Mapper[T, V], Callable[[T], V]]) -> "Stream[V]":
        """
        Produces a new stream by mapping the stream elements using the given mapper function.
        Args:
            mapper (Union[Mapper[T, V], Callable[[T], V]]): The mapper

        Returns:
            Stream[V]: The result stream
        """
        return Stream(_MapIterable(self.__arg, mapper_of(mapper)))

    def zip_longest(
        self, other: Iterable[V], fillvalue: Any = None
    ) -> "Stream[Pair[Optional[T], Optional[V]]]":
        """
        Zips this stream with another iterable, producing a stream of Pairs.
        Continues until the longest iterable is exhausted, filling missing
        values with `fillvalue`.

        Args:
            other: The iterable to zip with this stream.
            fillvalue: The value to use for missing elements from shorter iterables.
                        Defaults to None.

        Returns:
            Stream[Pair[Optional[T], Optional[V]]]: A stream of pairs, potentially
                                                    containing the fillvalue.
        """
        # Note: The Pair type hints need to reflect the Optional nature
        # Pair[Optional[T], Optional[V]] is correct.
        return Stream(_ZipLongestIterable(self.__arg, other, fillvalue))

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

    def scan(self, accumulator: Callable[[V, T], V], initial_value: V) -> "Stream[V]":
        """
        Performs a cumulative reduction operation on the stream elements,
        yielding each intermediate result, starting with the initial_value.

        Example:
            Stream([1, 2, 3]).scan(lambda acc, x: acc + x, 0).to_list()
            # Output: [0, 1, 3, 6]

        Args:
            accumulator: A function that takes the current accumulated value (V)
                        and the next element (T), returning the new accumulated value (V).
            initial_value: The initial value for the accumulation (V).

        Returns:
            Stream[V]: A stream of the intermediate accumulated values.
        """
        return Stream(_ScanIterable(self.__arg, accumulator, initial_value))

    def zip(self, other: Iterable[V]) -> "Stream[Pair[T, V]]":
        """
        Zips this stream with another iterable, producing a stream of Pairs.
        The resulting stream's length is the minimum of the lengths of the
        two input iterables.

        Args:
            other: The iterable to zip with this stream.

        Returns:
            Stream[Pair[T, V]]: A stream of pairs.
        """
        # Delegate to the pair_stream factory function
        return pair_stream(self.__arg, other)

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

    def to_tuple(self) -> tuple[T, ...]:
        """
        Collects the elements of the stream into a tuple.
        This is a terminal operation.

        Returns:
            tuple[T, ...]: A tuple containing the stream elements in order.
        """
        return tuple(self.__arg)

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
        self,
        predicate: Union[Predicate[T], Callable[[T], bool]],
        include_stop_value: bool = False,
    ) -> "Stream[T]":
        """
        Returns a stream of elements until the first element that DOES NOT match the given predicate

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(
            _TakeWhileIterable(self.__arg, predicate_of(predicate), include_stop_value)
        )

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

    def take_until(
        self,
        predicate: Union[Predicate[T], Callable[[T], bool]],
        include_stop_value: bool = False,
    ) -> "Stream[T]":
        """
        Returns a stream consisting of elements taken from this stream until
        the predicate returns True for the first time. The element that satisfies
        the predicate IS included in the resulting stream.

        Args:
            predicate: The predicate to test elements against.

        Returns:
            Stream[T]: The resulting stream.
        """
        return Stream(
            _TakeUntilIterable(self.__arg, predicate_of(predicate), include_stop_value)
        )

    def drop_until(
        self, predicate: Union[Predicate[T], Callable[[T], bool]]
    ) -> "Stream[T]":
        """
        Returns a stream consisting of the remaining elements after dropping
        elements until the predicate returns True for the first time. The element
        that satisfies the predicate IS included in the resulting stream.

        Args:
            predicate: The predicate to test elements against.

        Returns:
            Stream[T]: The resulting stream.
        """
        return Stream(_DropUntilIterable(self.__arg, predicate_of(predicate)))

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

    def distinct(self, key: Optional[Callable[[T], Any]] = None) -> "Stream[T]":
        """
        Returns a stream consisting of the distinct elements of this stream.
        Uniqueness is determined by the element itself or by the result of applying the key function.

        CAUTION: For objects without a key function, ensure `__eq__` and `__hash__` are properly implemented.
                 This operation requires storing seen keys/elements, potentially consuming memory.

        Args:
            key (Optional[Callable[[T], Ay]]): A function to extract the key for uniqueness comparison. If None, the element itself is used. Defaults to None.
        """
        return Stream(_DistinctIterable(self.__arg, key))

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

    def peek(
        self,
        action: Callable[[T], Any],
        logger: Optional[Callable[[Exception], Any]] = None,
    ) -> "Stream[T]":
        """
        Performs an action on each element of the stream as it passes through.
        Useful for debugging or logging intermediate values. Does not modify the stream elements.

        Args:
            action (Callable[[T], Any]): The action to perform on each element.

        Returns:
            Stream[T]: The same stream, allowing further chaining.
        """
        return Stream(_PeekIterable(self.__arg, action, logger))

    def count(self) -> int:
        """
        Counts the number of elements in the stream.
        This is a terminal operation and consumes the stream.

        Returns:
            int: The total number of elements.
        """
        # Using sum() with a generator expression is often efficient
        # Alternatively, iterate and count manually.
        # This approach avoids creating an intermediate list like len(self.to_list())
        count = 0
        for _ in self.__arg:
            count += 1
        return count

    def indexed(self) -> "Stream[Pair[int, T]]":
        """
        Returns a stream consisting of pairs of (index, element).
        The index is zero-based.

        Returns:
            Stream[Pair[int, T]]: A stream of index-element pairs.
        """
        return Stream(_IndexedIterable(self.__arg))

    # Alias for familiarity
    def enumerate(self) -> "Stream[Pair[int, T]]":
        """Alias for indexed()."""
        return self.indexed()

    def chunked(self, size: int) -> "Stream[list[T]]":
        """
        Groups elements of the stream into chunks (lists) of a specified size.
        The last chunk may contain fewer elements than the specified size.

        Args:
            size (int): The desired size of each chunk. Must be positive.

        Returns:
            Stream[list[T]]: A stream where each element is a list (chunk).

        Raises:
            ValueError: If size is not positive.
        """
        return Stream(_ChunkedIterable(self.__arg, size))

    def find_last(self, predicate: Union[Predicate[T], Callable[[T], bool]]) -> Opt[T]:
        """
        Finds the last element in the stream that matches the given predicate.
        This is a terminal operation and consumes the stream.

        Args:
            predicate (Union[Predicate[T], Callable[[T], bool]]): The predicate to match.

        Returns:
            Opt[T]: An Opt containing the last matching element, or empty if none match or the stream is empty.
        """
        last_match: Optional[T] = None
        pred = predicate_of(predicate)
        for element in self.__arg:
            if pred.apply(element):
                last_match = element
        return Opt(last_match)

    @staticmethod
    def range(start: int, stop: Optional[int] = None, step: int = 1) -> "Stream[int]":
        """
        Creates a stream of integers from a range, similar to Python's range().

        Args:
            start: The starting value (or stop value if stop is None).
            stop: The stopping value (exclusive). If None, range is from 0 to start.
            step: The step between values. Defaults to 1.

        Returns:
            Stream[int]: A stream of integers.
        """
        if stop is None:
            # Mimic range(stop) behavior
            return Stream(range(start))
        else:
            # Mimic range(start, stop, step) behavior
            return Stream(range(start, stop, step))

    @staticmethod
    def iterate(initial_value: T, next_value_fn: Callable[[T], T]) -> "Stream[T]":
        """
        Creates an infinite ordered stream produced by iterative application
        of a function f to an initial element seed.
        Produces seed, f(seed), f(f(seed)), etc.

        Example:
            Stream.iterate(0, lambda x: x + 2).limit(5).to_list()
            # Output: [0, 2, 4, 6, 8]

        Args:
            initial_value: The initial element.
            next_value_fn: A function to be applied to the previous element to produce the next element.

        Returns:
            Stream[T]: An infinite stream. Remember to use limit() or take_while() etc.
        """
        return Stream(_iterate_generator(initial_value, next_value_fn))

    @staticmethod
    def generate(supplier: Callable[[], T]) -> "Stream[T]":
        """
        Creates an infinite unordered stream where each element is generated
        by the provided supplier function.

        Example:
            import random
            Stream.generate(lambda: random.randint(1, 10)).limit(5).to_list()
            # Output: [e.g., 7, 2, 9, 1, 5]

        Args:
            supplier: A function that produces elements for the stream.

        Returns:
            Stream[T]: An infinite stream. Remember to use limit() or take_while() etc.
        """
        return Stream(_generate_generator(supplier))

    @staticmethod
    def empty() -> "Stream[Any]":  # Use Any as type T isn't bound here
        """
        Returns an empty sequential Stream.

        Returns:
            Stream[Any]: An empty stream.
        """
        # Could potentially cache a single empty stream instance
        return Stream([])

    @staticmethod
    def concat_of(*iterables: Iterable[T]) -> "Stream[T]":
        """
        Creates a lazily concatenated stream whose elements are all the
        elements of the first iterable followed by all the elements of the
        second iterable, and so on.

        Args:
            *iterables: The iterables to concatenate.

        Returns:
            Stream[T]: The concatenated stream.
        """
        if not iterables:
            return Stream.empty()
        # If only one iterable, just return a stream of it
        if len(iterables) == 1:
            return Stream(iterables[0])
        return Stream(_MultiConcatIterable(iterables))

    def pairwise(self) -> "Stream[Pair[T, T]]":
        """
        Returns a stream of pairs consisting of adjacent elements from this stream.
        If the stream has N elements, the resulting stream will have N-1 elements.
        Returns an empty stream if the original stream has 0 or 1 element.

        Example:
            Stream([1, 2, 3, 4]).pairwise().to_list()
            # Output: [Pair(1, 2), Pair(2, 3), Pair(3, 4)]

        Returns:
            Stream[Pair[T, T]]: A stream of adjacent pairs.
        """
        return Stream(_PairwiseIterable(self.__arg))

    def sliding_window(self, size: int, step: int = 1) -> "Stream[list[T]]":
        """
        Returns a stream of lists, where each list is a sliding window of
        elements from the original stream.

        Example:
            Stream([1, 2, 3, 4, 5]).sliding_window(3, 1).to_list()
            # Output: [[1, 2, 3], [2, 3, 4], [3, 4, 5]]

            Stream([1, 2, 3, 4, 5]).sliding_window(2, 2).to_list()
            # Output: [[1, 2], [3, 4]] (depends on exact end behavior)


        Args:
            size (int): The size of each window. Must be positive.
            step (int, optional): The number of elements to slide forward for
                                the next window. Defaults to 1. Must be positive.

        Returns:
            Stream[list[T]]: A stream of lists representing the sliding windows.

        Raises:
            ValueError: If size or step are not positive.
        """
        # NOTE: The _SlidingWindowIterable implementation above is complex and might need refinement
        # for full correctness and laziness, especially around edge cases and step > size.
        # Consider starting with a simpler implementation if needed.
        return Stream(_SlidingWindowIterable(self.__arg, size, step))

    def any_none(self) -> bool:
        """
        Checks if any element in this stream is None.
        This is a terminal operation and may short-circuit.

        Returns:
            bool: True if at least one element is None, False otherwise.
        """
        return self.any_match(is_none)

    def none_none(self) -> bool:
        """
        Checks if no element in this stream is None.
        Equivalent to `all_not_none()`.
        This is a terminal operation and may short-circuit.

        Returns:
            bool: True if no elements are None, False otherwise.
        """
        return self.none_match(is_none)

    @staticmethod
    def of_items(*items: T) -> "Stream[T]":
        """
        Creates a stream from the provided items.

        Example:
            Stream.of_items(1, 2, 3).map(lambda x: x * 2).to_list()
            # Output: [2, 4, 6]

        Args:
            *items: The items to include in the stream.

        Returns:
            Stream[T]: A stream containing the provided items.
        """
        return Stream(items)  # Pass the tuple of items directly

    def repeat(self, n: Optional[int] = None) -> "Stream[T]":
        """
        Returns a stream that repeats the elements of this stream n times,
        or indefinitely if n is None.

        CAUTION: This operation needs to buffer the original stream elements
                to allow repetition, which might consume significant memory
                for large streams. It should not be used on infinite streams
                unless n is specified and finite.

        Args:
            n (Optional[int]): The number of times to repeat the stream.
                            If None, repeats indefinitely. Defaults to None.

        Returns:
            Stream[T]: A stream consisting of the repeated elements.

        Raises:
            ValueError: If n is specified and is not positive.
        """
        if n is not None and n <= 0:
            raise ValueError("Number of repetitions 'n' must be positive if specified.")
        # The _RepeatIterable buffers the original self.__arg
        return Stream(_RepeatIterable(self.__arg, n))

    def intersperse(self, separator: T) -> "Stream[T]":
        """
        Returns a stream with the separator element inserted between each
        element of this stream.

        Example:
            Stream([1, 2, 3]).intersperse(0).to_list()
            # Output: [1, 0, 2, 0, 3, 0]

            Stream(["a", "b"]).intersperse("-").to_list()
            # Output: ["a", "-", "b", "-"]

            Stream([]).intersperse(0).to_list()
            # Output: []

            Stream([1]).intersperse(0).to_list()
            # Output: [1, 0]

        Args:
            separator (T): The element to insert between original elements.

        Returns:
            Stream[T]: The resulting stream with separators.
        """
        return Stream(_IntersperseIterable(self.__arg, separator))

    @staticmethod
    def unfold(seed: S, generator: Callable[[S], Optional[Pair[T, S]]]) -> "Stream[T]":
        """
        Creates a stream by repeatedly applying a generator function to a seed value.

        The generator function takes the current state (seed) and returns an
        Optional Pair containing the next element for the stream and the next state (seed).
        The stream terminates when the generator returns None.

        Example (Fibonacci sequence):
            def fib_generator(state: Pair[int, int]) -> Optional[Pair[int, Pair[int, int]]]:
                a, b = state.left(), state.right()
                return Pair(a, Pair(b, a + b)) # Yield a, next state is (b, a+b)

            Stream.unfold(Pair(0, 1), fib_generator).limit(10).to_list()
            # Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

        Example (Range):
            def range_generator(current: int) -> Optional[Pair[int, int]]:
                if current >= 10:
                    return None
                return Pair(current, current + 1) # Yield current, next state is current + 1

            Stream.unfold(0, range_generator).to_list()
            # Output: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


        Args:
            seed (S): The initial state.
            generator (Callable[[S], Optional[Pair[T, S]]]): Function that takes the
                current state and returns an Optional Pair(next_element, next_state).

        Returns:
            Stream[T]: The generated stream.
        """
        return Stream(_UnfoldIterable(seed, generator))


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


def pair_stream(left: Iterable[T], right: Iterable[V]) -> Stream[Pair[T, V]]:
    """
    Create a pair stream by zipping two iterables. The resulting stream will have the length
    of the shortest iterable.

    Args:
        left (Iterable[T]): The left iterable
        right (Iterable[V]): The right iterable

    Returns:
        Stream[Pair[T, V]]: The resulting pair stream
    """
    return Stream(_PairIterable(left, right))


def _generate_generator(supplier: Callable[[], T]) -> Iterator[T]:
    while True:
        yield supplier()


def _iterate_generator(
    initial_value: T, next_value_fn: Callable[[T], T]
) -> Iterator[T]:
    current = initial_value
    while True:
        yield current
        current = next_value_fn(current)
