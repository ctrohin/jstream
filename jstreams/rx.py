import logging
from threading import Lock, Thread
from typing import (
    Callable,
    Generic,
    Iterable,
    Optional,
    TypeVar,
    Any,
    cast,
    overload,
)
import uuid
from copy import deepcopy

from jstreams.predicate import not_strict
from jstreams.stream import Stream
import abc

from jstreams.utils import is_empty_or_none

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


ErrorHandler = Optional[Callable[[Exception], Any]]
CompletedHandler = Optional[Callable[[Optional[T]], Any]]
NextHandler = Callable[[T], Any]
DisposeHandler = Optional[Callable[[], Any]]


class RxOperator(Generic[T, V], abc.ABC):
    def __init__(self) -> None:
        pass

    def init(self) -> None:
        pass


class Pipe(Generic[T, V]):
    __slots__ = ("__operators",)

    def __init__(
        self,
        input_type: type[T],  # pylint: disable=unused-argument
        output_type: type[V],  # pylint: disable=unused-argument
        ops: list[RxOperator[Any, Any]],
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


class MultipleSubscriptionsException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ObservableSubscription(Generic[T]):
    __slots__ = (
        "__parent",
        "__on_next",
        "__on_error",
        "__on_completed",
        "__on_dispose",
        "__subscription_id",
        "__paused",
        "__asynchronous",
    )

    def __init__(
        self,
        parent: Any,
        on_next: NextHandler[T],
        on_error: ErrorHandler = None,
        on_completed: CompletedHandler[T] = None,
        on_dispose: DisposeHandler = None,
        asynchronous: bool = False,
    ) -> None:
        self.__parent = parent
        self.__on_next = on_next
        self.__on_error = on_error
        self.__on_completed = on_completed
        self.__on_dispose = on_dispose
        self.__subscription_id = str(uuid.uuid4())
        self.__paused = False
        self.__asynchronous = asynchronous

    def is_async(self) -> bool:
        return self.__asynchronous

    def get_subscription_id(self) -> str:
        return self.__subscription_id

    def on_next(self, obj: T) -> None:
        self.__on_next(obj)

    def on_error(self, ex: Exception) -> None:
        if self.__on_error:
            self.__on_error(ex)

    def on_completed(self, obj: Optional[T]) -> None:
        if self.__on_completed:
            self.__on_completed(obj)

    def is_paused(self) -> bool:
        return self.__paused

    def pause(self) -> None:
        self.__paused = True

    def resume(self) -> None:
        self.__paused = False

    def dispose(self) -> None:
        if self.__on_dispose:
            self.__on_dispose()

    def cancel(self) -> None:
        if hasattr(self.__parent, "cancel"):
            self.__parent.cancel(self)


class _ObservableParent(Generic[T]):
    def _push(self) -> None:
        pass

    def _push_to_sub_on_subscribe(self, sub: ObservableSubscription[T]) -> None:
        pass


class _OnNext(Generic[T]):
    def on_next(self, val: Optional[T]) -> None:
        if not hasattr(self, "__lock"):
            self.__lock = Lock()  # pylint: disable=attribute-defined-outside-init
        with self.__lock:
            self._on_next(val)

    def _on_next(self, val: Optional[T]) -> None:
        pass


class Subscribable(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def subscribe(
        self,
        on_next: NextHandler[T],
        on_error: ErrorHandler = None,
        on_completed: CompletedHandler[T] = None,
        on_dispose: DisposeHandler = None,
    ) -> ObservableSubscription[Any]:
        pass


class Piped(abc.ABC, Generic[T, V]):
    @overload
    def pipe(
        self,
        op1: RxOperator[T, V],
    ) -> "PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, V],
    ) -> "PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, V],
    ) -> "PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> "PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, V],
    ) -> "PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, V],
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

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
    ) -> "PipeObservable[T, V]": ...

    @abc.abstractmethod
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
    ) -> "PipeObservable[T, V]":
        pass


