# jstreams

jstreams is a Python library aiming to replicate the Java Streams and Optional functionality, as well as a basic ReactiveX implementation. The library is implemented with type safety in mind.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install jstreams.

```bash
pip install jstreams
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
            .isNotEmpty())
# Will output True

# Checks if all elements match a given condition
print(Stream(["Test", "Best", "Lest"]).allMatch(lambda s: s.endswith("est")))
# Will output True

print(Stream(["Test", "Best", "Lest"]).allMatch(lambda s: s.startswith("T")))
# Will output False

# Checks if any element matches a given condition
print(Stream(["Test", "Best", "Lest"]).anyMatch(lambda s: s.startswith("T")))
# Will output True

# Checks if no elements match the given condition
print(Stream(["Test", "Best", "Lest"]).noneMatch(lambda s: s.startswith("T")))
# Will output False

# Gets the first value of the stream as an Opt (optional object)
print(Stream(["Test", "Best", "Lest"])
            .findFirst(lambda s: s.startswith("L"))
            .getActual())
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

# If the stream elements are Iterables, flatMap will produce a list of all contained items
print(Stream([["a", "b"], ["c", "d"]]).flatMap(list).toList())
# Will output ["a", "b", "c", "d"]

# reduce will produce a single value, my applying the comparator function given as parameter
# in order to decide which value is higher. The comparator function is applied on subsequent elements
# and only the 'highest' one will be kept
print(Stream([1, 2, 3, 4, 20, 5, 6]).reduce(max).getActual())
# Will output 20

# notNull returns a new stream containing only non null elements
print(Stream(["A", None, "B", None, None, "C", None, None]).nonNull().toList())
# Will output ["A", "B", "C"]

```

### Opt
```python
from jstreams import Opt

# Checks if the value given is present
Opt(None).isPresent() # Will return False
Opt("test").isPresent() # Will return True


# There are two ways of getting the value from the Opt object. The get returns a non optional
# value and  will raise a value error if the object is None. On the other hand, getActual returns
# an optional object and does not raise a value error
Opt("test").get() # Does not fail, and returns the string "test"
Opt(None).get() # Raises ValueError since None cannot be casted to any type
Opt(None).getActual() # Returns None, does not raise value error

# The ifPresent method will execute a lambda function if the object is present
Opt("test").ifPresent(lambda s: print(s)) # Will print "test"
Opt(None).ifPresent(lambda s: print(s)) # Does nothing, since the object is None

# The getOrElse method will return the value of the Opt if not None, otherwise the given parameter
Opt("test").getOrElse("test1") # Will return "test", since the value is not None
Opt(None).getOrElse("test1") # Will return "test1", since the value is  None

# The getOrElseGet method will return the value of the Opt if not None, otherwise it will execute 
# the given function and return its value
Opt("test").getOrElseGet(lambda: "test1") # Will return "test", since the value is not None
Opt(None).getOrElseGet(lambda: "test1") # Will return "test1", since the value is  None

# stream will convert the object into a stream.
Opt("test").stream() # Is equivalent with Stream(["test"])
Opt(["test"]).stream() # Is equivalent with Stream([["test"]]). Notice the list stacking

# flatStream will convert the object into a stream, with the advantage that it can
# detect whether the object is a list and avoids stacking lists of lists.
Opt("test").flatStream() # Is equivalent with Stream(["test"])
Opt(["test", "test1", "test2"]).flatStream() # Is equivalent with Stream(["test", "test1", "test2"])

```

### Try
```python
# The Try class handles a chain of function calls with error handling

def throwErr() -> None:
    raise ValueError("Test")

def returnStr() -> str:
    return "test"

# It is important to call the get method, as this method actually triggers the entire chain
Try(throwErr).onFailure(lambda e: print(e)).get() # The onFailure is called

Try(returnStr).andThen(lambda s: print(s)).get() # Will print out "test"

# The of method can actually be used as a method to inject a value into a Try without
# actually calling a method or lambda
Try.of("test").andThen(lambda s: print(s)).get() # Will print out "test"
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
subject.onNext("B")

# Will print out "B" as this is the current value stored in the Subject
subject.subscribe(
    lambda s: print(s)
)

# Will print out "C" as this is the next value stored in the Subject,
# any new subscription at this point will receive "C"
subject.onNext("C")

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
subject.onNext("C")

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

# Will print out "C" as this is the next value added in the Subject,
# any new subscription at this point will receive "A", then "B", then "C"
subject.onNext("C")

# For long lived subjects and observables, it is wise to call the
# dispose method so that all subscriptions can be cleared and no
# references are kept. The subject can be reused, but all 
# subscriptions will need to be re-registered
subject.dispose()
```

