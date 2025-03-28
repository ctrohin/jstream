from typing import Callable, Generic, Optional, TypeVar, Union, cast, overload

from jstreams.stream import stream, Predicate
from jstreams.utils import is_callable, require_non_null


T = TypeVar("T")
V = TypeVar("V")


class Case(Generic[T, V]):
    __slots__ = ["__matching", "__resulting"]

    def __init__(
        self,
        matching: Union[T, Callable[[T], bool], Predicate[T]],
        resulting: Union[V, Callable[[], V]],
    ) -> None:
        self.__matching = matching
        self.__resulting = resulting

    def matches(self, value: T) -> bool:
        if isinstance(self.__matching, Predicate):
            return cast(Predicate[T], self.__matching).apply(value)
        if is_callable(self.__matching):
            return cast(Callable[[T], bool], self.__matching)(value)
        return value == self.__matching

    def result(self) -> V:
        if is_callable(self.__resulting):
            return cast(Callable[[], V], self.__resulting)()
        return cast(V, self.__resulting)


class DefaultCase(Case[T, V]):
    def __init__(
        self,
        resulting: Union[V, Callable[[], V]],
    ) -> None:
        super().__init__(lambda _: True, resulting)


class Match(Generic[T]):
    __slots__ = ["__value"]

    def __init__(self, value: T) -> None:
        self.__value = value

    @overload
    def of(self, case1: Case[T, V]) -> Optional[V]: ...

    @overload
    def of(self, case1: Case[T, V], case2: Case[T, V]) -> Optional[V]: ...

    @overload
    def of(
        self, case1: Case[T, V], case2: Case[T, V], case3: Case[T, V]
    ) -> Optional[V]: ...

    @overload
    def of(
        self, case1: Case[T, V], case2: Case[T, V], case3: Case[T, V], case4: Case[T, V]
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
        case10: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
        case10: Case[T, V],
        case11: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
        case10: Case[T, V],
        case11: Case[T, V],
        case12: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
        case10: Case[T, V],
        case11: Case[T, V],
        case12: Case[T, V],
        case13: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
        case10: Case[T, V],
        case11: Case[T, V],
        case12: Case[T, V],
        case13: Case[T, V],
        case14: Case[T, V],
    ) -> Optional[V]: ...

    @overload
    def of(
        self,
        case1: Case[T, V],
        case2: Case[T, V],
        case3: Case[T, V],
        case4: Case[T, V],
        case5: Case[T, V],
        case6: Case[T, V],
        case7: Case[T, V],
        case8: Case[T, V],
        case9: Case[T, V],
        case10: Case[T, V],
        case11: Case[T, V],
        case12: Case[T, V],
        case13: Case[T, V],
        case14: Case[T, V],
        case15: Case[T, V],
    ) -> Optional[V]: ...

    def of(
        self,
        case1: Case[T, V],
        case2: Optional[Case[T, V]] = None,
        case3: Optional[Case[T, V]] = None,
        case4: Optional[Case[T, V]] = None,
        case5: Optional[Case[T, V]] = None,
        case6: Optional[Case[T, V]] = None,
        case7: Optional[Case[T, V]] = None,
        case8: Optional[Case[T, V]] = None,
        case9: Optional[Case[T, V]] = None,
        case10: Optional[Case[T, V]] = None,
        case11: Optional[Case[T, V]] = None,
        case12: Optional[Case[T, V]] = None,
        case13: Optional[Case[T, V]] = None,
        case14: Optional[Case[T, V]] = None,
        case15: Optional[Case[T, V]] = None,
        case16: Optional[Case[T, V]] = None,
    ) -> Optional[V]:
        return (
            stream(
                [
                    case1,
                    case2,
                    case3,
                    case4,
                    case5,
                    case6,
                    case7,
                    case8,
                    case9,
                    case10,
                    case11,
                    case12,
                    case13,
                    case14,
                    case15,
                    case16,
                ]
            )
            .non_null()
            .map(require_non_null)
            .find_first(lambda c: c.matches(self.__value))
            .map(lambda c: c.result())
            .get_actual()
        )


def case(
    matching: Union[T, Callable[[T], bool], Predicate[T]],
    resulting: Union[V, Callable[[], V]],
) -> Case[T, V]:
    return Case(matching, resulting)


def match(value: T) -> Match[T]:
    return Match(value)


def match_opt(value: Optional[T]) -> Match[Optional[T]]:
    return Match(value)


def default_case(resulting: Union[V, Callable[[], V]]) -> Case[T, V]:
    return DefaultCase(resulting)
