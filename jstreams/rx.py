from threading import Lock
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
        self, input_type: type[T], output_type: type[V], ops: list[RxOperator[Any, Any]]
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
    )

    def __init__(
        self,
        parent: Any,
        on_next: NextHandler[T],
        on_error: ErrorHandler = None,
        on_completed: CompletedHandler[T] = None,
        on_dispose: DisposeHandler = None,
    ) -> None:
        self.__parent = parent
        self.__on_next = on_next
        self.__on_error = on_error
        self.__on_completed = on_completed
        self.__on_dispose = on_dispose
        self.__subscription_id = str(uuid.uuid4())
        self.__paused = False

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
            self.__lock = Lock()
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
            for sub in self.__subscriptions:
                self._push_to_subscription(sub, val)

    def _push_to_subscription(self, sub: ObservableSubscription[Any], val: T) -> None:
        if not sub.is_paused():
            try:
                sub.on_next(val)
            except Exception as e:
                if sub.on_error is not None:
                    sub.on_error(e)

    def subscribe(
        self,
        on_next: NextHandler[T],
        on_error: ErrorHandler = None,
        on_completed: CompletedHandler[T] = None,
        on_dispose: DisposeHandler = None,
    ) -> ObservableSubscription[Any]:
        sub = ObservableSubscription(self, on_next, on_error, on_completed, on_dispose)
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
    def __init__(self) -> None:
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
    ) -> ObservableSubscription[V]:
        """
        Subscribe to this pipe

        Args:
            on_next (NextHandler[V]): On next handler for incoming values
            on_error (ErrorHandler, optional): Error handler. Defaults to None.
            on_completed (CompletedHandler[V], optional): Competed handler. Defaults to None.
            on_dispose (DisposeHandler, optional): Dispose handler. Defaults to None.

        Returns:
            ObservableSubscription[V]: The subscription
        """
        wrapped_on_next, wrapped_on_completed = self.__wrap(on_next, on_completed)
        return self.__parent.subscribe(
            wrapped_on_next, on_error, wrapped_on_completed, on_dispose
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
    def __init__(self) -> None:
        super().__init__()

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
    def __init__(self, value: Optional[T]) -> None:
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
    def __init__(self, typ: type[T]) -> None:
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
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows only values that match the given predicate to flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        super().__init__(predicate)


class Map(BaseMappingOperator[T, V]):
    def __init__(self, mapper: Callable[[T], V]) -> None:
        """
        Maps a value to a differnt value/form using the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function
        """
        super().__init__(mapper)


class Take(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:
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

    def __take(self, val: T) -> bool:
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
    def __init__(self, typ: type[T], count: int) -> None:
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

    def __drop(self, val: T) -> bool:
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


class RX:
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
    return RX.take_until(predicate)


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
