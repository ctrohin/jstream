from threading import Lock
from typing import Any, Callable, Optional


class _EventBroadcaster:
    _instance: Optional["_EventBroadcaster"] = None
    _instance_lock = Lock()

    def __init__(self):
        self._listeners: dict[str, list[Callable[[Any], Any]]] = {}

    def subscribe(
        self,
        event_name: str,
        listener: Callable[[Any], Any],
    ) -> "_EventBroadcaster":
        """
        Subscribe to an event.

        Args:
            event_name (str): The event name
            listener (Callable[[Any], Any]): The callback function to be called when the event is published
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)
        return self

    def unsubscribe(
        self,
        event_name: str,
        listener: Callable[[Any], Any],
    ) -> "_EventBroadcaster":
        """
        Unsubscribe from an event.

        Args:
            event_name (str): The event name
            listener (Callable[[Any], Any]): The callback function to be removed
        """
        if event_name in self._listeners:
            self._listeners[event_name].remove(listener)
        return self

    def publish(self, event_name: str, payload: Any) -> "_EventBroadcaster":
        """
        Publish an event.

        Args:
            event_name (str): The event name
            payload (Any): The payload to be sent with the event
        """
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                listener(payload)
        return self

    def clear(self) -> "_EventBroadcaster":
        """
        Clear all events.
        """
        self._listeners = {}
        return self

    def clear_event(self, event_name: str) -> "_EventBroadcaster":
        """
        Clear a specific event.

        Args:
            event_name (str): The event name
        """
        if event_name in self._listeners:
            self._listeners.pop(event_name)
        return self

    @staticmethod
    def get_instance() -> "_EventBroadcaster":
        if _EventBroadcaster._instance is None:
            with _EventBroadcaster._instance_lock:
                if _EventBroadcaster._instance is None:
                    _EventBroadcaster._instance = _EventBroadcaster()
        return _EventBroadcaster._instance


def events() -> _EventBroadcaster:
    """
    Get the event broadcaster instance.
    """
    return _EventBroadcaster.get_instance()