#### Operators
**jstreams** provides a couple of operators, with more operators in the works.
The current operators are:
- *map* - converts a value to a different form or type
- *filter* - blocks or allows a value to be passed to the subscribers
- *reduce* - causes the observable to emit a single value produced by the reducer function.
- *take* - takes a number of values and ignores the rest
- *takeWhile* - takes values as long as they match the given predicate. Once a value is detected that does not match, no more values will be passing through
- *takeUntil* - takes values until the first value is found matching the given predicate. Once a value is detected that does not match, no more values will be passing through
- *drop* - blocks a number of values and allows the rest to pass through
- *dropWhile* - blocks values that match a given predicate. Once the first value is found not matching, all remaining values are allowed through
- *dropUntil* - blocks values until the first value that matches a given predicate. Once the first value is found matching, all remaining values are allowed through

##### Map - rxMap
```python
from jstreams import ReplaySubject, rxMap

# Initialize the subject with a default value
subject = ReplaySubject(["A", "BB", "CCC"])
# Create an operators pipe
pipe = subject.pipe(
    # Map the strings to their length
    rxMap(lambda s: len(s))
)
# Will print out 1, 2, 3, the lengths of the replay values
pipe.subscribe(
    lambda v: print(v)
)
```

##### Filter - rxFilter
```python
from jstreams import ReplaySubject, rxFilter

# Initialize the subject with a default value
subject = ReplaySubject(["A", "BB", "CCC"])
# Create an operators pipe
pipe = subject.pipe(
    # Filters the values for length higher than 2
    rxFilter(lambda s: len(s) > 2)
)
# Will print out "CCC", as this is the only string with a length higher than 2
pipe.subscribe(
    lambda v: print(v)
)
```

##### Reduce - rxReduce
```python
from jstreams import ReplaySubject, rxReduce

# Initialize the subject with a default value
subject = ReplaySubject([1, 20, 3, 12])
# Create an operators pipe
pipe = subject.pipe(
    # Reduce the value to max
    rxReduce(max)
)
# Will print out 1, then 20 since 1 is the first value, then 20, as the maximum between 
# the previous max (1) and the next value (20)
pipe.subscribe(
    lambda v: print(v)
)
```
##### Take - rxTake
```python
from jstreams import ReplaySubject, rxTake

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rxTake(int, 3)
)
# Will print out the first 3 elements, 1, 7 and 20
pipe1.subscribe(
    lambda v: print(v)
)
# Won't print anything anymore since the first 3 elements were already taken
subject.onNext(9)
```

##### TakeWhile - rxTakeWhile
```python
from jstreams import ReplaySubject, rxTakeWhile

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rxTakeWhile(lambda v: v < 10)
)
# Will print out 1, 7, since 20 is higher than 10
pipe1.subscribe(
    lambda v: print(v)
)
# Won't print anything since the while condition has already been reached
subject.onNext(9)
```

##### TakeUntil - rxTakeUntil
```python
from jstreams import ReplaySubject, rxTakeUntil

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
pipe1 = subject.pipe(
    rxTakeUntil(lambda v: v > 10)
)
# Will print out 1, 7, since 20 is higher than 10, which is our until condition
pipe1.subscribe(
    lambda v: print(v)
)
# Won't print anything since the until condition has already been reached
subject.onNext(9)
```

##### Drop - rxDrop
```python
from jstreams import ReplaySubject, rxDrop

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
self.val = []
pipe1 = subject.pipe(
    rxDrop(int, 3)
)
# Will print out 5, 100, 50, skipping the first 3 values
pipe1.subscribe(
    lambda v: print(v)
)
# Will print out 9, since it already skipped the first 3 values
subject.onNext(9)
```

##### DropWhile - rxDropWhile
```python
from jstreams import ReplaySubject, rxDropWhile

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
self.val = []
pipe1 = subject.pipe(
    rxDropWhile(lambda v: v < 100)
)
# Will print 100, 40, since the first items that are less than 100 are dropped
pipe1.subscribe(lambda v: print(v))
# Will 9, since the first items that are less than 100 are dropped, and 9 appears after the drop while condition is fulfilled
subject.onNext(9)
```

##### DropUntil - rxDropUntil
```python
from jstreams import ReplaySubject, rxDropWhile

subject = ReplaySubject([1, 7, 20, 5, 100, 40])
self.val = []
pipe1 = subject.pipe(
    rxDropUntil(lambda v: v > 20)
)
# Will print out 100, 40, skipping the rest of the values until the first one 
# that fulfills the condition appears
pipe1.subscribe(self.addVal)
# Will print out 9, since the condition is already fulfilled and all remaining values will
# flow through
subject.onNext(9)
```

##### Combining operators
```python
from jstreams import ReplaySubject, rxReduce, rxFilter

# Initialize the subject with a default value
subject = ReplaySubject([1, 7, 11, 20, 3, 12])
# Create an operators pipe
pipe = subject.pipe(
    # Filters only the values higher than 10
    rxFilter(lambda v: v > 10)
    # Reduce the value to max
    rxReduce(max)
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
                rxTakeUntil(lambda e: e > 20)
            )
            .pipe(
                rxFilter(lambda e: e < 10)
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
## License

[MIT](https://choosealicense.com/licenses/mit/)