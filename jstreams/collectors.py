from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
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
