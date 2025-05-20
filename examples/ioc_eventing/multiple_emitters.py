from threading import Thread
from time import sleep
import sys

sys.path.append(".")

from jstreams import is_higher_than, validate_args, event, RX

# This example aims to expose how an event can be emitted and used by multiple threads in the application.
# The idea is to have multiple event emitters/publishers and multiple consumers/subscribers.

# We create a class of threads that will emit values


class EventEmitter(Thread):
    @validate_args({"sleep_for": is_higher_than(0)})
    def __init__(self, start_from: int, end_at: int, sleep_for: float) -> None:
        super().__init__()
        self.start_from = start_from
        self.end_at = end_at
        self.sleep_for = sleep_for
        self.event = event(int)

    def send_event(self, value: int) -> None:
        self.event.publish(value)

    def run(self) -> None:
        for i in range(self.start_from, self.end_at + 1):
            self.send_event(i)
            sleep(1)


value_set: set[int] = set()
higher_than_10: set[int] = set()

# We then subscribe to this event for all values
event(int).subscribe(value_set.add)
# Then we subscribe to a pipe that only takes values higher than 10
event(int).pipe(RX.filter(is_higher_than(10))).subscribe(higher_than_10.add)

# Then start the emitters
emitter1 = EventEmitter(1, 10, 0.5)
emitter1.start()

emitter2 = EventEmitter(11, 20, 0.7)
emitter2.start()

emitter3 = EventEmitter(21, 30, 0.3)
emitter3.start()

# Then we wait for them to complete
emitter1.join()
emitter2.join()
emitter3.join()

print("All events received", value_set)

# Now, we expect to have received all the events emitted from all the threads.
expected_set = {i for i in range(1, 31)}
assert value_set == expected_set

print("Higher than 10 events received", higher_than_10)

expected_ht_10 = {i for i in range(11, 31)}
assert higher_than_10 == expected_ht_10
