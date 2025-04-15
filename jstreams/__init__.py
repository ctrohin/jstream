from jstreams.stream import (
    Stream,
    find_first,
    map_it,
    matching,
    flat_map,
    not_null_elements,
    reduce,
    take_while,
    drop_while,
    Opt,
    ClassOps,
    stream,
    optional,
    predicate_of,
    predicate_with_of,
    mapper_of,
    mapper_with_of,
    Predicate,
    Mapper,
    PredicateWith,
    MapperWith,
    Reducer,
    reducer_of,
    extract_list,
    extract_non_null_list,
)

from jstreams.try_opt import (
    Try,
    ErrorLog,
    try_,
    try_of,
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
    rx_reduce,
    rx_filter,
    rx_map,
    RxOperator,
    BaseFilteringOperator,
    BaseMappingOperator,
    rx_take,
    rx_take_while,
    rx_take_until,
    rx_drop_while,
    rx_drop_until,
    rx_drop,
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
    cancel_thread,
    Cancellable,
)

from jstreams.timer import (
    Timer,
    Interval,
    CountdownTimer,
    set_timer,
    set_interval,
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
    resolve_dependencies,
    resolve_variables,
    component,
    service,
    Variable,
    StrVariable,
    IntVariable,
    FloatVariable,
    DictVariable,
    SetVariable,
    ListVariable,
    Dependency,
    InjectedVariable,
    inject_args,
    autowired,
    autowired_optional,
    provide,
    provide_variable,
    configuration,
    return_wired,
    return_wired_optional,
)

from jstreams.noop import (
    NoOpCls,
    noop,
)

from jstreams.utils import (
    require_non_null,
    is_number,
    to_int,
    to_float,
    as_list,
    keys_as_list,
    is_callable,
    is_not_none,
    is_empty_or_none,
    each,
    dict_update,
    sort,
)

from jstreams.predicate import (
    is_true,
    is_false,
    is_none,
    is_in,
    is_not_in,
    equals,
    is_blank,
    default,
    all_none,
    all_not_none,
    str_contains,
    str_contains_ignore_case,
    str_starts_with,
    str_starts_with_ignore_case,
    str_ends_with,
    str_ends_with_ignore_case,
    str_matches,
    str_not_matches,
    str_longer_than,
    str_shorter_than,
    str_longer_than_or_eq,
    str_shorter_than_or_eq,
    equals_ignore_case,
    is_even,
    is_odd,
    is_positive,
    is_negative,
    is_zero,
    is_int,
    is_beween,
    is_beween_closed,
    is_beween_closed_start,
    is_beween_closed_end,
    not_,
    not_strict,
    not_equals,
    is_not_blank,
    is_higher_than,
    is_higher_than_or_eq,
    is_less_than,
    is_less_than_or_eq,
    any_of,
    all_of,
    none_of,
    has_key,
    has_value,
    is_in_interval,
    is_in_open_interval,
    is_key_in,
    is_value_in,
    contains,
)

from jstreams.match import (
    Case,
    Match,
    DefaultCase,
    case,
    match,
    match_opt,
    default_case,
)

from jstreams.tuples import (
    Pair,
    pair,
    Triplet,
    triplet,
    left_matches,
    right_matches,
    middle_matches,
    pair_of,
    triplet_of,
    pair_stream,
    triplet_stream,
)

from jstreams.collectors import (
    grouping_by,
    joining,
    Collectors,
)

from jstreams.state import (
    default_state,
    use_state,
    use_async_state,
    null_state,
)

from jstreams.scheduler import (
    scheduler,
    schedule_daily,
    schedule_duration,
    schedule_hourly,
    schedule_periodic,
    Duration,
)

__all__ = [
    "each",
    "dict_update",
    "Stream",
    "find_first",
    "map_it",
    "matching",
    "flat_map",
    "reduce",
    "take_while",
    "drop_while",
    "is_not_none",
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
    "rx_reduce",
    "rx_filter",
    "rx_map",
    "RxOperator",
    "BaseFilteringOperator",
    "BaseMappingOperator",
    "LoopingThread",
    "CallbackLoopingThread",
    "Timer",
    "Interval",
    "CountdownTimer",
    "cancel_thread",
    "set_timer",
    "set_interval",
    "clear",
    "injector",
    "NoOpCls",
    "noop",
    "inject",
    "var",
    "require_non_null",
    "is_number",
    "to_int",
    "to_float",
    "as_list",
    "keys_as_list",
    "is_true",
    "is_false",
    "is_none",
    "is_in",
    "is_not_in",
    "equals",
    "is_blank",
    "default",
    "all_none",
    "all_not_none",
    "str_contains",
    "str_contains_ignore_case",
    "str_starts_with",
    "str_starts_with_ignore_case",
    "str_ends_with",
    "str_ends_with_ignore_case",
    "str_matches",
    "str_not_matches",
    "str_longer_than",
    "str_shorter_than",
    "str_longer_than_or_eq",
    "str_shorter_than_or_eq",
    "equals_ignore_case",
    "is_even",
    "is_odd",
    "is_positive",
    "is_negative",
    "is_zero",
    "is_int",
    "is_beween",
    "is_beween_closed",
    "is_beween_closed_start",
    "is_beween_closed_end",
    "not_",
    "not_strict",
    "not_equals",
    "is_not_blank",
    "AutoStart",
    "AutoInit",
    "is_callable",
    "Case",
    "Match",
    "DefaultCase",
    "case",
    "match",
    "match_opt",
    "default_case",
    "is_higher_than",
    "is_higher_than_or_eq",
    "is_less_than",
    "is_less_than_or_eq",
    "any_of",
    "all_of",
    "none_of",
    "predicate_of",
    "predicate_with_of",
    "mapper_of",
    "mapper_with_of",
    "Predicate",
    "Mapper",
    "PredicateWith",
    "MapperWith",
    "Reducer",
    "reducer_of",
    "has_key",
    "has_value",
    "is_in_interval",
    "is_in_open_interval",
    "contains",
    "rx_take",
    "rx_take_while",
    "rx_take_until",
    "rx_drop_while",
    "rx_drop_until",
    "rx_drop",
    "Cancellable",
    "is_empty_or_none",
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
    "left_matches",
    "right_matches",
    "middle_matches",
    "pair_of",
    "triplet_of",
    "is_key_in",
    "is_value_in",
    "InjectedDependency",
    "OptionalInjectedDependency",
    "resolve_dependencies",
    "resolve_variables",
    "Variable",
    "StrVariable",
    "IntVariable",
    "FloatVariable",
    "Dependency",
    "InjectedVariable",
    "component",
    "inject_args",
    "grouping_by",
    "joining",
    "Collectors",
    "DictVariable",
    "default_state",
    "use_state",
    "use_async_state",
    "null_state",
    "extract_list",
    "extract_non_null_list",
    "not_null_elements",
    "ListVariable",
    "SetVariable",
    "service",
    "autowired",
    "autowired_optional",
    "provide",
    "provide_variable",
    "configuration",
    "return_wired",
    "return_wired_optional",
    "try_",
    "try_of",
    "scheduler",
    "schedule_daily",
    "schedule_duration",
    "schedule_hourly",
    "schedule_periodic",
    "Duration",
    "pair_stream",
    "triplet_stream",
]
