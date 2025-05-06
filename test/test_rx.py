from baseTest import BaseTestCase
from jstreams import (
    BehaviorSubject,
    Flowable,
    PublishSubject,
    ReplaySubject,
    Single,
    RX,
)
from jstreams.eventing import event, events
from jstreams.utils import Value


class TestRx(BaseTestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)

    def test_single(self) -> None:
        val = Value(None)
        Single("test").subscribe(val.set)
        self.assertEqual(val.get(), "test")

    def test_flowable(self) -> None:
        val = []
        init = ["test1", "test2"]
        Flowable(init).subscribe(val.append)
        self.assertListEqual(init, val)

    def test_behavior_subject(self) -> None:
        subject = BehaviorSubject("1")
        val = []
        sub = subject.subscribe(val.append)
        self.assertListEqual(
            val,
            ["1"],
            "BehaviorSubject should push the latest value on subscription",
        )
        subject.on_next("2")
        self.assertListEqual(
            val,
            ["1", "2"],
            "BehaviorSubject should push the latest value after subscription",
        )
        subject.on_next("3")
        self.assertListEqual(
            val,
            ["1", "2", "3"],
            "BehaviorSubject should push the latest value after subscription",
        )
        subject.pause(sub)
        subject.on_next("4")
        self.assertListEqual(
            val,
            ["1", "2", "3"],
            "BehaviorSubject should not push the latest value when subscription is paused",
        )
        subject.resume_paused()
        subject.on_next("5")
        self.assertListEqual(
            val,
            ["1", "2", "3", "5"],
            "BehaviorSubject should push the latest value when subscription is resumed",
        )
        subject.dispose()

    def test_publish_subject(self) -> None:
        subject = PublishSubject(str)
        val = []
        subject.on_next("1")
        sub = subject.subscribe(val.append)
        self.assertListEqual(
            val,
            [],
            "PublishSubject should not push the latest value on subscription",
        )
        subject.on_next("2")
        self.assertListEqual(
            val,
            ["2"],
            "PublishSubject should push the latest value after subscription",
        )
        subject.on_next("3")
        self.assertListEqual(
            val,
            ["2", "3"],
            "PublishSubject should push the latest value after subscription",
        )
        subject.pause(sub)
        subject.on_next("4")
        self.assertListEqual(
            val,
            ["2", "3"],
            "PublishSubject should not push the latest value when subscription is paused",
        )
        subject.resume_paused()
        subject.on_next("5")
        self.assertListEqual(
            val,
            ["2", "3", "5"],
            "PublishSubject should push the latest value when subscription is resumed",
        )
        subject.dispose()

    def test_replay_subject(self) -> None:
        subject = ReplaySubject(["A", "B", "C"])
        val = []
        val2 = []
        subject.subscribe(val.append)
        self.assertListEqual(val, ["A", "B", "C"])
        subject.on_next("1")
        self.assertListEqual(val, ["A", "B", "C", "1"])
        subject.subscribe(val2.append)
        self.assertListEqual(val2, ["A", "B", "C", "1"])
        subject.dispose()

    def test_replay_subject_map(self) -> None:
        subject = ReplaySubject(["a1", "a2", "a3"])
        val = []
        subject.pipe(RX.map(str.upper)).subscribe(val.append)
        self.assertListEqual(val, ["A1", "A2", "A3"])
        subject.on_next("a4")
        self.assertListEqual(val, ["A1", "A2", "A3", "A4"])
        subject.dispose()

    def test_replay_subject_filter(self) -> None:
        subject = ReplaySubject(["a1", "a2", "a3", "b", "c", "a4"])
        val = []
        subject.pipe(RX.filter(lambda s: s.startswith("a"))).subscribe(val.append)
        self.assertListEqual(val, ["a1", "a2", "a3", "a4"])
        subject.on_next("a5")
        self.assertListEqual(val, ["a1", "a2", "a3", "a4", "a5"])
        subject.on_next("b")
        self.assertListEqual(val, ["a1", "a2", "a3", "a4", "a5"])
        subject.dispose()

    def test_replay_subject_map_and_filter(self) -> None:
        subject = ReplaySubject(["a1", "a2", "a3"])
        val = []
        pipe1 = subject.pipe(RX.map(str.upper), RX.filter(lambda s: s.endswith("3")))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, ["A3"])
        subject.on_next("a4")
        self.assertListEqual(val, ["A3"])
        subject.dispose()

    def test_replay_subject_map_and_filter_multiple(self) -> None:
        subject = ReplaySubject(["a1", "a2", "a3"])
        val = []
        pipe1 = subject.pipe(
            RX.map(str.upper),
            RX.filter(lambda s: s.endswith("3")),
            RX.map(lambda s: s + "Test"),
        )
        pipe1.subscribe(val.append)
        self.assertListEqual(val, ["A3Test"])
        subject.on_next("a4")
        self.assertListEqual(val, ["A3Test"])
        subject.dispose()

    def test_replay_subject_filter_and_reduce(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(
            RX.filter(lambda nr: nr <= 10), RX.reduce(lambda a, b: max(a, b))
        )
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [1, 7])
        subject.on_next(9)
        self.assertListEqual(val, [1, 7, 9])
        subject.dispose()

    def test_replay_subject_with_take(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(RX.take(int, 3))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [1, 7, 20])
        subject.on_next(9)
        self.assertListEqual(val, [1, 7, 20])
        subject.dispose()

    def test_replay_subject_with_takeWhile(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(RX.take_while(lambda v: v < 10))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [1, 7])
        subject.on_next(9)
        self.assertListEqual(val, [1, 7])
        subject.dispose()

    def test_replay_subject_with_takeUntil(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(RX.take_until(lambda v: v > 10))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [1, 7])
        subject.on_next(9)
        self.assertListEqual(val, [1, 7])
        subject.dispose()

    def test_replay_subject_with_drop(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(RX.drop(int, 3))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [5, 100, 40])
        subject.on_next(9)
        self.assertListEqual(val, [5, 100, 40, 9])
        subject.dispose()

    def test_replay_subject_with_dropWhile(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(RX.drop_while(lambda v: v < 100))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [100, 40])
        subject.on_next(9)
        self.assertListEqual(val, [100, 40, 9])
        subject.dispose()

    def test_replay_subject_with_dropUntil(self) -> None:
        subject = ReplaySubject([1, 7, 20, 5, 100, 40])
        val = []
        pipe1 = subject.pipe(RX.drop_until(lambda v: v > 20))
        pipe1.subscribe(val.append)
        self.assertListEqual(val, [100, 40])
        subject.on_next(9)
        self.assertListEqual(val, [100, 40, 9])
        subject.dispose()

    def test_replay_subject_with_pipe_chaining(self) -> None:
        subject = ReplaySubject(range(1, 100))
        val = []
        val2 = []
        chainedPipe = (
            subject.pipe(RX.take_until(lambda e: e > 20))
            .pipe(RX.filter(lambda e: e % 2 == 0))
            .pipe(RX.take_while(lambda e: e < 10))
        )
        chainedPipe.subscribe(val.append)
        chainedPipe.subscribe(val2.append)
        chainedPipe.dispose()
        self.assertListEqual(val, [2, 4, 6, 8])
        self.assertListEqual(val2, [2, 4, 6, 8])

    def test_event_cancelling_subs(self) -> None:
        self.__test_event(True)

    def test_event_cancelling_events(self) -> None:
        self.__test_event(False)

    def __test_event(self, subs: bool) -> None:
        disposed_val = Value(False)
        disposed_valsub = Value(False)

        vals = []
        valsub = []

        subpipe = (
            event(int)
            .pipe(RX.map(lambda i: str(i)))
            .subscribe(vals.append, on_dispose=lambda: disposed_val.set(True))
        )
        subval = event(int).subscribe(valsub.append, lambda: disposed_valsub.set(True))

        self.assertIsNotNone(subpipe)
        self.assertIsNotNone(subval)

        event(int).publish(1)
        event(int).publish(2)

        if subs:
            subpipe.cancel()
            subval.cancel()
            subpipe.dispose()
            subval.dispose()
        else:
            events().clear_event(int)

        event(int).publish(3)
        self.assertEqual(event(int).latest(), 3)

        self.assertListEqual(vals, ["1", "2"])
        self.assertListEqual(valsub, [1, 2])
        self.assertTrue(disposed_val.get())
        self.assertTrue(disposed_valsub.get())
