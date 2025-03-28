from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


def grouping_by(group_by: Callable[[T], K], elements: Iterable[T]) -> dict[K, list[T]]:
    values: dict[K, list[T]] = {}
    for element in elements:
        key = group_by(element)
        if key in values:
            arr = values.get(key)
            if arr is not None:
                arr.append(element)
        else:
            values[key] = [element]
    return values


def joining(separator: str, elements: Iterable[str]) -> str:
    return separator.join(elements)


class Collectors:
    @staticmethod
    def to_list() -> Callable[[Iterable[T]], list[T]]:
        def transform(elements: Iterable[T]) -> list[T]:
            return list(elements)

        return transform

    @staticmethod
    def to_set() -> Callable[[Iterable[T]], set[T]]:
        def transform(elements: Iterable[T]) -> set[T]:
            return set(elements)

        return transform

    @staticmethod
    def grouping_by(
        group_by: Callable[[T], K],
    ) -> Callable[[Iterable[T]], dict[K, list[T]]]:
        def transform(elements: Iterable[T]) -> dict[K, list[T]]:
            return grouping_by(group_by, elements)

        return transform

    @staticmethod
    def joining(separator: str = "") -> Callable[[Iterable[str]], str]:
        return lambda it: joining(separator, it)

    @staticmethod
    def partitioning_by(
        condition: Callable[[T], bool],
    ) -> Callable[[Iterable[T]], dict[bool, list[T]]]:
        def transform(elements: Iterable[T]) -> dict[bool, list[T]]:
            return grouping_by(condition, elements)

        return transform
