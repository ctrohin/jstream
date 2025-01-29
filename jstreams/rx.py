from threading import Lock
from typing import (
    Callable,
    Generic,
    Iterable,
    Optional,
    TypeAlias,
    TypeVar,
    Union,
    Any,
    overload,
)
import uuid

from jstreams.stream import Stream
from jstreams.rxops import Pipe, RxOperator

T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
E = TypeVar("E")
F = TypeVar("F")
G = TypeVar("G")
H = TypeVar("H")
I = TypeVar("I")
J = TypeVar("J")
K = TypeVar("K")
L = TypeVar("L")
M = TypeVar("M")
V = TypeVar("V")


ErrorHandler = Optional[Callable[[Exception], Any]]
CompletedHandler = Optional[Callable[[Optional[T]], Any]]
NextHandler = Callable[[T], Any]
DisposeHandler = Optional[Callable[[], Any]]


class MultipleSubscriptionsException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ObservableSubscription(Generic[T]):
    __slots__ = (
        "__parent",
        "__onNext",
        "__onError",
        "__onCompleted",
        "__onDispose",
        "__subscriptionId",
        "__paused",
    )

    def __init__(
        self,
        parent: Any,
        onNext: NextHandler[T],
        onError: ErrorHandler = None,
        onCompleted: CompletedHandler[T] = None,
        onDispose: DisposeHandler = None,
    ) -> None:
        self.__parent = parent
        self.__onNext = onNext
        self.__onError = onError
        self.__onCompleted = onCompleted
        self.__onDispose = onDispose
        self.__subscriptionId = str(uuid.uuid4())
        self.__paused = False

    def getSubscriptionId(self) -> str:
        return self.__subscriptionId

    def onNext(self, obj: T) -> None:
        self.__onNext(obj)

    def onError(self, ex: Exception) -> None:
        if self.__onError:
            self.__onError(ex)

    def onCompleted(self, obj: Optional[T]) -> None:
        if self.__onCompleted:
            self.__onCompleted(obj)

    def isPaused(self) -> bool:
        return self.__paused

    def pause(self) -> None:
        self.__paused = True

    def resume(self) -> None:
        self.__paused = False

    def dispose(self) -> None:
        if self.__onDispose:
            self.__onDispose()

    def cancel(self) -> None:
        if hasattr(self.__parent, "cancel"):
            self.__parent.cancel(self)


class _ObservableParent(Generic[T]):
    def push(self) -> None:
        pass

    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None:
        pass


class _OnNext(Generic[T]):
    def onNext(self, val: Optional[T]) -> None:
        if not hasattr(self, "__lock"):
            self.__lock = Lock()
        with self.__lock:
            self._onNext(val)

    def _onNext(self, val: Optional[T]) -> None:
        pass


class _ObservableBase(Generic[T]):
    __slots__ = ("__subscriptions", "_parent", "_lastVal")

    def __init__(self) -> None:
        self.__subscriptions: list[ObservableSubscription[Any]] = []
        self._parent: Optional[_ObservableParent[T]] = None
        self._lastVal: Optional[T] = None

    def _notifyAllSubs(self, val: T) -> None:
        self._lastVal = val

        if self.__subscriptions is not None:
            for sub in self.__subscriptions:
                self.pushToSubscription(sub, val)

    def pushToSubscription(self, sub: ObservableSubscription[Any], val: T) -> None:
        if not sub.isPaused():
            try:
                sub.onNext(val)
            except Exception as e:
                if sub.onError is not None:
                    sub.onError(e)

    def subscribe(
        self,
        onNext: NextHandler[T],
        onError: ErrorHandler = None,
        onCompleted: CompletedHandler[T] = None,
        onDispose: DisposeHandler = None,
    ) -> ObservableSubscription[Any]:
        sub = ObservableSubscription(self, onNext, onError, onCompleted, onDispose)
        self.__subscriptions.append(sub)
        if self._parent is not None:
            self._parent.pushToSubOnSubscribe(sub)
        return sub

    def cancel(self, sub: ObservableSubscription[Any]) -> None:
        (
            Stream(self.__subscriptions)
            .filter(lambda e: e.getSubscriptionId() == sub.getSubscriptionId())
            .each(self.__subscriptions.remove)
        )

    def dispose(self) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.dispose()))
        self.__subscriptions.clear()

    def pause(self, sub: ObservableSubscription[Any]) -> None:
        (
            Stream(self.__subscriptions)
            .filter(lambda e: e.getSubscriptionId() == sub.getSubscriptionId())
            .each(lambda s: s.pause())
        )

    def resume(self, sub: ObservableSubscription[Any]) -> None:
        (
            Stream(self.__subscriptions)
            .filter(lambda e: e.getSubscriptionId() == sub.getSubscriptionId())
            .each(lambda s: s.resume())
        )

    def pauseAll(self) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.pause()))

    def resumePaused(self) -> None:
        (
            Stream(self.__subscriptions)
            .filter(ObservableSubscription.isPaused)
            .each(lambda s: s.resume())
        )

    def onCompleted(self, val: Optional[T]) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.onCompleted(val)))
        # Clear all subscriptions. This subject is out of business
        self.dispose()

    def onError(self, ex: Exception) -> None:
        (Stream(self.__subscriptions).each(lambda s: s.onError(ex)))


