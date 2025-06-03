# jstreams
jstreams is a Python library aiming to replicate the following:
- Java [Streams](https://github.com/ctrohin/jstream/wiki/Streams-API) and [Optional](https://github.com/ctrohin/jstream/wiki/Opt) functionality.
- a basic [ReactiveX](https://github.com/ctrohin/jstream/wiki/ReactiveX) implementation
- a replica of Java's vavr.io [Try API](https://github.com/ctrohin/jstream/wiki/Try)
- a [dependency injection](https://github.com/ctrohin/jstream/wiki/Dependency-Injection) container
- some utility classes for [threads as well as JavaScript-like timer and interval](https://github.com/ctrohin/jstream/wiki/Threads-and-timers) functionality
- a simple [state management](https://github.com/ctrohin/jstream/wiki/State) API
- a [task scheduler](https://github.com/ctrohin/jstream/wiki/Scheduler) with support for decorated functions and on-demand scheduling
- an [eventing](https://github.com/ctrohin/jstream/wiki/Eventing) framework that supports event publishing an subscribing
- [decorators](https://github.com/ctrohin/jstream/wiki/Decorators) such as `@builder`, `@setter`, `@getter`, `@synchronized` and `@synchronized_static`, `@required_args`, `@validate_args`,`@default_on_error` for reducing boilerplate code
- a [serialization](https://github.com/ctrohin/jstream/wiki/Serialization) framework capable of deep serializiation and deserialization of objects based on type hints
The library is implemented with type safety in mind.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install jstreams.

## Examples
If you wish to check out some example integrations you can visit the [examples](https://github.com/ctrohin/jstream/tree/master/examples) repo, or the [integration tests](https://github.com/ctrohin/jstream/tree/master/tests_integration) repo.

```bash
pip install jstreams
```

## Documentation
You can check out the full documentation with examples [here](https://github.com/ctrohin/jstream/wiki).


## Changelog
### v2025.6.1
- ReactiveX
    - Added `throttle`, `buffer`. `buffer_count`, `debounce`, `defer`, `distinct`, `element_at`, `empty`, `ignore_all`, `map_to`, `never`, `of_type`, `range`, `scan`, `tap`, `throw` and `timestamp` ReactiveX operators
    - Added `BackpressureStrategy` to observable subscriptions
    - Allow empty subscriptions on observables, since now they can be tapped
    - Added `combine_latest`, `zip` and `merge` for observables.
    - Pipes can now use async operators such as `debounce`
- Stream
    - Added `to_sorted_list` collector
    - Added `just` factory method for a stream of a single value
    - Added `map_indexed`, `filter_indexed`, `group_adjacent`, `windowed`, `pad` and `flatten_opt` operations 
    - Improved performance of `flat_map` to perform lazy mapping
- Python version compatibility
    - Added python 3.12 and 3.13 to the build pipelines

### v2025.5.3
- Added serialization module
- Performance improvements for dependency injection
- Added Wiki [documentation](https://github.com/ctrohin/jstream/wiki)

### v2025.5.2
- Fixed bugs in intersperse, scan, pairwise and sliding window
- Added factory methods for Stream and Opt

### v2025.5.1 (yanked)
- Added [eventing](https://github.com/ctrohin/jstream/wiki/Eventing) framework
- Added [decorators](https://github.com/ctrohin/jstream/wiki/Decorators) for boilerplate code reduction decorators
- Added `resolve_all` and `resolve` decorators for the injection mechanism, which will try to inject all type hinted fields of a class.
- Added `retry`, `recover` and `recover_from` chains to [Try](https://github.com/ctrohin/jstream/wiki/Try) objects allowing the user to specify a number of times the operation should be retried if a failure happenns, recover from a failure by providing a result supplier, and also recover from specific types of exceptions. 
### v2025.4.2
Added new scheduler module with the following functionality:
- *schedule_periodic* decorator for functions that need to be executed at a given time interval
- *schedule_hourly* decorator for functions that need to be executed at a certain minute every hour
- *schedule_daily* decorator for functions that need to be executed at a certain hour an minute every day
- *scheduler* function to access the scheduler and explicitly (without a need for decoration) schedule task
See the [Scheduler](https://github.com/ctrohin/jstream/wiki/Scheduler) section below for more details


### v2025.4.1
#### BREAKING CHANGES
Since version **v2025.4.1** **jstreams** has been refactored to use naming conventions in compliance with **PEP8**. As such, any projects depending on **jstreams** must be updated to use the **snake_case** naming convention for members and functions, instead of the **mixedCase** used until this version.

#### Improvements
- Classes using attribute injection using *resolve_dependencies* and *resolve_variables* no longer need the dependencies declared ahead of time
- *Dependency* and *Variable* classes used for injecting dependencies have now the *is_optional* flag, which will use the *find* injection mechanism instead of the *get* mechanism.
- Dependency injection profiles: you can now specify profiles for each provided component. In order to activate a profile, you can use the `injector().activate_profile(profile)` call.
This versions adds the following features:
- [stream collectors](https://github.com/ctrohin/jstream/wiki/Collectors)
    - the *Stream* class has been enriched with the *collectUsing* method to transform/reduce a stream
    - the *Collectors* class has been added containing the following collectors:
        - to_list - produces a list of the elements of the stream
        - to_set - produces a set of the elements of the stream
        - grouping_by - produces a dictionary of the stream with the grouping value as key and a list of elements as values
        - partitioning_by - produces a dictionary of the string with True/False as key (as returned by the given condition) and a list of elements as values
        - joining - produces a string from all elements of the stream by joining them with the given separator
- [argument injection](https://github.com/ctrohin/jstream/wiki/Dependency-Injection#inject_argsdependencies-dictstr-uniontype-dependency-variable---callablecallable-t-callable-t) via the *inject_args* decorator.
- the ability to retrieve all dependencies of a certain type using the *all_of_type* and *all_of_type_stream* methods. This method is useful when multiple dependecies that implement the same parent class are provided, for cases where you have multiple validators that can be dynamically provided.
- a simple state management API - [State management](https://github.com/ctrohin/jstream/wiki/State)

### v2025.3.2
This version adds more [dependency injection](https://github.com/ctrohin/jstream/wiki/Dependency-Injection) options (for usage, check the Dependency injection section below):
- *resolve_variables* decorator - provides class level variable injection
- *resolve_dependencies* decorator - provides class level dependency injection
- *component* decorator - provides decoration for classes. A decorated class will be injected once its module is imported
- *InjectedVariable* class - a class providing access to a injected variable without the need for decoration or using the `injector` directly
- added callable functionality to `InjectedDependency` and `OptionalInjectedDependency` classes. You can now call `dep()` instead of `dep.get()`
### v2025.2.11
Version 2025.2.11 adds the following enhancements:
#### Pair and Triplet
The [Pair and triplet](https://github.com/ctrohin/jstream/wiki/Pair-and-Triplet) classes are object oriented substitutions for Python tuples of 2 and 3 values. A such, they don't need to be unpacked and can be used by calling the **left**, **right** and **middle**(Triplets only) methods.
For enhanced support with predicates and streams, **jstreams** also provides the following predicates dedicated to pairs and triplets:
- *left_matches* - A predicate that takes another predicate as a parameter, and applies it to the **left** of a Pair/Triplet
- *right_matches* - A predicate that takes another predicate as a parameter, and applies it to the **right** of a Pair/Triplet
- *middle_matches* - A predicate that takes another predicate as a parameter, and applies it to the **middle** of a Triplet
#### New predicates
The following general purpose predicates have been added:
- *is_key_in* - checks if the predicate argument is present as a key in the predicate mapping
- *is_value_in* - checks if the predicate argument is present as a value in the predicate mapping
### v2025.2.9
From this version onwards, **jstreams** is switching the the following semantic versioning *YYYY.M.R*. YYYY means the release year, M means the month of the release within that year, and R means the number of release within that month. So, 2025.2.9 means the ninth release of February 2025.

Version v2025.2.9 updates the *Predicate*, *PredicateWith*, *Mapper*, *MapperWith* and *Reducer* classes to be callable, so they can now be used without explicitly calling their underlying methods. This change allows predicates, mappers and reducers to be used as functions, not just in *Stream*, *Opt* and *Case* operations. v2025.2.9 also introduces a couple of new predicates:
- has_key - checks if a map contains a key
- has_value - checks if a map contains a value
- is_in_interval - checks if a value is in a closed interval, alias for *isBetweenClosed*
- is_in_open_interval - checks if a value is in an open interval, aloas for *isBetween*
- contains - checks if an Iterable contains an element (the symetrical function for *isIn*)
- all_of - produces a new predicate that checks for a list of given predicates. Returns True if all predicates are satisfied
- any_of - produces a new predicate that checks for a list of given predicates. Returns True if any of the predicates are satisfied
- none_of - produces a new predicate that checks for a list of given predicates. Returns True if none of the predicates are satisfied

The *Predicate* and *PredicateWith* classes have been enriched with the *and_* and *or_* methods in order to be chained with another predicate.

### v4.1.0 

#### What's new?
Version 4.1.0 introduces the *Match* and *Case* classes that can implement switching based on predicate functions and predicate classes.

### v4.0.0 
#### What's new?
Version 4.0.0 introduces the *Predicate*, *Mapper* and *Reducer* classes that can replace the functions used so far for predicate matchig, mapping and reducing of streams. The added advantage for these classes is that they can be extended and can contain dynamic business logic.

#### BREAKING CHANGES

In version 4.0.0, the Opt class has been refactored to fall in line with the Java implementation. The methods *getOrElse*, *getOrElseOpt*, *getOrElseGet* and *getOrElseGetOpt* have been removed, and the methods *orElse*, *orElseOpt*, *orElseGet* and *orElseGetOpt* will be replacing them. The older signatures for the *orElse* and *orElseOpt* have been changed to adapt to this change. In order to migrate you can follow this guide:

```python
# Old usage of orElse
Opt(None).orElse(lambda: "test")
# can be replaced with
Opt(None).or_else_get(lambda: "test")

# Old usage of getOrElse
Opt(None).getOrElse("test")
# can be replaced with
Opt(None).or_else("test")

# Old usage of getOrElseGet, which was the same as orElse
Opt(None).getOrElseGet(lambda: "test")
# can be replaced with
Opt(None).or_else_get(lambda: "test")
```

## License

[MIT](https://choosealicense.com/licenses/mit/)