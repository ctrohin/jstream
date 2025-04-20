from threading import Lock
from typing import Any, Callable, Generic, Optional, TypeVar, overload

from jstreams.rx import (
    ObservableSubscription,
    Pipe,
    PipeObservable,
    RxOperator,
    SingleValueSubject,
)
from jstreams.stream import Opt, Stream

T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
E = TypeVar("E")
F = TypeVar("F")
G = TypeVar("G")
H = TypeVar("H")
J = TypeVar("J")
K = TypeVar("K")
L = TypeVar("L")
M = TypeVar("M")
N = TypeVar("N")
V = TypeVar("V")

__DEFAULT_EVENT_NAME__ = "__default__"


class Event(Generic[T]):
    __slots__ = ["__subject"]

    def __init__(self, subject: SingleValueSubject[T]) -> None:
        self.__subject = subject

    def publish(self, event: T) -> None:
        self.__subject.on_next(event)

    def subscribe(
        self,
        on_publish: Callable[[T], Any],
    ) -> ObservableSubscription[T]:
        return self.__subject.subscribe(on_publish)

    @overload
    def pipe(
        self,
        op1: RxOperator[T, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, G],
        op8: RxOperator[G, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, G],
        op8: RxOperator[G, H],
        op9: RxOperator[H, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, G],
        op8: RxOperator[G, H],
        op9: RxOperator[H, N],
        op10: RxOperator[N, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, G],
        op8: RxOperator[G, H],
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
        op11: RxOperator[J, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, G],
        op8: RxOperator[G, H],
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
        op11: RxOperator[J, K],
        op12: RxOperator[K, V],
    ) -> PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, F],
        op7: RxOperator[F, G],
        op8: RxOperator[G, H],
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
        op11: RxOperator[J, K],
        op12: RxOperator[K, L],
        op13: RxOperator[L, V],
    ) -> PipeObservable[T, V]: ...

    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: Optional[RxOperator[A, B]] = None,
        op3: Optional[RxOperator[B, C]] = None,
        op4: Optional[RxOperator[C, D]] = None,
        op5: Optional[RxOperator[D, E]] = None,
        op6: Optional[RxOperator[E, F]] = None,
        op7: Optional[RxOperator[F, G]] = None,
        op8: Optional[RxOperator[G, H]] = None,
        op9: Optional[RxOperator[H, N]] = None,
        op10: Optional[RxOperator[N, J]] = None,
        op11: Optional[RxOperator[J, K]] = None,
        op12: Optional[RxOperator[K, L]] = None,
        op13: Optional[RxOperator[L, M]] = None,
        op14: Optional[RxOperator[M, V]] = None,
    ) -> PipeObservable[T, V]:
        op_list = (
            Stream(
                [
                    op1,
                    op2,
                    op3,
                    op4,
                    op5,
                    op6,
                    op7,
                    op8,
                    op9,
                    op10,
                    op11,
                    op12,
                    op13,
                    op14,
                ]
            )
            .non_null()
            .to_list()
        )
        return PipeObservable(self.__subject, Pipe(T, Any, op_list))  # type: ignore


class _EventBroadcaster:
    _instance: Optional["_EventBroadcaster"] = None
    _instance_lock = Lock()

    def __init__(self) -> None:
        self._subjects: dict[type, dict[str, SingleValueSubject[Any]]] = {}

    def clear(self) -> "_EventBroadcaster":
        """
        Clear all events.
        """
        Stream(self._subjects.values()).each(
            lambda s: Stream(s.values()).each(lambda s: s.dispose())
        )
        self._subjects.clear()
        return self

    def clear_event(self, event_type: type) -> "_EventBroadcaster":
        """
        Clear a specific event.

        Args:
            event_type (type): The event type
        """
        (
            Opt(self._subjects.pop(event_type))
            .map(lambda d: Stream(d.values()))
            .if_present(lambda s: s.each(lambda s: s.dispose()))
        )
        return self

    def get_event(
        self, event_type: type[T], event_name: str = __DEFAULT_EVENT_NAME__
    ) -> Event[T]:
        if event_type not in self._subjects:
            self._subjects[event_type] = {}
        if event_name not in self._subjects[event_type]:
            self._subjects[event_type][event_name] = Event(SingleValueSubject(None))  # type: ignore[assignment]
        return self._subjects[event_type][event_name]  # type: ignore[return-value]

    @staticmethod
    def get_instance() -> "_EventBroadcaster":
        if _EventBroadcaster._instance is None:
            with _EventBroadcaster._instance_lock:
                if _EventBroadcaster._instance is None:
                    _EventBroadcaster._instance = _EventBroadcaster()
        return _EventBroadcaster._instance


def events() -> _EventBroadcaster:
    """
    Get the event broadcaster instance.
    """
    return _EventBroadcaster.get_instance()


def event(event_type: type[T], event_name: str = __DEFAULT_EVENT_NAME__) -> Event[T]:
    return _EventBroadcaster.get_instance().get_event(event_type, event_name)
