import sys
from typing import Any, Callable, Iterable, Optional, TypeVar, Union

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
ErrorHandler = Optional[Callable[[Exception], Any]]
CompletedHandler = Optional[Callable[[Optional[T]], Any]]
NextHandler = Callable[[T], Any]
DisposeHandler = Optional[Callable[[], Any]]
TSupplier = Callable[[], T]
TParamSupplier = Callable[[T], V]
TAction = Callable[[], Any]
TParamAction = Callable[[T], Any]
TTwoParamAction = Callable[[T, K], Any]
TPredicate = Callable[[T], bool]
TParamPredicate = Callable[[T, K], bool]
TMapper = Callable[[T], V]
TParamMapper = Callable[[T, K], V]
TAccumulator = Callable[[V, T], V]
TReducer = Callable[[T, T], T]
TGenerator = Callable[[T], V]
TComparator = Callable[[T, T], int]
TFactory = Callable[[], T]
TErrorFactory = TFactory[Exception]
TErrorOrFactory = Union[Exception, TErrorFactory]
TTransformer = Callable[[T], T]
TFunction = Callable[..., Any]
TFuncDecorator = TTransformer[TFunction]
TKeyMapper = Callable[[T], V]
TCollector = Callable[[Iterable[T]], V]
TFactoryOrValue = Union[T, TFactory[T]]
TTypedReturnFunction = Callable[..., T]
TNoReturnFunction = Callable[..., None]
TTypedFunction = Callable[[T], V]
TPredicateOrValue = Union[T, Callable[[T], bool]]
TSupplierOrValue = Union[V, Callable[[], V]]
TAnyFunction = Callable[[Any], Any]
TLogger = TParamAction[Exception]
TExceptionHandler = TLogger
TSetter = Callable[[T], None]
TGetter = TSupplier[T]

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec
__all__ = ["ParamSpec"]
