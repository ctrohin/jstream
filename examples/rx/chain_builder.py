import sys

sys.path.append(".")

from jstreams.predicate import is_higher_than
from jstreams.rx import BackpressureStrategy, SingleValueSubject

# First we create a subject
subject = SingleValueSubject(1)

# The chain builder is a fluent API for RX operations. For a classical 'pipe' example, see pipe.py

# We want to store the emitted piped values in two different lists in order
# to illustrate the two ways the filtered values can be used
# First list is for the subscription
values = []

# Second list is used with the tap operator
tap_values = []
(
    subject.chain()
    # We filter for distinct consecutive values
    .distinct_until_changed()
    # We drop the first 2 values
    .drop(2)
    # We want only values higher than 10
    .filter(is_higher_than(10))
    # We group the values in lists of 5
    .buffer_count(5)
    # Then we use tap in order to intercept the values
    # Tap can also be used anywhere in the chain in order to intercept
    # any intermediate values
    .tap(tap_values.append)
    # The build method needs to be called at the end of the rx operation
    # chain in order to build the desired subscribable.
    .build()
).subscribe(values.append)

second_sub_values = []

# We can also use subscribe directly, while providing the subscription elements in the builder
(
    subject.chain()
    .distinct_until_changed()
    .drop(2)
    .filter(is_higher_than(10))
    .buffer_count(5)
    # We can also add error handling
    .catch(lambda e: print(e))
    # completion handler
    .completed(lambda v: print(v))
    # disposed handler
    .disposed(lambda: print("Disposed"))
    # as well as asynchronous and backpressure
    # .asynchronous(True)
    # .backpressure(BackpressureStrategy.DROP)
    .next(second_sub_values.append)
    .subscribe()
)

# Then we emmit the values
subject.on_next(1)
subject.on_next(1)
subject.on_next(2)
subject.on_next(3)
subject.on_next(10)
subject.on_next(10)
subject.on_next(11)
subject.on_next(11)
subject.on_next(12)
subject.on_next(13)
subject.on_next(14)
subject.on_next(14)
subject.on_next(15)
subject.on_next(16)

print(tap_values)
print(values)

assert values == [[11, 12, 13, 14, 15]]
assert second_sub_values == [[11, 12, 13, 14, 15]]
assert values == tap_values
assert values == second_sub_values