class _ObservableBase(Subscribable[T]):
    __slots__ = ("__subscriptions", "_parent", "_last_val")

    def __init__(self) -> None:
        self.__subscriptions: list[ObservableSubscription[Any]] = []
        self._parent: Optional[_ObservableParent[T]] = None
        self._last_val: Optional[T] = None

    def _notify_all_subs(self, val: T) -> None:
        self._last_val = val

        if self.__subscriptions is not None:
            # Notify async subscriptions first, so they can be executed in parallel
            sub_stream = Stream(self.__subscriptions)
            (
                sub_stream.filter(lambda s: not s.is_paused())
                .filter(lambda s: s.is_async())
                .each(lambda s: self._push_to_subscription(s, val))
            )
            # Notify sync subscriptions after async ones
            (
                sub_stream.filter(lambda s: not s.is_paused())
                .filter(lambda s: not s.is_async())
                .each(lambda s: self._push_to_subscription(s, val))
            )

    def __push_value(self, sub: ObservableSubscription[Any], val: T) -> None:
        try:
            sub.on_next(val)
        except Exception as e:
            if sub.on_error is not None:
                try:
                    sub.on_error(e)
                except Exception as exc:
                    # Log uncaught exceptions in the error handler
                    logging.getLogger("observable").error(exc)

    def _push_to_subscription(self, sub: ObservableSubscription[Any], val: T) -> None:
        if not sub.is_paused():
            if sub.is_async():
                Thread(target=lambda: self.__push_value(sub, val)).start()
            else:
                self.__push_value(sub, val)

    def subscribe(
        self,
        on_next: NextHandler[T],
        on_error: ErrorHandler = None,
        on_completed: CompletedHandler[T] = None,
        on_dispose: DisposeHandler = None,
        asynchronous: bool = False,
    ) -> ObservableSubscription[Any]:
        """
        Subscribe to this pipe in either synchronous(default) or asynchronous mode.
        The subscription will be executed in a thread pool if asynchronous is set to True.
        Asynchronous subscriptions will receive events emitted from the parent observable
        as soon as they are available. Synchronous subscriptions will receive events in the order of subscription.
        Heavy computations in the subscription will block the parent observable until the subscription is completed.
        As such, it is recommended to use asynchronous subscriptions for heavy computations.

        Args:
            on_next (NextHandler[V]): On next handler for incoming values
            on_error (ErrorHandler, optional): Error handler. Defaults to None.
            on_completed (CompletedHandler[V], optional): Competed handler. Defaults to None.
            on_dispose (DisposeHandler, optional): Dispose handler. Defaults to None.
            asynchronous (boolean): Flags if the subscription should be asynchronous. Asynchronous subscriptions
                                    are executed in a thread pool. Defaults to False.

        Returns:
            ObservableSubscription[V]: The subscription
        """

        sub = ObservableSubscription(
            self, on_next, on_error, on_completed, on_dispose, asynchronous
        )
        self.__subscriptions.append(sub)
        if self._parent is not None:
            self._parent._push_to_sub_on_subscribe(sub)
        return sub

    def cancel(self, sub: ObservableSubscription[Any]) -> None:
        (
            Stream(self.__subscriptions)
            .filter(lambda e: e.get_subscription_id() == sub.get_subscription_id())
            .each(self.__subscriptions.remove)
        )

    def dispose(self) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.dispose()))
        self.__subscriptions.clear()

    def pause(self, sub: ObservableSubscription[Any]) -> None:
        (
            Stream(self.__subscriptions)
            .filter(lambda e: e.get_subscription_id() == sub.get_subscription_id())
            .each(lambda s: s.pause())
        )

    def resume(self, sub: ObservableSubscription[Any]) -> None:
        (
            Stream(self.__subscriptions)
            .filter(lambda e: e.get_subscription_id() == sub.get_subscription_id())
            .each(lambda s: s.resume())
        )

    def pause_all(self) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.pause()))

    def resume_paused(self) -> None:
        (
            Stream(self.__subscriptions)
            .filter(ObservableSubscription.is_paused)
            .each(lambda s: s.resume())
        )

    def on_completed(self, val: Optional[T]) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.on_completed(val)))
        # Clear all subscriptions. This subject is out of business
        self.dispose()

    def on_error(self, ex: Exception) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.on_error(ex)))


