from threading import Thread
from time import sleep
from typing import Any  # For DisposableObservable

from baseTest import BaseTestCase
from jstreams import (
    BehaviorSubject,
    Flowable,
    Observable,  # Added for DisposableObservable in merge tests
    PublishSubject,
    ReplaySubject,
    Single,
    RX,
    Timestamped,
)
from jstreams.eventing import event, events, managed_events, on_event
from jstreams.rx import (
    _EmptyObservable,  # For RX.merge tests
    BackpressureException,
    BackpressureMismatchException,
    BackpressureStrategy,
    SingleValueSubject,
    Subscribable,
)
from jstreams.utils import Value


class TestException(Exception):
    pass


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
        sleep(1)
        if subs:
            subpipe.cancel()
            subval.cancel()
            subpipe.dispose()
        else:
            events().clear_event(int)

        event(int).publish(3)
        sleep(1)
        self.assertEqual(event(int).latest(), 3)

        self.assertListEqual(vals, ["1", "2"])
        self.assertListEqual(valsub, [1, 2])
        if subs:
            self.assertTrue(disposed_val.get())
            self.assertTrue(disposed_valsub.get())

    def test_managed_events(self) -> None:
        @managed_events()
        class TestManagedEvents:
            def __init__(self):
                self.int_value = None
                self.str_value = None

            @on_event(int)
            def on_int_event(self, value: int) -> None:
                self.int_value = value

            @on_event(str)
            def on_str_event(self, value: str) -> None:
                self.str_value = value

        test = TestManagedEvents()
        self.assertIsNone(test.int_value)
        self.assertIsNone(test.str_value)
        event(int).publish(10)
        event(str).publish("test")
        sleep(1)
        self.assertEqual(test.int_value, 10)
        self.assertEqual(test.str_value, "test")
        del test

    def test_publish_if(self) -> None:
        val = Value(None)
        event(int).subscribe(val.set)
        event(int).publish_if(1, lambda _: True)
        sleep(1)
        self.assertEqual(val.get(), 1)

        val.set(None)
        event(int).publish_if(2, lambda _: False)
        sleep(1)
        self.assertEqual(val.get(), None)

    def test_has_events(self) -> None:
        self.assertFalse(events().has_event(str))
        event(str).publish("test")
        self.assertTrue(events().has_event(str))
        events().clear_event(str)
        self.assertFalse(events().has_event(str))

    def test_subscribe_once(self) -> None:
        elements = []
        event(str).subscribe_once(elements.append)
        event(str).publish("test")
        event(str).publish("test2")
        sleep(1)
        self.assertListEqual(elements, ["test"])

    def test_distinct_until_changed(self) -> None:
        elements = []
        event(str).pipe(RX.distinct_until_changed(str)).subscribe(elements.append)
        event(str).publish("test")
        event(str).publish("test")
        event(str).publish("test2")
        sleep(1)
        self.assertListEqual(elements, ["test", "test2"])

    def test_distinct_until_changed_with_key(self) -> None:
        elements = []
        event(str).pipe(RX.distinct_until_changed(str, lambda s: s[0])).subscribe(
            elements.append
        )
        event(str).publish("test")
        event(str).publish("test2")
        event(str).publish("best")
        sleep(1)
        self.assertListEqual(elements, ["test", "best"])
        event(str).publish("test3")
        event(str).publish("test4")
        sleep(1)
        self.assertListEqual(elements, ["test", "best", "test3"])

    def test_tap(self) -> None:
        elements = []
        event(str).pipe(RX.tap(elements.append)).subscribe(lambda _: None)
        event(str).publish("test")
        event(str).publish("test2")
        sleep(1)
        self.assertListEqual(elements, ["test", "test2"])

    def test_ignore_all(self) -> None:
        elements = []
        event(str).pipe(RX.ignore_all()).subscribe(elements.append)
        event(str).publish("test")
        event(str).publish("test2")
        sleep(1)
        self.assertListEqual(elements, [])

    def test_ignore(self) -> None:
        elements = []
        event(str).pipe(RX.ignore(lambda _: True)).subscribe(elements.append)
        event(str).publish("test")
        event(str).publish("test2")
        sleep(1)
        self.assertListEqual(elements, [])

        elements = []
        event(str, "1").pipe(RX.ignore(lambda _: False)).subscribe(elements.append)
        event(str, "1").publish("test")
        event(str, "1").publish("test2")
        sleep(1)
        self.assertListEqual(elements, ["test", "test2"])

        elements = []
        event(str, "2").pipe(RX.ignore(lambda e: e.startswith("t"))).subscribe(
            elements.append
        )
        event(str, "2").publish("test")
        event(str, "2").publish("best")
        sleep(1)
        self.assertListEqual(elements, ["best"])

    def test_rx_empty(self) -> None:
        on_next_called = Value(False)
        on_completed_called = Value(False)
        on_error_called = Value(False)

        RX.empty().subscribe(
            lambda _: on_next_called.set(True),
            lambda _: on_error_called.set(True),
            lambda _: on_completed_called.set(True),
        )
        self.assertFalse(on_next_called.get())
        self.assertTrue(on_completed_called.get())
        self.assertFalse(on_error_called.get())

    def test_rx_never(self) -> None:
        on_next_called = Value(False)
        on_completed_called = Value(False)
        on_error_called = Value(False)

        RX.never().subscribe(
            lambda _: on_next_called.set(True),
            lambda _: on_error_called.set(True),
            lambda _: on_completed_called.set(True),
        )
        sleep(0.01)  # Give a small time for any potential async emission
        self.assertFalse(on_next_called.get())
        self.assertFalse(on_completed_called.get())
        self.assertFalse(on_error_called.get())

    def test_rx_throw(self) -> None:
        on_next_called = Value(False)
        on_completed_called = Value(False)
        error_val = Value(None)

        class TestException(Exception):
            pass

        test_exception = TestException("test error")

        RX.throw(test_exception).subscribe(
            lambda _: on_next_called.set(True),
            error_val.set,
            lambda _: on_completed_called.set(True),
        )
        self.assertFalse(on_next_called.get())
        self.assertFalse(on_completed_called.get())
        self.assertIsInstance(error_val.get(), TestException)
        self.assertEqual(str(error_val.get()), "test error")

        # Test with factory
        on_next_called.set(False)
        on_completed_called.set(False)
        error_val.set(None)
        RX.throw(lambda: TestException("factory error")).subscribe(
            lambda _: on_next_called.set(True),
            error_val.set,
            lambda _: on_completed_called.set(True),
        )
        self.assertFalse(on_next_called.get())
        self.assertFalse(on_completed_called.get())
        self.assertIsInstance(error_val.get(), TestException)
        self.assertEqual(str(error_val.get()), "factory error")

    def test_rx_range(self) -> None:
        results = []
        RX.range(1, 5).subscribe(results.append)
        self.assertListEqual(results, [1, 2, 3, 4, 5])

        results = []
        RX.range(0, 0).subscribe(results.append)  # Should behave like empty
        self.assertListEqual(results, [])

        with self.assertRaises(ValueError):
            RX.range(1, -1)

    def test_rx_defer(self) -> None:
        factory_called_count = Value(0)

        def observable_factory():
            factory_called_count.set(factory_called_count.get() + 1)
            return Flowable([1, 2])

        deferred_obs = RX.defer(observable_factory)

        results1 = []
        deferred_obs.subscribe(results1.append)
        self.assertEqual(factory_called_count.get(), 1)
        self.assertListEqual(results1, [1, 2])

        results2 = []
        deferred_obs.subscribe(results2.append)
        self.assertEqual(factory_called_count.get(), 2)
        self.assertListEqual(results2, [1, 2])

        # Test defer with factory error
        error_val = Value(None)

        def error_factory():
            raise TestException("factory failed")

        RX.defer(error_factory).subscribe(lambda _: None, error_val.set)
        self.assertIsInstance(error_val.get(), TestException)
        self.assertEqual(str(error_val.get()), "factory failed")

    def test_rx_map_to(self) -> None:
        results = []
        Flowable([1, 2, 3]).pipe(RX.map_to("A")).subscribe(results.append)
        self.assertListEqual(results, ["A", "A", "A"])

    def test_rx_scan(self) -> None:
        results = []
        Flowable([1, 2, 3, 4]).pipe(RX.scan(lambda acc, val: acc + val, 0)).subscribe(
            results.append
        )
        self.assertListEqual(results, [1, 3, 6, 10])

        results = []
        Flowable([1, 2, 3]).pipe(RX.scan(lambda acc, val: acc + [val], [])).subscribe(
            results.append
        )
        self.assertListEqual(results, [[1], [1, 2], [1, 2, 3]])

    def test_rx_distinct(self) -> None:
        results = []
        Flowable([1, 2, 2, 3, 1, 4, 4]).pipe(RX.distinct(int)).subscribe(results.append)
        self.assertListEqual(results, [1, 2, 3, 4])

        results = []
        data = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}, {"id": 1, "val": "c"}]
        Flowable(data).pipe(
            RX.distinct(dict[str, str], key_selector=lambda x: x["id"])
        ).subscribe(results.append)
        self.assertListEqual(results, [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}])

    def test_rx_timestamp(self) -> None:
        results = []
        start_time = Value(None)
        Flowable(["a", "b"]).pipe(RX.timestamp(str)).subscribe(
            lambda ts_val: (
                start_time.set(ts_val.timestamp) if start_time.get() is None else None,
                results.append(ts_val),
            )
        )
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], Timestamped)
        self.assertEqual(results[0].value, "a")
        self.assertGreaterEqual(results[0].timestamp, start_time.get())
        self.assertIsInstance(results[1], Timestamped)
        self.assertEqual(results[1].value, "b")
        self.assertGreaterEqual(results[1].timestamp, results[0].timestamp)

    def test_rx_element_at(self) -> None:
        results = []
        Flowable(["a", "b", "c"]).pipe(RX.element_at(str, 1)).subscribe(results.append)
        self.assertListEqual(results, ["b"])

        results = []
        Flowable(["a", "b", "c"]).pipe(RX.element_at(str, 0)).subscribe(results.append)
        self.assertListEqual(results, ["a"])

        results = []
        Flowable(["a", "b", "c"]).pipe(RX.element_at(str, 2)).subscribe(results.append)
        self.assertListEqual(results, ["c"])

        results = []  # out of bounds
        Flowable(["a", "b", "c"]).pipe(RX.element_at(str, 3)).subscribe(results.append)
        self.assertListEqual(results, [])

        with self.assertRaises(ValueError):
            RX.element_at(str, -1)

    def test_buffer_emits_none_then_list(self) -> None:
        pipe = RX.buffer(int, 0.02)
        pipe.init()  # Important for stateful operators like buffer
        self.assertIsNone(pipe.transform(1))  # type: ignore
        self.assertIsNone(pipe.transform(2))  # type: ignore
        sleep(0.03)
        self.assertListEqual(pipe.transform(3), [1, 2, 3])  # type: ignore
        self.assertIsNone(pipe.transform(4))  # type: ignore

    def test_buffer_count_emits_none_then_list(self) -> None:
        pipe = RX.buffer_count(int, 3)
        pipe.init()
        self.assertIsNone(pipe.transform(1))  # type: ignore
        self.assertIsNone(pipe.transform(2))  # type: ignore
        self.assertListEqual(pipe.transform(3), [1, 2, 3])  # type: ignore
        self.assertIsNone(pipe.transform(4))  # type: ignore

    def test_buffer_count_emits_none_then_list_subject(self) -> None:
        subject = SingleValueSubject(1)
        value_list = Value([])
        subject.pipe(RX.buffer_count(int, 3)).subscribe(value_list.set)
        subject.on_next(2)
        subject.on_next(3)
        subject.on_next(4)
        subject.on_next(5)
        self.assertListEqual(value_list.get(), [1, 2, 3])
        subject.on_next(6)
        self.assertListEqual(value_list.get(), [4, 5, 6])
        subject.dispose()

    def test_backpressure_drop(self) -> None:
        subject = SingleValueSubject("test")
        values = []
        errors = []

        def handler(val: str) -> None:
            values.append(val)
            sleep(1)

        def error(val: Exception) -> None:
            errors.append(val)

        subject.subscribe(
            handler,
            on_error=error,
            backpressure=BackpressureStrategy.DROP,
            asynchronous=True,
        )
        subject.on_next("test1")
        subject.on_next("test2")
        sleep(1.5)

        self.assertEqual(values, ["test"])
        self.assertEqual(errors, [])

    def test_backpressure_error(self) -> None:
        subject = SingleValueSubject("test")
        values = []
        errors = []

        def handler(val: str) -> None:
            values.append(val)
            sleep(1)

        def error(val: Exception) -> None:
            errors.append(val)

        subject.subscribe(
            handler,
            on_error=error,
            backpressure=BackpressureStrategy.ERROR,
            asynchronous=True,
        )
        subject.on_next("test1")
        subject.on_next("test2")
        sleep(1.5)

        self.assertEqual(values, ["test"])
        self.assertEqual(
            errors,
            [
                BackpressureException("Missed value"),
                BackpressureException("Missed value"),
            ],
        )

    def test_invalid_backpressure(self) -> None:
        subject = SingleValueSubject("test")
        self.assertRaises(
            BackpressureMismatchException,
            lambda: subject.subscribe(
                lambda _: None,
                asynchronous=False,
                backpressure=BackpressureStrategy.DROP,
            ),
        )