class _Observable(_ObservableBase[T], _ObservableParent[T]):
    def __init__(self) -> None:
        super().__init__()


class _PipeObservable(Generic[T, V], _Observable[V]):
    __slots__ = ("__pipe", "__parent")

    def __init__(self, parent: _Observable[T], pipe: Pipe[T, V]) -> None:
        self.__pipe = pipe
        self.__parent = parent
        super().__init__()

    def subscribe(
        self,
        onNext: NextHandler[V],
        onError: ErrorHandler = None,
        onCompleted: CompletedHandler[V] = None,
        onDispose: DisposeHandler = None,
    ) -> ObservableSubscription[Any]:
        """
        Subscribe to this pipe

        Args:
            onNext (NextHandler[V]): On next handler for incoming values
            onError (ErrorHandler, optional): Error handler. Defaults to None.
            onCompleted (CompletedHandler[V], optional): Competed handler. Defaults to None.
            onDispose (DisposeHandler, optional): Dispose handler. Defaults to None.

        Returns:
            ObservableSubscription[V]: The subscription
        """
        wrappedOnNext, wrappedOnCompleted = self.__wrap(onNext, onCompleted)
        return self.__parent.subscribe(
            wrappedOnNext, onError, wrappedOnCompleted, onDispose
        )

    def __wrap(
        self, onNext: Callable[[V], Any], onCompleted: CompletedHandler[V]
    ) -> tuple[Callable[[T], Any], CompletedHandler[T]]:
        clonePipe = self.__pipe.clone()

        def onNextWrapped(val: T) -> None:
            result = clonePipe.apply(val)
            if result is not None:
                onNext(result)

        def onCompletedWrapped(val: Optional[T]) -> None:
            if val is None or onCompleted is None:
                return
            result = clonePipe.apply(val)
            if result is not None:
                onCompleted(result)

        return (onNextWrapped, onCompletedWrapped)

    def cancel(self, sub: ObservableSubscription[Any]) -> None:
        self.__parent.cancel(sub)

    def pause(self, sub: ObservableSubscription[Any]) -> None:
        self.__parent.pause(sub)

    @overload
    def pipe(
        self,
        op1: RxOperator[T, V],
    ) -> "_PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, V],
    ) -> "_PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, V],
    ) -> "_PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> "_PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> "_PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, V],
    ) -> "_PipeObservable[T, V]": ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, V],
    ) -> "_PipeObservable[T, V]": ...

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
    ) -> "_PipeObservable[T, V]": ...

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
    ) -> "_PipeObservable[T, V]": ...

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
    ) -> "_PipeObservable[T, V]": ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, V],
    ) -> "_PipeObservable[T, V]": ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, J],
        op11: RxOperator[J, V],
    ) -> "_PipeObservable[T, V]": ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, J],
        op11: RxOperator[J, K],
        op12: RxOperator[K, V],
    ) -> "_PipeObservable[T, V]": ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, J],
        op11: RxOperator[J, K],
        op12: RxOperator[K, L],
        op13: RxOperator[L, V],
    ) -> "_PipeObservable[T, V]": ...

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
        op9: Optional[RxOperator[H, I]] = None,
        op10: Optional[RxOperator[I, J]] = None,
        op11: Optional[RxOperator[J, K]] = None,
        op12: Optional[RxOperator[K, L]] = None,
        op13: Optional[RxOperator[L, M]] = None,
        op14: Optional[RxOperator[M, V]] = None,
    ) -> "_PipeObservable[T, V]":
        opList = (
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
            .nonNull()
            .toList()
        )
        return _PipeObservable(self, Pipe(T, V, opList))  # type: ignore


