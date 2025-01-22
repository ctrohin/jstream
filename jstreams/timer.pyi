from jstreams.thread import Cancellable as Cancellable, LoopingThread as LoopingThread
from threading import Thread
from typing import Any, Callable

class Timer(Thread, Cancellable):
    def __init__(self, time: float, cancelPollingTime: float, callback: Callable[[], Any]) -> None: ...
    def cancel(self) -> None: ...
    def run(self) -> None: ...

class Interval(LoopingThread):
    def __init__(self, interval: float, callback: Callable[[], Any]) -> None: ...
    def loop(self) -> None: ...

class CountdownTimer(Thread):
    def __init__(self, timeout: float, callback: Callable[[], Any]) -> None: ...
    def run(self) -> None: ...

def setTimer(timeout: float, callback: Callable[[], Any]) -> Cancellable: ...
def setInterval(interval: float, callback: Callable[[], Any]) -> Cancellable: ...
def clear(cancellable: Cancellable) -> None: ...