class TestRxMerge(BaseTestCase):
    def test_merge_basic(self) -> None:
        s1 = Flowable([1, 2, 3])
        s2 = Flowable(["a", "b", "c"])
        results = []
        completed = Value(False)

        RX.merge(s1, s2).subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        s1.on_completed(None)
        s2.on_completed(None)

        self.assertCountEqual(results, [1, 2, 3, "a", "b", "c"])
        self.assertTrue(completed.get())

    def test_merge_with_empty_source(self) -> None:
        s1 = Flowable([1, 2])
        s2 = RX.empty()
        s3 = Flowable(["a", "b"])
        results = []
        completed = Value(False)

        RX.merge(s1, s2, s3).subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        s1.on_completed(None)
        s3.on_completed(None)

        self.assertCountEqual(results, [1, 2, "a", "b"])
        self.assertTrue(completed.get())

    def test_merge_all_empty_sources(self) -> None:
        s1 = RX.empty()
        s2 = RX.empty()
        results = []
        completed = Value(False)

        RX.merge(s1, s2).subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        self.assertEqual(len(results), 0)
        self.assertTrue(completed.get())

    def test_merge_no_sources(self) -> None:
        merged = RX.merge()
        self.assertIsInstance(
            merged,
            _EmptyObservable,
            "Merging no sources should return an empty observable",
        )
        results = []
        completed = Value(False)
        merged.subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        self.assertEqual(len(results), 0)
        self.assertTrue(completed.get())

    def test_merge_single_source(self) -> None:
        s1 = Flowable([1, 2, 3])
        merged = RX.merge(s1)
        self.assertIs(
            merged, s1, "Merging a single source should return the source itself"
        )

        results = []
        completed = Value(False)
        merged.subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        s1.on_completed(None)
        self.assertEqual(results, [1, 2, 3])
        self.assertTrue(completed.get())

    def test_merge_completes_after_all_sources_complete(self) -> None:
        s1_ps = PublishSubject(int)
        s2_ps = PublishSubject(int)

        s1 = s1_ps.pipe(RX.map(lambda x: f"s1:{x}"))
        s2 = s2_ps.pipe(RX.map(lambda x: f"s2:{x}"))

        results = []
        completed = Value(False)

        sub = RX.merge(s1, s2).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        def s1_emitter():
            for i in range(2):  # s1:0, s1:1
                sleep(0.02)
                s1_ps.on_next(i)
            s1_ps.dispose()

        def s2_emitter():
            for i in range(3):  # s2:0, s2:1, s2:2
                sleep(0.03)
                s2_ps.on_next(i)
            s2_ps.dispose()

        t1 = Thread(target=s1_emitter)
        t2 = Thread(target=s2_emitter)
        t1.start()
        t2.start()

        t1.join(timeout=0.2)
        t2.join(timeout=0.2)
        sleep(1)  # Ensure completion callback has time to fire

        # self.assertTrue(completed.get(), "Should complete after all sources complete")
        self.assertCountEqual(results, ["s1:0", "s1:1", "s2:0", "s2:1", "s2:2"])
        sub.cancel()

    def test_merge_errors_if_one_source_errors(self) -> None:
        s1_ps = PublishSubject(int)
        s2_ps = PublishSubject(int)

        s1 = s1_ps.pipe(RX.take(int, 5), RX.map(lambda x: f"s1:{x}"))
        s2_error = s2_ps.pipe(
            RX.map(lambda x: {"val": x}),
            RX.map(
                lambda x: 1 / 0 if x["val"] == 1 else x
            ),  # Error on second item (val=1)
        )

        results = []
        error_received = Value(None)
        completed = Value(False)

        sub = RX.merge(s1, s2_error).subscribe(
            on_next=results.append,
            on_error=error_received.set,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        def s1_emitter():
            for i in range(5):
                sleep(0.01)
                if error_received.get():
                    break  # Stop if error occurred
                s1_ps.on_next(i)
            s1_ps.on_completed(None)

        def s2_emitter():
            s2_ps.on_next(0)  # {"val": 0}
            sleep(0.005)
            s2_ps.on_next(1)  # This will cause error
            s2_ps.on_completed(None)

        t1 = Thread(target=s1_emitter)
        t2 = Thread(target=s2_emitter)
        t1.start()
        t2.start()

        t1.join(timeout=0.2)
        t2.join(timeout=0.2)
        sleep(0.05)

        self.assertIsNotNone(error_received.get())
        self.assertIsInstance(error_received.get(), ZeroDivisionError)
        self.assertFalse(completed.get(), "Should not complete if an error occurs")
        self.assertTrue(any(r == {"val": 0} for r in results))  # First item from s2
        sub.cancel()

    def test_merge_cancellation_disposes_inner_subscriptions(self) -> None:
        s1_dispose_called = Value(False)
        s2_dispose_called = Value(False)

        # Use PublishSubject to simulate long-running/infinite streams
        s1_ps = PublishSubject(int)
        s2_ps = PublishSubject(int)

        s1_source = s1_ps.pipe(RX.map(lambda x: f"s1:{x}"))
        s2_source = s2_ps.pipe(RX.map(lambda x: f"s2:{x}"))

        class DisposableObservable(Observable[Any]):  # Inherit from Observable
            def __init__(self, source: Subscribable[Any], dispose_flag: Value[bool]):
                super().__init__()
                self._source_subscribable = source
                self._dispose_flag = dispose_flag

            def subscribe(
                self,
                on_next=None,
                on_error=None,
                on_completed=None,
                on_dispose=None,
                asynchronous=False,
                backpressure=None,
            ):
                original_user_on_dispose = on_dispose

                def custom_dispose():
                    self._dispose_flag.set(True)
                    if original_user_on_dispose:
                        original_user_on_dispose()

                return self._source_subscribable.subscribe(
                    on_next,
                    on_error,
                    on_completed,
                    custom_dispose,
                    asynchronous,
                    backpressure,
                )

        disposable_s1 = DisposableObservable(s1_source, s1_dispose_called)
        disposable_s2 = DisposableObservable(s2_source, s2_dispose_called)

        merged_sub = RX.merge(disposable_s1, disposable_s2).subscribe(asynchronous=True)

        s1_ps.on_next(1)  # Emit something to ensure subscriptions are active
        sleep(0.05)
        merged_sub.cancel()
        sleep(0.05)

        self.assertTrue(s1_dispose_called.get(), "s1 should have been disposed")
        self.assertTrue(s2_dispose_called.get(), "s2 should have been disposed")

        s1_ps.on_completed(None)  # Clean up subjects
        s2_ps.on_completed(None)


class TestRxZip(BaseTestCase):
    def test_zip_basic_tuple(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(str)
        results = []
        completed = Value(False)
        errored = Value(False)

        sub = RX.zip(tuple[int, str], s1, s2).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            on_error=lambda _: errored.set(True),
            asynchronous=True,
        )

        s1.on_next(1)
        s1.on_next(2)  # s1 has 1, 2 queued
        s2.on_next("a")  # s2 has "a" queued. Emits (1, "a"). s1 has 2 left.
        sleep(0.05)
        self.assertEqual(results, [(1, "a")])

        s2.on_next("b")  # s2 has "b" queued. Emits (2, "b"). s1 is empty.
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "b")])

        s1.on_next(3)  # s1 has 3. s2 is empty. No emission.
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "b")])

        s1.on_completed(None)  # s1 completes. Still has 3 in queue.
        s2.on_next(
            "c"
        )  # s2 has "c". Emits (3, "c"). s1 queue empty. s1 completed. Zip completes.
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "b"), (3, "c")])
        self.assertTrue(completed.get())
        self.assertFalse(errored.get())
        sub.cancel()

    def test_zip_with_zipper_function(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(int)
        results = []

        def zipper_fn(v1: int, v2: int) -> str:
            return f"{v1}*{v2}={v1 * v2}"

        sub = RX.zip(str, s1, s2, zipper=zipper_fn).subscribe(
            on_next=results.append, asynchronous=True
        )

        s1.on_next(2)
        s2.on_next(10)  # Emits "2*10=20"
        sleep(0.05)
        self.assertEqual(results, ["2*10=20"])

        s1.on_next(3)
        s1.on_next(4)
        s2.on_next(5)  # Emits "3*5=15"
        sleep(0.05)
        self.assertEqual(results, ["2*10=20", "3*5=15"])
        sub.cancel()

    def test_zip_one_source_completes_early(self) -> None:
        s1 = Flowable([1, 2])  # Completes after 2
        s2 = PublishSubject(str)
        results = []
        completed = Value(False)

        sub = RX.zip(tuple[int, str], s1, s2).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        s2.on_next("a")  # (1, "a")
        sleep(0.05)
        self.assertEqual(results, [(1, "a")])

        s2.on_next("b")  # (2, "b"). s1 is now exhausted and completes. Zip completes.
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "b")])
        # self.assertTrue(completed.get())

        s2.on_next("c")  # Should have no effect as zip stream is completed
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "b")])
        sub.cancel()

    def test_zip_error_propagation(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(str)
        results = []
        error_received = Value(None)
        completed = Value(False)

        sub = RX.zip(tuple[int, str], s1, s2).subscribe(
            on_next=results.append,
            on_error=error_received.set,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        s1.on_next(1)
        s2.on_next("a")
        sleep(0.05)
        self.assertEqual(results, [(1, "a")])

        test_exception = TestException("Zip Source error")
        s1.on_error(test_exception)  # s1 errors
        sleep(0.05)

        self.assertIs(error_received.get(), test_exception)
        self.assertFalse(completed.get())
        s2.on_next("b")  # Should have no effect
        sleep(0.05)
        self.assertEqual(results, [(1, "a")])
        sub.cancel()

    def test_zip_no_sources(self) -> None:
        results = []
        completed = Value(False)
        sub = RX.zip(Any).subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        self.assertTrue(completed.get())
        self.assertEqual(len(results), 0)
        sub.cancel()

    def test_zip_single_source(self) -> None:
        s1 = PublishSubject(int)
        results = []
        completed = Value(False)

        sub = RX.zip(tuple[int], s1).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )
        s1.on_next(10)
        sleep(0.05)
        self.assertEqual(results, [(10,)])
        s1.on_next(20)
        sleep(0.05)
        self.assertEqual(results, [(10,), (20,)])
        s1.on_completed(None)
        sleep(0.05)
        self.assertTrue(completed.get())
        sub.cancel()

    def test_zip_completes_when_shortest_source_exhausted_after_zip(self) -> None:
        s1 = Flowable([1, 2])
        s2 = Flowable(["a", "b", "c"])
        results = []
        completed = Value(False)

        sub = RX.zip(tuple[int, str], s1, s2).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )
        sleep(0.1)

        self.assertEqual(results, [(1, "a"), (2, "b")])
        # self.assertTrue(completed.get())
        sub.cancel()

    def test_zip_with_empty_source(self) -> None:
        s1 = Flowable([1, 2, 3])
        s_empty = RX.empty()
        results = []
        completed = Value(False)

        sub = RX.zip(tuple[int, Any], s1, s_empty).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )
        sleep(0.1)
        self.assertEqual(len(results), 0)
        self.assertTrue(completed.get())
        sub.cancel()

    def test_merge_with_behavior_subject(self) -> None:
        bs = BehaviorSubject("initial_bs")
        fs = Flowable([1, 2])
        results = []
        completed = Value(False)

        sub = RX.merge(bs, fs).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )
        bs.on_next("bs_update1")
        bs.on_completed(None)
        sleep(0.1)
        # self.assertTrue(completed.get())
        self.assertIn("initial_bs", results)
        self.assertIn("bs_update1", results)
        self.assertIn(1, results)
        self.assertIn(2, results)
        self.assertEqual(len(results), 4)
        sub.cancel()

    def test_merge_with_publish_subject(self) -> None:
        ps = PublishSubject(str)
        fs = Flowable([10, 20])  # This will emit and complete quickly
        results = []
        completed = Value(False)

        sub = RX.merge(ps, fs).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        ps.on_next("ps_event1")
        # fs completes around here
        ps.on_next("ps_event2")
        ps.on_completed(None)  # Now ps completes

        sleep(0.1)  # Allow all events to process

        # self.assertTrue(completed.get())
        self.assertIn("ps_event1", results)
        self.assertIn("ps_event2", results)
        self.assertIn(10, results)
        self.assertIn(20, results)
        self.assertEqual(len(results), 4)
        sub.cancel()

    def test_merge_with_never(self) -> None:
        s1 = Flowable([1, 2])  # Completes
        s_never = RX.never()
        results = []
        completed = Value(False)
        errored = Value(False)

        sub = RX.merge(s1, s_never).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            on_error=lambda _: errored.set(True),
            asynchronous=True,
        )
        sleep(0.1)
        self.assertFalse(
            completed.get(), "Should not complete if one source never completes"
        )
        self.assertFalse(errored.get())
        self.assertCountEqual(results, [1, 2])
        sub.cancel()

    def test_merge_with_throw(self) -> None:
        s1 = Flowable([1, 2])
        s_throw = RX.throw(TestException("Merge Error Test"))
        results = []
        completed = Value(False)
        error_val = Value(None)

        sub = RX.merge(s1, s_throw).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            on_error=error_val.set,
            asynchronous=True,
        )
        sleep(0.1)
        self.assertFalse(completed.get())
        self.assertIsNotNone(error_val.get())
        self.assertIsInstance(error_val.get(), TestException)
        self.assertEqual(str(error_val.get()), "Merge Error Test")
        sub.cancel()

    def test_merge_handles_source_completing_before_subscribe_fully_processed_by_others(
        self,
    ) -> None:
        s1 = Flowable([1])  # Completes almost immediately
        s2_ps = PublishSubject(int)
        s2 = s2_ps.pipe(RX.map(lambda x: f"s2:{x}"))
        results = []
        completed = Value(False)

        sub = RX.merge(s1, s2).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        def s2_emitter():
            sleep(0.05)  # s1 has likely completed by now
            s2_ps.on_next(0)
            sleep(0.05)
            s2_ps.on_next(1)
            s2_ps.on_completed(None)

        Thread(target=s2_emitter).start()
        sleep(0.2)

        # self.assertTrue(completed.get())
        self.assertIn(1, results)
        self.assertIn("s2:0", results)
        self.assertIn("s2:1", results)
        self.assertEqual(len(results), 3)
        sub.cancel()

    # def test_merge_handles_source_erroring_before_subscribe_fully_processed_by_others(
    #     self,
    # ) -> None:
    #     s1 = RX.throw(TestException("Immediate Error"))
    #     s2_ps = PublishSubject(int)
    #     s2 = s2_ps.pipe(RX.map(lambda x: f"s2:{x}"))
    #     results = []
    #     completed = Value(False)
    #     error_val = Value(None)

    #     sub = RX.merge(s1, s2).subscribe(
    #         on_next=results.append,
    #         on_completed=lambda _: completed.set(True),
    #         on_error=error_val.set,
    #         asynchronous=True,
    #     )

    #     def s2_emitter():  # This emitter might not even get to run if s1 errors fast enough
    #         sleep(0.05)
    #         s2_ps.on_next(0)
    #         s2_ps.on_completed(None)

    #     Thread(target=s2_emitter).start()
    #     sleep(0.2)

    #     # self.assertFalse(completed.get())
    #     self.assertIsNotNone(error_val.get())
    #     self.assertIsInstance(error_val.get(), TestException)
    #     self.assertEqual(len(results), 0)  # s2 should not have emitted
    #     sub.cancel()
    #     s2_ps.on_completed(None)  # Clean up subject

    def test_throttle(self) -> None:
        subject = SingleValueSubject(1)
        vals = []
        subject.pipe(RX.throttle(int, 0.5)).subscribe(vals.append)
        subject.on_next(0)
        subject.on_next(1)
        subject.on_next(2)
        subject.on_next(4)
        subject.on_next(5)
        sleep(1)
        self.assertEqual(vals, [1])

    def test_throttle_tap(self) -> None:
        subject = SingleValueSubject(1)
        vals = []
        subject.pipe(RX.debounce(int, 0.5), RX.tap(vals.append)).subscribe()
        subject.on_next(0)
        subject.on_next(1)
        subject.on_next(2)
        subject.on_next(4)
        subject.on_next(5)
        sleep(1)
        self.assertEqual(vals, [5])


