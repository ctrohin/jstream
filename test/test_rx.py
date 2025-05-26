from time import sleep

from baseTest import BaseTestCase
from jstreams import (
    BehaviorSubject,
    Flowable,
    PublishSubject,
    ReplaySubject,
    Single,
    RX,
    Timestamped,
)
from jstreams.eventing import event, events, managed_events, on_event
from jstreams.rx import (
    BackpressureException,
    BackpressureMismatchException,
    BackpressureStrategy,
    SingleValueSubject,
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
        event(str).pipe(RX.distinct_until_changed()).subscribe(elements.append)
        event(str).publish("test")
        event(str).publish("test")
        event(str).publish("test2")
        sleep(1)
        self.assertListEqual(elements, ["test", "test2"])

    def test_distinct_until_changed_with_key(self) -> None:
        elements = []
        event(str).pipe(RX.distinct_until_changed(lambda s: s[0])).subscribe(
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
        Flowable([1, 2, 2, 3, 1, 4, 4]).pipe(RX.distinct()).subscribe(results.append)
        self.assertListEqual(results, [1, 2, 3, 4])

        results = []
        data = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}, {"id": 1, "val": "c"}]
        Flowable(data).pipe(RX.distinct(key_selector=lambda x: x["id"])).subscribe(
            results.append
        )
        self.assertListEqual(results, [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}])

    def test_rx_timestamp(self) -> None:
        results = []
        start_time = Value(None)
        Flowable(["a", "b"]).pipe(RX.timestamp()).subscribe(
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
        Flowable(["a", "b", "c"]).pipe(RX.element_at(1)).subscribe(results.append)
        self.assertListEqual(results, ["b"])

        results = []
        Flowable(["a", "b", "c"]).pipe(RX.element_at(0)).subscribe(results.append)
        self.assertListEqual(results, ["a"])

        results = []
        Flowable(["a", "b", "c"]).pipe(RX.element_at(2)).subscribe(results.append)
        self.assertListEqual(results, ["c"])

        results = []  # out of bounds
        Flowable(["a", "b", "c"]).pipe(RX.element_at(3)).subscribe(results.append)
        self.assertListEqual(results, [])

        with self.assertRaises(ValueError):
            RX.element_at(-1)

    def test_buffer_emits_none_then_list(self) -> None:
        pipe = RX.buffer(0.02)
        pipe.init()  # Important for stateful operators like buffer
        self.assertIsNone(pipe.transform(1))  # type: ignore
        self.assertIsNone(pipe.transform(2))  # type: ignore
        sleep(0.03)
        self.assertListEqual(pipe.transform(3), [1, 2, 3])  # type: ignore
        self.assertIsNone(pipe.transform(4))  # type: ignore

    def test_buffer_count_emits_none_then_list(self) -> None:
        pipe = RX.buffer_count(3)
        pipe.init()
        self.assertIsNone(pipe.transform(1))  # type: ignore
        self.assertIsNone(pipe.transform(2))  # type: ignore
        self.assertListEqual(pipe.transform(3), [1, 2, 3])  # type: ignore
        self.assertIsNone(pipe.transform(4))  # type: ignore

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

        self.assertEquals(values, ["test"])
        self.assertEquals(errors, [])

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

        self.assertEquals(values, ["test"])
        self.assertEquals(
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
