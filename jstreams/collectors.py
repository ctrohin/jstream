from typing import Any, Callable, Iterable, Optional, TypeVar

from jstreams.stream import Opt
from jstreams.utils import cmp_to_key

T = TypeVar("T")
R = TypeVar("R")
V = TypeVar("V")
K = TypeVar("K")


def grouping_by(group_by: Callable[[T], K], elements: Iterable[T]) -> dict[K, list[T]]:
    """
    Groups elements of an iterable into a dictionary based on a classification function.

    The classification function (`group_by`) is applied to each element, and the
    result is used as the key in the dictionary. Each value in the dictionary
    is a list of elements that produced the corresponding key.

    Args:
        group_by (Callable[[T], K]): The function to classify elements into groups.
                                    It takes an element and returns a key.
        elements (Iterable[T]): The iterable containing elements to be grouped.

    Returns:
        dict[K, list[T]]: A dictionary where keys are the results of the `group_by`
                        function and values are lists of elements belonging to that group.
    """
    values: dict[K, list[T]] = {}
    for element in elements:
        key = group_by(element)
        if key in values:
            values.setdefault(key, []).append(element)
        else:
            values[key] = [element]
    return values


def grouping_by_mapping(
    group_by: Callable[[T], K], elements: Iterable[T], mapper: Callable[[T], R]
) -> dict[K, list[R]]:
    """
    Groups elements of an iterable into a dictionary based on a classification function.

    The classification function (`group_by`) is applied to each element, and the
    result is used as the key in the dictionary. Each value in the dictionary
    is a list of elements that produced the corresponding key.

    Args:
        group_by (Callable[[T], K]): The function to classify elements into groups.
                                    It takes an element and returns a key.
        elements (Iterable[T]): The iterable containing elements to be grouped.
        mapper (Callable[[T], R]): The mapping function that transforms the iterable
                                    elements into resulting elements

    Returns:
        dict[K, list[R]]: A dictionary where keys are the results of the `group_by`
                        function and values are mapped lists of elements belonging to that group.
    """
    values: dict[K, list[R]] = {}
    for element in elements:
        key = group_by(element)
        if key in values:
            values.setdefault(key, []).append(mapper(element))
        else:
            values[key] = [mapper(element)]
    return values


def joining(separator: str, elements: Iterable[str]) -> str:
    """
    Concatenates the elements of an iterable of strings into a single string,
    separated by the specified separator.

    Args:
        separator (str): The string to use as a separator between elements.
        elements (Iterable[str]): The iterable of strings to join.

    Returns:
        str: A single string resulting from joining the elements with the separator.
    """
    return separator.join(elements)