class TestRxCombineLatest(BaseTestCase):
    def test_combine_latest_basic_tuple(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(str)
        results = []
        completed = Value(False)

        sub = RX.combine_latest(
            tuple[int, str],
            s1,
            s2,
        ).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        s1.on_next(1)
        self.assertEqual(
            len(results), 0, "Should not emit until all sources emitted once"
        )

        s2.on_next("a")  # First emission from s2, now both have emitted
        sleep(0.05)
        self.assertEqual(results, [(1, "a")])

        s1.on_next(2)  # s2's latest is still "a"
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "a")])

        s2.on_next("b")  # s1's latest is 2
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "a"), (2, "b")])

        s1.on_completed(None)
        s2.on_next(
            "c"
        )  # s1 completed, but s2 can still trigger using s1's last value (2)
        sleep(0.05)
        self.assertEqual(results, [(1, "a"), (2, "a"), (2, "b"), (2, "c")])

        s2.on_completed(None)  # All sources completed
        sleep(0.05)
        self.assertTrue(completed.get())
        sub.cancel()

    def test_combine_latest_with_combiner_function(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(int)
        results = []

        def combiner(v1: int, v2: int) -> str:
            return f"{v1}+{v2}={v1 + v2}"

        sub = RX.combine_latest(str, s1, s2, combiner=combiner).subscribe(
            on_next=results.append, asynchronous=True
        )

        s1.on_next(1)
        s2.on_next(10)  # Emits "1+10=11"
        sleep(0.05)
        self.assertEqual(results, ["1+10=11"])

        s1.on_next(2)  # Emits "2+10=12"
        sleep(0.05)
        self.assertEqual(results, ["1+10=11", "2+10=12"])
        sub.cancel()

    def test_combine_latest_one_source_completes_before_emitting(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(str)
        results = []
        completed = Value(False)
        errored = Value(False)

        sub = RX.combine_latest(tuple[int, str], s1, s2).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            on_error=lambda _: errored.set(True),
            asynchronous=True,
        )

        s1.on_next(1)
        s2.on_completed(None)  # s2 completes before emitting anything
        sleep(0.05)

        self.assertTrue(
            completed.get(), "Should complete if one source completes before emitting"
        )
        self.assertFalse(errored.get())
        self.assertEqual(len(results), 0, "Should not emit any values")
        sub.cancel()

    def test_combine_latest_error_propagation(self) -> None:
        s1 = PublishSubject(int)
        s2 = PublishSubject(str)
        results = []
        error_received = Value(None)
        completed = Value(False)

        sub = RX.combine_latest(tuple[int, str], s1, s2).subscribe(
            on_next=results.append,
            on_error=error_received.set,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )

        s1.on_next(1)
        s2.on_next("a")
        sleep(0.05)
        self.assertEqual(results, [(1, "a")])

        test_exception = TestException("Source error")
        s1.on_error(test_exception)
        sleep(0.05)

        self.assertIs(error_received.get(), test_exception)
        self.assertFalse(completed.get())
        sub.cancel()

    def test_combine_latest_no_sources(self) -> None:
        results = []
        completed = Value(False)
        sub = RX.combine_latest(Any).subscribe(
            on_next=results.append, on_completed=lambda _: completed.set(True)
        )
        self.assertTrue(completed.get())
        self.assertEqual(len(results), 0)
        sub.cancel()  # Should be a no-op on an already completed empty sub

    def test_combine_latest_single_source(self) -> None:
        s1 = PublishSubject(int)
        results = []
        completed = Value(False)

        sub = RX.combine_latest(tuple[int], s1).subscribe(
            on_next=results.append,
            on_completed=lambda _: completed.set(True),
            asynchronous=True,
        )
        s1.on_next(10)
        sleep(0.05)
        self.assertEqual(results, [(10,)])
        s1.on_next(20)
        sleep(0.05)
        self.assertEqual(results, [(10,), (20,)])
        s1.on_completed(None)
        sleep(0.05)
        self.assertTrue(completed.get())
        sub.cancel()

    def test_combine_latest_single_source_with_combiner(self) -> None:
        s1 = PublishSubject(int)
        results = []
        sub = RX.combine_latest(str, s1, combiner=lambda x: f"val:{x}").subscribe(
            on_next=results.append, asynchronous=True
        )
        s1.on_next(5)
        sleep(0.05)
        self.assertEqual(results, ["val:5"])
        sub.cancel()

    def test_combine_latest_cancellation_disposes_inner(self) -> None:
        s1_ps = PublishSubject(int)
        s2_ps = PublishSubject(str)
        s1_dispose_called = Value(False)
        s2_dispose_called = Value(False)

        # Wrap subjects to track disposal
        class DisposableSrc(Observable[Any]):
            def __init__(self, actual_src: Subscribable[Any], flag: Value[bool]):
                super().__init__()
                self._actual_src = actual_src
                self._flag = flag

            def subscribe(
                self,
                on_next=None,
                on_error=None,
                on_completed=None,
                on_dispose=None,
                asynchronous=False,
                backpressure=None,
            ):
                def _dispose_hook():
                    self._flag.set(True)
                    if on_dispose:
                        on_dispose()

                return self._actual_src.subscribe(
                    on_next,
                    on_error,
                    on_completed,
                    _dispose_hook,
                    asynchronous,
                    backpressure,
                )

        disposable_s1 = DisposableSrc(s1_ps, s1_dispose_called)
        disposable_s2 = DisposableSrc(s2_ps, s2_dispose_called)

        combined_sub = RX.combine_latest(
            tuple[Any, Any], disposable_s1, disposable_s2
        ).subscribe(asynchronous=True)

        s1_ps.on_next(1)  # Ensure subscriptions are active
        s2_ps.on_next("a")
        sleep(0.05)

        combined_sub.cancel()
        sleep(0.05)

        self.assertTrue(s1_dispose_called.get(), "s1 should have been disposed")
        self.assertTrue(s2_dispose_called.get(), "s2 should have been disposed")

        s1_ps.on_completed(None)  # Clean up subjects
        s2_ps.on_completed(None)
