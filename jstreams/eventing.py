from threading import Lock
from typing import Any, Callable, Generic, Optional, TypeVar, overload

from jstreams.rx import (
    DisposeHandler,
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


class _Event(Generic[T]):
    __slots__ = ["__subject"]

    def __init__(self, subject: SingleValueSubject[T]) -> None:
        self.__subject = subject

    def publish(self, event: T) -> None:
        """
        Publishes an event of type T to all current subscribers of this channel.

        Args:
            event (T): The event object to publish.
        """
        self.__subject.on_next(event)

    def subscribe(
        self,
        on_publish: Callable[[T], Any],
        on_dispose: DisposeHandler = None,
    ) -> ObservableSubscription[T]:
        """
        Subscribes to events published on this channel.

        Args:
            on_publish (Callable[[T], Any]): The function to call whenever an event is published.
                                            It receives the published event object as its argument.
            on_dispose (DisposeHandler, optional): A function to call when the subscription is disposed.
                                                Defaults to None.

        Returns:
            ObservableSubscription[T]: An object representing the subscription, which can be used
                                    to cancel the subscription later (`.cancel()`).
        """
        return self.__subject.subscribe(on_publish, on_dispose=on_dispose)

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

    def _destroy(self) -> None:
        self.__subject.dispose()

    def latest(self) -> Optional[T]:
        return self.__subject.latest()


class _EventBroadcaster:
    _instance: Optional["_EventBroadcaster"] = None
    _instance_lock = Lock()
    _event_lock = Lock()

    def __init__(self) -> None:
        self._subjects: dict[type, dict[str, _Event[Any]]] = {}

    def clear(self) -> "_EventBroadcaster":
        """
        Clear all events.
        """
        with self._event_lock:
            Stream(self._subjects.values()).each(
                lambda s: Stream(s.values()).each(lambda s: s._destroy())
            )
            self._subjects.clear()
        return self

    def clear_event(self, event_type: type) -> "_EventBroadcaster":
        """
        Clear a specific event.

        Args:
            event_type (type): The event type
        """
        with self._event_lock:
            (
                Opt(self._subjects.pop(event_type))
                .map(lambda d: Stream(d.values()))
                .if_present(lambda s: s.each(lambda s: s._destroy()))
            )
        return self

    def get_event(
        self, event_type: type[T], event_name: str = __DEFAULT_EVENT_NAME__
    ) -> _Event[T]:
        with self._event_lock:
            if event_type not in self._subjects:
                self._subjects[event_type] = {}
            if event_name not in self._subjects[event_type]:
                self._subjects[event_type][event_name] = _Event(
                    SingleValueSubject(None)
                )
            return self._subjects[event_type][event_name]

    @staticmethod
    def get_instance() -> "_EventBroadcaster":
        if _EventBroadcaster._instance is None:
            with _EventBroadcaster._instance_lock:
                if _EventBroadcaster._instance is None:
                    _EventBroadcaster._instance = _EventBroadcaster()
        return _EventBroadcaster._instance


class EventBroadcaster:
    """
    Public interface for event broadcaster
    """

    _instance: Optional["EventBroadcaster"] = None
    _instance_lock = Lock()

    @staticmethod
    def get_instance() -> "EventBroadcaster":
        if EventBroadcaster._instance is None:
            with EventBroadcaster._instance_lock:
                if EventBroadcaster._instance is None:
                    EventBroadcaster._instance = EventBroadcaster()
        return EventBroadcaster._instance

    def clear_event(self, event_type: type) -> "EventBroadcaster":
        """
        Clear a specific event.

        Args:
            event_type (type): The event type
        """
        _EventBroadcaster.get_instance().clear_event(event_type)
        return self

    def clear(self) -> "EventBroadcaster":
        """
        Clear all events.
        """
        _EventBroadcaster.get_instance().clear()
        return self


def events() -> EventBroadcaster:
    """
    Get the event broadcaster instance.
    """
    return EventBroadcaster.get_instance()


def event(event_type: type[T], event_name: str = __DEFAULT_EVENT_NAME__) -> _Event[T]:
    """
    Retrieves or creates a specific event channel based on type and name.

    This function acts as the main entry point for accessing event streams managed
    by the global `_EventBroadcaster`. It returns an `_Event` object which allows
    publishing events of the specified `event_type` and subscribing to receive them.

    If an event channel for the given `event_type` and `event_name` does not
    exist, it will be created automatically, backed by a `SingleValueSubject`.
    Subsequent calls with the same type and name will return the *same* channel instance.

    Args:
        event_type (type[T]): The class/type of the event objects that will be
                                published and received on this channel (e.g., `str`,
                                `int`, a custom data class).
        event_name (str, optional): A name to distinguish between multiple event
                                    channels that might use the same `event_type`.
                                    Useful for creating separate streams for the same
                                    kind of data. Defaults to `__DEFAULT_EVENT_NAME__`
                                    (which is "__default__").

    Returns:
        _Event[T]: An object representing the specific event channel. This object
                    provides methods for:
                    - Publishing events: `.publish(event_instance)`
                    - Subscribing to events: `.subscribe(on_next_callback, ...)`
                    - Piping events through Rx operators: `.pipe(operator1, ...)`
                    - Getting the latest published event (if any): `.latest()`

                    Note: Since the underlying mechanism uses a `SingleValueSubject`,
                    new subscribers do *not* receive the most recently published event
                    upon subscription. However, that value can be retrieved using the `latest`
                    function on the event itself.

    Example:
        >>> from jstreams import event, rx_map

        >>> # Get the default event channel for strings
        >>> string_event = event(str)

        >>> # Subscribe to receive string events
        >>> def handle_string(s: str):
        ...     print(f"Received string: {s}")
        >>> subscription = string_event.subscribe(handle_string)

        >>> # Publish a string event
        >>> string_event.publish("Hello")
        Received string: Hello

        >>> # Get a named event channel for integers
        >>> counter_event = event(int, event_name="counter")

        >>> # Subscribe to the counter event via a pipe
        >>> def handle_doubled_count(c: int):
        ...     print(f"Doubled count: {c}")
        >>> counter_pipe_sub = counter_event.pipe(rx_map(lambda x: x * 2)).subscribe(handle_doubled_count)

        >>> # Publish to the counter event
        >>> counter_event.publish(5)
        Doubled count: 10

        >>> # Clean up subscriptions (optional but good practice)
        >>> subscription.cancel()
        >>> counter_pipe_sub.cancel()
    """
    return _EventBroadcaster.get_instance().get_event(event_type, event_name)
