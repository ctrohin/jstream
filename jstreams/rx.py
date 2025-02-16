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
        self, inputType: type[T], outputType: type[V], ops: list[RxOperator[Any, Any]]
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, V],
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
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
        op9: Optional[RxOperator[H, N]] = None,
        op10: Optional[RxOperator[N, J]] = None,
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, V],
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
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
        op9: RxOperator[H, N],
        op10: RxOperator[N, J],
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
        op9: Optional[RxOperator[H, N]] = None,
        op10: Optional[RxOperator[N, J]] = None,
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
        self.__prevVal: Optional[T] = None
        super().__init__(self.__mapper)

    def init(self) -> None:
        self.__prevVal = None

    def __mapper(self, val: T) -> bool:
        if self.__prevVal is None:
            # When reducing, the first value is always returned
            self.__prevVal = val
            return True
        reduced = self.__reducer(self.__prevVal, val)
        if reduced != self.__prevVal:
            # Push and store the reduced value only if it's different than the previous value
            self.__prevVal = reduced
            return True
        return False


def rxReduce(reducer: Callable[[T, T], T]) -> RxOperator[T, T]:
    """
    Reduces two consecutive values into one by applying the provided reducer function

    Args:
        reducer (Callable[[T, T], T]): The reducer function

    Returns:
        RxOperator[T, T]: A reduce operator
    """
    return Reduce(reducer)


class Filter(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows only values that match the given predicate to flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        super().__init__(predicate)


def rxFilter(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows only values that match the given predicate to flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A filter operator
    """
    return Filter(predicate)


class Map(BaseMappingOperator[T, V]):
    def __init__(self, mapper: Callable[[T], V]) -> None:
        """
        Maps a value to a differnt value/form using the mapper function

        Args:
            mapper (Callable[[T], V]): The mapper function
        """
        super().__init__(mapper)


def rxMap(mapper: Callable[[T], V]) -> RxOperator[T, V]:
    """
    Maps a value to a differnt value/form using the mapper function

    Args:
        mapper (Callable[[T], V]): The mapper function

    Returns:
        RxOperator[T, V]: A map operator
    """
    return Map(mapper)


class Take(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:
        """
        Allows only the first "count" values to flow through

        Args:
            typ (type[T]): The type of the values that will pass throgh
            count (int): The number of values that will pass through
        """
        self.__count = count
        self.__currentlyPushed = 0
        super().__init__(self.__take)

    def init(self) -> None:
        self.__currentlyPushed = 0

    def __take(self, val: T) -> bool:
        if self.__currentlyPushed >= self.__count:
            return False
        self.__currentlyPushed += 1
        return True


def rxTake(typ: type[T], count: int) -> RxOperator[T, T]:
    """
    Allows only the first "count" values to flow through

    Args:
        typ (type[T]): The type of the values that will pass throgh
        count (int): The number of values that will pass through

    Returns:
        RxOperator[T, T]: A take operator
    """
    return Take(typ, count)


class TakeWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = True
        super().__init__(self.__take)

    def init(self) -> None:
        self.__shouldPush = True

    def __take(self, val: T) -> bool:
        if not self.__shouldPush:
            return False
        if not self.__fn(val):
            self.__shouldPush = False
            return False
        return True


def rxTakeWhile(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows values to pass through as long as they match the give predicate. After one value is found not matching, no other values will flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A takeWhile operator
    """
    return TakeWhile(predicate)


class TakeUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = True
        super().__init__(self.__take)

    def init(self) -> None:
        self.__shouldPush = True

    def __take(self, val: T) -> bool:
        if not self.__shouldPush:
            return False
        if self.__fn(val):
            self.__shouldPush = False
            return False
        return True


def rxTakeUntil(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Allows values to pass through until the first value found to match the give predicate. After that, no other values will flow through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A takeUntil operator
    """
    return TakeUntil(predicate)


class Drop(BaseFilteringOperator[T]):
    def __init__(self, typ: type[T], count: int) -> None:
        """
        Blocks the first "count" values, then allows all remaining values to pass through

        Args:
            typ (type[T]): The type of the values
            count (int): The number of values to pass through
        """
        self.__count = count
        self.__currentlyDropped = 0
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__currentlyDropped = 0

    def __drop(self, val: T) -> bool:
        if self.__currentlyDropped < self.__count:
            self.__currentlyDropped += 1
            return False
        return True


def rxDrop(typ: type[T], count: int) -> RxOperator[T, T]:
    """
    Blocks the first "count" values, then allows all remaining values to pass through

    Args:
        typ (type[T]): The type of the values
        count (int): The number of values to pass through

    Returns:
        RxOperator[T, T]: A drop operator
    """
    return Drop(typ, count)


class DropWhile(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = False
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__shouldPush = False

    def __drop(self, val: T) -> bool:
        if self.__shouldPush:
            return True

        if not self.__fn(val):
            self.__shouldPush = True
            return True
        return False


def rxDropWhile(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Blocks values as long as they match the given predicate. Once a value is encountered that does not match the predicate, all remaining values will be allowed to pass through

    Args:
        predicate (Callable[[T], bool]): The predicate

    Returns:
        RxOperator[T, T]: A dropWhile operator
    """
    return DropWhile(predicate)


class DropUntil(BaseFilteringOperator[T]):
    def __init__(self, predicate: Callable[[T], bool]) -> None:
        """
        Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

        Args:
            predicate (Callable[[T], bool]): The predicate
        """
        self.__fn = predicate
        self.__shouldPush = False
        super().__init__(self.__drop)

    def init(self) -> None:
        self.__shouldPush = False

    def __drop(self, val: T) -> bool:
        if self.__shouldPush:
            return True

        if self.__fn(val):
            self.__shouldPush = True
            return True
        return False


def rxDropUntil(predicate: Callable[[T], bool]) -> RxOperator[T, T]:
    """
    Blocks values until the first value found that matches the given predicate. All remaining values will be allowed to pass through

    Args:
        predicate (Callable[[T], bool]): The given predicate

    Returns:
        RxOperator[T, T]: A dropUntil operator
    """
    return DropUntil(predicate)
