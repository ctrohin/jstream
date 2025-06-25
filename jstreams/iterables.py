from abc import ABC
from collections import deque
from itertools import dropwhile, islice, takewhile
import itertools
import sys
from typing import Any, Generic, Optional, TypeVar, cast
from collections.abc import Callable, Iterable, Iterator
from jstreams.mapper import Mapper
from jstreams.predicate import not_strict, _extract_predicate_fn
from jstreams.tuples import Pair
from jstreams.utils import require_non_null

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")
S = TypeVar("S")

if sys.version_info >= (3, 12):
    from itertools import batched


class GenericIterable(ABC, Generic[T], Iterator[T], Iterable[T]):
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

    def __next__(self) -> T:
        raise StopIteration()


def _extract_mapper_fn(mapper: Callable[[T], V]) -> Callable[[T], V]:
    if isinstance(mapper, Mapper):
        return mapper.map
    return mapper


class FilterIterable(GenericIterable[T]):
    __slots__ = ("__predicate",)

    def __init__(self, it: Iterable[T], predicate: Callable[[T], bool]) -> None:
        super().__init__(it)
        self.__predicate = _extract_predicate_fn(predicate)

    def __iter__(self) -> Iterator[V]:
        return filter(self.__predicate, self._iterable)  # type: ignore[arg-type]