class Collectors:
    """
    Provides static methods that return collector functions.

    These collector functions are designed to be used with `Stream.collect_using()`
    to transform a stream into a different collection type (list, set, dict) or
    a summary value (like a joined string).
    """

    @staticmethod
    def to_list() -> Callable[[Iterable[T]], list[T]]:
        """
        Returns a collector function that accumulates stream elements into a list.

        Usage:
            my_list = stream_instance.collect_using(Collectors.to_list())

        Returns:
            Callable[[Iterable[T]], list[T]]: A function that takes an iterable and returns a list.
        """

        def transform(elements: Iterable[T]) -> list[T]:
            """Accumulates elements into a list."""
            return list(elements)

        return transform

    @staticmethod
    def to_set() -> Callable[[Iterable[T]], set[T]]:
        """
        Returns a collector function that accumulates stream elements into a set.
        Duplicate elements will be removed.

        Usage:
            my_set = stream_instance.collect_using(Collectors.to_set())

        Returns:
            Callable[[Iterable[T]], set[T]]: A function that takes an iterable and returns a set.
        """

        def transform(elements: Iterable[T]) -> set[T]:
            """Accumulates elements into a set."""
            return set(elements)

        return transform

    @staticmethod
    def grouping_by(
        group_by_func: Callable[[T], K],
    ) -> Callable[[Iterable[T]], dict[K, list[T]]]:
        """
        Returns a collector function that groups elements into a dictionary based on a
        classification function.

        The classification function (`group_by_func`) is applied to each element, and the
        result is used as the key in the dictionary. Each value in the dictionary
        is a list of elements that produced the corresponding key.

        Usage:
            grouped_dict = stream_instance.collect_using(Collectors.grouping_by(lambda x: x.category))

        Args:
            group_by_func (Callable[[T], K]): The function to classify elements into groups.

        Returns:
            Callable[[Iterable[T]], dict[K, list[T]]]: A function that takes an iterable
            and returns a dictionary grouped by the classification function.
        """

        def transform(elements: Iterable[T]) -> dict[K, list[T]]:
            """Groups elements based on the provided function."""
            # Delegates to the standalone grouping_by function
            return grouping_by(group_by_func, elements)

        return transform

    @staticmethod
    def grouping_by_mapping(
        group_by_func: Callable[[T], K],
        mapper: Callable[[T], R],
    ) -> Callable[[Iterable[T]], dict[K, list[R]]]:
        """
        Returns a collector function that groups mapped elements into a dictionary based on a
        classification function.

        The classification function (`group_by_func`) is applied to each element, and the
        result is used as the key in the dictionary. Each value in the dictionary
        is a list of elements that produced the corresponding key.

        Usage:
            grouped_dict = stream_instance.collect_using(Collectors.grouping_by(lambda x: x.category, lambda x: x.value))

        Args:
            group_by_func (Callable[[T], R]): The function to classify mapped elements into groups.

        Returns:
            Callable[[Iterable[T]], dict[K, list[R]]]: A function that takes an iterable
            and returns a dictionary grouped by the classification function.
        """

        def transform(elements: Iterable[T]) -> dict[K, list[R]]:
            """Groups elements based on the provided function."""
            # Delegates to the standalone grouping_by function
            return grouping_by_mapping(group_by_func, elements, mapper)

        return transform

    @staticmethod
    def joining(separator: str = "") -> Callable[[Iterable[str]], str]:
        """
        Returns a collector function that concatenates string elements into a single string,
        separated by the specified separator.

        Usage:
            joined_string = stream_of_strings.collect_using(Collectors.joining(","))
            joined_string_no_sep = stream_of_strings.collect_using(Collectors.joining())

        Args:
            separator (str, optional): The string to use as a separator. Defaults to "".

        Returns:
            Callable[[Iterable[str]], str]: A function that takes an iterable of strings
            and returns a single joined string.
        """
        # Delegates to the standalone joining function using a lambda
        return lambda it: joining(separator, it)

    @staticmethod
    def partitioning_by(
        condition: Callable[[T], bool],
    ) -> Callable[[Iterable[T]], dict[bool, list[T]]]:
        """
        Returns a collector function that partitions elements into a dictionary
        based on whether they satisfy a given predicate (condition).

        The dictionary will have two keys: `True` and `False`. The value associated
        with `True` is a list of elements for which the condition returned True,
        and the value associated with `False` is a list of elements for which
        the condition returned False.

        Usage:
            partitioned_dict = stream_instance.collect_using(Collectors.partitioning_by(lambda x: x > 10))

        Args:
            condition (Callable[[T], bool]): The predicate used to partition elements.

        Returns:
            Callable[[Iterable[T]], dict[bool, list[T]]]: A function that takes an iterable
            and returns a dictionary partitioned by the condition.
        """

        return Collectors.grouping_by(condition)

    @staticmethod
    def partitioning_by_mapping(
        condition: Callable[[T], bool],
        mapper: Callable[[T], R],
    ) -> Callable[[Iterable[T]], dict[bool, list[R]]]:
        """
        Returns a collector function that partitions mapped elements into a dictionary
        based on whether they satisfy a given predicate (condition).

        The dictionary will have two keys: `True` and `False`. The value associated
        with `True` is a list of mapped elements for which the condition returned True,
        and the value associated with `False` is a list of mapped elements for which
        the condition returned False.

        Usage:
            partitioned_dict = stream_instance.collect_using(Collectors.partitioning_by(lambda x: x > 10, lambda x: x*x))

        Args:
            condition (Callable[[T], bool]): The predicate used to partition elements.
            mapper (Callable[[T], R]): The mapper function

        Returns:
            Callable[[Iterable[T]], dict[bool, list[R]]]: A function that takes an iterable
            and returns a dictionary partitioned by the condition.
        """

        return Collectors.grouping_by_mapping(condition, mapper)

    @staticmethod
    def counting() -> Callable[[Iterable[Any]], int]:
        """
        Returns a collector function that counts the number of elements.

        Usage:
            count = stream_instance.collect_using(Collectors.counting())

        Returns:
            Callable[[Iterable[Any]], int]: A function that takes an iterable and returns its count.
        """

        def transform(elements: Iterable[Any]) -> int:
            """Counts the elements in the iterable."""
            # Using sum(1 for _ in elements) is generally efficient for iterables
            return sum(1 for _ in elements)

        return transform

    @staticmethod
    def summing_int() -> Callable[[Iterable[int]], int]:
        """
        Returns a collector function that sums integer elements.
        Assumes the iterable contains integers.

        Usage:
            total = stream_of_ints.collect_using(Collectors.summing_int())

        Returns:
            Callable[[Iterable[int]], int]: A function that takes an iterable of ints and returns their sum.
        """

        def transform(elements: Iterable[int]) -> int:
            """Sums the integer elements."""
            return sum(elements)

        return transform

    @staticmethod
    def averaging_float() -> Callable[[Iterable[float]], Optional[float]]:
        """
        Returns a collector function that calculates the average of float elements.
        Returns None if the iterable is empty. Assumes the iterable contains floats.

        Usage:
            avg = stream_of_floats.collect_using(Collectors.averaging_float())

        Returns:
            Callable[[Iterable[float]], Optional[float]]: A function that takes an iterable of floats
                                                        and returns their average, or None if empty.
        """

        def transform(elements: Iterable[float]) -> Optional[float]:
            """Calculates the average of float elements."""
            count = 0
            total = 0.0
            for element in elements:
                total += element
                count += 1
            return total / count if count > 0 else None

        return transform

    @staticmethod
    def max_by(comparator: Callable[[T, T], int]) -> Callable[[Iterable[T]], Opt[T]]:
        """
        Returns a collector function that finds the maximum element according to the
        provided comparator. Returns an empty Opt if the iterable is empty.

        Usage:
            max_opt = stream_instance.collect_using(Collectors.max_by(my_comparator))

        Args:
            comparator (Callable[[T, T], int]): A function that compares two elements,
                                                returning > 0 if first is greater, < 0 if second is greater, 0 if equal.

        Returns:
            Callable[[Iterable[T]], Opt[T]]: A function that takes an iterable and returns an Opt
                                            containing the maximum element, or empty Opt if none.
        """
        key_func = cmp_to_key(comparator)

        def transform(elements: Iterable[T]) -> Opt[T]:
            """Finds the maximum element using the comparator."""
            try:
                # max() with a key function derived from the comparator
                return Opt(max(elements, key=key_func))
            except ValueError:  # max() raises ValueError on empty sequence
                return Opt(None)

        return transform

    @staticmethod
    def to_tuple() -> Callable[[Iterable[T]], tuple[T, ...]]:
        """
        Returns a collector function that accumulates stream elements into a tuple.
        """
        return lambda elements: tuple(elements)

    @staticmethod
    def summing_float() -> Callable[[Iterable[float]], float]:
        """
        Returns a collector function that sums float elements.
        Assumes the iterable contains floats.

        Usage:
            total = stream_of_floats.collect_using(Collectors.summing_float())

        Returns:
            Callable[[Iterable[float]], float]: A function that takes an iterable of floats and returns their sum.
        """

        def transform(elements: Iterable[float]) -> float:
            """Sums the float elements."""
            return sum(elements)

        return transform

    @staticmethod
    def averaging_int() -> Callable[[Iterable[int]], Optional[float]]:
        """
        Returns a collector function that calculates the average of integer elements.
        Returns None if the iterable is empty. Assumes the iterable contains integers.
        The result is always a float.

        Usage:
            avg = stream_of_ints.collect_using(Collectors.averaging_int())

        Returns:
            Callable[[Iterable[int]], Optional[float]]: A function that takes an iterable of ints
                                                        and returns their average as a float, or None if empty.
        """

        def transform(elements: Iterable[int]) -> Optional[float]:
            """Calculates the average of integer elements."""
            count = 0
            total = 0
            for element in elements:
                total += element
                count += 1
            return float(total) / count if count > 0 else None

        return transform

    @staticmethod
    def min_by(comparator: Callable[[T, T], int]) -> Callable[[Iterable[T]], Opt[T]]:
        """
        Returns a collector function that finds the minimum element according to the
        provided comparator. Returns an empty Opt if the iterable is empty.

        Usage:
            min_opt = stream_instance.collect_using(Collectors.min_by(my_comparator))

        Args:
            comparator (Callable[[T, T], int]): A function that compares two elements,
                                                returning > 0 if first is greater, < 0 if second is greater, 0 if equal.

        Returns:
            Callable[[Iterable[T]], Opt[T]]: A function that takes an iterable and returns an Opt
                                            containing the minimum element, or empty Opt if none.
        """
        key_func = cmp_to_key(comparator)

        def transform(elements: Iterable[T]) -> Opt[T]:
            """Finds the minimum element using the comparator."""
            try:
                # min() with a key function derived from the comparator
                return Opt(min(elements, key=key_func))
            except ValueError:  # min() raises ValueError on empty sequence
                return Opt(None)

        return transform