class _Observable(_ObservableBase[T], _ObservableParent[T]):
    def __init__(self) -> None:  # pylint: disable=useless-parent-delegation
        super().__init__()


class PipeObservable(Generic[T, V], _Observable[V], Piped[T, V]):
    __slots__ = ("__pipe", "__parent")

    def __init__(self, parent: _Observable[T], pipe: Pipe[T, V]) -> None:
        self.__pipe = pipe
        self.__parent = parent
        super().__init__()

    def subscribe(
        self,
        on_next: NextHandler[V],
        on_error: ErrorHandler = None,
        on_completed: CompletedHandler[V] = None,
        on_dispose: DisposeHandler = None,
        asynchronous: bool = False,
    ) -> ObservableSubscription[V]:
        """
        Subscribe to this pipe in either synchronous(default) or asynchronous mode.
        The subscription will be executed in a thread pool if asynchronous is set to True.
        Asynchronous subscriptions will receive events emitted from the parent observable
        as soon as they are available. Synchronous subscriptions will receive events in the order of subscription.
        Heavy computations in the subscription will block the parent observable until the subscription is completed.
        As such, it is recommended to use asynchronous subscriptions for heavy computations.

        Args:
            on_next (NextHandler[V]): On next handler for incoming values
            on_error (ErrorHandler, optional): Error handler. Defaults to None.
            on_completed (CompletedHandler[V], optional): Competed handler. Defaults to None.
            on_dispose (DisposeHandler, optional): Dispose handler. Defaults to None.
            asynchronous (boolean): Flags if the subscription should be asynchronous. Asynchronous subscriptions
                                    are executed in a thread pool. Defaults to False.

        Returns:
            ObservableSubscription[V]: The subscription
        """
        wrapped_on_next, wrapped_on_completed = self.__wrap(on_next, on_completed)
        return self.__parent.subscribe(
            wrapped_on_next, on_error, wrapped_on_completed, on_dispose, asynchronous
        )

    def __wrap(
        self, on_next: Callable[[V], Any], on_completed: CompletedHandler[V]
    ) -> tuple[Callable[[T], Any], CompletedHandler[T]]:
        clone_pipe = self.__pipe.clone()

        def on_next_wrapped(val: T) -> None:
            result = clone_pipe.apply(val)
            if result is not None:
                on_next(result)

        def on_completed_wrapped(val: Optional[T]) -> None:
            if val is None or on_completed is None:
                return
            result = clone_pipe.apply(val)
            if result is not None:
                on_completed(result)

        return (on_next_wrapped, on_completed_wrapped)

    def cancel(self, sub: ObservableSubscription[Any]) -> None:
        self.__parent.cancel(sub)

    def pause(self, sub: ObservableSubscription[Any]) -> None:
        self.__parent.pause(sub)

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
    ) -> "PipeObservable[T, V]":
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
        return PipeObservable(self, Pipe(T, V, op_list))  # type: ignore


class Observable(_Observable[T]):
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
        return PipeObservable(self, Pipe(T, Any, op_list))  # type: ignore


class Flowable(Observable[T]):
    __slots__ = ("_values",)

    def __init__(self, values: Iterable[T]) -> None:
        super().__init__()
        self._values = values
        self._parent = self

    def _push(self) -> None:
        for v in self._values:
            self._notify_all_subs(v)

    def _push_to_sub_on_subscribe(self, sub: ObservableSubscription[T]) -> None:
        for v in self._values:
            self._push_to_subscription(sub, v)

    def first(self) -> Observable[T]:
        return Single(Stream(self._values).first().get_actual())

    def last(self) -> Observable[T]:
        return Single(self._last_val if self._last_val is not None else None)


