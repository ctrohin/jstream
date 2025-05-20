import inspect
from threading import Lock, Event as ThreadingEvent
from typing import Any, Callable, Generic, Optional, TypeVar, Union, overload

from jstreams.predicate import Predicate
from jstreams.rx import (
    RX,
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

ClsT = TypeVar("ClsT", bound=type)
__DEFAULT_EVENT_NAME__ = "__default__"
# Attribute name for storing event listener metadata on function objects
# Using a somewhat unique name to minimize collision chances.
_EVENT_LISTENERS_METADATA_ATTR = "_jstreams_event_listeners_metadata_"


class EventSubscription(Generic[T]):
    slots = ("__subscription",)

    def __init__(self, subscription: ObservableSubscription[T]) -> None:
        self.__subscription = subscription

    def pause(self) -> None:
        """
        Pause the subscription. While paused, the subscription will not receive any incoming events.
        """
        self.__subscription.pause()

    def resume(self) -> None:
        """
        Resume the subscription. When resumed, the subscription will start receiving upcoming events.
        """
        self.__subscription.resume()

    def cancel(self) -> None:
        """
        Cancel the subscription. Once canceled, the subscription will no longer receive events.
        NOTE: Pause/resume will have no effect once the subscription is canceled.
        """
        self.__subscription.cancel()
        self.__subscription.dispose()

    def is_paused(self) -> bool:
        """
        Checks if the subscription is paused.

        Returns:
            bool: True if the subscription is paused, False if the subscription is active.
        """
        return self.__subscription.is_paused()


class _Event(Generic[T]):
    __slots__ = ("__subject",)

    def __init__(self, subject: SingleValueSubject[T]) -> None:
        self.__subject = subject

    def publish(self, event: T) -> None:  # pylint: disable=redefined-outer-name
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
    ) -> EventSubscription[T]:
        """
        Subscribes to events published on this channel.

        Args:
            on_publish (Callable[[T], Any]): The function to call whenever an event is published.
                                            It receives the published event object as its argument.
            on_dispose (DisposeHandler, optional): A function to call when the subscription is disposed.
                                                Defaults to None.

        Returns:
            EventSubscription[T]: An object representing the subscription, which can be used
                                    to pause, resume or cancel the subscription later.
        """
        return EventSubscription(
            self.__subject.subscribe(
                on_publish, on_dispose=on_dispose, asynchronous=True
            )
        )

    def publish_if(
        self, event_payload: T, condition: Union[Callable[[T], bool], Predicate[T]]
    ) -> bool:
        """
        Publishes the event only if the condition is met.
        Args:
            event_payload (T): The event to potentially publish.
            condition (Callable[[T], bool]): A function that takes the event and returns True if it should be published.
        Returns:
            bool: True if the event was published, False otherwise.
        """
        if condition(event_payload):
            self.publish(event_payload)
            return True
        return False

    def subscribe_once(
        self,
        on_publish: Callable[[T], Any],
        on_dispose: DisposeHandler = None,
    ) -> EventSubscription[T]:
        """
        Subscribes to the event channel for only the very next event.
        The subscription is automatically canceled after the first event is received.

        Args:
            on_publish (Callable[[T], Any]): The function to call when the next event is published.
            on_dispose (DisposeHandler, optional): A function to call when the subscription is disposed
                                                (either after the event or if canceled manually).
                                                Defaults to None.

        Returns:
            EventSubscription[T]: An object representing the subscription.
        """
        # Uses RX.take(1) to limit to one event
        return EventSubscription(
            self.pipe(RX.take(T, 1)).subscribe(  # type: ignore[misc]
                on_publish, on_dispose=on_dispose, asynchronous=True
            )
        )

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

    def __event_is_present(self, event_type: type, event_name: str) -> bool:
        return event_type in self._subjects and event_name in self._subjects[event_type]

    def has_event(
        self, event_type: type, event_name: str = __DEFAULT_EVENT_NAME__
    ) -> bool:
        # Try to find the event without locking
        found = self.__event_is_present(event_type, event_name)
        # If we can't find the event, try with locking
        if not found:
            with self._event_lock:
                return self.__event_is_present(event_type, event_name)
        return found

    def get_event(
        self, event_type: type[T], event_name: str = __DEFAULT_EVENT_NAME__
    ) -> _Event[T]:
        # Check if we have the event without locking
        if self.__event_is_present(event_type, event_name):
            # And return it
            return self._subjects[event_type][event_name]
        # Otherwise, lock and create the subject if needed
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

    def has_event(
        self, event_type: type, event_name: str = __DEFAULT_EVENT_NAME__
    ) -> bool:
        """
        Check if an event exists.

        Args:
            event_type (type): The event type
            event_name (str): The event name

        Returns:
            bool: True if the event exists, False otherwise.
        """
        return _EventBroadcaster.get_instance().has_event(event_type, event_name)

    def get_event_types(self) -> list[type]:
        """
        Get all event types.

        Returns:
            list[type]: A list of all event types.
        """
        return list(_EventBroadcaster.get_instance()._subjects.keys())


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


