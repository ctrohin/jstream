from typing import (
    Any,
    Optional,
    TypeVar,
    Generic,
    cast,
    final,
)
from collections.abc import Callable, Iterable, Iterator
from jstreams.class_operations import ClassOps
import itertools
from jstreams.iterable_operations import (
    all_match,
    any_match,
    find_first,
    find_last,
    none_match,
    reduce,
)
from jstreams.iterables import (
    cast_to,
    chunked,
    concat,
    concat_of,
    cycle,
    defer,
    distinct,
    drop_until,
    drop_while,
    filter_it,
    group_adjacent,
    indexed,
    intersperse,
    limit,
    map_indexed,
    map_it,
    pair_it,
    pairwise,
    peek,
    repeat,
    scan,
    skip,
    sliding_window,
    take_until,
    take_while,
    unfold,
    windowed,
    zip_longest,
)
from jstreams.mapper import flat_map
from jstreams.predicate import (
    is_none,
)
from jstreams.tuples import Pair, pair_of
from jstreams.utils import is_not_none, require_non_null, each, is_empty_or_none, sort

A = TypeVar("A")
B = TypeVar("B")

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")
L = TypeVar("L")
S = TypeVar("S")
U = TypeVar("U")


@final
class Opt(Generic[T]):
    __slots__ = ("__val",)
    __NONE: "Optional[Opt[Any]]" = None

    def __init__(self, val: Optional[T]) -> None:
        self.__val = val

    def __get_none(self) -> "Opt[T]":
        if Opt.__NONE is None:
            Opt.__NONE = Opt(None)
        return cast(Opt[T], Opt.__NONE)

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, Opt):
            return False
        return self.__val == value.__val

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
        return self.__get_none()

    def filter_with(self, with_val: K, predicate: Callable[[T, K], bool]) -> "Opt[T]":
        """
        Returns the filtered value of the Opt if it matches the given predicate, by
        providing the predicat with an additional value

        Args:
            with_val (K): the additional value
            predicate (Callable[[T, K], bool]): The predicate

        Returns:
            Opt[T]: The resulting Opt
        """
        if self.__val is None:
            return self
        if predicate(self.__val, with_val):
            return self
        return self.__get_none()

    def map(self, mapper: Callable[[T], V]) -> "Opt[V]":
        """
        Maps the Opt value into another Opt by applying the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function

        Returns:
            Opt[V]: The resulting Opt
        """
        if self.__val is None:
            return cast(Opt[V], self.__get_none())
        return Opt(mapper(self.__val))

    def map_with(self, with_val: K, mapper: Callable[[T, K], V]) -> "Opt[V]":
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
        return Opt(mapper(self.__val, with_val))

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
        predicate: Callable[[T], bool],
        action: Callable[[T], Any],
    ) -> "Opt[T]":
        """
        Executes the given action on the value of this Opt, if the value is present and
        matches the given predicate. Returns the same Opt

        Args:
            predicate (Callable[[T], bool]): The predicate
            action (Callable[[T], Any]): The action to be executed

        Returns:
            Opt[T]: The same Opt
        """
        if self.__val is not None and predicate(self.__val):
            action(self.__val)
        return self

    def if_matches_opt(
        self,
        predicate: Callable[[Optional[T]], bool],
        action: Callable[[Optional[T]], Any],
    ) -> "Opt[T]":
        """
        Executes the given action on the value of this Opt, regardless of whether the value
        is present, if the value matches the given predicate. Returns the same Opt

        Args:
            predicate (Callable[[Optional[T]], bool]): The predicate
            action (Callable[[Optional[T]], Any]): The action to be executed

        Returns:
            Opt[T]: The same Opt
        """
        if predicate(self.__val):
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

    def flat_stream(self, typ: type[V]) -> "Stream[V]":  # pylint: disable=unused-argument
        """
        Returns a Stream containing the current Opt value if the value
        is not an Iterable, or a Stream containing all the values in
        the Opt if the Opt contains an iterable

        Args:
            typ: (type[V]): The type of the resulting stream
        Returns:
            Stream[V]: The resulting Stream
        """
        if self.__val is not None:
            if isinstance(self.__val, Iterable):
                return Stream(self.__val)
            return Stream([self.__val])  # type: ignore[list-item]
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
        is_present_mapper: Callable[[T], V],
        or_else_supplier: Callable[[], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by is_present_mapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by or_else_supplier

        Args:
            is_present_mapper (Callable[[T], V]): The presence mapper
            or_else_supplier (Callable[[], Optional[V]]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(or_else_supplier())
        return Opt(is_present_mapper(self.__val))

    def if_present_map_with(
        self,
        with_val: K,
        is_present_mapper: Callable[[T, K], V],
        or_else_supplier: Callable[[K], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present, returns the value mapped by is_present_mapper wrapped in an Opt.
        If the optional value is not present, returns the value produced by or_else_supplier.
        In addition to ifPresentMap, this method also passes the with_val param to the mapper and supplier

        Args:
            with_val (K): The additional mapper value
            is_present_mapper (Callable[[T, K], V]): The presence mapper
            or_else_supplier (Callable[[K], V]): The missing value producer

        Returns:
            Opt[V]: An optional
        """
        if self.__val is None:
            return Opt(or_else_supplier(with_val))
        return Opt(is_present_mapper(self.__val, with_val))

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

    def cast(self, class_type: type[V]) -> "Opt[V]":  # pylint: disable=unused-argument
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
        predicate: Callable[[T], bool],
        mapper: Callable[[T], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present and matches the given predicate, returns the value mapped
        by mapper wrapped in an Opt.
        If the optional value is not present, returns an empty Opt.

        Args:
            predicate (Callable[[T], bool]): The predicate
            mapper (Callable[[T], Optional[V]]): The the mapper

        Returns:
            Opt[V]: An optional
        """
        if self.__val is not None and predicate(self.__val):
            return Opt(mapper(self.__val))
        return cast(Opt[V], self.__get_none())

    def if_matches_map_with(
        self,
        with_val: K,
        predicate: Callable[[T, K], bool],
        mapper: Callable[[T, K], Optional[V]],
    ) -> "Opt[V]":
        """
        If the optional value is present and matches the given predicate, returns the value mapped by mapper wrapped in an Opt.
        If the optional value is not present, returns an empty Opt.
        In addition to ifMatchesMap, this method also passes the withVal param to the mapper and supplier

        Args:
            with_val (K): The additional mapper value
            predicate (Callable[[T, K], bool]): The predicate
            mapper (Callable[[T, K], Optional[V]]): The mapper

        Returns:
            Opt[V]: An optional
        """
        if self.__val is not None and predicate(self.__val, with_val):
            return Opt(mapper(self.__val, with_val))
        return cast(Opt[V], self.__get_none())

    def flatten(self, typ: type[U]) -> "Opt[U]":  # pylint: disable=unused-argument
        """
        Flattens a nested Opt[Opt[U]] into Opt[U].
        If the outer Opt is empty, or the inner Opt is empty, returns an empty Opt.
        Args:
            typ (type[U]): The type of the returned opt
        Returns:
            Opt[U]: The flattened Opt.
        """
        if self.is_present():
            inner_opt = self.__val  # self.__val is Opt[U] here
            if isinstance(inner_opt, Opt):
                return inner_opt  # Return the inner Opt[U]
            # This case shouldn't happen if type hints are correct,
            # but defensively return empty if the contained value isn't an Opt.
            # Or perhaps raise a TypeError? Returning empty seems safer.
            return cast(Opt[U], self.__get_none())
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

    def unzip(self, left_type: type[A], right_type: type[B]) -> "Pair[Opt[A], Opt[B]]":  # pylint: disable=unused-argument
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
            # Should not happen with correct types, return pair of empty
            return Pair(
                cast(Opt[A], self.__get_none()), cast(Opt[B], self.__get_none())
            )
        return Pair(cast(Opt[A], self.__get_none()), cast(Opt[B], self.__get_none()))

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


@final
class Stream(Generic[T]):
    __slots__ = ("__arg",)

    def __init__(self, arg: Iterable[T]) -> None:
        self.__arg = require_non_null(arg)

    def map(self, mapper: Callable[[T], V]) -> "Stream[V]":
        """
        Produces a new stream by mapping the stream elements using the given mapper function.
        Args:
            mapper (Callable[[T], V]): The mapper

        Returns:
            Stream[V]: The result stream
        """
        return Stream(map_it(self.__arg, mapper))

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
        return Stream(zip_longest(self.__arg, other, fillvalue))

    def flat_map(self, mapper: Callable[[T], Iterable[V]]) -> "Stream[V]":
        """
        Produces a flat stream by mapping an element of this stream to an iterable, then concatenates
        the iterables into a single stream.
        Args:
            mapper (Callable[[T], Iterable[V]]): The mapper

        Returns:
            Stream[V]: the result stream
        """
        return Stream(flat_map(self.__arg, mapper))

    def flatten(self, typ: type[V]) -> "Stream[V]":  # pylint: disable=unused-argument
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

    def find_first(self, predicate: Callable[[T], bool]) -> Opt[T]:
        """
        Finds and returns the first element matching the predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Opt[T]: The firs element found
        """
        return Opt(find_first(self.__arg, predicate))

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Returns a stream of objects that match the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Stream[T]: The stream of filtered objects
        """

        return Stream(filter_it(self.__arg, predicate))

    def cast(self, cast_to_type: type[V]) -> "Stream[V]":
        """
        Returns a stream of objects casted to the given type. Useful when receiving untyped data lists
        and they need to be used in a typed context.

        Args:
            cast_to_type (type[V]): The type all objects will be casted to

        Returns:
            Stream[V]: The stream of casted objects
        """
        return Stream(cast_to(self.__arg, cast_to_type))

    def any_match(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks if any stream object matches the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            bool: True if any object matches, False otherwise
        """
        return any_match(self.__arg, predicate)

    def none_match(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks if none of the stream objects matches the given predicate. This is the inverse of 'any_match`

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            bool: True if no object matches, False otherwise
        """
        return none_match(self.__arg, predicate)

    def all_match(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks if all of the stream objects matche the given predicate.

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            bool: True if all objects matche, False otherwise
        """
        return all_match(self.__arg, predicate)

    def is_empty(self) -> bool:
        """
        Checks if the stream is empty

        Returns:
            bool: True if the stream is empty, False otherwise
        """
        return is_empty_or_none(self.__arg)

    def is_not_empty(self) -> bool:
        """
        Checks if the stream is not empty

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
        return Stream(scan(self.__arg, accumulator, initial_value))

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
        key_mapper: Callable[[T], V],
        value_mapper: Callable[[T], K],
    ) -> dict[V, K]:
        """
        Creates a dictionary with the contents of the stream creating keys using
        the given key mapper and values using the value mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            key_mapper (Callable[[T], V]): The key mapper
            value_mapper (Callable[[T], K]): The value mapper

        Returns:
            dict[V, K]: The resulting dictionary
        """
        return {key_mapper(v): value_mapper(v) for v in self.__arg}

    def to_dict_as_values(self, key_mapper: Callable[[T], V]) -> dict[V, T]:
        """
        Creates a dictionary with the contents of the stream creating keys using
        the given key mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            key_mapper (Callable[[T], V]): The key mapper

        Returns:
            dict[V, T]: The resulting dictionary
        """
        return {key_mapper(v): v for v in self.__arg}

    def to_dict_as_keys(self, value_mapper: Callable[[T], V]) -> dict[T, V]:
        """
        Creates a dictionary using the contents of the stream as keys and mapping
        the dictionary values using the given value mapper
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            value_mapper (Callable[[T], V]): The value mapper

        Returns:
            dict[V, T]: The resulting dictionary
        """
        return {v: value_mapper(v) for v in self.__arg}

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
        Returns all items of the exact given type as a stream. Subclasses will not
        be considered of the exact same type

        Args:
            the_type (type[V]): The given type

        Returns:
            Stream[V]: The result stream
        """
        return self.filter(ClassOps(the_type).type_equals).cast(the_type)

    def instances_of(self, the_type: type[V]) -> "Stream[V]":
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
        return Stream(skip(self.__arg, count))

    def limit(self, count: int) -> "Stream[T]":
        """
        Returns a stream limited to the first 'count' items of this stream

        Args:
            count (int): The max amount of items

        Returns:
            Stream[T]: The result stream
        """
        return Stream(limit(self.__arg, count))

    def take_while(
        self,
        predicate: Callable[[T], bool],
    ) -> "Stream[T]":
        """
        Returns a stream of elements until the first element that DOES NOT match the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(take_while(self.__arg, predicate))

    def drop_while(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Returns a stream of elements by dropping the first elements that match the given predicate

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            Stream[T]: The result stream
        """
        return Stream(drop_while(self.__arg, predicate))

    def take_until(
        self,
        predicate: Callable[[T], bool],
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
        return Stream(take_until(self.__arg, predicate))

    def drop_until(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """
        Returns a stream consisting of the remaining elements after dropping
        elements until the predicate returns True for the first time. The element
        that satisfies the predicate IS included in the resulting stream.

        Args:
            predicate: The predicate to test elements against.

        Returns:
            Stream[T]: The resulting stream.
        """
        return Stream(drop_until(self.__arg, predicate))

    def reduce(self, reducer: Callable[[T, T], T]) -> Opt[T]:
        """
        Reduces a stream to a single value. The reducer takes two values and
        returns only one. This function can be used to find min or max from a stream of ints.
        CAUTION: This method will actually iterate the entire stream, so if you're using
        infinite generators, calling this method will block the execution of the program.

        Args:
            reducer (Callable[[T, T], T]): The reducer

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
        return Stream(distinct(self.__arg, key))

    def concat(self, new_stream: "Stream[T]") -> "Stream[T]":
        """
        Returns a stream concatenating the values from this stream with the ones
        from the given stream.

        Args:
            new_stream (Stream[T]): The stream to be concatenated with

        Returns:
            Stream[T]: The resulting stream
        """
        return Stream(concat(self.__arg, new_stream.__arg))

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
        return Stream(peek(self.__arg, action, logger))

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
        return Stream(indexed(self.__arg))

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
        return Stream(chunked(self.__arg, size))

    def find_last(self, predicate: Callable[[T], bool]) -> Opt[T]:
        """
        Finds the last element in the stream that matches the given predicate.
        This is a terminal operation and consumes the stream.

        Args:
            predicate (Callable[[T], bool]): The predicate to match.

        Returns:
            Opt[T]: An Opt containing the last matching element, or empty if none match or the stream is empty.
        """
        return Opt(find_last(self.__arg, predicate))

    def map_indexed(self, mapper: Callable[[int, T], V]) -> "Stream[V]":
        """
        Applies a mapping function to each element of the stream, along with its index.

        Args:
            mapper: A function that takes the index and the element, and returns a transformed value.

        Returns:
            Stream[V]: A stream of transformed values.
        """
        return Stream(map_indexed(self.__arg, mapper))

    def filter_indexed(self, predicate: Callable[[int, T], bool]) -> "Stream[T]":
        """
        Filters the elements of the stream based on a predicate that takes both the index and the element.

        Args:
            predicate: A function that takes the index and the element, and returns True if the element should be included in the result, False otherwise.

        Returns:
            Stream[T]: A stream of filtered elements.
        """

        def indexed_predicate(element: Pair[int, T]) -> bool:
            return predicate(element.left(), element.right())

        return self.indexed().filter(indexed_predicate).map(lambda p: p.right())

    def group_adjacent(self, key_func: Callable[[T], K]) -> "Stream[list[T]]":
        """
        Groups consecutive elements of the stream that have the same key. The order is preserved.

        Args:
            key_func: A function that extracts a key from each element. Consecutive elements with the same key will be grouped together.

        Returns:
            Stream[list[T]]: A stream of lists, where each list is a group of adjacent elements with the same key.
        """
        return Stream(group_adjacent(self.__arg, key_func))

    def windowed(
        self, size: int, step: int = 1, partial: bool = False
    ) -> "Stream[list[T]]":
        """
        Creates a stream of windows (sublists) from the elements of this stream,
        where each window has a specified size and consecutive windows are
        separated by a specified step.

        Args:
            size (int): The size of each window. Must be positive.
            step (int): The number of elements to move forward for the start of
                       the next window. Defaults to 1 (consecutive windows). Must be positive.
            partial (bool): If True, allows windows that are smaller than 'size'
                           at the end of the stream. If False (default), only windows
                           of exactly 'size' are returned, and any remaining elements
                           that cannot form a full window are discarded.

        Returns:
            Stream[list[T]]: A stream of windows (lists of elements).
        Raises:
            ValueError: If size or step is not positive.
        """
        return Stream(windowed(self.__arg, size, step, partial))

    def pad(self, size: int, value: T) -> "Stream[T]":
        """
        Pads the stream with a specified value until it reaches a desired size.
        If the stream already has the target size or is larger, it's returned unmodified.

        CAUTION: This operation buffers the entire stream up to the padding point,
                 so may consume memory.

        Args:
            size (int): The desired final size of the stream after padding.
                       Must be non-negative.
            value (T): The value to use for padding.

        Returns:
            Stream[T]: The padded stream.

        Raises:
            ValueError: If size is negative.
        """
        if size < 0:
            raise ValueError("Padding size must be non-negative.")

        current_elements = list(self.__arg)  # Force evaluation of the iterable
        if len(current_elements) >= size:  # No padding needed
            return Stream(current_elements)
        return Stream(current_elements + [value] * (size - len(current_elements)))

    def flatten_opt(self, typ: type[L]) -> "Stream[L]":  # pylint: disable=unused-argument
        """
        Flattens a stream of Opts into a stream of their contained values, discarding empty Opts.

        This requires the stream to be of type Stream[Opt[L]], but type hinting can't
        fully enforce this at runtime, so incorrect usage may result in errors.

        Args:
            typ (type[L]): the type of the return stream

        Returns:
            Stream[L]: A stream of values contained in the non-empty Opts.
        """
        # The type hint self: "Stream[Opt[L]]" constrains what streams this can be called on.
        # We map to extract values from Opts, and filter to remove Nones.
        return (
            self.map(lambda e: self.__type_check(e, Opt))
            .map(lambda e: e.get_actual())  # type: ignore[attr-defined]
            .filter(is_not_none)
            .map(lambda x: require_non_null(x))
        )

    def __type_check(self, obj: U, typ: type[U]) -> U:
        if not isinstance(obj, typ):
            raise ValueError(f"Unexpected object {obj}. Was expecting type {typ}")
        return obj

    def clone(self) -> "Stream[T]":
        # If self.__arg is a list, tuple, or set, a shallow copy is often enough
        # to allow independent iteration if the elements themselves are not modified.
        if isinstance(self.__arg, (list, tuple, set)):
            return Stream(list(self.__arg))  # Create a new list from it

        # For generic iterables/iterators, use tee to allow multiple "independent" iterations.
        it1, it2 = itertools.tee(self.__arg)
        self.__arg = it1  # Current stream continues with one tee'd iterator
        return Stream(it2)  # New stream gets the other tee'd iterator

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
        return Stream(pairwise(self.__arg))

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
        return Stream(sliding_window(self.__arg, size, step))

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
        return Stream(repeat(self.__arg, n))

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
        return Stream(intersperse(self.__arg, separator))

    # ==========================================
    #          FACTORY METHODS
    # ==========================================
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

    @staticmethod
    def just(value: T) -> "Stream[T]":
        """
        Creates a stream from a single value. This is a convenience method
        for creating a stream with a single element.

        Args:
            value (T): The single value to include in the stream.

        Returns:
            Stream[T]: A stream containing only the provided value.
        """
        # Internally, it creates a list with a single element.
        return Stream([value])

    @staticmethod
    def just_nullable(value: Optional[T]) -> "Stream[T]":
        """
        Creates a stream from a single optional value. This is a convenience method
        for creating a stream with a single element.

        Args:
            value (Optional[T]): The single optional value to include in the stream.

        Returns:
            Stream[T]: A stream containing only the provided value.
        """
        return Stream.of_nullable([value])

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
        return Stream(cycle(iterable, n))

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
        return Stream(defer(supplier))

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
        return Stream(concat_of(*iterables))

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
        return Stream(unfold(seed, generator))


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


def nullable(val: Optional[T]) -> Opt[T]:
    """
    Helper method, equivalent to Opt.of_nullable(val)

    Args:
        val (Optional[T]): The value

    Returns:
        Opt[T]: The optional
    """
    return Opt.of_nullable(val)


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
    return Stream(pair_it(left, right))


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