def filter_it(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Iterable[T]:
    """
    Returns an iterable of objects that match the given predicate

    Args:
        iterable (Iterable[T]): The iterable to filter
        predicate (Callable[[T], bool]): The predicate

    Returns:
        Iterable[T]: The iterable of filtered objects
    """

    return FilterIterable(iterable, predicate)


class MapIndexedIterable(Generic[T, V], Iterator[V], Iterable[V]):
    __slots__ = ("_iterable", "_iterator", "__mapper", "__index")

    def __init__(self, it: Iterable[T], mapper: Callable[[int, T], V]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()
        self.__mapper = mapper
        self.__index = 0

    def _prepare(self) -> None:
        self.__index = 0

    def __iter__(self) -> Iterator[V]:
        self._iterator = self._iterable.__iter__()
        self._prepare()
        return self

    def __next__(self) -> V:
        # Get the next element, increment the index, and then apply the mapper.
        # This ensures that the mapper function always receives the current
        # (correctly incremented) index alongside the element.
        obj = self._iterator.__next__()
        current_index = self.__index
        self.__index += 1
        return self.__mapper(current_index, obj)


def map_indexed(iterable: Iterable[T], mapper: Callable[[int, T], V]) -> Iterable[V]:
    """
    Applies a mapping function to each element of the iterable, along with its index.

    Args:
        iterable (Iterable[T]): The iterable to map
        mapper: A function that takes the index and the element, and returns a transformed value.

    Returns:
        Iterable[V]: An iterable of the transformed values.
    """
    return MapIndexedIterable(iterable, mapper)


class GroupAdjacentIterable(Generic[T, K], Iterator[list[T]], Iterable[list[T]]):
    __slots__ = (
        "_iterable",
        "_iterator",
        "__key_func",
        "_current_group",
        "_current_key",
    )

    def __init__(self, it: Iterable[T], key_func: Callable[[T], K]) -> None:
        self._iterable = it
        self._iterator = iter(self._iterable)
        self.__key_func = key_func
        self._current_group: list[T] = []
        self._current_key: Optional[K] = None

    def __iter__(self) -> Iterator[list[T]]:
        self._iterator = iter(self._iterable)
        self._current_group = []
        self._current_key = None
        return self

    def __next__(self) -> list[T]:
        try:
            if not self._current_group:
                # Start a new group: get the first element, initialize group and key
                first_element = next(self._iterator)
                self._current_key = self.__key_func(first_element)
                self._current_group.append(first_element)

            while True:  # Keep trying to extend the current group
                next_element = next(self._iterator)
                next_key = self.__key_func(next_element)

                if next_key == self._current_key:
                    # Same key: add to group and continue
                    self._current_group.append(next_element)
                else:
                    # Different key: yield current group, start a new group, and stop iteration for now
                    group_to_yield = self._current_group
                    self._current_key = next_key
                    self._current_group = [next_element]
                    return group_to_yield

        except StopIteration as exc:
            if self._current_group:
                # Yield any remaining group at the end
                group_to_yield = self._current_group
                self._current_group = []  # Clear it after yielding
                return group_to_yield
            # No current group (probably empty iterator to start)
            raise StopIteration from exc


def group_adjacent(
    iterable: Iterable[T], key_func: Callable[[T], K]
) -> Iterable[list[T]]:
    """
    Groups consecutive elements of the stream that have the same key. The order is preserved.

    Args:
        iterable (Iterable[T]): The iterable to group
        key_func (Callable[[T], K]): A function that extracts a key from each element. Consecutive elements with the same key will be grouped together.

    Returns:
        Stream[list[T]]: A stream of lists, where each list is a group of adjacent elements with the same key.
    """
    return GroupAdjacentIterable(iterable, key_func)


class WindowedIterable(Generic[T], Iterator[list[T]], Iterable[list[T]]):
    __slots__ = ("_iterable", "_iterator", "_size", "_step", "_partial")

    def __init__(
        self, it: Iterable[T], size: int, step: int = 1, partial: bool = False
    ) -> None:
        if size <= 0 or step <= 0:
            raise ValueError("Size and step must be positive")
        self._iterable = it
        self._iterator = iter(self._iterable)
        self._size = size
        self._step = step
        self._partial = partial

    def __iter__(self) -> Iterator[list[T]]:
        self._iterator = iter(self._iterable)  # Reset iterator
        return self

    def __next__(self) -> list[T]:
        window: list[T] = []
        try:
            # Try to populate a new window by skipping elements first if step > 1
            if len(window) == 0:
                for _ in range(
                    self._step - 1
                ):  # Consume and discard elements (if step > 1)
                    next(
                        self._iterator
                    )  # Will raise StopIteration if not enough elements
            # Fill as much of window as possible until end of data or window size
            for _ in range(self._size):
                window.append(next(self._iterator))
        except StopIteration as exc:
            # Check whether to yield a partial window if allowed or stop iteration
            if not window or (not self._partial and len(window) < self._size):
                raise StopIteration from exc
        # If full or partial (if allowed), return the window
        return window


def windowed(
    iterable: Iterable[T], size: int, step: int = 1, partial: bool = False
) -> Iterable[list[T]]:
    """
    Creates an itreable of windows (sublists) from the elements of the given iterable,
    where each window has a specified size and consecutive windows are
    separated by a specified step.

    Args:
        iterable (Iterable[T]): The iterable to window
        size (int): The size of each window. Must be positive.
        step (int): The number of elements to move forward for the start of
                    the next window. Defaults to 1 (consecutive windows). Must be positive.
        partial (bool): If True, allows windows that are smaller than 'size'
                        at the end of the iterable. If False (default), only windows
                        of exactly 'size' are returned, and any remaining elements
                        that cannot form a full window are discarded.

    Returns:
        Iterable[list[T]]: A list of windows (lists of elements).
    Raises:
        ValueError: If size or step is not positive.
    """
    return WindowedIterable(iterable, size, step, partial)


class CastIterable(Generic[T, V], Iterable[T]):
    __slots__ = "__iterable"

    def __init__(self, it: Iterable[V], typ: type[T]) -> None:  # pylint: disable=unused-argument
        self.__iterable = it

    def __iter__(self) -> Iterator[T]:
        return map(lambda x: cast(T, x), self.__iterable)


def cast_to(iterable: Iterable[T], cast_to_type: type[V]) -> Iterable[V]:
    """
    Returns an iterable of objects casted to the given type. Useful when receiving untyped data lists
    and they need to be used in a typed context.

    Args:
        iterable (Iterable[T]): The iterable to cast
        cast_to_type (type[V]): The type all objects will be casted to

    Returns:
        Iterable[V]: The iterable of casted objects
    """
    return CastIterable(iterable, cast_to_type)


class SkipIterable(GenericIterable[T]):
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

    def __iter__(self) -> Iterator[T]:
        return islice(self._iterable, self.__count, None, 1)


def skip(iterable: Iterable[T], count: int) -> Iterable[T]:
    """
    Returns an iterable without the first number of items specified by 'count'

    Args:
        iterable (Iterable[T]): The iterable to skip
        count (int): How many items should be skipped

    Returns:
        Iterable[T]: The result iterable
    """
    return SkipIterable(iterable, count)


class LimitIterable(GenericIterable[T]):
    __slots__ = "__count"

    def __init__(self, it: Iterable[T], count: int) -> None:
        super().__init__(it)
        self.__count = count

    def __iter__(self) -> Iterator[T]:
        return islice(self._iterable, 0, self.__count, 1)


def limit(iterable: Iterable[T], count: int) -> Iterable[T]:
    """
    Returns an iterable limited to the first 'count' items of this iterable

    Args:
        iterable (Iterable[T]): The iterable to limit
        count (int): The max amount of items

    Returns:
        Iterable[T]: The result iterable
    """
    return LimitIterable(iterable, count)


class TakeWhileIterable(GenericIterable[T]):
    __slots__ = ("__predicate",)

    def __init__(
        self,
        it: Iterable[T],
        predicate: Callable[[T], bool],
    ) -> None:
        super().__init__(it)
        self.__predicate = _extract_predicate_fn(predicate)

    def __iter__(self) -> Iterator[T]:
        return takewhile(self.__predicate, self._iterable)


def take_while(
    iterable: Iterable[T],
    predicate: Callable[[T], bool],
) -> Iterable[T]:
    """
    Returns an iterable of elements until the first element that DOES NOT match the given predicate

    Args:
        iterable (Iterable[T]): The iterable
        predicate (Callable[[T], bool]): The predicate
    Returns:
        Iterable[T]: The result iterable
    """
    return TakeWhileIterable(iterable, predicate)


class DropWhileIterable(GenericIterable[T]):
    __slots__ = ("__predicate",)

    def __init__(
        self,
        it: Iterable[T],
        predicate: Callable[[T], bool],
    ) -> None:
        super().__init__(it)
        self.__predicate = _extract_predicate_fn(predicate)

    def __iter__(self) -> Iterator[T]:
        return dropwhile(self.__predicate, self._iterable)


def drop_while(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Iterable[T]:
    """
    Returns an iterable of elements by dropping the first elements that match the given predicate

    Args:
        iterable (Iterable[T]): The iterable
        predicate (Callable[[T], bool]): The predicate

    Returns:
        Iterable[T]: The result iterable
    """
    return DropWhileIterable(iterable, predicate)


class ConcatIterable(GenericIterable[T]):
    __slots__ = ("__iterable2", "__iterator2")

    def __init__(self, it1: Iterable[T], it2: Iterable[T]) -> None:
        super().__init__(it1)
        self.__iterable2 = it2

    def __iter__(self) -> Iterator[T]:
        return itertools.chain(self._iterable, self.__iterable2)


def concat(iterable1: Iterable[T], iterable2: Iterable[T]) -> Iterable[T]:
    """
    Returns an iterable concatenating the values from iterable1 with the ones
    from iterable2.

    Args:
        iterable1 (Iterable[T]): The first iterable
        iterable2 (Iterable[T]): The second iterable

    Returns:
        Iterable[T]: The resulting iterable
    """
    return ConcatIterable(iterable1, iterable2)


class DistinctIterable(GenericIterable[T]):
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


def distinct(
    iterable: Iterable[T], key: Optional[Callable[[T], Any]] = None
) -> Iterable[T]:
    """
    Returns an iterable consisting of the distinct elements of the given iterable.
    Uniqueness is determined by the element itself or by the result of applying the key function.

    CAUTION: For objects without a key function, ensure `__eq__` and `__hash__` are properly implemented.
            This operation requires storing seen keys/elements, potentially consuming memory.

    Args:
        iterable (Iterable[T]): The iterable
        key (Optional[Callable[[T], Any]]): A function to extract the key for uniqueness comparison. If None, the element itself is used. Defaults to None.
    """
    return DistinctIterable(iterable, key)


class MapIterable(Generic[T, V], Iterable[V]):
    __slots__ = ("_iterable", "_iterator", "__mapper")

    def __init__(self, it: Iterable[T], mapper: Callable[[T], V]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()
        self.__mapper = _extract_mapper_fn(mapper)

    def __iter__(self) -> Iterator[V]:
        return map(self.__mapper, self._iterable)


def map_it(iterable: Iterable[T], mapper: Callable[[T], V]) -> Iterable[V]:
    """
    Produces a new iterable by mapping the initial elements using the given mapper function.
    Args:
        iterable (Iterable[T]): The initial iterable
        mapper (Callable[[T], V]): The mapper

    Returns:
        Iterable[V]: The resulting mapped iterable
    """
    return MapIterable(iterable, mapper)


class PeekIterable(GenericIterable[T]):
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
            print(  # pylint: disable=expression-not-assigned
                f"Exception during peek: {e}"
            ) if self.__logger is None else self.__logger(e)
        return obj  # Return the original object


def peek(
    it: Iterable[T],
    action: Callable[[T], Any],
    logger: Optional[Callable[[Exception], Any]] = None,
) -> Iterable[T]:
    return PeekIterable(it, action, logger)


class _InlineIndex:
    __slots__ = ("_index",)

    def __init__(self) -> None:
        self._index = 0

    def next(self) -> int:
        result = self._index
        self._index += 1
        return result


class IndexedIterable(Generic[T], Iterable[Pair[int, T]]):
    __slots__ = ("_iterable", "_iterator", "_index")

    def __init__(self, it: Iterable[T]) -> None:
        self._iterable = it
        self._iterator = self._iterable.__iter__()
        self._index = 0

    def __iter__(self) -> Iterator[Pair[int, T]]:
        index = _InlineIndex()
        return map(lambda x: Pair(index.next(), x), self._iterable)


def indexed(iterable: Iterable[T]) -> Iterable[Pair[int, T]]:
    """
    Returns an iterable consisting of pairs of (index, element).
    The index is zero-based.

    Returns:
        Iterable[Pair[int, T]]: An iterable of index-element pairs.
    """
    return IndexedIterable(iterable)


class ChunkedIterable(Generic[T], Iterable[list[T]]):
    __slots__ = ("_size", "_iterable")

    def __init__(self, it: Iterable[T], size: int) -> None:
        if size <= 0:
            raise ValueError("Chunk size must be positive")
        # Store the original iterator directly
        self._iterable = it
        self._size = size

    def __iter__(self) -> Iterator[list[T]]:
        # Resetting isn't straightforward without consuming the original iterable again.
        # This implementation assumes the stream is consumed once.
        # If re-iteration is needed, the original iterable must support it.
        # Or, store the original iterable and get a new iterator here.
        if sys.version_info >= (3, 12):
            return map(list, batched(iter(self._iterable), self._size))
        it = iter(self._iterable)
        return iter(lambda: list(islice(it, self._size)), [])


def chunked(iterable: Iterable[T], size: int) -> Iterable[list[T]]:
    """
    Groups elements of the iterable into chunks (lists) of a specified size.
    The last chunk may contain fewer elements than the specified size.

    Args:
        iterable (Iterable[T]): The iterable
        size (int): The desired size of each chunk. Must be positive.

    Returns:
        Iterable[list[T]]: An iterable where each element is a list (chunk).

    Raises:
        ValueError: If size is not positive.
    """
    return ChunkedIterable(iterable, size)


class _StoppingPredicate(Generic[T]):
    __slots__ = ("__predicate", "__stopped", "__include_stop_value")

    def __init__(
        self, predicate: Callable[[T], bool], include_stop_value: bool
    ) -> None:
        self.__predicate = predicate
        self.__stopped: bool = False
        self.__include_stop_value = include_stop_value

    def __call__(self, obj: T) -> bool:
        if self.__stopped:
            return False
        if self.__predicate(obj):
            self.__stopped = True
        if self.__include_stop_value and self.__stopped:
            return True
        return not self.__stopped


class _AllowingPredicate(Generic[T]):
    __slots__ = ("__predicate", "__stopped", "__include_stop_value")

    def __init__(
        self, predicate: Callable[[T], bool], include_stop_value: bool
    ) -> None:
        self.__predicate = predicate
        self.__stopped: bool = False
        self.__include_stop_value = include_stop_value

    def __call__(self, obj: T) -> bool:
        if self.__stopped:
            return False
        if not self.__predicate(obj):
            self.__stopped = True
        if self.__include_stop_value and self.__stopped:
            return True
        return not self.__stopped


class TakeUntilIterable(GenericIterable[T]):
    __slots__ = ("__predicate",)

    def __init__(self, it: Iterable[T], predicate: Callable[[T], bool]) -> None:
        super().__init__(it)
        self.__predicate = _extract_predicate_fn(predicate)

    def __iter__(self) -> Iterator[T]:
        return takewhile(
            not_strict(self.__predicate),
            self._iterable,
        )


def take_until(
    iterable: Iterable[T],
    predicate: Callable[[T], bool],
) -> Iterable[T]:
    """
    Returns an iterable consisting of elements taken from the initial iterable until
    the predicate returns True for the first time.

    Args:
        iterable: The intial iterable
        predicate: The predicate to test elements against.

    Returns:
        Iterable[T]: The resulting iterable.
    """
    return TakeUntilIterable(iterable, predicate)


class DropUntilIterable(GenericIterable[T]):
    __slots__ = ("__predicate",)

    def __init__(self, it: Iterable[T], predicate: Callable[[T], bool]) -> None:
        super().__init__(it)
        self.__predicate = _extract_predicate_fn(predicate)

    def __iter__(self) -> Iterator[T]:
        return dropwhile(not_strict(self.__predicate), self._iterable)


def drop_until(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Iterable[T]:
    """
    Returns an iterable consisting of the remaining elements after dropping
    elements until the predicate returns True for the first time. The element
    that satisfies the predicate IS included in the resulting iterable.

    Args:
        iterable: The initial iterable
        predicate: The predicate to test elements against.

    Returns:
        Iterable[T]: The resulting iterable.
    """
    return DropUntilIterable(iterable, predicate)


class ScanIterable(Generic[T, V], Iterable[V]):
    __slots__ = (
        "_accumulator",
        "_iterable",
        "_initial_value",
    )

    def __init__(
        self, it: Iterable[T], accumulator: Callable[[V, T], V], initial_value: V
    ) -> None:
        # Store original iterable to allow re-iteration if needed
        self._iterable = it
        self._accumulator = accumulator
        self._initial_value = initial_value

    def __iter__(self) -> Iterator[V]:
        return itertools.accumulate(
            self._iterable, self._accumulator, initial=self._initial_value
        )


def scan(
    iterable: Iterable[T], accumulator: Callable[[V, T], V], initial_value: V
) -> Iterable[V]:
    """
    Performs a cumulative reduction operation on the iterable elements,
    yielding each intermediate result, starting with the initial_value.

    Example:
        scan([1, 2, 3], lambda acc, x: acc + x, 0)
        # Output: [0, 1, 3, 6]

    Args:
        iterable: The initial iterable
        accumulator: A function that takes the current accumulated value (V)
                    and the next element (T), returning the new accumulated value (V).
        initial_value: The initial value for the accumulation (V).

    Returns:
        Iterable[V]: An iterable of the intermediate accumulated values.
    """
    return ScanIterable(iterable, accumulator, initial_value)


class PairIterable(Generic[T, V], Iterator[Pair[T, V]], Iterable[Pair[T, V]]):
    __slots__ = ("_it1", "_it2", "_iter1", "_iter2")

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


def pair_it(left: Iterable[T], right: Iterable[V]) -> Iterable[Pair[T, V]]:
    """
    Create a pair iterable by zipping two iterables. The resulting iterable will have the length
    of the shortest iterable.

    Args:
        left (Iterable[T]): The left iterable
        right (Iterable[V]): The right iterable

    Returns:
        Itreable[Pair[T, V]]: The resulting pair iterable
    """
    return PairIterable(left, right)


class MultiConcatIterable(Generic[T], Iterable[T]):
    __slots__ = ("_iterables",)

    def __init__(self, *iterables: Iterable[T]) -> None:
        self._iterables = iterables

    def __iter__(self) -> Iterator[T]:
        return itertools.chain(*self._iterables)


def concat_of(*iterables: Iterable[T]) -> Iterable[T]:
    """
    Creates a lazily concatenated iterable whose elements are all the
    elements of the first iterable followed by all the elements of the
    second iterable, and so on.

    Args:
        *iterables: The iterables to concatenate.

    Returns:
        Iterable[T]: The concatenated iterable.
    """
    if not iterables:
        return []
    # If only one iterable, just return a stream of it
    if len(iterables) == 1:
        return iterables[0]
    return MultiConcatIterable(*iterables)

    # class PairwiseIterable(Generic[T], Iterable[Pair[T, T]]):
    #     __slots__ = "_iterable"

    #     def __init__(self, it: Iterable[T]) -> None:
    #         self._iterable = it  # Store original iterable if re-iteration needed

    #     def __iter__(self) -> Iterator[Pair[T, T]]:
    #         return map(lambda t: Pair(t[0], t[1]), itertools.pairwise(self._iterable))


class PairwiseIterable(Generic[T], Iterator[Pair[T, T]], Iterable[Pair[T, T]]):
    __slots__ = ("_iterator", "_previous", "_first_element_consumed", "_iterable")

    def __init__(self, it: Iterable[T]) -> None:
        self._iterable = (
            it  # Store original iterable if re-iteration neededAdd commentMore actions
        )
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
            self._previous = next(self._iterator)
            self._first_element_consumed = True

        # Get the next element to form a pair with the previous one
        current = next(self._iterator)  # Raises StopIteration when done
        pair_to_yield = Pair(
            require_non_null(self._previous), current
        )  # require_non_null is safe here
        self._previous = current  # Update previous for the next iteration
        return pair_to_yield


def pairwise(iterable: Iterable[T]) -> Iterable[Pair[T, T]]:
    """
    Returns an iterable of pairs consisting of adjacent elements from this stream.
    If the stream has N elements, the resulting stream will have N-1 elements.
    Returns an empty iterable if the original stream has 0 or 1 element.

    Example:
        pairwise([1, 2, 3, 4])
        # Output: [Pair(1, 2), Pair(2, 3), Pair(3, 4)]

    Returns:
        Iterable[Pair[T, T]]: An iterable of adjacent pairs.
    """
    return PairwiseIterable(iterable)


class SlidingWindowIterable(Generic[T], Iterator[list[T]], Iterable[list[T]]):
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

            except StopIteration as exc:
                # Not enough elements to form a full window initially or remaining
                if len(self._window) > 0 and len(self._window) < self._size:
                    # Option: yield partial window at the end? Or require full windows?
                    # Current StopIteration implies only full windows.
                    pass  # Let StopIteration be raised below if window is empty
                raise StopIteration from exc

        # Yield the current full window
        result = list(self._window)  # Create list copy

        # Prepare for the next window by sliding
        for _ in range(self._step):
            if not self._window:
                break  # Should not happen if size > 0
            self._window.popleft()  # Remove element(s) from the left

        return result  # Return the window captured before sliding


def sliding_window(
    iterable: Iterable[T], size: int, step: int = 1
) -> "Iterable[list[T]]":
    """
    Returns an iterable of lists, where each list is a sliding window of
    elements from the original iterable.

    Example:
        sliding_window([1, 2, 3, 4, 5], 3, 1)
        # Output: [[1, 2, 3], [2, 3, 4], [3, 4, 5]]

    Args:
        iterable (Iterable[T]): The initial iterable
        size (int): The size of each window. Must be positive.
        step (int, optional): The number of elements to slide forward for
                            the next window. Defaults to 1. Must be positive.

    Returns:
        Iterable[list[T]]: An iterable of lists representing the sliding windows.

    Raises:
        ValueError: If size or step are not positive.
    """
    # NOTE: The _SlidingWindowIterable implementation above is complex and might need refinement
    # for full correctness and laziness, especially around edge cases and step > size.
    # Consider starting with a simpler implementation if needed.
    return SlidingWindowIterable(iterable, size, step)


class RepeatIterable(Generic[T], Iterable[T]):
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
        except StopIteration as exc:
            # End of current cycle reached
            if self._n is not None:  # Finite repetitions
                self._current_n += 1
                if self._current_n >= self._n:
                    raise StopIteration from exc  # Max repetitions reached
            # Start next cycle
            if not self._buffered_elements:  # Handle empty source
                raise StopIteration from exc
            self._iterator = iter(self._buffered_elements)
            return next(self._iterator)  # Get first element of next cycle


def repeat(iterable: Iterable[T], n: Optional[int] = None) -> Iterable[T]:
    """
    Returns an iterable that repeats the elements of the given iterable n times,
    or indefinitely if n is None.

    Args:
        iterable (Iterable[T]): The initial iterable
        n (Optional[int]): The number of times to repeat the iterable.
                        If None, repeats indefinitely. Defaults to None.

    Returns:
        Iterable[T]: An iterable consisting of the repeated elements.

    Raises:
        ValueError: If n is specified and is not positive.
    """
    if n is not None and n <= 0:
        raise ValueError("Number of repetitions 'n' must be positive if specified.")
    # The RepeatIterable buffers the original iterable
    return RepeatIterable(iterable, n)


class IntersperseIterable(Generic[T], Iterator[T], Iterable[T]):
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
        # Get the next actual element from the source
        next_element = next(self._iterator)  # Raises StopIteration when source is done
        # Set flag to insert separator *before* the *next* element
        self._needs_separator = True
        return next_element


def intersperse(iterable: Iterable[T], separator: T) -> Iterable[T]:
    """
    Returns a stream with the separator element inserted between each
    element of this stream.

    Example:
        intersperse([1, 2, 3], 0)
        # Output: [1, 0, 2, 0, 3, 0]

        intersperse(["a", "b"], "-")
        # Output: ["a", "-", "b", "-"]

        intersperse([], 0)
        # Output: []

        intersperse([1], 0)
        # Output: [1, 0]

    Args:
        iterable (Iterable[T]): The iterable
        separator (T): The element to insert between original elements.

    Returns:
        Iterable[T]: The resulting iterable with separators.
    """
    return IntersperseIterable(iterable, separator)


class UnfoldIterable(Generic[T, S], Iterator[T], Iterable[T]):
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


def unfold(seed: S, generator: Callable[[S], Optional[Pair[T, S]]]) -> Iterable[T]:
    """
    Creates an iterable by repeatedly applying a generator function to a seed value.

    The generator function takes the current state (seed) and returns an
    Optional Pair containing the next element for the iterable and the next state (seed).
    The iterable terminates when the generator returns None.

    Example (Fibonacci sequence):
        def fib_generator(state: Pair[int, int]) -> Optional[Pair[int, Pair[int, int]]]:
            a, b = state.left(), state.right()
            return Pair(a, Pair(b, a + b)) # Yield a, next state is (b, a+b)

        limit(unfold(Pair(0, 1), fib_generator), 10)
        # Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    Example (Range):
        def range_generator(current: int) -> Optional[Pair[int, int]]:
            if current >= 10:
                return None
            return Pair(current, current + 1) # Yield current, next state is current + 1

        unfold(0, range_generator)
        # Output: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    Args:
        seed (S): The initial state.
        generator (Callable[[S], Optional[Pair[T, S]]]): Function that takes the
            current state and returns an Optional Pair(next_element, next_state).

    Returns:
        Iterable[T]: The generated stream.
    """
    return UnfoldIterable(seed, generator)


class ZipLongestIterable(
    Generic[T, V],
    Iterable[Pair[Optional[T], Optional[V]]],
):
    __slots__ = ("_it1", "_it2", "_fillvalue")

    def __init__(
        self, it1: Iterable[T], it2: Iterable[V], fillvalue: Any = None
    ) -> None:
        self._it1 = it1
        self._it2 = it2
        self._fillvalue = fillvalue

    def __iter__(self) -> Iterator[Pair[Optional[T], Optional[V]]]:
        return map(
            lambda x: Pair(x[0], x[1]),
            itertools.zip_longest(self._it1, self._it2, fillvalue=self._fillvalue),
        )


def zip_longest(
    iterable1: Iterable[T], iterable2: Iterable[V], fillvalue: Any = None
) -> Iterable[Pair[Optional[T], Optional[V]]]:
    """
    Zips iterable1 and iterable2, producing an iterable of Pairs.
    Continues until the longest iterable is exhausted, filling missing
    values with `fillvalue`.

    Args:
        iterable1: The first iterable
        iterable2: The second iterable
        fillvalue: The value to use for missing elements from shorter iterables.
                    Defaults to None.

    Returns:
        Iterable[Pair[Optional[T], Optional[V]]]: An iterable of pairs, potentially
                                                containing the fillvalue.
    """
    # Note: The Pair type hints need to reflect the Optional nature
    # Pair[Optional[T], Optional[V]] is correct.
    return ZipLongestIterable(iterable1, iterable2, fillvalue)


class CycleIterable(Generic[T], Iterator[T], Iterable[T]):
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
        except StopIteration as exc:
            if self._n is not None:
                self._current_n += 1
                if self._current_n >= self._n:
                    raise StopIteration from exc
            # Reset for next cycle (will raise StopIteration if _elements is empty,
            # but we've guarded against that if n > 0)
            self._iterator = iter(self._elements)
            return next(self._iterator)


def cycle(iterable: Iterable[T], n: Optional[int] = None) -> Iterable[T]:
    """
    Creates an iterable that cycles over the elements of the initial iterable.

    The elements of the input iterable are buffered. The stream will then
    repeat these buffered elements.

    Args:
        iterable (Iterable[T]): The iterable whose elements are to be cycled.
        n (Optional[int]): The number of times to cycle through the iterable.
            If None (default), cycles indefinitely.
            If 0, results in an empty iterable.
            If the input iterable is empty and n > 0, an empty iterable is also produced.

    Returns:
        Iterable[T]: An iterable that cycles through the elements of the iterable.

    Raises:
        ValueError: If n is specified and is negative.
    """
    if n is not None and n < 0:
        raise ValueError("Number of repetitions 'n' must be non-negative.")
    if n == 0:
        return []
    return CycleIterable(iterable, n)


class DeferIterable(Generic[T], Iterable[T]):
    __slots__ = ("_supplier",)

    def __init__(self, supplier: Callable[[], Iterable[T]]) -> None:
        self._supplier = supplier

    def __iter__(self) -> Iterator[T]:
        return iter(self._supplier())


def defer(supplier: Callable[[], Iterable[T]]) -> Iterable[T]:
    """
    Creates an iterable which is obtained by calling the
    supplier function only when the iterable is iterated.
    """
    return DeferIterable(supplier)
