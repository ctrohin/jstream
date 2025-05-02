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
    predicate_of,
    predicate_with_of,
)
from jstreams.tuples import Pair
from jstreams.utils import is_not_none, require_non_null, each, is_empty_or_none, sort

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
C = TypeVar("C")


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


class _PeekIterable(_GenericIterable[T]):
    __slots__ = ("__action",)

    def __init__(self, it: Iterable[T], action: Callable[[T], Any]) -> None:
        super().__init__(it)
        self.__action = action

    def __next__(self) -> T:
        obj = self._iterator.__next__()
        try:
            self.__action(obj)  # Perform the side-effect
        except Exception as e:
            # Decide how to handle exceptions in peek: log? ignore? re-raise?
            # Logging and ignoring is often the 'peek' behavior.
            print(f"Exception during Stream.peek: {e}")  # Simple example
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

    def peek(self, action: Callable[[T], Any]) -> "Stream[T]":
        """
        Performs an action on each element of the stream as it passes through.
        Useful for debugging or logging intermediate values. Does not modify the stream elements.

        Args:
            action (Callable[[T], Any]): The action to perform on each element.

        Returns:
            Stream[T]: The same stream, allowing further chaining.
        """
        return Stream(_PeekIterable(self.__arg, action))

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