class Single(Flowable[T]):
    def __init__(self, value: Optional[T]) -> None:
        super().__init__([value] if value is not None else [])


class SingleValueSubject(Single[T], _OnNext[T]):
    def __init__(self, value: Optional[T]) -> None:  # pylint: disable=useless-parent-delegation
        super().__init__(value)

    def _on_next(self, val: Optional[T]) -> None:
        if val is not None:
            self._values = [val]
            self._notify_all_subs(val)

    def latest(self) -> Optional[T]:
        if is_empty_or_none(self._values):
            return None
        return self._values.__iter__().__next__()


class BehaviorSubject(SingleValueSubject[T]):
    def __init__(self, value: T) -> None:
        super().__init__(value)


class PublishSubject(SingleValueSubject[T]):
    def __init__(self, typ: type[T]) -> None:  # pylint: disable=unused-argument
        super().__init__(None)

    def _push(self) -> None:
        """
        Publish subject should not emmit anything on subscribe
        """

    def _push_to_sub_on_subscribe(self, sub: ObservableSubscription[T]) -> None:
        """
        Publish subject should not emmit anything on subscribe
        """


class ReplaySubject(Flowable[T], _OnNext[T]):
    __slots__ = "__value_list"

    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(values)
        self.__value_list: list[T] = []

    def _on_next(self, val: Optional[T]) -> None:
        if val is not None:
            self.__value_list.append(val)
            self._notify_all_subs(val)

    def _push(self) -> None:
        super()._push()
        for v in self.__value_list:
            self._notify_all_subs(v)

    def _push_to_sub_on_subscribe(self, sub: ObservableSubscription[T]) -> None:
        for v in self._values:
            self._push_to_subscription(sub, v)
        for v in self.__value_list:
            self._push_to_subscription(sub, v)


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
        self.__prev_val: Optional[T] = None
        super().__init__(self.__mapper)

    def init(self) -> None:
        self.__prev_val = None

    def __mapper(self, val: T) -> bool:
        if self.__prev_val is None:
            # When reducing, the first value is always returned
            self.__prev_val = val
            return True
        reduced = self.__reducer(self.__prev_val, val)
        if reduced != self.__prev_val:
            # Push and store the reduced value only if it's different than the previous value
            self.__prev_val = reduced
            return True
        return False


