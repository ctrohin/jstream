from jstreams.rxops import Pipe, RxOperator
from typing import Any, Callable, Generic, Iterable, TypeVar, overload

__all__ = [
    "ObservableSubscription",
    "Observable",
    "Flowable",
    "Single",
    "BehaviorSubject",
    "PublishSubject",
    "ReplaySubject",
]

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
ErrorHandler = Callable[[Exception], Any] | None
CompletedHandler = Callable[[T], Any] | None
NextHandler = Callable[[T], Any]

class ObservableSubscription(Generic[T]):
    def __init__(
        self,
        onNext: NextHandler[T],
        onError: ErrorHandler = None,
        onCompleted: CompletedHandler[T] = None,
    ) -> None: ...
    def getSubscriptionId(self) -> str: ...
    def onNext(self, obj: T) -> None: ...
    def onError(self, ex: Exception) -> None: ...
    def onCompleted(self, obj: T) -> None: ...
    def isPaused(self) -> bool: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...

class _ObservableParent(Generic[T]):
    def push(self) -> None: ...
    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None: ...

class _OnNext(Generic[T]):
    def onNext(self, val: T | None) -> None: ...

class _ObservableBase(Generic[T]):
    def __init__(self) -> None: ...
    def pushToSubscription(self, sub: ObservableSubscription[T], val: T) -> None: ...
    def subscribe(
        self,
        onNext: NextHandler[T],
        onError: ErrorHandler = None,
        onCompleted: CompletedHandler[T] = None,
    ) -> ObservableSubscription[T]: ...
    def cancel(self, sub: ObservableSubscription[T]) -> None: ...
    def pause(self, sub: ObservableSubscription[T]) -> None: ...
    def resume(self, sub: ObservableSubscription[T]) -> None: ...
    def pauseAll(self) -> None: ...
    def resumePaused(self) -> None: ...
    def onCompleted(self, val: T) -> None: ...
    def onError(self, ex: Exception) -> None: ...

class _Observable(_ObservableBase[T], _ObservableParent[T]):
    def __init__(self) -> None: ...

class _PipeObservable(_Observable[V], Generic[T, V]):
    def __init__(self, parent: _Observable[T], pipe: Pipe[T, V]) -> None: ...
    def subscribe(
        self,
        onNext: NextHandler[V],
        onError: ErrorHandler = None,
        onCompleted: CompletedHandler[V] = None,
    ) -> ObservableSubscription[V]: ...

class Observable(_Observable[T]):
    def __init__(self) -> None: ...
    @overload
    def pipe(self, op1: RxOperator[T, V]) -> _Observable[V]: ...
    @overload
    def pipe(self, op1: RxOperator[T, A], op2: RxOperator[A, V]) -> _Observable[V]: ...
    @overload
    def pipe(
        self, op1: RxOperator[T, A], op2: RxOperator[A, B], op3: RxOperator[B, V]
    ) -> _Observable[V]: ...
    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> _Observable[V]: ...
    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, V],
    ) -> _Observable[V]: ...
    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, V],
    ) -> _Observable[V]: ...
    @overload
    def pipe(
        self,
        op1: RxOperator[T, A],
        op2: RxOperator[A, B],
        op3: RxOperator[B, C],
        op4: RxOperator[C, D],
        op5: RxOperator[D, E],
        op6: RxOperator[E, V],
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...
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
    ) -> _Observable[V]: ...

class Flowable(Observable[T]):
    def __init__(self, values: Iterable[T]) -> None: ...
    def push(self) -> None: ...
    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None: ...
    def first(self) -> Observable[T]: ...
    def last(self) -> Observable[T]: ...

class Single(Flowable[T]):
    def __init__(self, value: T | None) -> None: ...

class _SingleValueSubject(Single[T], _OnNext[T]):
    def __init__(self, value: T | None) -> None: ...

class BehaviorSubject(_SingleValueSubject[T]):
    def __init__(self, value: T) -> None: ...

class PublishSubject(_SingleValueSubject[T]):
    def __init__(self, typ: type[T]) -> None: ...
    def push(self) -> None: ...
    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None: ...

class ReplaySubject(Flowable[T], _OnNext[T]):
    def __init__(self, values: Iterable[T]) -> None: ...
    def push(self) -> None: ...
    def pushToSubOnSubscribe(self, sub: ObservableSubscription[T]) -> None: ...
