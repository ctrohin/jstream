from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K")


def groupingBy(groupBy: Callable[[T], K], elements: Iterable[T]) -> dict[K, list[T]]:
    values: dict[K, list[T]] = {}
    for element in elements:
        key = groupBy(element)
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
    def toList() -> Callable[[Iterable[T]], list[T]]:
        def transform(elements: Iterable[T]) -> list[T]:
            return list(elements)

        return transform

    @staticmethod
    def toSet() -> Callable[[Iterable[T]], set[T]]:
        def transform(elements: Iterable[T]) -> set[T]:
            return set(elements)

        return transform

    @staticmethod
    def groupingBy(
        groupBy: Callable[[T], K],
    ) -> Callable[[Iterable[T]], dict[K, list[T]]]:
        def transform(elements: Iterable[T]) -> dict[K, list[T]]:
            return groupingBy(groupBy, elements)

        return transform

    @staticmethod
    def joining(separator: str = "") -> Callable[[Iterable[str]], str]:
        return lambda it: joining(separator, it)

    @staticmethod
    def partitioningBy(
        condition: Callable[[T], bool],
    ) -> Callable[[Iterable[T]], dict[bool, list[T]]]:
        def transform(elements: Iterable[T]) -> dict[bool, list[T]]:
            return groupingBy(condition, elements)

        return transform