class Filter(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:  # pylint: disable=useless-parent-delegation
        """
        Allows only values that match the given predicate to flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        super().__init__(predicate)


class Map(BaseMappingOperator[T, V]):
    def __init__(self, mapper: Callable[[T], V]) -> None:  # pylint: disable=useless-parent-delegation
        """
        Maps a value to a differnt value/form using the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function
        """
        super().__init__(mapper)


class Take(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:  # pylint: disable=unused-argument
        """
        Allows only the first "count" values to flow through

        Args:
            typ (type[T]): The type of the values that will pass throgh
            count (int): The number of values that will pass through
        """
        self.__count = count
        self.__currently_pushed = 0
        super().__init__(self.__take)

    def init(self) -> None:
        self.__currently_pushed = 0

    def __take(self, _: T) -> bool:
        if self.__currently_pushed >= self.__count:
            return False
        self.__currently_pushed += 1
        return True


class TakeWhile(BaseFilteringOperator[T]):
    def __init__(
        self, predicate: Callable[[T], bool], include_stop_value: bool
    ) -> None:
        """
        Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__should_push = True
        self.__include_stop_value = include_stop_value
        super().__init__(self.__take)

    def init(self) -> None:
        self.__should_push = True

    def __take(self, val: T) -> bool:
        if not self.__should_push:
            return False
        if not self.__fn(val):
            self.__should_push = False
            return self.__include_stop_value
        return True


class TakeUntil(BaseFilteringOperator[T]):
    def __init__(
        self, predicate: Callable[[T], bool], include_stop_value: bool
    ) -> None:
        """
        Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__should_push = True
        self.__include_stop_value = include_stop_value
        super().__init__(self.__take)

    def init(self) -> None:
        self.__should_push = True

    def __take(self, val: T) -> bool:
        if not self.__should_push:
            return False
        if self.__fn(val):
            self.__should_push = False
            return self.__include_stop_value
        return True


class Drop(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:  # pylint: disable=unused-argument
        """
        Blocks the first "count" values, then allows all remaining values to pass through

        Args:
            typ (type[T]): The type of the values
            count (int): The number of values to pass through
        """
        self.__count = count
        self.__currently_dropped = 0
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__currently_dropped = 0

    def __drop(self, _: T) -> bool:
        if self.__currently_dropped < self.__count:
            self.__currently_dropped += 1
            return False
        return True


class DropWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__should_push = False
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__should_push = False

    def __drop(self, val: T) -> bool:
        if self.__should_push:
            return True

        if not self.__fn(val):
            self.__should_push = True
            return True
        return False


class DropUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__should_push = False
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__should_push = False

    def __drop(self, val: T) -> bool:
        if self.__should_push:
            return True

        if self.__fn(val):
            self.__should_push = True
            return True
        return False


_SENTINEL = object()


class DistinctUntilChanged(BaseFilteringOperator[T]):
    __slots__ = ("__key_selector", "__prev_key")

    def __init__(self, key_selector: Optional[Callable[[T], K]] = None) -> None:
        self.__key_selector = key_selector
        self.__prev_key: Any = _SENTINEL  # Stores the key of the previous item
        super().__init__(self.__is_distinct)

    def init(self) -> None:
        """Called when the operator is (re)initialized, e.g., when a pipe is cloned."""
        self.__prev_key = _SENTINEL

    def __is_distinct(self, val: T) -> bool:
        current_key = self.__key_selector(val) if self.__key_selector else val

        if self.__prev_key is _SENTINEL:
            self.__prev_key = current_key
            return True

        is_new: bool = self.__prev_key != current_key
        if is_new:
            self.__prev_key = current_key
        return is_new


class Tap(BaseMappingOperator[T, T]):
    __slots__ = ("__action",)

    def __init__(self, action: Callable[[T], None]) -> None:
        self.__action = action
        super().__init__(self.__perform_action_and_return)

    def __perform_action_and_return(self, val: T) -> T:
        self.__action(val)
        return val


class IgnoreAll(BaseFilteringOperator[T]):
    """
    Discards all items emitted by the source Observable.
    It's useful when you're only interested in the `complete` or `error`
    notifications from the stream, not the values themselves.
    """

    def __init__(self) -> None:
        super().__init__(
            lambda _: False
        )  # Always return False to filter out all elements

    def init(self) -> None:
        pass  # No specific state to reset


class Ignore(BaseFilteringOperator[T]):
    """
    Discards all items emitted by the source Observable that match the given predicate.
    This operator is useful when you want to ignore specific values
    while still allowing others to pass through. It functions as the inverse of the filter operator.
    """

    def __init__(self, predicate: Callable[[T], bool]) -> None:
        super().__init__(not_strict(predicate))

    def init(self) -> None:
        pass  # No specific state to reset


class Debounce(BaseFilteringOperator[T]):
    __slots__ = ("__timespan", "__last_emitted")

    def __init__(self, timespan: float) -> None:
        """
        Emits a value from the source Observable only after a particular timespan has passed without another source emission.

        Args:
            timespan (float): The timespan in seconds to wait for inactivity before emitting.
        """
        self.__timespan = timespan
        self.__last_emitted: Optional[float] = None
        super().__init__(self.__debounce)

    def init(self) -> None:
        self.__last_emitted = None

    def __debounce(self, _: T) -> bool:
        import time

        current_time = time.time()
        if self.__last_emitted is None or (
            current_time - self.__last_emitted >= self.__timespan
        ):
            self.__last_emitted = current_time
            return True
        return False


class Throttle(BaseFilteringOperator[T]):
    __slots__ = ("__timespan", "__last_emitted")

    def __init__(self, timespan: float) -> None:
        """
        Emits a value from the source Observable, then ignores subsequent source emissions for a particular timespan.

        Args:
            timespan (float): The timespan in seconds to wait before allowing another emission.
        """
        self.__timespan = timespan
        self.__last_emitted: Optional[float] = None
        super().__init__(self.__throttle)

    def init(self) -> None:
        self.__last_emitted = None

    def __throttle(self, _: T) -> bool:
        import time

        current_time = time.time()
        if self.__last_emitted is None or (
            current_time - self.__last_emitted >= self.__timespan
        ):
            self.__last_emitted = current_time
            return True
        return False


class Buffer(BaseMappingOperator[T, list[T]]):
    __slots__ = ("__timespan", "__buffer", "__last_checked")

    def __init__(self, timespan: float) -> None:
        """
        Buffers the source Observable for a specific timespan then emits the buffered values as a list.

        Args:
            timespan (float): The timespan in seconds for which to buffer values.
        """
        self.__timespan = timespan
        self.__buffer: list[T] = []
        self.__last_checked: Optional[float] = None
        super().__init__(self.__emit_buffer)

    def init(self) -> None:
        self.__buffer = []
        self.__last_checked = None

    def __emit_buffer(self, val: T) -> list[T]:
        import time

        current_time = time.time()
        if self.__last_checked is None:
            self.__last_checked = current_time

        self.__buffer.append(val)

        if current_time - self.__last_checked >= self.__timespan:
            self.__last_checked = current_time
            emitted_buffer = self.__buffer
            self.__buffer = []
            return emitted_buffer
        return []  # Return an empty list if the buffer should not emit yet


class BufferCount(BaseMappingOperator[T, list[T]]):
    __slots__ = ("__count", "__buffer")

    def __init__(self, count: int) -> None:
        """
        Buffers a specified number of values from the source Observable and emits them as a list.

        Args:
            count (int): The number of values to buffer before emitting.
        """
        self.__count = count
        self.__buffer: list[T] = []
        super().__init__(self.__emit_buffer)

    def init(self) -> None:
        self.__buffer = []

    def __emit_buffer(self, val: T) -> list[T]:
        self.__buffer.append(val)
        if len(self.__buffer) >= self.__count:
            emitted_buffer = self.__buffer
            self.__buffer = []
            return emitted_buffer
        return []  # Return an empty list if the buffer is not full yet


class RX:
    @staticmethod
    def of_type(typ: type[T]) -> RxOperator[T, T]:
        """
        Allows only values of the given type to flow through

        Args:
            typ (type[T]): The type of the values that will pass throgh

        Returns:
            RxOperator[T, T]: A OfType operator
        """
        return Filter(lambda v: isinstance(v, typ))

    @staticmethod
    def tap(action: Callable[[T], Any]) -> RxOperator[T, T]:
        """
        Performs a side-effect action for each item in the stream without
        modifying the item.
        ...
        """
        return Tap(action)

    @staticmethod
    def distinct_until_changed(
        key_selector: Optional[Callable[[T], Any]] = None,
    ) -> RxOperator[T, T]:
        """
        Emits only items from an Observable that are distinct from their immediate
        predecessor, based on the item itself or a key selected by key_selector.
        """
        return DistinctUntilChanged(key_selector)

    @staticmethod
    def filter(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
        """
        Allows only values that match the given predicate to flow through

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            RxOperator[T, T]: A Filter operator
        """

        return Filter(predicate)

    @staticmethod
    def map(mapper: Callable[[T], V]) -> RxOperator[T, V]:
        """
        Maps a value to a differnt value/form using the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function

        Returns:
            RxOperator[T, V]: A Map operator
        """
        return Map(mapper)

    @staticmethod
    def reduce(reducer: Callable[[T, T], T]) -> RxOperator[T, T]:
        """
        Reduces two consecutive values into one by applying the provided reducer function

        Args:
            reducer (Callable[[T, T], T]): The reducer function

        Returns:
            RxOperator[T, T]: A Reduce operator
        """

        return Reduce(reducer)

    @staticmethod
    def take(typ: type[T], count: int) -> RxOperator[T, T]:
        """
        Allows only the first "count" values to flow through

        Args:
            typ (type[T]): The type of the values that will pass throgh
            count (int): The number of values that will pass through

        Returns:
            RxOperator[T, T]: A Take operator
        """
        return Take(typ, count)

    @staticmethod
    def take_while(
        predicate: Callable[[T], bool], include_stop_value: bool = False
    ) -> RxOperator[T, T]:
        """
        Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
            include_stop_value (bool): Flag indicating that the stop value should be included

        Returns:
            RxOperator[T, T]: A TakeWhile operator
        """
        return TakeWhile(predicate, include_stop_value)

    @staticmethod
    def take_until(
        predicate: Callable[[T], bool], include_stop_value: bool = False
    ) -> RxOperator[T, T]:
        """
        Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
            include_stop_value (bool): Flag indicating that the stop value should be included

        Returns:
            RxOperator[T, T]: A TakeUntil operator
        """

        return TakeUntil(predicate, include_stop_value)

    @staticmethod
    def drop(typ: type[T], count: int) -> RxOperator[T, T]:
        """
        Blocks the first "count" values, then allows all remaining values to pass through

        Args:
            typ (type[T]): The type of the values
            count (int): The number of values to pass through

        Returns:
            RxOperator[T, T]: A Drop operator
        """
        return Drop(typ, count)

    @staticmethod
    def drop_while(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
        """
        Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate

        Returns:
            RxOperator[T, T]: A DropWhile operator
        """
        return DropWhile(predicate)

    @staticmethod
    def drop_until(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
        """
        Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The given predicate

        Returns:
            RxOperator[T, T]: A DropUntil operator
        """
        return DropUntil(predicate)

    @staticmethod
    def ignore_all() -> RxOperator[T, T]:
        """
        Discards all items emitted by the source Observable.
        Useful when only `complete` or `error` notifications are of interest.
        """
        return IgnoreAll()

    @staticmethod
    def ignore(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
        """
        Discards all items emitted by the source Observable that match the given predicate.
        """
        return Ignore(predicate)

    @staticmethod
    def debounce(timespan: float) -> RxOperator[T, T]:
        """
        Emits a value from the source Observable only after a particular timespan has passed without another source emission.

        Args:
            timespan (float): The timespan in seconds to wait for inactivity before emitting.
        """
        return Debounce(timespan)

    @staticmethod
    def throttle(timespan: float) -> RxOperator[T, T]:
        """
        Emits a value from the source Observable, then ignores subsequent source emissions for a particular timespan.

        Args:
            timespan (float): The timespan in seconds to wait before allowing another emission.
        """
        return Throttle(timespan)

    @staticmethod
    def buffer(timespan: float) -> RxOperator[T, list[T]]:
        """
        Buffers the source Observable for a specific timespan then emits the buffered values as a list.

        Args:
            timespan (float): The timespan in seconds for which to buffer values.
        """
        return Buffer(timespan)

    @staticmethod
    def buffer_count(count: int) -> RxOperator[T, list[T]]:
        """
        Buffers a specified number of values from the source Observable and emits them as a list.

        Args:
            count (int): The number of values to buffer before emitting.
        """
        return BufferCount(count)


def rx_reduce(reducer: Callable[[T, T], T]) -> RxOperator[T, T]:
    """
    Reduces two consecutive values into one by applying the provided reducer function

    Args:
        reducer (Callable[[T, T], T]): The reducer function

    Returns:
        RxOperator[T, T]: A Reduce operator
    """
    return RX.reduce(reducer)


def rx_filter(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows only values that match the given predicate to flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A Filter operator
    """
    return RX.filter(predicate)


def rx_map(mapper: Callable[[T], V]) -> RxOperator[T, V]:
    """
    Maps a value to a differnt value/form using the mapper function

    Args:
        mapper (Callable[[T], V]): The mapper function

    Returns:
        RxOperator[T, V]: A Map operator
    """
    return RX.map(mapper)


def rx_take(typ: type[T], count: int) -> RxOperator[T, T]:
    """
    Allows only the first "count" values to flow through

    Args:
        typ (type[T]): The type of the values that will pass throgh
        count (int): The number of values that will pass through

    Returns:
        RxOperator[T, T]: A Take operator
    """
    return RX.take(typ, count)


def rx_take_while(
    predicate: Callable[[T], bool], include_stop_value: bool = False
) -> RxOperator[T, T]:
    """
    Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

    Args:
        predicate (Callable[[T], bool]): The predicate
        include_stop_value (bool): Flag indicating that the stop value should be included

    Returns:
        RxOperator[T, T]: A TakeWhile operator
    """
    return RX.take_while(predicate, include_stop_value)


def rx_take_until(
    predicate: Callable[[T], bool], include_stop_value: bool = False
) -> RxOperator[T, T]:
    """
    Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

    Args:
        predicate (Callable[[T], bool]): The predicate
        include_stop_value (bool): Flag indicating that the stop value should be included

    Returns:
        RxOperator[T, T]: A TakeUntil operator
    """
    return RX.take_until(predicate, include_stop_value)


def rx_drop(typ: type[T], count: int) -> RxOperator[T, T]:
    """
    Blocks the first "count" values, then allows all remaining values to pass through

    Args:
        typ (type[T]): The type of the values
        count (int): The number of values to pass through

    Returns:
        RxOperator[T, T]: A Drop operator
    """
    return RX.drop(typ, count)


def rx_drop_while(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A DropWhile operator
    """
    return RX.drop_while(predicate)


def rx_drop_until(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

    Args:
        predicate (Callable[[T], bool]): The given predicate

    Returns:
        RxOperator[T, T]: A DropUntil operator
    """
    return RX.drop_until(predicate)


def rx_distinct_until_changed(
    key_selector: Optional[Callable[[T], Any]] = None,
) -> RxOperator[T, T]:
    """
    Emits only items from an Observable that are distinct from their immediate
    predecessor, based on the item itself or a key selected by key_selector.
    """
    return RX.distinct_until_changed(key_selector)


def rx_tap(action: Callable[[T], Any]) -> RxOperator[T, T]:
    """
    Performs a side-effect action for each item in the stream without
    modifying the item.
    ...
    """
    return RX.tap(action)


def rx_of_type(typ: type[T]) -> RxOperator[T, T]:
    """
    Allows only values of the given type to flow through

    Args:
        typ (type[T]): The type of the values that will pass throgh

    Returns:
        RxOperator[T, T]: A OfType operator
    """
    return RX.of_type(typ)


def rx_ignore_all() -> RxOperator[T, T]:
    """
    Discards all items emitted by the source Observable.
    Useful when only `complete` or `error` notifications are of interest.

    Returns:
        RxOperator[T, T]: An IgnoreElements operator.
    """
    return RX.ignore_all()


def rx_debounce(timespan: float) -> RxOperator[T, T]:
    """
    Emits a value from the source Observable only after a particular timespan has passed without another source emission.

    Args:
        timespan (float): The timespan in seconds to wait for inactivity before emitting.
    """
    return RX.debounce(timespan)


def rx_throttle(timespan: float) -> RxOperator[T, T]:
    """
    Emits a value from the source Observable, then ignores subsequent source emissions for a particular timespan.

    Args:
        timespan (float): The timespan in seconds to wait before allowing another emission.
    """
    return RX.throttle(timespan)


def rx_buffer(timespan: float) -> RxOperator[T, list[T]]:
    """
    Buffers the source Observable for a specific timespan then emits the buffered values as a list.

    Args:
        timespan (float): The timespan in seconds for which to buffer values.
    """
    return RX.buffer(timespan)


def rx_buffer_count(count: int) -> RxOperator[T, list[T]]:
    """
    Buffers a specified number of values from the source Observable and emits them as a list.

    Args:
        count (int): The number of values to buffer before emitting.
    """
    return RX.buffer_count(count)
