from jstreams.stream import (
    each,
    dictUpdate,
    Stream,
    findFirst,
    mapIt,
    matching,
    flatMap,
    reduce,
    takeWhile,
    dropWhile,
    isNotNone,
    sort,
    Opt,
    ClassOps,
    stream,
    optional,
    predicateOf,
    predicateWithOf,
    mapperOf,
    mapperWithOf,
    Predicate,
    Mapper,
    PredicateWith,
    MapperWith,
    Reducer,
    reducerOf,
    isEmptyOrNone,
)

from jstreams.tryOpt import (
    Try,
    ErrorLog,
)

from jstreams.rx import (
    ObservableSubscription,
    Observable,
    Flowable,
    Single,
    BehaviorSubject,
    PublishSubject,
    ReplaySubject,
    CompletedHandler,
    ErrorHandler,
    DisposeHandler,
    NextHandler,
    Pipe,
    Reduce,
    Filter,
    Map,
    rxReduce,
    rxFilter,
    rxMap,
    RxOperator,
    BaseFilteringOperator,
    BaseMappingOperator,
    rxTake,
    rxTakeWhile,
    rxTakeUntil,
    rxDropWhile,
    rxDropUntil,
    rxDrop,
    TakeWhile,
    TakeUntil,
    Drop,
    DropUntil,
    DropWhile,
    Take,
)

from jstreams.thread import (
    LoopingThread,
    CallbackLoopingThread,
    cancelThread,
    Cancellable,
)

from jstreams.timer import (
    Timer,
    Interval,
    CountdownTimer,
    setTimer,
    setInterval,
    clear,
)

from jstreams.ioc import (
    injector,
    AutoInit,
    AutoStart,
    inject,
    var,
    InjectedDependency,
    OptionalInjectedDependency,
    resolveDependencies,
    resolveVariables,
    component,
    Variable,
    StrVariable,
    IntVariable,
    FloatVariable,
    Dependency,
    InjectedVariable,
)

from jstreams.noop import (
    NoOpCls,
    noop,
)

from jstreams.utils import (
    requireNotNull,
    isNumber,
    toInt,
    toFloat,
    asList,
    keysAsList,
    isCallable,
)

from jstreams.predicate import (
    isTrue,
    isFalse,
    isNone,
    isIn,
    isNotIn,
    equals,
    isBlank,
    default,
    allNone,
    allNotNone,
    strContains,
    strContainsIgnoreCase,
    strStartsWith,
    strStartsWithIgnoreCase,
    strEndsWith,
    strEndsWithIgnoreCase,
    strMatches,
    strNotMatches,
    strLongerThan,
    strShorterThan,
    strLongerThanOrEqual,
    strShorterThanOrEqual,
    equalsIgnoreCase,
    isEven,
    isOdd,
    isPositive,
    isNegative,
    isZero,
    isInt,
    isBeween,
    isBeweenClosed,
    isBeweenClosedStart,
    isBeweenClosedEnd,
    not_,
    notStrict,
    notEquals,
    isNotBlank,
    isHigherThan,
    isHigherThanOrEqual,
    isLessThan,
    isLessThanOrEqual,
    anyOf,
    allOf,
    noneOf,
    Not,
    NotStrict,
    hasKey,
    hasValue,
    isInInterval,
    isInOpenInterval,
    isKeyIn,
    isValueIn,
    contains,
)

from jstreams.match import (
    Case,
    Match,
    DefaultCase,
    case,
    match,
    matchOpt,
    defaultCase,
)

from jstreams.tuples import (
    Pair,
    pair,
    Triplet,
    triplet,
    leftMatches,
    rightMatches,
    middleMatches,
)

__all__ = [
    "each",
    "dictUpdate",
    "Stream",
    "findFirst",
    "mapIt",
    "matching",
    "flatMap",
    "reduce",
    "takeWhile",
    "dropWhile",
    "isNotNone",
    "sort",
    "Opt",
    "ClassOps",
    "stream",
    "optional",
    "Try",
    "ErrorLog",
    "ObservableSubscription",
    "Observable",
    "Flowable",
    "Single",
    "BehaviorSubject",
    "PublishSubject",
    "ReplaySubject",
    "Pipe",
    "Reduce",
    "Filter",
    "Map",
    "rxReduce",
    "rxFilter",
    "rxMap",
    "RxOperator",
    "BaseFilteringOperator",
    "BaseMappingOperator",
    "LoopingThread",
    "CallbackLoopingThread",
    "Timer",
    "Interval",
    "CountdownTimer",
    "cancelThread",
    "setTimer",
    "setInterval",
    "clear",
    "injector",
    "NoOpCls",
    "noop",
    "inject",
    "var",
    "requireNotNull",
    "isNumber",
    "toInt",
    "toFloat",
    "asList",
    "keysAsList",
    "isTrue",
    "isFalse",
    "isNone",
    "isIn",
    "isNotIn",
    "equals",
    "isBlank",
    "default",
    "allNone",
    "allNotNone",
    "strContains",
    "strContainsIgnoreCase",
    "strStartsWith",
    "strStartsWithIgnoreCase",
    "strEndsWith",
    "strEndsWithIgnoreCase",
    "strMatches",
    "strNotMatches",
    "strLongerThan",
    "strShorterThan",
    "strLongerThanOrEqual",
    "strShorterThanOrEqual",
    "equalsIgnoreCase",
    "isEven",
    "isOdd",
    "isPositive",
    "isNegative",
    "isZero",
    "isInt",
    "isBeween",
    "isBeweenClosed",
    "isBeweenClosedStart",
    "isBeweenClosedEnd",
    "not_",
    "notStrict",
    "notEquals",
    "isNotBlank",
    "AutoStart",
    "AutoInit",
    "isCallable",
    "Case",
    "Match",
    "DefaultCase",
    "case",
    "match",
    "matchOpt",
    "defaultCase",
    "isHigherThan",
    "isHigherThanOrEqual",
    "isLessThan",
    "isLessThanOrEqual",
    "anyOf",
    "allOf",
    "noneOf",
    "predicateOf",
    "predicateWithOf",
    "mapperOf",
    "mapperWithOf",
    "Predicate",
    "Mapper",
    "PredicateWith",
    "MapperWith",
    "Reducer",
    "reducerOf",
    "Not",
    "NotStrict",
    "hasKey",
    "hasValue",
    "isInInterval",
    "isInOpenInterval",
    "contains",
    "rxTake",
    "rxTakeWhile",
    "rxTakeUntil",
    "rxDropWhile",
    "rxDropUntil",
    "rxDrop",
    "Cancellable",
    "isEmptyOrNone",
    "CompletedHandler",
    "ErrorHandler",
    "DisposeHandler",
    "NextHandler",
    "TakeWhile",
    "TakeUntil",
    "Drop",
    "DropUntil",
    "DropWhile",
    "Take",
    "Pair",
    "pair",
    "Triplet",
    "triplet",
    "leftMatches",
    "rightMatches",
    "middleMatches",
    "isKeyIn",
    "isValueIn",
    "InjectedDependency",
    "OptionalInjectedDependency",
    "resolveDependencies",
    "resolveVariables",
    "Variable",
    "StrVariable",
    "IntVariable",
    "FloatVariable",
    "Dependency",
    "InjectedVariable",
    "component",
]
