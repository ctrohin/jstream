import sys

sys.path.append(".")

from jstreams.predicate import is_higher_than
from jstreams.rx import RX, SingleValueSubject

# First we create a subject
subject = SingleValueSubject(1)

# The pipe is the classic way to chain RX operations. For fluent API version of the same example, see 'chain_builder.py'

# We want to store the emitted piped values in two different lists in order
# to illustrate the two ways the filtered values can be used
# First list is for the subscription
values = []

# Second list is used with the tap operator
tap_values = []
subject.pipe(
    # We filter for distinct consecutive values
    RX.distinct_until_changed(int),
    # We drop the first 2 values
    RX.drop(int, 2),
    # We want only values higher than 10
    RX.filter(is_higher_than(10)),
    # We group the values in lists of 5
    RX.buffer_count(int, 5),
    # Then we use tap in order to intercept the values
    # Tap can also be used anywhere in the chain in order to intercept
    # any intermediate values
    RX.tap(tap_values.append),
).subscribe(values.append)

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
assert values == tap_values