class Observable(_Observable[T]):
    def __init__(self) -> None:
        super().__init__()

    @overload
    def pipe(
        self,
        op1: RxOperator[T, V],
    ) -> _PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, V],
    ) -> _PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, V],
    ) -> _PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> _PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> _PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, V],
    ) -> _PipeObservable[T, V]: ...

    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, V],
    ) -> _PipeObservable[T, V]: ...

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
    ) -> _PipeObservable[T, V]: ...

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
    ) -> _PipeObservable[T, V]: ...

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
    ) -> _PipeObservable[T, V]: ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, V],
    ) -> _PipeObservable[T, V]: ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, J],
        op11: RxOperator[J, V],
    ) -> _PipeObservable[T, V]: ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, J],
        op11: RxOperator[J, K],
        op12: RxOperator[K, V],
    ) -> _PipeObservable[T, V]: ...

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
        op9: RxOperator[H, I],
        op10: RxOperator[I, J],
        op11: RxOperator[J, K],
        op12: RxOperator[K, L],
        op13: RxOperator[L, V],
    ) -> _PipeObservable[T, V]: ...

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
        op9: Optional[RxOperator[H, I]] = None,
        op10: Optional[RxOperator[I, J]] = None,
        op11: Optional[RxOperator[J, K]] = None,
        op12: Optional[RxOperator[K, L]] = None,
        op13: Optional[RxOperator[L, M]] = None,
        op14: Optional[RxOperator[M, V]] = None,
    ) -> _PipeObservable[T, V]:
        opList = (
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
            .nonNull()
            .toList()
        )
        return _PipeObservable(self, Pipe(T, Any, opList))  # type: ignore


class Flowable(Observable[T]):
    __slots__ = ("_values",)

    def __init__(self, values: Iterable[T]) -> None:
        super().__init__()
        self._values = values
        self._parent = self

    def push(self) -> None:
        for v in self._values:
            self._notifyAllSubs(v)

    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None:
        for v in self._values:
            self.pushToSubscription(sub, v)

    def first(self) -> Observable[T]:
        return Single(Stream(self._values).first().getActual())

    def last(self) -> Observable[T]:
        return Single(self._lastVal if self._lastVal is not None else None)


class Single(Flowable[T]):
    def __init__(self, value: Optional[T]) -> None:
        super().__init__([value] if value is not None else [])


class _SingleValueSubject(Single[T], _OnNext[T]):
    def __init__(self, value: Optional[T]) -> None:
        super().__init__(value)

    def _onNext(self, val: Optional[T]) -> None:
        if val is not None:
            self._values = [val]
            self._notifyAllSubs(val)


class BehaviorSubject(_SingleValueSubject[T]):
    def __init__(self, value: T) -> None:
        super().__init__(value)


class PublishSubject(_SingleValueSubject[T]):
    def __init__(self, typ: type[T]) -> None:
        super().__init__(None)

    def push(self) -> None:
        """
        Publish subject should not emmit anything on subscribe
        """

    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None:
        """
        Publish subject should not emmit anything on subscribe
        """


class ReplaySubject(Flowable[T], _OnNext[T]):
    __slots__ = "__valueList"

    def __init__(self, values: Iterable[T]) -> None:
        super().__init__(values)
        self.__valueList: list[T] = []

    def _onNext(self, val: Optional[T]) -> None:
        if val is not None:
            self.__valueList.append(val)
            self._notifyAllSubs(val)

    def push(self) -> None:
        super().push()
        for v in self.__valueList:
            self._notifyAllSubs(v)

    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None:
        for v in self._values:
            self.pushToSubscription(sub, v)
        for v in self.__valueList:
            self.pushToSubscription(sub, v)


__all__ = [
    "ObservableSubscription",
    "Observable",
    "Flowable",
    "Single",
    "BehaviorSubject",
    "PublishSubject",
    "ReplaySubject",
]