def on_event(
    event_type: type, event_name: str = __DEFAULT_EVENT_NAME__
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Method decorator to mark a method as a listener for a specific event.

    When a class is decorated with `@managed_events`, methods decorated
    with `@on_event` will be automatically subscribed to the specified event.
    The decorated method will be called with the event payload as its single
    argument (after `self`).

    A method can be decorated multiple times with `@on_event` to listen to
    different events.

    Args:
        event_type (type): The type of the event to listen for.
        event_name (str, optional): The specific name of the event channel.
                                    Defaults to `__DEFAULT_EVENT_NAME__`.
    """

    def decorator(method: Callable[..., Any]) -> Callable[..., Any]:
        if not hasattr(method, _EVENT_LISTENERS_METADATA_ATTR):
            setattr(method, _EVENT_LISTENERS_METADATA_ATTR, [])
        # Store as a list of tuples (event_type, event_name)
        getattr(method, _EVENT_LISTENERS_METADATA_ATTR).append((event_type, event_name))
        return method

    return decorator


def managed_events() -> Callable[[ClsT], ClsT]:
    """
    Class decorator that automatically subscribes methods marked with `@on_event`
    to their respective events and manages their subscriptions.

    It wraps the class's `__init__` method to set up subscriptions after
    the instance is initialized. Subscriptions are made for `@on_event` decorated
    methods found in the class itself and its base classes.

    A `dispose_managed_events()` method is added to the class for explicit cleanup
    of all subscriptions made through this mechanism for an instance.

    The decorated class also becomes a context manager, so using an instance
    in a `with` statement will automatically call `dispose_managed_events()`
    on exit.
    """

    def decorator(cls: ClsT) -> ClsT:
        """
        Inner decorator function that modifies the class.
        """
        original_init = cls.__init__  # type: ignore[misc]

        def new_init(self: object, *args: Any, **kwargs: Any) -> None:
            # Call the original __init__ first. This allows base class initializers
            # (potentially also decorated by managed_events) to run and set up their part.
            original_init(self, *args, **kwargs)

            # Initialize instance-specific storage for subscriptions and setup tracking.
            # These are initialized here to ensure they exist before any method tries to use them.
            if not hasattr(self, "_managed_event_subscriptions"):
                self._managed_event_subscriptions: list[  # type: ignore[misc,attr-defined]
                    ObservableSubscription[Any]
                ] = []
            if not hasattr(self, "_already_setup_managed_handlers"):
                # Stores (function_object, event_type, event_name) to avoid double setup
                # for the same handler on the same instance, especially with inheritance.
                self._already_setup_managed_handlers: set[  # type: ignore[attr-defined,misc]
                    tuple[Callable[..., Any], type, str]
                ] = set()

            # Discover and subscribe event handlers from this class and its bases.
            # Iterate over all methods of the instance (including inherited ones).
            for _name, method_obj in inspect.getmembers(
                self, predicate=inspect.ismethod
            ):
                # The metadata is stored on the original function object, not the bound method.
                func_obj = method_obj.__func__
                if hasattr(func_obj, _EVENT_LISTENERS_METADATA_ATTR):
                    event_info_list = getattr(func_obj, _EVENT_LISTENERS_METADATA_ATTR)
                    for etype, ename in event_info_list:
                        handler_key = (func_obj, etype, ename)
                        if handler_key not in self._already_setup_managed_handlers:  # type: ignore[attr-defined]
                            # 'method_obj' is the bound method (e.g., self.method_name)
                            subscription = event(etype, ename).subscribe(method_obj)
                            self._managed_event_subscriptions.append(subscription)  # type: ignore[attr-defined]
                            self._already_setup_managed_handlers.add(handler_key)  # type: ignore[attr-defined]

        cls.__init__ = new_init  # type: ignore[misc]

        # Define and add the explicit cleanup method
        def dispose_managed_events(self_instance: object) -> None:
            if hasattr(self_instance, "_managed_event_subscriptions"):
                subscriptions = getattr(self_instance, "_managed_event_subscriptions")
                for sub in subscriptions:
                    try:
                        sub.cancel()
                    except Exception:  # pragma: no cover
                        pass  # Best effort to cancel
                subscriptions.clear()
            if hasattr(self_instance, "_already_setup_managed_handlers"):
                getattr(self_instance, "_already_setup_managed_handlers").clear()

        setattr(cls, "dispose_managed_events", dispose_managed_events)

        # Add context manager methods for automatic cleanup
        if not hasattr(cls, "__enter__"):
            setattr(cls, "__enter__", lambda self_instance: self_instance)
        if not hasattr(cls, "__exit__"):
            setattr(
                cls,
                "__exit__",
                lambda self_instance, exc_type, exc_val, exc_tb: getattr(
                    self_instance, "dispose_managed_events"
                )(),
            )

        return cls

    return decorator


def dispose_managed_events_from(obj: Any) -> None:
    """
    Dispose managed events for the given object, if the object has one.

    Args:
        obj (Any): The object to dispose managed events for.
    """
    if hasattr(obj, "dispose_managed_events"):
        try:
            obj.dispose_managed_events()
        except BaseException as _:
            pass


def wait_for_event(
    event_type: type[T],
    event_name: str = __DEFAULT_EVENT_NAME__,
    timeout: Optional[float] = None,
    condition: Optional[Callable[[T], bool]] = None,
) -> Opt[T]:
    received_signal = ThreadingEvent()
    payload_holder: list[T] = []  # Use list for closure modification
    payload_lock = Lock()

    def _on_event(data: T) -> None:
        with payload_lock:
            if not payload_holder:  # Process only the first valid event
                if condition is None or condition(data):
                    payload_holder.append(data)
                    received_signal.set()

    subscription = event(event_type, event_name).subscribe(_on_event)

    try:
        if not received_signal.wait(timeout):
            return Opt.empty()  # Timeout

        with payload_lock:
            return Opt.of_nullable(payload_holder[0] if payload_holder else None)
    finally:
        subscription.cancel()
