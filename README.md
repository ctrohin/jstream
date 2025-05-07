# jstreams
jstreams is a Python library aiming to replicate the following:
- Java [Streams](#streams) and [Optional](#opt) functionality.
- a basic [ReactiveX](#reactivex) implementation
- a minimal replication of Java's vavr.io [Try](#try)
- a [dependency injection](#dependency-injection-container) container
- some utility classes for [threads](#threads) as well as JavaScript-like [timer](#timer) and [interval](#interval) functionality
- a simple [state management](#state-management-api) API
- a [task scheduler](#scheduler) with support for decorated functions and on-demand scheduling
- an [eventing](#eventing) framework that supports event publishing an subscribing
- [annotations](#annotations) such as `@builder`, `@setter`, `@getter`, `@synchronized` and `@synchronized_static`, `@required_args`, `@validate_args`,`@default_on_error` for reducing boilerplate code
The library is implemented with type safety in mind.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install jstreams.

## Examples
If you wish to check out some example integrations you can visit the [examples](https://github.com/ctrohin/jstream/tree/master/examples) repo, or the [integration tests](https://github.com/ctrohin/jstream/tree/master/tests_integration) repo.

```bash
pip install jstreams
```
## Changelog
### v2025.5.2
- Fixed bugs in intersperse, scan, pairwise and sliding window
- Added factory methods for Stream and Opt

### v2025.5.1 (yanked)
- Added [eventing](#eventing) framework
- Added [annotations](#annotations) biolerplate code reduction decorators
- Added `resolve_all` and `resolve` decorators for the injection mechanism, which will try to inject all type hinted fields of a class.
- Added `retry`, `recover` and `recover_from` chains to [Try](#try) objects allowing the user to specify a number of times the operation should be retried if a failure happenns, recover from a failure by providing a result supplier, and also recover from specific types of exceptions. 
### v2025.4.2
Added new scheduler module with the following functionality:
- *schedule_periodic* decorator for functions that need to be executed at a given time interval
- *schedule_hourly* decorator for functions that need to be executed at a certain minute every hour
- *schedule_daily* decorator for functions that need to be executed at a certain hour an minute every day
- *scheduler* function to access the scheduler and explicitly (without a need for decoration) schedule task
See the [Scheduler](#scheduler) section below for more details


### v2025.4.1
#### BREAKING CHANGES
Since version **v2025.4.1** **jstreams** has been refactored to use naming conventions in compliance with **PEP8**. As such, any projects depending on **jstreams** must be updated to use the **snake_case** naming convention for members and functions, instead of the **mixedCase** used until this version.

#### Improvements
- Classes using attribute injection using *resolve_dependencies* and *resolve_variables* no longer need the dependencies declared ahead of time
- *Dependency* and *Variable* classes used for injecting dependencies have now the *is_optional* flag, which will use the *find* injection mechanism instead of the *get* mechanism.
- Dependency injection profiles: you can now specify profiles for each provided component. In order to activate a profile, you can use the `injector().activate_profile(profile)` call.
This versions adds the following features:
- [stream collectors](#stream-collectors)
    - the *Stream* class has been enriched with the *collectUsing* method to transform/reduce a stream
    - the *Collectors* class has been added containing the following collectors:
        - to_list - produces a list of the elements of the stream
        - to_set - produces a set of the elements of the stream
        - grouping_by - produces a dictionary of the stream with the grouping value as key and a list of elements as values
        - partitioning_by - produces a dictionary of the string with True/False as key (as returned by the given condition) and a list of elements as values
        - joining - produces a string from all elements of the stream by joining them with the given separator
- [argument injection](#attribute-and-argument-injection) via the *inject_args* decorator.
- the ability to retrieve all dependencies of a certain type using the *all_of_type* and *all_of_type_stream* methods. This method is useful when multiple dependecies that implement the same parent class are provided, for cases where you have multiple validators that can be dynamically provided.
- a simple state management API - [State management](#state-management-api)
```python
class ValidatorInterface(abc.ABC):
    @abc.abstractmethod
    def validate(self, value: str) -> bool:
        pass

class ContainsAValidator(ValidatorInterface):
    def validate(self, value: str) -> bool:
        return "A" in value

class ContainsBValidator(ValidatorInterface):
    def validate(self, value: str) -> bool:
        return "B" in value

# Provide both validators
injector().provide_dependencies({
    ContainsAValidator: ContainsAValidator(),
    ContainsBValidator: ContainsBValidator()
})

# Then validate a string against all provided validators implementing 'ValidatorInterface'
validators = injector().all_of_type(ValidatorInterface)
isValid = True
testString = "AB"
for validator in validators:
    if not validator.validate(testString):
        isValid = False
        break
print(isValid) # Prints out "True" since the string passes both validations

# Or use the stream functionality
isValid = injector().all_of_type_stream(ValidatorInterface).all_match(lambda v: v.validate(testString))
print(isValid) # Prints out "True" since the string passes both validations
```
### v2025.3.2
This version adds more [dependency injection](#dependency-injection-container) options (for usage, check the Dependency injection section below):
- *resolve_variables* decorator - provides class level variable injection
- *resolve_dependencies* decorator - provides class level dependency injection
- *component* decorator - provides decoration for classes. A decorated class will be injected once its module is imported
- *InjectedVariable* class - a class providing access to a injected variable without the need for decoration or using the `injector` directly
- added callable functionality to `InjectedDependency` and `OptionalInjectedDependency` classes. You can now call `dep()` instead of `dep.get()`
### v2025.2.11
Version 2025.2.11 adds the following enhancements:
#### Pair and Triplet
The [Pair and triplet](#pair-and-triplet) classes are object oriented substitutions for Python tuples of 2 and 3 values. A such, they don't need to be unpacked and can be used by calling the **left**, **right** and **middle**(Triplets only) methods.
For enhanced support with predicates and streams, **jstreams** also provides the following predicates dedicated to pairs and triplets:
- *left_matches* - A predicate that takes another predicate as a parameter, and applies it to the **left** of a Pair/Triplet
- *right_matches* - A predicate that takes another predicate as a parameter, and applies it to the **right** of a Pair/Triplet
- *middle_matches* - A predicate that takes another predicate as a parameter, and applies it to the **middle** of a Triplet
```python
p = pair("string", 0)
pred = right_matches(isZero)
pred(p) 
# Returns True since the right value is, indeed, zero

# Usage with optional
optional(pair("string", 0)).filter(left_matches(contains("tri"))).filter(right_matches(is_zero)).get() 
# Returns the pair, since both fields match the given predicates

# Usage with stream
pairs = [pair("test", 1), pair("another", 11), pair("test1", 2)]
stream(pairs).filter(left_matches(contains("test"))).filter(right_matches(is_higher_than(1))).toList() 
# Produces [pair("test1", 2)], since this is the only item that can pass both filters

```
#### New predicates
The following general purpose predicates have been added:
- *is_key_in* - checks if the predicate argument is present as a key in the predicate mapping
- *is_value_in* - checks if the predicate argument is present as a value in the predicate mapping
```python
predIsKeyIn = is_key_in({"test": "1"})
predIsKeyIn("test") 
# Returns True, since the given string is a key in the predicate dictionary

predIsKeyIn("other") 
# Returns False, since the givem string is not a key in the predicate dictionary

predIsValueIn = is_value_in({"test": "1"})
predIsValueIn("1")
# Returns True, since the given string is a value in the predicate dictionary

predIsValueIn("0")
# Returns False, since the given string is not a value in the predicate dictionary

```
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

```python
# Define a predicate
isNonePredicate = predicate_of(isNone)

# Before 2025.2.9
isNonePredicate.apply(None) # Returns True
isNonePredicate.apply("test") # Returns False

# After 2025.2.9
isNonePredicate(None) # Returns True, internally calls the *Apply* method of the predicate
isNonePredicate("test") # Returns False

# Chain predicates
chainedPredicate = predicate_of(is_not_none).and_(equals("test"))
chainedPredicate("test") # Returns True, since the parameter is not none and matches the equals predicate
chainedPredicate(None) # Returns False, since the parameter fails the first predicate, isNotNone
chainedPredicate("other") # Returns False, since the parameter passes the isNotNone
```

### v4.1.0 

#### What's new?
Version 4.1.0 introduces the *Match* and *Case* classes that can implement switching based on predicate functions and predicate classes.

```python
# Returns the string "Hurray!"
match("test").of(
    case("test", "Hurray!"),
    case("test1", "Not gonna happen")
)

# Default casing, as a fallback for when the value doesn't match any of the cases
# IMPORTANT NOTE! The default case should ALWAYS be called last, as it will break the match if called before all cases are tested.
match("not-present").of(
    case("test", "Hurray!"),
    case("test1", "Not gonna happen"),
    default_case("Should never get here!")
)
```

Version 4.0.0 introduces the *Predicate*, *Mapper* and *Reducer* classes that can replace the functions used so far for predicate matchig, mapping and reducing of streams. The added advantage for these classes is that they can be extended and can contain dynamic business logic.
```python
# Take the numbers from a stream until the third prime number is found.

def is_prime(value: int) -> bool:
    ...

class TakeUntilThreePrimes(Predicate[int]):
    def __init__(self) -> None:
        self.numberOfPrimesFound = 0

    def apply(self, value: int) -> bool:
        if self.numberOfPrimesFound >= 3:
            return False

        if is_prime(value):
            self.numberOfPrimesFound += 1
        return True

# Then we take a stream if ints
Stream([3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]).take_while(TakeUntilThreePrimes()).each(print)
# This will print 3, 4, 5, 6, 8, 9, 10, 11, then stop the stream since three prime numbers were found.
```

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
## Usage
### Streams

```python
from jstreams import Stream

# Applies a mapping function on each element then produces a new string
print(Stream(["Test", "Best", "Lest"]).map(str.upper).collect())
# will output ["TEST", "BEST", "LEST"]

# Filter the stream elements
print(Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .collect())
# Will output ['Test']

# isNotEmpty checks if the stream is empty
print(Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .is_not_empty())
# Will output True

# Checks if all elements match a given condition
print(Stream(["Test", "Best", "Lest"]).all_match(lambda s: s.endswith("est")))
# Will output True

print(Stream(["Test", "Best", "Lest"]).all_match(lambda s: s.startswith("T")))
# Will output False

# Checks if any element matches a given condition
print(Stream(["Test", "Best", "Lest"]).any_match(lambda s: s.startswith("T")))
# Will output True

# Checks if no elements match the given condition
print(Stream(["Test", "Best", "Lest"]).none_match(lambda s: s.startswith("T")))
# Will output False

# Gets the first value of the stream as an Opt (optional object)
print(Stream(["Test", "Best", "Lest"])
            .find_first(lambda s: s.startswith("L"))
            .get_actual())
# Will output "Lest"

# Returns the first element in the stream
print(Stream(["Test", "Best", "Lest"]).first())
# Will output "Test"

# cast casts the elements to a different type. Useful if you have a stream
# of base objects and want to get only those of a super class
print(Stream(["Test1", "Test2", 1, 2])
            .filter(lambda el: el == "Test1")
            # Casts the filtered elements to the given type
            .cast(str)
            .first())
# Will output "Test1"

# If the stream elements are Iterables, flat_map will produce a list of all contained items
print(Stream([["a", "b"], ["c", "d"]]).flat_map(list).toList())
# Will output ["a", "b", "c", "d"]

# reduce will produce a single value, my applying the comparator function given as parameter
# in order to decide which value is higher. The comparator function is applied on subsequent elements
# and only the 'highest' one will be kept
print(Stream([1, 2, 3, 4, 20, 5, 6]).reduce(max).get_actual())
# Will output 20

# notNull returns a new stream containing only non null elements
print(Stream(["A", None, "B", None, None, "C", None, None]).non_null().to_list())
# Will output ["A", "B", "C"]

```

#### Stream collectors
```python
def collector_group_by() -> None:
    values = Stream(
        [
            {"key": 1, "prop": "prop", "value": "X1"},
            {"key": 1, "prop": "prop", "value": "X2"},
            {"key": 1, "prop": "prop1", "value": "X3"},
            {"key": 1, "prop": "prop1", "value": "X4"},
        ]
    ).collect_using(Collectors.grouping_by(lambda x: x["prop"]))
    # values will be equal to:
    # {
    #     "prop": [
    #         {"key": 1, "prop": "prop", "value": "X1"},
    #         {"key": 1, "prop": "prop", "value": "X2"},
    #     ],
    #     "prop1": [
    #         {"key": 1, "prop": "prop1", "value": "X3"},
    #         {"key": 1, "prop": "prop1", "value": "X4"},
    #     ],
    # }
    # The collector groups the values into a dictionary, for each provided grouping
```

### Opt
```python
from jstreams import Opt

# Checks if the value given is present
Opt(None).is_present() # Will return False
Opt("test").is_present() # Will return True


# There are two ways of getting the value from the Opt object. The get returns a non optional
# value and  will raise a value error if the object is None. On the other hand, getActual returns
# an optional object and does not raise a value error
Opt("test").get() # Does not fail, and returns the string "test"
Opt(None).get() # Raises ValueError since None cannot be casted to any type
Opt(None).get_actual() # Returns None, does not raise value error

# The ifPresent method will execute a lambda function if the object is present
Opt("test").if_present(lambda s: print(s)) # Will print "test"
Opt(None).if_present(lambda s: print(s)) # Does nothing, since the object is None

# The orElse method will return the value of the Opt if not None, otherwise the given parameter
Opt("test").or_else("test1") # Will return "test", since the value is not None
Opt(None).or_else("test1") # Will return "test1", since the value is  None

# The orElseGet method will return the value of the Opt if not None, otherwise it will execute 
# the given function and return its value
Opt("test").or_else_get(lambda: "test1") # Will return "test", since the value is not None
Opt(None).or_else_get(lambda: "test1") # Will return "test1", since the value is  None

# stream will convert the object into a stream.
Opt("test").stream() # Is equivalent with Stream(["test"])
Opt(["test"]).stream() # Is equivalent with Stream([["test"]]). Notice the list stacking

# flat_stream will convert the object into a stream, with the advantage that it can
# detect whether the object is a list and avoids stacking lists of lists.
Opt("test").flat_stream() # Is equivalent with Stream(["test"])
Opt(["test", "test1", "test2"]).flat_stream() # Is equivalent with Stream(["test", "test1", "test2"])

```

### Predicates
Predicates are functions and function wrappers that can be used to filter streams and optionals. **jstreams** contains a comprehensive list of predefined predicates. The names are pretty self explanatory. Here are some of the predicates included:
- is_true
- is_false
- is_none
- is_not_none
- is_in
- is_not_in
- equals
- is_blank
- default
- all_none
- all_not_none
- str_contains
- str_contains_ignore_case
- str_starts_with
- str_starts_with_ignore_case
- str_ends_with
- str_ends_with_ignore_case
- str_matches
- str_not_matches
- str_longer_than
- str_shorter_than
- str_longer_than_or_eq
- str_shorter_than_or_eq
- equals_ignore_case
- is_even
- is_odd
- is_positive
- is_negative
- is_zero
- is_int
- is_beween
- is_beween_closed
- is_beween_closed_start
- is_beween_closed_end
- not_
- not_strict
- has_key
- has_value
- is_in_interval
- is_in_open_interval
- contains
- any_of
- all_of
- none_of

The predicates provided fall into one of two categories:
- functions - can be applied directly to a value
- function wrappers - take comparison parameters and then can be applied to a value

Examples:
```python
from jstreams import is_blank, is_not_blank, is_zero, is_between, not_

# functions
is_blank("test") # returns False
is_zero(0) # returns True

# function wrappers
is_between(1,10)(5) # First call generates the wraper, that can then be used for the value comparison
# reusing a function wrapper
isBetween1And10 = is_between(1, 10)
isBetween1And10(5) # Returns True
isBetween1And10(20) # Returns False

not_(is_blank)("test") # Returns True. The not_ predicate negates the given predicate, in this case isBlank, then applies it to the given value "test"

# Usage with Opt and Stream
Stream([2, 4, 5, 20, 40]).filter(is_between(0, 10)).to_list() # Results in [2, 4, 5], since the rest of the items are filtered out
# Usage of not with Opt and Stream
Stream(["", "", "", "test"]).filter(not_(is_blank)).to_list() # Results in ["test"] since the rest of the items are blank
# this is equivalent to 
Stream(["", "", "", "test"]).filter(is_not_blank).to_list() # isNotBlank is another predefined predicate that uses not_(isBlank) in its actual implementation
# Check if a stream contains the value 0
Stream([1, 2, 4, 0, 5]).any_match(is_zero) # Returns True, since 0 exists in the stream
```


### Try
```python
# The Try class handles a chain of function calls with error handling

def throwErr() -> None:
    raise ValueError("Test")

def returnStr() -> str:
    return "test"

# It is important to call the get method, as this method actually triggers the entire chain
Try(throwErr).on_failure(lambda e: print(e)).get() # The on_failure is called

# You can also use the and_finally method to execute code regardless of the failure status of the try
Try(throwErr).on_failure(lambda e: print(e)).and_finally(lambda val: print(f"The actual value is {val}")).get() # The on_failure is called, then the finally method is called.

# Both on_failure and and_finally are defined as chains, so you can add as many methods as you want here
(
    Try(throwErr)
    .on_failure(lambda e: print(e))
    .on_failure(lambda e: print(f"Second failure handler {e}"))
    .and_finally(lambda val: print(f"The actual value is {val}"))
    .and_finally(lambda val: print(f"Second finally handler. The actual value is {val}"))
    .get()
) 

Try(returnStr).and_then(lambda s: print(s)).get() # Will print out "test"

# The of method can actually be used as a method to inject a value into a Try without
# actually calling a method or lambda
Try.of("test").and_then(lambda s: print(s)).get() # Will print out "test"

# You can use `retry` for API calls
Try(lambda: requests.get(...)).retry(3).recover(lambda _: DefaultResponse()).get()
# in this case, the recovery happens for any raised exception (and only after 3 retries)
# or specify error types to recover from
Try(lambda: requests.get(...)).retry(3).recover_from(HttpError, lambda _: DefaultResponse()).get()
# in this case, the recovery only happens if an HttpError is raised.
```

### ReactiveX
The **jstreams** library includes a basic implementation of the ReactiveX API including observables, subjects and a handful of reactive operators.

#### Observables
Observables that are currently implemented in **jstreams** are of two types:
- *Single* - will only hold a single value
- *Flowable* - will hold an iterable providing values

##### Single
```python
from jstreams import Single

singleObs = Single("test")
# Will print out "test"
# When subscribing, the observable will emit the value it holds
# to the subscriber
singleObs.subscribe(
    lambda s: print(s)
)
```

##### Flowable
```python
from jstreams import Flowable

flowableObs = Flowable(["test1", "test2"])
# Will print out "test1" then "test2"
# When subscribing, the observable will emit the values it holds
# to the subscriber
flowableObs.subscribe(
    lambda s: print(s)
)
```
#### Subjects
**jstreams** implements the following Subject types:
- *BehaviorSubject* - will only hold a single value, keep it stored, then emit it whenever a subscriber subscribes, then emit any change to all subscribers
- *PublishSubject* - similar to *BehaviorSubject*, but only emits a change to all subscribers. No emission happens when subscribing
- *ReplaySubject* - will hold an list of past values and emit them all when subscribing to the subject. Subsequent changes are also emitted

##### BehaviorSubject
```python
from jstreams import BehaviorSubject

# Initialize the subject with a default value
subject = BehaviorSubject("A")
subject.on_next("B")

# Will print out "B" as this is the current value stored in the Subject
subject.subscribe(
    lambda s: print(s)
)

# Will print out "C" as this is the next value stored in the Subject,
# any new subscription at this point will receive "C"
subject.on_next("C")

# For long lived subjects and observables, it is wise to call the
# dispose method so that all subscriptions can be cleared and no
# references are kept. The subject can be reused, but all 
# subscriptions will need to be re-registered
subject.dispose()
```

##### PublishSubject
```python
from jstreams import PublishSubject

# Initialize the subject. Since the subject doesn't hold any initial value
# it cannot infer the type, so the type needs to be specified
subject = PublishSubject(str)

# Nothing happens at this point, since PublishSubject won't store the current value
subject.subscribe(
    lambda s: print(s)
)

# Will print out "C" as this is the next value sent tothe Subject.
# Any new subscription after this call not receive a value
subject.on_next("C")

# No value is sent to the subscriber, so nothing to print
subject.subscribe(
    lambda s: print(s)
)

# For long lived subjects and observables, it is wise to call the
# dispose method so that all subscriptions can be cleared and no
# references are kept. The subject can be reused, but all 
# subscriptions will need to be re-registered
subject.dispose()
```

##### ReplaySubject
```python
from jstreams import ReplaySubject

# Initialize the subject with a default value
subject = ReplaySubject(["A", "B", "C"])

# Will print out "A", then "B", then "C" as this the subject will replay
# the entire list of values whnever someone subscribes
subject.subscribe(
    lambda s: print(s)
)

# Will print out "D" as this is the next value added in the Subject,
# any new subscription at this point will receive "A", then "B", then "C", then "D"
subject.on_next("D")

# For long lived subjects and observables, it is wise to call the
# dispose method so that all subscriptions can be cleared and no
# references are kept. The subject can be reused, but all 
# subscriptions will need to be re-registered
subject.dispose()
```

#### Operators
**jstreams** provides a couple of operators, with more operators in the works.
The current operators are:
- *rx_map* - converts a value to a different form or type
- *rx_filter* - blocks or allows a value to be passed to the subscribers
- *rx_reduce* - causes the observable to emit a single value produced by the reducer function.
- *rx_take* - takes a number of values and ignores the rest
- *rx_take_while* - takes values as long as they match the given predicate. Once a value is detected that does not match, no more values will be passing through
- *rx_take_until* - takes values until the first value is found matching the given predicate. Once a value is detected that does not match, no more values will be passing through
- *rx_drop* - blocks a number of values and allows the rest to pass through
- *rx_drop_while* - blocks values that match a given predicate. Once the first value is found not matching, all remaining values are allowed through
- *rx_drop_until* - blocks values until the first value that matches a given predicate. Once the first value is found matching, all remaining values are allowed through

##### Map - rx_map
```python
from jstreams import ReplaySubject, rx_map

# Initialize the subject with a default value
subject = ReplaySubject(["A", "BB", "CCC"])
# Create an operators pipe
pipe = subject.pipe(
    # Map the strings to their length
    rx_map(lambda s: len(s))
)
# Will print out 1, 2, 3, the lengths of the replay values
pipe.subscribe(
    lambda v: print(v)
)
```

##### Filter - rx_filter
```python
from jstreams import ReplaySubject, rx_filter

# Initialize the subject with a default value
subject = ReplaySubject(["A", "BB", "CCC"])
# Create an operators pipe
pipe = subject.pipe(
    # Filters the values for length higher than 2
    rx_filter(lambda s: len(s) > 2)
)
# Will print out "CCC", as this is the only string with a length higher than 2
pipe.subscribe(
    lambda v: print(v)
)
```

##### Reduce - rx_reduce
```python
from jstreams import ReplaySubject, rx_reduce

# Initialize the subject with a default value
subject = ReplaySubject([1, 20, 3, 12])
# Create an operators pipe
pipe = subject.pipe(
    # Reduce the value to max
    rx_reduce(max)
)
# Will print out 1, then 20 since 1 is the first value, then 20, as the maximum between 
# the previous max (1) and the next value (20)
pipe.subscribe(
    lambda v: print(v)
)
```
##### Take - rx_take
```python
from jstreams import ReplaySubject, rx_take

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rx_take(int, 3)
)
# Will print out the first 3 elements, 1, 7 and 20
pipe1.subscribe(
    lambda v: print(v)
)
# Won't print anything anymore since the first 3 elements were already taken
subject.on_next(9)
```

##### TakeWhile - rx_take_while
```python
from jstreams import ReplaySubject, rx_take_while

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rx_take_while(lambda v: v < 10)
)
# Will print out 1, 7, since 20 is higher than 10
pipe1.subscribe(
    lambda v: print(v)
)
# Won't print anything since the while condition has already been reached
subject.on_next(9)
```

##### TakeUntil - rx_take_until
```python
from jstreams import ReplaySubject, rx_take_until

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rx_take_until(lambda v: v > 10)
)
# Will print out 1, 7, since 20 is higher than 10, which is our until condition
pipe1.subscribe(
    lambda v: print(v)
)
# Won't print anything since the until condition has already been reached
subject.on_next(9)
```

##### Drop - rx_drop
```python
from jstreams import ReplaySubject, rx_drop

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
self.val = []
pipe1 = subject.pipe(
    rx_drop(int, 3)
)
# Will print out 5, 100, 50, skipping the first 3 values
pipe1.subscribe(
    lambda v: print(v)
)
# Will print out 9, since it already skipped the first 3 values
subject.on_next(9)
```

##### DropWhile - rx_drop_while
```python
from jstreams import ReplaySubject, rx_drop_while

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rx_drop_while(lambda v: v < 100)
)
# Will print 100, 40, since the first items that are less than 100 are dropped
pipe1.subscribe(lambda v: print(v))
# Will 9, since the first items that are less than 100 are dropped, and 9 appears after the drop while condition is fulfilled
subject.on_next(9)
```

##### DropUntil - rx_drop_until
```python
from jstreams import ReplaySubject, rx_drop_until

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
val = []
pipe1 = subject.pipe(
    rx_drop_until(lambda v: v > 20)
)
# Will print out 100, 40, skipping the rest of the values until the first one 
# that fulfills the condition appears
pipe1.subscribe(val.append)
# Will print out 9, since the condition is already fulfilled and all remaining values will
# flow through
subject.on_next(9)
```

##### Combining operators
```python
from jstreams import ReplaySubject, rx_reduce, rx_filter

# Initialize the subject with a default value
subject = ReplaySubject([1, 7, 11, 20, 3, 12])
# Create an operators pipe
pipe = subject.pipe(
    # Filters only the values higher than 10
    rx_filter(lambda v: v > 10)
    # Reduce the value to max
    rx_reduce(max)
)
# Will print out 11, then 20 since 11 is the first value found higher than 10, then 20, as the maximum between the previous max (11) and the next value (20)
pipe.subscribe(
    lambda v: print(v)
)
```

##### Chaining pipes
**jstreams** allows pipes to be chained
```python
subject = ReplaySubject(range(1, 100))
val = []
val2 = []
chainedPipe = subject.pipe(
                rx_take_until(lambda e: e > 20)
            ).pipe(
                rx_filter(lambda e: e < 10)
            )
# val will contain 0..9
chainedPipe.subscribe(val.append)

# pipes allow multiple subscriptions
val2 = []
# val2 will contain 0..9
chainedPipe.subscribe(val2.append)
```

#### Custom operators
**jstreams** allows you to implement your own operators using two main base classes:
- *BaseMappingOperator* - any operator that can transform one value to another
- *BaseFilteringOperator* - any operator that can allow a value to pass through or not

As an example, you can see below the implementation of the reduce operator.
```python
class ReduceOperator(BaseFilteringOperator[T]):
    def __init__(self, reducer: Callable[[T, T], T]) -> None:
        self.__reducer = reducer
        self.__prevVal: Optional[T] = None
        super().__init__(self.__mapper)

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
```

### Dependency injection container
The dependency injection container built into **jstreams** is a simple and straightforward implementation, providing two sets of methods for:
- providing dependencies
- retrieving dependencies
The container does not support parameter injection or constructor injection, but does (as of March 2025) support attributes injection.

#### How can I use the dependency injection container
The idea behind the DI container is to use interfaces in order to provide functionality in applications.
```python
import abc
from jstreams import injector

# Use the abstraction of interfaces
class MyInterface(abc):
    def doSomething(self) -> None:
        pass

# This is the actual class we want to use
class MyConcreteClass(MyInterface):
    def doSomething(self) -> None:
        print("Something got done")

injector().provide(MyInterface, MyConcreteClass())

# When the functionality defined by the interface is needed, you can retrieve it
myObj = injector().get(MyInterface)
myObj.doSomething()

# Then, during testing, you can mock the interface
class MyInterfaceMock(MyInterface):
    def __init__(self) -> None:
        self.methodCalled = False
    
    def doSomething(self) -> None:
        self.methodCalled = True

# the provide it to the injector before executing your tests
mock = MyInterfaceMock()
injector().provide(MyInterface, mock)
## execute test code
injector().get(MyInterface).doSomething()
# then check if the execution happened
assertTrue(mock.methodCalled)
```

#### Providing and retrieving dependencies
**jstreams** implements various ways to provide/declare an injected dependency, such as:
- direct injector provisioning
- component/service declaration
- configuration class dependencies creation

**jstreams** provides a various strategies for retrieving injected dependencies, such as:
- direct injector retrieval
- method/function arguments injection
- dependency classes
- dependency resolving

##### Direct injection/retrieving
```python
from jstreams import injector
from mypackage import MyClass, MyOtherClass

# Providing a single dependency using the Injector object
injector().provide(MyClass, MyClass())

# Providing multiple dependecies
injector().provide_dependencies({
    MyClass: MyClass(),
    MyOtherClass: MyOtherClass(),
})

# Retrieve using get. This method will raise a ValueError if no object was provided for MyClass
myClass = injector().get(MyClass)

# Retrieve using find. This method returns an Optional and does not raise a ValueError. The missing dependency needs to be handled by the caller
myOtherClass = injector().find(MyOtherClass)
```
##### Component/service declaration and module scanning
Dependencies can also be provided by using the `component` decorator:
```python
@component()
class Service:
    def doSomething(self) -> None:
        print("Do something")

injector().get(Service).doSomething() # Will print out "Do something"
```

Components can be defined using two different strategies:
- Lazy
- Eager

A lazy component will only be instatianted when needed:

```python
@component(Strategy.LAZY)
class Service:
    def doSomething(self) -> None:
        print("Do something")

# The dependency is not yet instantiated
injector().get(Service) # Now the dependency is created
```

An eager component will be instantiated once its module or the class itself is imported:
```python
@component(Strategy.EAGER)
class Service:
    def doSomething(self) -> None:
        print("Do something")

# The dependency is already instantiated
injector().get(Service) # Now the dependency can be retrieved
```

You can also use the `component` decorator to specify the class/interface the service needs to substitute
```python
@component(Strategy.LAZY, ServiceInterface)
class Service(ServiceInterface):
    def serviceMethod(self) -> None:
        pass

# Inject the dependency using the interface
injector().get(ServiceInterface)
```

However, if your interface is defined in a different class, then you need to use the module scanning functionality in order to retrieve a decorated component that implements an interface from another module.
This mechanism is necessary since python does not load any classes from non imported modules. By providing the modules to be scanned, **jstreams** will attempt to load the provided modules and automatically provide the decorated classes from those modules during injection.

**interface.py**
```python
class Interface(abc.ABC):
    @abc.abstractmethod
    def doSomething(self) -> None:
        pass
```

**service.py**
```python
@component(class_name=Interface)
class Service(Interface):
    def doSomething(self) -> None:
        print("Something got done")
```

**main.py**
```python
injector().scan_modules(["service"]) # Provide fully qualified name for the module
injector().get(Interface).doSomething() # Wil print out 'Something got done'
```

#### Providing dependencies using configuration classes using @configuration and @provide/@provideVariable
In order to abstract the creation of dependencies from the code that are using those dependencies, you can use configuration classes. In the following example, we will use configuration classes to define two different sets of declared dependencies that will be injected.

**api_config.py**
```python
class APIConfiguration:
    def __init__(self, apiHost: str, apiPort: int) -> None:
        self.apiHost = apiHost
        self.apiPort = apiPort
```

**configuration_dev.py**
```python
# First we define a configuration for a development environment
@configuration(profiles=["dev"])
class DevConfiguration:
    @provide(APIConfiguration)
    def provideDevConfiguration(self) -> APIConfiguration:
        return APIConfiguration("dev.host.api", 8080)
```

**configuration_prod.py**
```python
# Then we define a configuration for a production environment
@configuration(profiles=["prod"])
class ProdConfiguration:
    @provide(APIConfiguration)
    def provideDevConfiguration(self) -> APIConfiguration:
        return APIConfiguration("prod.host.api", 8080)
```

**dev.py**
```python
# This would be the development launcher of your application
injector().scan_modules(["configuration_dev"]) # Inform the container where to load the configuration from
injector().activate_profile("dev")
apiConfiguration = inject(APIConfiguration)
print(apiConfiguration.apiHost) # Will print out 'dev.host.api'
```

**main.py**
```python
# This would be the production launcher of your application
injector().scan_modules(["configuration_prod"]) # Inform the container where to load the configuration from
injector().activate_profile("prod")
apiConfiguration = inject(APIConfiguration)
print(apiConfiguration.apiHost) # Will print out 'prod.host.api'
```

#### Providing and retrieving qualified dependencies
```python
from jstreams import injector
from mypackage import MyClass, MyNotCalledClass

# Providing a single dependency using the Injector object and a qualified name
injector().provide(MyClass, MyClass(), "qualifiedName")

# Retrieve the first object using get by its name. This method will raise a ValueError if no object was provided for MyClass and the given qualifier
myClass = injector().get(MyClass, "qualifiedName")
# Retrieve the second provided object by its qualified name. 
myClassDifferentInstance = injector().get(MyClass, "differentName")

# Retrieve using find. This method returns an Optional and does not raise a ValueError. The missing dependency needs to be handled by the caller
myClass = injector().find(MyClass, "qualifiedName")
# or get the different instance
myClassDifferentInstance = injector().find(MyClass, "differentName")

# Using defaults. This method will try to resolve the object for MyNotCalledClass, and if no object is found, the builder function provider will be called and its return value returned and used by the container for the given class.
myNotCalledObject = injector().find_or(MyNotCalledClass, lambda: MyNotCalledClass())
```

#### Retrieving dependencies using @autowired and @autowired_optional decorators
```python
from jstreams import autowired, autowired_optional, return_autowired, return_autowired_optional

injector().provide(MyClass, MyClass())

@autowired(MyClass)
def getMyClass() -> MyClass:
    # This method does not have to return anything, but for
    # strict typechecking, we need to use this masking method
    return return_autowired(MyClass)

@autowired_optional(MyClass)
def getMyClass() -> Optional[MyClass]:
    # This method does not have to return anything, but for
    # strict typechecking, we need to use this masking method
    return return_autowired_optional(MyClass)

print(getMyClass()) # Will print out the injected class string representation
```

#### Providing and retrieving variables
```python
from jstreams import injector

# Provide a single variable of type string
injector().provide_var(str, "myString", "myStringValue")

# Provide a single variable of type int
injector().provide_var(int, "myInt", 7)

# Provide multiple variables
injector().provide_variables([
    (str, "myString", "myStringValue"),
    (int, "myInt", 7),
])

# Retrieving a variable value using get. This method will raise a ValueError if no object was provided for the variable class and the given name
myString = injector().get_var(str, "myString")
# retrieving another value using find. This method returns an Optional and does not raise a ValueError. The missing value needs to be handled by the caller
myInt = injector().find_var(int, "myInt")
# retrieving a value with a default fallback if the value is not present
myString = injector().find_var_or(str, "myStrint", "defaultValue")
```
Qualified dependencies can also be injected by using the `component` decorator:
You can also use qualifiers with the `component` decorator:
```python
@component(Strategy.LAZY, ServiceInterface, "service")
class Service(ServiceInterface):
    def serviceMethod(self) -> None:
        pass

# Inject the dependency using the interface and a qualifier
injector().get(ServiceInterface, "service")
```

#### Attribute and argument injection
##### Attribute injection
Attributes can be injected by providing the dependency classes or variable definitions.
```python
@resolve_dependencies({
    "myAttribute": AttributeClassName
})
class MyDependentComponent:
    myAttribute: AttributeClassName

# Alternative usage
@resolve_all()
class MyDependentComponent:
    myAttribute: AttributeClassName

# Provide the dependency at some point before actually instantiating a MyDependentComponent object
injector().provide(AttributeClassName, AttributeClassName())

myDepComp = MyDependentComponent() # The dependency gets injected when the constructor is called
myDepComp.myAttribute # Will have the value provided


@resolve_variables({
    "myVariable": StrVariable("myVar"), # Type agnostic syntax: Variable(str, "myVar")
})
class MyVariableNeededComponent:
    myVariable: str

@resolve({
    "myAttribute": AttributeClassName,
    "myVariable": StrVariable("myVar"),
})
class MyComponent:
    myAttribute: AttributeClassName
    myVariable: str

injector().provide_var(str, "myVariable", "myVariableValue")

myVarNeededComp = MyVariableNeededComponent() # Value gets injected when the constructor is called
print(myVarNeededComp.myVariable) # Will print out 'myVariableValue'

myComponent = MyComponent()
# At instantiation, both `myAttribute` and `myVariable` are injected
print(myComponent.myAttribute) # will print out the value provided
print(myComponent.myVariable) # will print out 'myVariableValue'
```

##### Argument injection
Arguments can be injected to functions, methods and class constructors.
```python
# Provide dependencies using argument injection
# 1. To functions

injector().provide(str, "test")
injector().provide(int, 10)

@inject_args({"a": str, "b": int})
def fn(a: str, b: int) -> None:
    print(a + str(b))

fn() # Will print out "test10" as the arguments will be injected

# Arguments can be overriden by the caller by specifying the overriden argument as a kwarg
fn(a="other") # Will print out "other10" as only the argument 'a' is overriden. Argument 'b' will be injected

# 2. To constructors
class TestArgInjection:
    @inject_args({"a": str, "b": int})
    def __init__(self, a: str, b: int) -> None:
        self.a = a
        self.b = b

    def print(self) -> None:
        print(a + str(b))

TestArgInjection().print() # Will print out "test10" as both arguments are injected into the constructor
# IMPORTANT: For constructors, kw arg overriding is not available. When overriding arguments, all arguments must be specified
TestArgInjection("other", 5).print() # Will print out "other5" as all args are overriden 

```
#### Injected dependecies
Injected dependecies can be used when the needed dependencies are not present in the container ahead of time (this is also possible now with *resovle_dependencies* and *resolve_variables*). For example, you can create a class that requires a dependency even if the dependency is not yet present, provide the dependency later on, then use it in the class you've initialized.

Injected dependencies are available through 3 classes:
- InjectedDependency
- OptionalInjectedDependency
- InjectedVariable

```python
injector().provide(str, "Test")
dep = InjectedDependency(str)
# you can either use the get() method, or use the callable functionality of the class
print(dep.get()) # will print out "Test"
# or the equivalent
print(dep()) # will also print out "Test"
```

#### Using profiles
In order to activate only certain services or components, you can use profiles. Once a profile is activated, only components that have been defined without a specific list of profiles, or whose list of profiles contain the selected profiles will be injected. It is recommended that you use lazy initialization for profile specific components, so that the components are not created unless they are needed.
**IMPORTANT** Please note that only one profile can be activated. Once a profile is active, any subsequent calls to the `activateProfile` method will raise an error.
```python
# The component decorator uses LAZY initialization strategy by default, unless the EAGER strategy is specified.
@component(profiles=["profileA", "profileB"])
class Test1:
    pass

@component(profiles=["profileA", "profileC"])
class Test2:
    pass

# Both Test1 and Test2 components will be available when selecting "profileA"
injector().activate_profile("profileA")

# Only Test1 component will be available when selecting "profileB"
injector().activate_profile("profileB")

# Only Test2 component will be available when selecting "profileC"
injector().activate_profile("profileC")

# You can also provide the profiles to the "provide" and "provideDependencies" methods
# this example uses a lambda to provide the component, so that the component is not created
# ahead of time, since it is possible that the component will not be used with the active profile
injector().provide(Test1, lambda: Test1(), profiles=["profileA", "profileB"])
```
Profiles can also be used to provided different implementations of an interface or abstract class depending on the selected profile.
```python
class LoggerInterface(abc.ABC):
    @abc.abstractmethod
    def log(operation: str) -> None:
        pass

@component(class_name=LoggerInterface, profiles=["console"])
class ConsoleLogger(LoggerInterface):
    def log(operation: str) -> None:
        print(operation)

@component(class_name=LoggerInterface, profiles=["file"])
class FileLogger(LoggerInterface):
    fileName = "logfile"
    def log(operation: str) -> None:
        with open(self.fileName, "w+") as file:
            file.write(operation)

# activate console profile
injector().activate_profile("console")
inject(LoggerInterface).log("test") # Will print out to console, as the console profile activation will inject the ConsoleLogger class

# or

# activate file profile
injector().activate_profile("file")
inject(LoggerInterface).log("test") # Will write the content to the "logfile" file, as the file profile activation will inject the FileLogger class

```
### Threads

#### LoopingThread

```python
from jstreams import LoopingThread
from time import sleep

class MyThread(LoopingThread):
    def __init__(self) -> None:
        LoopingThread.__init__(self)
        self.count = 0
    
    def loop(self) -> None:
        # Write here the code that you want executed in a loop
        self.count += 1
        print(f"Executed {self.count} times")
        # This thread calls the loop implementation with no delay. Any sleeps need to be handled in the loop method
        sleep(1)
thread = MyThread()
thread.start()
sleep(5)
# Stop the thread from loopiong
thread.cancel()
```

#### CallbackLoopingThread
This looping thread doesn't require overriding the loop method. Instead, you provide a callback
```python
from jstreams import import CallbackLoopingThread
from time import sleep

def threadCallback() -> None:
    print("Callback executed")
    sleep(1)

thread = CallbackLoopingThread(threadCallback)
# will print "Callback executed" until the thread is cancelled
thread.start()

sleep(5)
# Stops the thread from looping
thread.cancel()
```
#### Timer
The Timer thread will start counting down to the given time period, and execute the provided callback once the time period has ellapsed. The timer can be cancelled before the period expires.
```python
from jstreams import import Timer
from time import sleep

timer = Timer(10, 1, lambda: print("Executed"))
timer.start()
# After 10 seconds "Executed" will be printed
```

```python
from jstreams import import Timer
from time import sleep

# The first parameter is the time period, the second is the cancelPollingInterval.
# The cancel polling interval is used by the timer to check if cancel was called on the timer.
timer = Timer(10, 1, lambda: print("Executed"))
timer.start()
sleep(5)
timer.cancel()
# Nothing will be printed, as this timer has been canceled before the period could ellapse
```

#### Interval
The interval executes a given callback at fixed intervals of time.
```python
from jstreams import Interval
from time import sleep
interval = Interval(2, lambda: print("Interval executed"))
interval.start()
# Will print "Interval executed" every 2 seconds
sleep(10)
# Stops the interval from executing
interval.cancel()
```

#### CountdownTimer
The countdown timer is similar in functionality with the Timer class, with the exception that this timer cannot be canceled. Once started, the callback will always execute after the period has ellapsed.
```python
from jstreams import CountdownTimer

CountdownTimer(5, lambda: print("Countdown executed")).start()
# Will always print "Countdown executed" after 5 seconds
```

#### JS-like usage
jstreams also provides some helper functions to simplify the usage of timers in the style of JavaScript.

```python
from jstreams import setTimer, setInterval, clear

# Starts a timer for 5 seconds
set_timer(5, lambda: print("Timer done"))

# Starts an interval at 5 seconds
set_interval(5, lambda: print("Interval executed"))

# Starts another timer for 10 seconds
timer = setTimer(10, lambda: print("Second timer done"))
# Wait 5 seconds
sleep(5)
# Clear the timer. The timer will not complete, since it was cancelled
clear(timer)

# Starts another interval at 2 seconds
interval = set_interval(2, lambda: print("Second interval executed"))
# Allow the interval to execute for 10 seconds
sleep(10)
# Cancel the interval. This interval will stop executing the callback
clear(interval)
```

### State management API
The State management API aims to provide sharing data between your application's components, in a way with React's state management.
**jstreams** offers two ways to manage states shared within your application:
- synchronous
- asynchronous
```python
# Create a state
STATE_KEY = "myState"

# Simple synchronous usage, provide a state key, and the default value
(getState, setState) = use_state(STATE_KEY, "initial")

print(getState()) # Prints out "initial", as there have been no changes to the state

# we update the state
setState("updated")
print(getState()) # Prints out "updated"

# Asynchronous usage
(getAsyncState, setAsyncState) = use_async_state(STATE_KEY, "initial")
print(getAsyncState()) # Will print out "updated" since that is the state's current value

# You can also provide an onChange callback to the state.
# The difference between use_state and use_async_state is that the onChange callbacks
# will be called in a synchronous manner (in order of subscription) for the use_state
# while the use_async_state provided callbacks will be called from separate threads.
# This behavior aims to avoid waiting to a callback that may do intensive processing
# and unlock the other callbacks as soon as possible
(getAsyncStateCB, setAsyncStateCB) = use_async_state(
    STATE_KEY, 
    "initial", 
    lambda newState, oldState: print("New state is '" + str(newState) + "' old state is '" + str(oldState) + "'")
)

setState("Update no 2")
# At this point, the lambda callback will be called, and the output will read
# "New state is 'Updated no 2' old state is 'updated'"
```

### Scheduler
**schedule.py**
```python
from jstreams import schedule_periodic

global two_seconds_counter
two_seconds_counter = 0

global two_seconds_class_counter
two_seconds_class_counter = 0

# Will be scheduled at 20 seconds interval
@schedule_periodic(20)
def run_at_two_seconds() -> None:
    global two_seconds_counter
    two_seconds_counter += 1


class SchedulerStaticClass:
    # Also scheduled at 20 seconds interval. The decorated scheduled functions
    # need to be static and cannot depend on an instance of a class.
    @staticmethod
    @schedule_periodic(20)
    def run_at_two_seconds() -> None:
        global two_seconds_class_counter
        two_seconds_class_counter += 1
```

**run.py**
```python
import unittest
# Since the module where the scheduled functions is not imported by default,
# the scheduler needs to be informed where the scheduled functions are located,
# so that it can load the scheduled taks from those modules. Fully qualified names
# need to be provided for the modules
scheduler().scan_modules(["schedule"])
# After the scan_modules call, the scheduled jobs are created and the scheduler started
sleep(40)
scheduler().stop()

from schedule import two_seconds_counter, two_seconds_class_counter

tc = unittest.TestCase()
# At this point, we are guaranteed to have at least two runs
tc.assertGreaterEqual(
    two_seconds_counter, 2, "The function should have been called at least 2 times"
)
# Same for the static class
tc.assertGreaterEqual(
    two_seconds_class_counter,
    2,
    "The static function should have been called at least 2 times",
)
```

You can also schedule jobs on demand:
```python
# Will print out "I just ran" every 10 seconds
scheduler().schedule_periodic(lambda: print("I just ran"), 10)
# Will print out "I just ran" once, since the job will have the run once flag set
scheduler().schedule_periodic(lambda: print("I just ran"), 10, True)

```

The difference between the **Interval** class and a periodic scheduled job is that **Interval** is itself a thread and will be a long lived object, while a scheduled job lives in its own thread only when executed. Same for the difference between a run once scheduled job and a **Timer**. Another difference is that both an **Interval** and **Timer** objects can be canceled, while a scheduled job can only be stopped if the scheduler is stopped.
As an example, let's consider we need to call 10 functions at given intervals. When using **Timer** or **Interval** we start 10 threads when we create the jobs, while with the scheduler, we only have a single thread, the scheduler itself, and spawn one thread for each job whenever the job needs to run. Basically, with the scheduler we have a *maximum* of jobs count + 1 (one for the scheduler) threads, while using **Timer** or **Interval** we have a *minimum* number of 10 threads all the time.
It is a matter of application design whether to use threads or the scheduler, but, of course, they can be combined and used as needed.
 
### Eventing
The `eventing` module provides a simple, global event bus built on top of the Rx primitives (`PublishSubject`). It allows different parts of an application to communicate asynchronously without having direct dependencies on each other. Components can publish events, and other components can subscribe to specific event types to react accordingly.

```python
from jstreams import event, events, rx_map, rx_filter, ObservableSubscription
from typing import Any, Optional, Callable
import time

# Define event types (can be any class or built-in type)
class UserLoggedInEvent:
    def __init__(self, username: str):
        self.username = username
    def __repr__(self):
        return f"UserLoggedInEvent(username='{self.username}')"

class SystemMessageEvent:
    def __init__(self, message: str, level: str = "INFO"):
        self.message = message
        self.level = level
    def __repr__(self):
        return f"SystemMessageEvent(message='{self.message}', level='{self.level}')"

# --- Publisher Side ---
def login_user(username: str):
    print(f"\nAttempting login for {username}...")
    # ... perform login logic ...
    print(f"Login successful for {username}")
    # Publish an event using the event type as the identifier
    event(UserLoggedInEvent).publish(UserLoggedInEvent(username))
    event(SystemMessageEvent).publish(SystemMessageEvent(f"User '{username}' logged in."))

# --- Subscriber Side ---

# 1. Simple subscription to an event type
def welcome_user(evt: UserLoggedInEvent):
    print(f"EVENT HANDLER [Welcome]: Welcome, {evt.username}! Sending welcome email...")

# Subscribe the handler to the UserLoggedInEvent type
login_subscription: ObservableSubscription[UserLoggedInEvent] = event(UserLoggedInEvent).subscribe(welcome_user)
print(f"Subscribed 'welcome_user' to {UserLoggedInEvent.__name__}")

# 2. Subscription with filtering and mapping (using pipe)
def log_errors(evt: SystemMessageEvent):
    # This handler only receives ERROR level messages due to the filter below
    print(f"EVENT HANDLER [Error Log]: ERROR DETECTED - {evt.message}")

# Subscribe to SystemMessageEvent, but only process ERROR level messages
error_log_subscription: ObservableSubscription[SystemMessageEvent] = event(SystemMessageEvent).pipe(
    rx_filter(lambda e: e.level == "ERROR")
).subscribe(log_errors)
print(f"Subscribed 'log_errors' to {SystemMessageEvent.__name__} (filtered for level='ERROR')")


# 3. Using a named event channel (for the same event type)
# Useful if you need separate streams for the same data type
status_update_channel = event(str, event_name="status_updates")

def display_status(status: str):
    print(f"EVENT HANDLER [Status Display]: Status Update -> {status}")

status_subscription: ObservableSubscription[str] = status_update_channel.subscribe(display_status)
print(f"Subscribed 'display_status' to event type 'str' with name 'status_updates'")


# --- Triggering Events ---
print("\n--- Triggering Events ---")
login_user("Alice")
# Output should show the "Welcome" handler running

event(SystemMessageEvent).publish(SystemMessageEvent("Disk space low!", level="ERROR"))
# Output should show the "Error Log" handler running

event(SystemMessageEvent).publish(SystemMessageEvent("Service started.", level="INFO"))
# Output should *not* show the "Error Log" handler running (filtered out)

status_update_channel.publish("System Initialized")
# Output should show the "Status Display" handler running

# --- Getting Latest Event ---
# Note: event() uses PublishSubject internally, so new subscribers don't get past events.
# Use .latest() to retrieve the most recently published event on a specific channel, if needed.
latest_status: Optional[str] = event(str, event_name="status_updates").latest()
print(f"\nLatest status retrieved via .latest(): {latest_status}") # Output: System Initialized

latest_login: Optional[UserLoggedInEvent] = event(UserLoggedInEvent).latest()
print(f"Latest login event retrieved via .latest(): {latest_login}") # Output: UserLoggedInEvent(username='Alice')

# --- Cleanup ---
print("\n--- Cleaning Up Subscriptions ---")

# Cancel individual subscriptions when no longer needed
print("Cancelling 'login_subscription'...")
login_subscription.cancel()
login_user("Bob") # The "Welcome" handler should NOT run now

# Or clear all subscriptions and history for a specific event type (across all its names)
print(f"\nClearing all subscriptions for {SystemMessageEvent.__name__}...")
events().clear_event(SystemMessageEvent)
event(SystemMessageEvent).publish(SystemMessageEvent("Another critical error!", level="ERROR")) # "Error Log" handler should NOT run

# Or clear all event channels and subscriptions entirely
print("\nClearing ALL events...")
events().clear()
status_update_channel.publish("System Shutdown") # "Status Display" handler should NOT run
print("Eventing system cleared.")
```

### Annotations 
`@builder`, `@getter`, `@setter`, `@locked`, `@synchronized`, `@synchronized_static`, `@required_args`, `@all_args`, `@validate_args`, `@default_on_error`

The `jstreams.annotations` module provides several class and method decorators to reduce boilerplate code and implement common patterns like the builder pattern, object factories or thread synchronization.
#### Builder, getter and setter patterns
```python
from jstreams import builder, getter, setter, locked, synchronized, synchronized_static
from typing import Optional
import threading
import time
import abc 
# For the example

# --- @builder, @getter, @setter ---
# These decorators work together to simplify class creation and access.

@builder() # Adds a static Config.builder() method
@getter()  # Adds get_host(), get_port() methods
@setter()  # Adds set_host(v), set_port(v) methods
class Config:
    # Public attributes are targeted by the decorators
    host: str
    port: int
    timeout: Optional[int] = None # Optional attributes work too

    # Private attributes (starting with _) are ignored
    _api_key: str = "default_key"

    def __repr__(self):
        return f"Config(host='{self.host}', port={self.port}, timeout={self.timeout})"

# Use the builder pattern provided by @builder
config_instance = Config.builder() \
    .with_host("localhost") \
    .with_port(8080) \
    .with_timeout(5000) \
    .build() # Creates the Config instance

print(f"Config built: {config_instance}")

# Use methods generated by @getter
print(f"Host from getter: {config_instance.get_host()}") # Output: localhost

# Use methods generated by @setter
config_instance.set_port(9090)
print(f"Port after setter: {config_instance.get_port()}") # Output: 9090

# Attempting to access builder/getter/setter for private attributes fails
# config_instance.get__api_key() -> AttributeError
# Config.builder().with__api_key("...") -> AttributeError
```

**Why should you use these annotations?** Well, typically, if you want to implement a class with the builder patter for fluent programming, you would have to do something like this:
```python
class Person:
    name: str
    age: int
    address: str

    def with_name(self, name: str) -> 'Person':
        self.name = name
        return self

    def with_age(self, age: int) -> 'Person':
        self.age = age
        return self

    def with_address(self, address: str) -> 'Person':
        self.address = address
        return self

# Then call it like this:
person = Person().with_name("John Doe").with_age(30).with_address("123 Main St")
```

What the `@builder` annotation allows you to do is simply define your class and let the annotation handle the boilerplate code for you.

```python
@builder()
class Person:
    name: str
    age: int
    address: str

# Then call it like this:
person = Person.builder().with_name("John Doe").with_age(30).with_address("123 Main St").build()
```
The same goes for the `@setter` and `@getter` decorators.

```python
@builder()
@setter()
@getter()
class Person:
    name: str
    age: int
    address: str

# First we create the object
person = Person.builder().with_name("John Doe").with_age(30).with_address("123 Main St").build()
# This is the @getter generated method
print(person.get_name()) # Will print out 'John Doe`
# This is the @setter generated method
person.set_name("Jane Doe")
print(person.get_name()) # Will print out 'Jane Doe'
```
#### Thread syncronization using `@locked`, `@synchronized` and `@synchronized_static`
```python
# --- @locked ---
# Makes instances of the decorated class thread-safe by wrapping attribute
# access (get/set/del) and method calls with an instance-specific RLock.

@locked()
class ThreadSafeCounter:
    def __init__(self):
        self.count = 0

    def increment(self):
        # This operation is now atomic per instance due to @locked
        current_count = self.count
        time.sleep(0.01) # Simulate work / potential race condition point
        self.count = current_count + 1

    def get_count(self):
        # Attribute access is also locked
        return self.count

safe_counter = ThreadSafeCounter()
threads = []
for _ in range(10):
    t = threading.Thread(target=safe_counter.increment)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print(f"\nLocked Counter final value: {safe_counter.get_count()}") # Should reliably be 10

# --- @synchronized (Instance Lock) ---
# Decorator for *instance methods*. Ensures only one thread can execute
# the decorated method *on the same instance* at a time. Uses an
# instance-specific RLock.

class Worker:
    def __init__(self, id_num: int):
        self.id = id_num
        # @synchronized will create a lock attribute if needed,
        # or you can specify one: @synchronized(lock_attribute_name='_my_lock')

    @synchronized()
    def do_work(self, duration: float):
        print(f"Worker {self.id} starting work (Thread: {threading.current_thread().name})")
        time.sleep(duration)
        print(f"Worker {self.id} finished work (Thread: {threading.current_thread().name})")

worker1 = Worker(1)
worker2 = Worker(2)

# Threads targeting the *same* instance (worker1) will be serialized by @synchronized
t1 = threading.Thread(target=worker1.do_work, args=(0.2,))
t2 = threading.Thread(target=worker1.do_work, args=(0.2,))

# Thread targeting a *different* instance (worker2) can run concurrently
t3 = threading.Thread(target=worker2.do_work, args=(0.2,))

print("\nStarting @synchronized demo:")
t1.start(); t2.start(); t3.start()
t1.join(); t2.join(); t3.join()
print("@synchronized demo finished.")
# Observe that worker1's "starting" and "finished" messages appear sequentially,
# while worker2 might interleave with worker1.


# --- @synchronized_static (Static/Global Lock) ---
# Decorator for *functions or methods*. Ensures only one thread can execute
# *any* function/method decorated with this decorator (or sharing the same
# `lock_name`) *globally* at a time. Uses a static RLock.

shared_resource = []
log_lock = threading.Lock() # For printing cleanly in demo

@synchronized_static("resource_access_lock") # Shared lock name
def add_to_resource(item):
     with log_lock: print(f"Acquired lock to ADD {item} (Thread: {threading.current_thread().name})")
     time.sleep(0.1)
     shared_resource.append(item)
     with log_lock: print(f"Released lock after ADDING {item}")

@synchronized_static("resource_access_lock") # Same shared lock name
def check_resource_status():
     with log_lock: print(f"Acquired lock to CHECK status (Thread: {threading.current_thread().name})")
     time.sleep(0.1)
     status = len(shared_resource) > 0
     with log_lock: print(f"Released lock after CHECKING status (Result: {status})")
     return status

threads_static = []
for i in range(3):
    threads_static.append(threading.Thread(target=add_to_resource, args=(i,)))
threads_static.append(threading.Thread(target=check_resource_status))

print("\nStarting @synchronized_static demo:")
for t in threads_static: t.start()
for t in threads_static: t.join()
print("@synchronized_static demo finished.")
print(f"Final shared resource: {shared_resource}")
# Observe that all "Acquired lock..." / "Released lock..." messages appear
# sequentially, regardless of which function was called, due to the shared static lock.
```

#### Factory methods using `@required_args` and `@all_args`

These decorators provide alternative static constructors for your classes based on their declared public members, bypassing the standard `__init__` method. This is useful for creating instances when you want to directly populate fields without necessarily calling the initialization logic, or when you want constructors that strictly enforce required fields or allow setting all fields directly.

**`@required_args`**

This decorator adds a static method named `required` to the decorated class. This method accepts arguments corresponding *only* to the public members of the class that are **not** declared as `Optional`.

```python
from jstreams import required_args
from typing import Optional

@required_args()
class Product:
    product_id: int       # Required
    name: str             # Required
    description: Optional[str] = None # Optional
    _internal_code: str = "XYZ"      # Private, ignored

# Use the generated 'required' static method
# It only expects 'product_id' and 'name'
product1 = Product.required(101, "Gadget")
print(f"Product 1: id={product1.product_id}, name='{product1.name}', desc={product1.description}")
# Output: Product 1: id=101, name='Gadget', desc=None

product2 = Product.required(name="Widget", product_id=102) # Keyword args work too
print(f"Product 2: id={product2.product_id}, name='{product2.name}', desc={product2.description}")
# Output: Product 2: id=102, name='Widget', desc=None

# Trying to provide the optional 'description' will fail:
# Product.required(103, "Gizmo", "A cool gizmo") -> TypeError: too many arguments
```

**`@all_args`**
This decorator adds a static method named `all` to the decorated class. This method accepts arguments corresponding to all public members of the class, including `Optional` ones.
```python
from jstreams import all_args
from typing import Optional

@all_args()
class Product:
    product_id: int       # Required
    name: str             # Required
    description: Optional[str] = None # Optional
    _internal_code: str = "XYZ"      # Private, ignored

# Use the generated 'all' static method

# Provide all arguments
product1 = Product.all(201, "Thingamajig", "Does amazing things")
print(f"Product 1: id={product1.product_id}, name='{product1.name}', desc='{product1.description}'")
# Output: Product 1: id=201, name='Thingamajig', desc='Does amazing things'

# Provide arguments using keywords
product3 = Product.all(name="Contraption", product_id=203, description="Very complex")
print(f"Product 3: id={product3.product_id}, name='{product3.name}', desc='{product3.description}'")
# Output: Product 3: id=203, name='Contraption', desc='Very complex'

```

#### Argument validation using `@validate_args`

**`@validate_args`**

This decorator performs runtime validation of function arguments against their type hints *before* the function body is executed. If an argument's type doesn't match its hint, it raises a `TypeError`. This helps catch type errors early, especially when dealing with external data or complex function signatures.

It currently supports basic types (`int`, `str`, etc.), `typing.Optional`, `typing.Union`, and `typing.Any`. For generic collections like `list` or `dict`, it validates the container type itself (e.g., checks if the argument is a `list`) but does not perform deep validation of the contents (e.g., it won't check if every item in a `list[int]` is actually an `int`). Arguments without type hints or hinted with `Any` are skipped.

```python
from jstreams import validate_args
from typing import Optional

@validate_args()
def process_user(user_id: int, name: str, email: Optional[str] = None):
    print(f"Processing User ID: {user_id}, Name: {name}, Email: {email or 'N/A'}")

# Valid calls
process_user(123, "Alice")
process_user(user_id=456, name="Bob", email="bob@example.com")
process_user(789, "Charlie", None) # Optional allows None

# Invalid calls (will raise TypeError)
try:
    process_user("123", "Alice") # user_id should be int
except TypeError as e:
    print(f"\nCaught Error: {e}")

try:
    process_user(456, "Bob", 12345) # email should be str or None
except TypeError as e:
    print(f"Caught Error: {e}")
```

#### Error handling using `@default_on_error`

Sometimes, you want a function to return a default value if it encounters an error, rather than letting the exception propagate. The `@default_on_error` decorator provides a clean way to achieve this.

It wraps your function and catches specified exceptions (or any `BaseException` by default). If a caught exception occurs during the function's execution, the decorator returns a predefined default value instead. You can also optionally provide a logger to record the error.

**Arguments:**

*   `default_value` (Required): The value to return if a specified exception is caught. The type should match the expected return type of the function or be compatible.
*   `catch_exceptions` (Optional\[list\[type]]): A list of specific exception types to catch. If `None` or empty, it defaults to catching all `BaseException` subclasses.
*   `logger` (Optional\[Any]): A logger object (like one from Python's `logging` module) with a `.warning()` method. If provided, the caught exception will be logged using this logger. Defaults to `None` (no logging).
*   `log_message` (str): A format string for the log message if a `logger` is provided. Available placeholders are `{func_name}`, `{exception}`, `{args}`, and `{kwargs}`. Defaults to `"Caught exception in {func_name} ({exception}), returning default value."`.

**Example Usage:**

```python
from jstreams import default_on_error
import logging

# Configure a simple logger (optional)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

@default_on_error(default_value=-1, catch_exceptions=[ValueError, TypeError], logger=logger)
def parse_int_safely(value: str) -> int:
    """Attempts to parse a string to an int, returns -1 on failure."""
    return int(value)

@default_on_error(default_value=0.0) # Catches any BaseException by default
def safe_divide(a: float, b: float) -> float:
    """Divides a by b, returns 0.0 if any error occurs (like division by zero)."""
    return a / b

# --- Function Calls ---

result1 = parse_int_safely("123")
print(f"Parsing '123': {result1}") # Output: Parsing '123': 123

result2 = parse_int_safely("abc")
print(f"Parsing 'abc': {result2}") # Output: Parsing 'abc': -1
# WARNING:__main__:Caught exception in parse_int_safely (invalid literal for int() with base 10: 'abc'), returning default value. (Logged if logger provided)

result3 = parse_int_safely(None) # type: ignore
print(f"Parsing None: {result3}") # Output: Parsing None: -1
# WARNING:__main__:Caught exception in parse_int_safely (int() argument must be a string, a bytes-like object or a real number, not 'NoneType'), returning default value. (Logged if logger provided)

result4 = safe_divide(10.0, 2.0)
print(f"Dividing 10.0 by 2.0: {result4}") # Output: Dividing 10.0 by 2.0: 5.0

result5 = safe_divide(10.0, 0.0)
print(f"Dividing 10.0 by 0.0: {result5}") # Output: Dividing 10.0 by 0.0: 0.0
# (ZeroDivisionError is caught because we didn't specify catch_exceptions)
```

## License

[MIT](https://choosealicense.com/licenses/mit/)