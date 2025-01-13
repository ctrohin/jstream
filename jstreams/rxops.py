import abc
from copy import deepcopy
from typing import Any, Callable, Generic, TypeVar, cast, Optional

from jstreams import Stream

T = TypeVar("T")
V = TypeVar("V")


class RxOperator(Generic[T, V], abc.ABC):
    def __init__(self) -> None:
        pass

    def init(self) -> None:
        pass


class BaseFilteringOperator(RxOperator[T, T]):
    __slots__ = ("__fn",)

    def __init__(self, predicate: Callable[[T], bool]) -> None:
        self.__fn = predicate

    def matches(self, val: T) -> bool:
        return self.__fn(val)


class BaseMappingOperator(RxOperator[T, V]):
    __slots__ = ("__fn",)

    def __init__(self, mapper: Callable[[T], V]) -> None:
        self.__fn = mapper

    def transform(self, val: T) -> V:
        return self.__fn(val)


class Reduce(BaseFilteringOperator[T]):
    def __init__(self, reducer: Callable[[T, T], T]) -> None:
        """
        Reduces two consecutive values into one by applying the provided reducer function

        Args:
            reducer (Callable[[T, T], T]): Reducer function
        """
        self.__reducer = reducer
        self.__prevVal: Optional[T] = None
        super().__init__(self.__mapper)

    def init(self) -> None:
        self.__prevVal = None

    def __mapper(self, val: T) -> bool:
        if self.__prevVal is None:
            # When reducing, the first value is always returned
            self.__prevVal = val
            return True
        reduced = self.__reducer(self.__prevVal, val)
        if reduced != self.__prevVal:
            # Push and store the reduced value only if it's different than the previous value
            self.__prevVal = reduced
            return True
        return False


def rxReduce(reducer: Callable[[T, T], T]) -> RxOperator[T, T]:
    """
    Reduces two consecutive values into one by applying the provided reducer function

    Args:
        reducer (Callable[[T, T], T]): The reducer function

    Returns:
        RxOperator[T, T]: A reduce operator
    """
    return Reduce(reducer)


class Filter(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows only values that match the given predicate to flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        super().__init__(predicate)


def rxFilter(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows only values that match the given predicate to flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A filter operator
    """
    return Filter(predicate)


class Map(BaseMappingOperator[T, V]):
    def __init__(self, mapper: Callable[[T], V]) -> None:
        """
        Maps a value to a differnt value/form using the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function
        """
        super().__init__(mapper)


def rxMap(mapper: Callable[[T], V]) -> RxOperator[T, V]:
    """
    Maps a value to a differnt value/form using the mapper function

    Args:
        mapper (Callable[[T], V]): The mapper function

    Returns:
        RxOperator[T, V]: A map operator
    """
    return Map(mapper)


class Take(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:
        """
        Allows only the first "count" values to flow through

        Args:
            typ (type[T]): The type of the values that will pass throgh
            count (int): The number of values that will pass through
        """
        self.__count = count
        self.__currentlyPushed = 0
        super().__init__(self.__take)

    def init(self) -> None:
        self.__currentlyPushed = 0

    def __take(self, val: T) -> bool:
        if self.__currentlyPushed >= self.__count:
            return False
        self.__currentlyPushed += 1
        return True


def rxTake(typ: type[T], count: int) -> RxOperator[T, T]:
    """
    Allows only the first "count" values to flow through

    Args:
        typ (type[T]): The type of the values that will pass throgh
        count (int): The number of values that will pass through

    Returns:
        RxOperator[T, T]: A take operator
    """
    return Take(typ, count)


class TakeWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = True
        super().__init__(self.__take)

    def init(self) -> None:
        self.__shouldPush = True

    def __take(self, val: T) -> bool:
        if not self.__shouldPush:
            return False
        if not self.__fn(val):
            self.__shouldPush = False
            return False
        return True


def rxTakeWhile(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A takeWhile operator
    """
    return TakeWhile(predicate)


class TakeUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = True
        super().__init__(self.__take)

    def init(self) -> None:
        self.__shouldPush = True

    def __take(self, val: T) -> bool:
        if not self.__shouldPush:
            return False
        if self.__fn(val):
            self.__shouldPush = False
            return False
        return True


def rxTakeUntil(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A takeUntil operator
    """
    return TakeUntil(predicate)


class Drop(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:
        """
        Blocks the first "count" values, then allows all remaining values to pass through

        Args:
            typ (type[T]): The type of the values
            count (int): The number of values to pass through
        """
        self.__count = count
        self.__currentlyDropped = 0
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__currentlyDropped = 0

    def __drop(self, val: T) -> bool:
        if self.__currentlyDropped < self.__count:
            self.__currentlyDropped += 1
            return False
        return True


def rxDrop(typ: type[T], count: int) -> RxOperator[T, T]:
    """
    Blocks the first "count" values, then allows all remaining values to pass through

    Args:
        typ (type[T]): The type of the values
        count (int): The number of values to pass through

    Returns:
        RxOperator[T, T]: A drop operator
    """
    return Drop(typ, count)


class DropWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = False
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__shouldPush = False

    def __drop(self, val: T) -> bool:
        if self.__shouldPush:
            return True

        if not self.__fn(val):
            self.__shouldPush = True
            return True
        return False


def rxDropWhile(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A dropWhile operator
    """
    return DropWhile(predicate)


class DropUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = False
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__shouldPush = False

    def __drop(self, val: T) -> bool:
        if self.__shouldPush:
            return True

        if self.__fn(val):
            self.__shouldPush = True
            return True
        return False


def rxDropUntil(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

    Args:
        predicate (Callable[[T], bool]): The given predicate

    Returns:
        RxOperator[T, T]: A dropUntil operator
    """
    return DropUntil(predicate)


class Pipe(Generic[T, V]):
    __slots__ = ("__operators",)

    def __init__(
        self, inputType: type[T], outputType: type[V], ops: list[RxOperator[Any, Any]]
    ) -> None:
        super().__init__()
        self.__operators: list[RxOperator[Any, Any]] = ops

    def apply(self, val: T) -> Optional[V]:
        v: Any = val
        for op in self.__operators:
            if isinstance(op, BaseFilteringOperator):
                if not op.matches(val):
                    return None
            if isinstance(op, BaseMappingOperator):
                v = op.transform(v)
        return cast(V, v)

    def clone(self) -> "Pipe[T, V]":
        return Pipe(T, V, deepcopy(self.__operators))  # type: ignore[misc]

    def init(self) -> None:
        Stream(self.__operators).each(lambda op: op.init())


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
