from threading import Thread
from time import sleep
from typing import Any

from jstreams.eventing import managed_events, on_event, event


class IntEvent:
    def __init__(self, value: int) -> None:
        self.value = value


class StrEvent:
    def __init__(self, value: str) -> None:
        self.value = value


# We create a subscriber class that will subscribe to events of a specific type
# and store the values in a set. This is a simple example of how to use the
# eventing system in jstreams.
# This class is not managed by the eventing system, so we need to manually
# subscribe to the events. We do this by calling the event function with the
# event type and then calling the subscribe method with the add method of
# the set we want to store the values in.
class Subscriber:
    def __init__(self, event_type: type) -> None:
        self.event_type = event_type
        self.values: set[Any] = set()
        event(self.event_type).subscribe(lambda event: self.values.add(event.value))


# We create a managed subscriber class that will subscribe to events of a
# specific type and store the values in a list. This is a simple example of
# how to use the eventing system in jstreams. This class is managed by the
# eventing system, so we don't need to manually subscribe to the events.
@managed_events()
class ManagedSubscriber:
    def __init__(self) -> None:
        self.int_values: set[int] = set()
        self.str_values: set[str] = set()

    @on_event(IntEvent)
    def int_sub(self, event: IntEvent) -> None:
        self.int_values.add(event.value)

    @on_event(StrEvent)
    def str_sub(self, event: StrEvent) -> None:
        self.str_values.add(event.value)


# We create two subscriber objects that will subscribe to events of different
# types. The first subscriber will subscribe to int events and the second
# subscriber will subscribe to str events.
int_subscriber = Subscriber(IntEvent)
str_subscriber = Subscriber(StrEvent)

# We create a managed subscriber object that will subscribe to events of
# both event types.
managed_subscriber = ManagedSubscriber()

# Now, we start emitting events of different types. We emit an int event and a str
# event. The int event will be handled by the int_sub method of the
# ManagedSubscriber class and the str event will be handled by the str_sub method
# of the ManagedSubscriber class. The int event will also be handled by the int_subscriber
# Subscriber object and the str event will also be handled by the str_subscriber Subscriber object.


def publish_events(events: list[Any], event_type: type) -> None:
    for ev in events:
        event(event_type).publish(event_type(ev))


# We create two threads that will publish events of different types. The first thread
# will publish int events and the second thread will publish str events. We use
# the Thread class from the threading module to create the threads. We use the
# lambda function to pass the events to the publish_events function. This is a simple
# example of how to use the threading module to create threads that will publish
# events of different types. We use the sleep function to wait for the events to be
# processed.
Thread(target=lambda: publish_events([1, 2, 3], IntEvent)).start()
Thread(target=lambda: publish_events(["a", "b", "c"], StrEvent)).start()
# Wait for the events to be processed
sleep(5)

print(managed_subscriber.int_values)
print(managed_subscriber.str_values)
print(int_subscriber.values)
print(str_subscriber.values)

# The output should be:
# {1, 2, 3}
# {'a', 'b', 'c'}
# {1, 2, 3}
# {'a', 'b', 'c']}


# We can now verify that the events were processed correctly.
assert managed_subscriber.int_values == {1, 2, 3}
assert managed_subscriber.str_values == {"a", "b", "c"}
assert int_subscriber.values == {1, 2, 3}
assert str_subscriber.values == {"a", "b", "c"}
