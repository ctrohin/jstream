from typing import Iterator, Optional
from baseTest import BaseTestCase
from jstreams import Stream
from jstreams.collectors import Collectors
from jstreams.stream import Opt
from jstreams.tuples import Pair


class TestStream(BaseTestCase):
    def test_stream_map(self) -> None:
        """
        Test stream map function
        """
        self.assertEqual(
            Stream(["Test", "Best", "Lest"]).map(str.upper).to_list(),
            ["TEST", "BEST", "LEST"],
        )

    def test_stream_filter(self) -> None:
        """
        Test stream filter function
        """
        self.assertEqual(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .to_list(),
            ["Test"],
        )
        self.assertFalse(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .is_empty()
        )
        self.assertTrue(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .is_not_empty()
        )

        self.assertEqual(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("X"))
            .to_list(),
            [],
        )

        self.assertTrue(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("X"))
            .is_empty()
        )

        self.assertFalse(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("X"))
            .is_not_empty()
        )

    def test_stream_anyMatch(self) -> None:
        """
        Test stream anyMatch function
        """
        self.assertFalse(
            Stream(["Test", "Best", "Lest"]).any_match(lambda s: s.startswith("X"))
        )

        self.assertTrue(
            Stream(["Test", "Best", "Lest"]).any_match(lambda s: s.startswith("T"))
        )

    def test_stream_allMatch(self) -> None:
        """
        Test stream allMatch function
        """
        self.assertTrue(
            Stream(["Test", "Best", "Lest"]).all_match(lambda s: s.endswith("est"))
        )

        self.assertFalse(
            Stream(["Test", "Best", "Lest1"]).all_match(lambda s: s.endswith("est"))
        )

    def test_stream_noneMatch(self) -> None:
        """
        Test stream noneMatch function
        """
        self.assertFalse(
            Stream(["Test", "Best", "Lest"]).none_match(lambda s: s.endswith("est"))
        )

        self.assertTrue(
            Stream(["Test", "Best", "Lest1"]).none_match(lambda s: s.endswith("xx"))
        )

    def test_stream_findFirst(self) -> None:
        """
        Test stream findFirst function
        """

        self.assertEqual(
            Stream(["Test", "Best", "Lest"])
            .find_first(lambda s: s.startswith("L"))
            .get_actual(),
            "Lest",
        )

    def test_stream_first(self) -> None:
        """
        Test stream first function
        """

        self.assertEqual(
            Stream(["Test", "Best", "Lest"]).first().get_actual(),
            "Test",
        )

    def test_stream_cast(self) -> None:
        """
        Test stream cast function
        """

        self.assertEqual(
            Stream(["Test1", "Test2", 1, 2])
            .filter(lambda el: el == "Test1")
            .cast(str)
            .first()
            .get_actual(),
            "Test1",
        )

    def test_stream_flatMap(self) -> None:
        """
        Test stream flatMap function
        """

        self.assertEqual(
            Stream([["a", "b"], ["c", "d"]]).flat_map(list).to_list(),
            ["a", "b", "c", "d"],
        )

    def test_stream_skip(self) -> None:
        """
        Test stream skip function
        """

        self.assertEqual(
            Stream(["a", "b", "c", "d"]).skip(2).to_list(),
            ["c", "d"],
        )

    def test_stream_limit(self) -> None:
        """
        Test stream limit function
        """

        self.assertEqual(
            Stream(["a", "b", "c", "d"]).limit(2).to_list(),
            ["a", "b"],
        )

    def test_stream_takeWhile(self) -> None:
        """
        Test stream takeWhile function
        """

        self.assertEqual(
            Stream(["a1", "a2", "a3", "b", "c", "d", "a4"])
            .take_while(lambda e: e.startswith("a"))
            .to_list(),
            ["a1", "a2", "a3"],
        )

    def test_stream_reduce(self) -> None:
        """
        Test stream reduce function
        """

        self.assertEqual(
            Stream(["aaa", "aa", "aaaa", "b", "c", "d"])
            .reduce(lambda el1, el2: el1 if len(el1) > len(el2) else el2)
            .get_actual(),
            "aaaa",
        )

    def test_stream_reduce_integers(self) -> None:
        """
        Test stream reduce function
        """

        self.assertEqual(
            Stream([1, 2, 3, 4, 20, 5, 6]).reduce(max).get_actual(),
            20,
        )

    def test_stream_nonNull(self) -> None:
        """
        Test stream nonNull function
        """

        self.assertEqual(
            Stream(["A", None, "B", None, None, "C", None, None]).non_null().to_list(),
            ["A", "B", "C"],
        )

    def str_len_cmp(self, a: str, b: str) -> int:
        return len(b) - len(a)

    def test_stream_sort(self) -> None:
        """
        Test stream sort function
        """

        self.assertEqual(
            Stream(["1", "333", "22", "4444", "55555"])
            .sort(self.str_len_cmp)
            .to_list(),
            ["55555", "4444", "333", "22", "1"],
        )

    def test_stream_reverse(self) -> None:
        """
        Test stream reverse function
        """

        self.assertEqual(
            Stream(["1", "333", "22", "4444", "55555"])
            .sort(self.str_len_cmp)
            .reverse()
            .to_list(),
            ["1", "22", "333", "4444", "55555"],
        )

    def test_stream_distinct(self) -> None:
        """
        Test stream distinct function
        """

        self.assertEqual(
            Stream(["1", "1", "2", "3", "3", "4"]).distinct().to_list(),
            ["1", "2", "3", "4"],
        )

    def test_stream_dropWhile(self) -> None:
        """
        Test stream dropWhile function
        """

        self.assertEqual(
            Stream(["a1", "a2", "a3", "b", "c", "d"])
            .drop_while(lambda e: e.startswith("a"))
            .to_list(),
            ["b", "c", "d"],
        )

        self.assertEqual(
            Stream(["a1", "a2", "a3", "a4", "a5", "a6"])
            .drop_while(lambda e: e.startswith("a"))
            .to_list(),
            [],
        )

    def test_stream_concat(self) -> None:
        """
        Test stream concat function
        """

        self.assertEqual(
            Stream(["a", "b", "c", "d"]).concat(Stream(["e", "f"])).to_list(),
            ["a", "b", "c", "d", "e", "f"],
        )

    def test_stream_flatten(self) -> None:
        """
        Test stream flattening
        """

        self.assertEqual(
            Stream([["A", "B"], ["C", "D"], ["E", "F"]]).flatten(str).to_list(),
            ["A", "B", "C", "D", "E", "F"],
        )

        self.assertEqual(
            Stream(["A", "B"]).flatten(str).to_list(),
            ["A", "B"],
        )

    def test_collector_group_by(self) -> None:
        values = Stream(
            [
                {"key": 1, "prop": "prop", "value": "X1"},
                {"key": 1, "prop": "prop", "value": "X2"},
                {"key": 1, "prop": "prop1", "value": "X3"},
                {"key": 1, "prop": "prop1", "value": "X4"},
            ]
        ).collect_using(Collectors.grouping_by(lambda x: x["prop"]))
        expected = {
            "prop": [
                {"key": 1, "prop": "prop", "value": "X1"},
                {"key": 1, "prop": "prop", "value": "X2"},
            ],
            "prop1": [
                {"key": 1, "prop": "prop1", "value": "X3"},
                {"key": 1, "prop": "prop1", "value": "X4"},
            ],
        }
        self.assertDictEqual(values, expected, "Values should be properly grouped")

    def test_collector_list(self) -> None:
        expected = [
            {"key": 1, "prop": "prop", "value": "X1"},
            {"key": 1, "prop": "prop", "value": "X2"},
            {"key": 1, "prop": "prop1", "value": "X3"},
            {"key": 1, "prop": "prop1", "value": "X4"},
        ]
        values = Stream(expected).collect_using(Collectors.to_list())
        self.assertListEqual(
            values, expected, "Values should be collected in the same list"
        )

    def test_collector_partitioning_by(self) -> None:
        values = Stream(
            [
                {"key": 1, "prop": "prop", "value": "X1"},
                {"key": 1, "prop": "prop", "value": "X2"},
                {"key": 2, "prop": "prop1", "value": "X3"},
                {"key": 2, "prop": "prop1", "value": "X4"},
            ]
        ).collect_using(Collectors.partitioning_by(lambda x: x["key"] == 1))
        expected = {
            True: [
                {"key": 1, "prop": "prop", "value": "X1"},
                {"key": 1, "prop": "prop", "value": "X2"},
            ],
            False: [
                {"key": 2, "prop": "prop1", "value": "X3"},
                {"key": 2, "prop": "prop1", "value": "X4"},
            ],
        }
        self.assertDictEqual(values, expected, "Values should be properly partitioned")

    def test_collector_joining_default(self) -> None:
        values = ["A", "B", "C"]
        value = Stream(values).collect_using(Collectors.joining())
        expected = "ABC"
        self.assertEqual(
            value, expected, "Value should contain the concatenated string array"
        )

    def test_collector_joining_specific(self) -> None:
        values = ["A", "B", "C"]
        value = Stream(values).collect_using(Collectors.joining(","))
        expected = "A,B,C"
        self.assertEqual(
            value, expected, "Value should contain the concatenated string array"
        )

    def test_collector_set(self) -> None:
        values = ["A", "B", "C"]
        value = Stream(values).collect_using(Collectors.to_set())
        expected = {"A", "B", "C"}
        self.assertSetEqual(
            value, expected, "Collection should produce a set of the values"
        )

    def test_collector_partitioning_by_mapping(self) -> None:
        values = Stream(
            [
                {"key": 1, "prop": "prop", "value": "X1"},
                {"key": 1, "prop": "prop", "value": "X2"},
                {"key": 2, "prop": "prop1", "value": "X3"},
                {"key": 2, "prop": "prop1", "value": "X4"},
            ]
        ).collect_using(
            Collectors.partitioning_by_mapping(
                lambda x: x["key"] == 1, lambda x: x["value"]
            )
        )
        expected = {
            True: ["X1", "X2"],
            False: ["X3", "X4"],
        }
        self.assertDictEqual(values, expected, "Values should be properly partitioned")

    def test_collector_group_by_mapping(self) -> None:
        values = Stream(
            [
                {"key": 1, "prop": "prop", "value": "X1"},
                {"key": 1, "prop": "prop", "value": "X2"},
                {"key": 1, "prop": "prop1", "value": "X3"},
                {"key": 1, "prop": "prop1", "value": "X4"},
            ]
        ).collect_using(
            Collectors.grouping_by_mapping(lambda x: x["prop"], lambda x: x["value"])
        )
        expected = {
            "prop": ["X1", "X2"],
            "prop1": ["X3", "X4"],
        }
        self.assertDictEqual(values, expected, "Values should be properly grouped")

    def test_chunked(self) -> None:
        expected = [
            list(range(0, 10)),
            list(range(10, 20)),
            list(range(20, 30)),
        ]
        self.assertEqual(Stream(range(30)).chunked(10).to_list(), expected)

        init = range(0, 10)
        self.assertEqual(Stream(init).chunked(100).to_list(), [list(init)])

    def test_range(self) -> None:
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(Stream.range(10).to_list(), expected)

    def test_stream_of(self) -> None:
        self.assertEqual(Stream.of([1, 2, 3]).to_list(), [1, 2, 3])
        self.assertEqual(Stream.of([]).to_list(), [])

    def test_stream_of_nullable(self) -> None:
        self.assertEqual(Stream.of_nullable([1, None, 2, None, 3]).to_list(), [1, 2, 3])
        self.assertEqual(Stream.of_nullable([None, None]).to_list(), [])
        self.assertEqual(Stream.of_nullable([]).to_list(), [])

    def test_stream_cycle(self) -> None:
        self.assertEqual(Stream.cycle([], n=5).to_list(), [])
        self.assertEqual(Stream.cycle([1, 2], n=0).to_list(), [])
        self.assertEqual(Stream.cycle([1, 2], n=2).to_list(), [1, 2, 1, 2])
        self.assertEqual(Stream.cycle([1, 2]).limit(5).to_list(), [1, 2, 1, 2, 1])
        self.assertEqual(
            Stream.cycle([]).limit(5).to_list(), []
        )  # Infinite cycle of empty is empty
        with self.assertRaises(ValueError):
            Stream.cycle([1], n=-1)

    def test_stream_of_dict_methods(self) -> None:
        d = {"a": 1, "b": 2, "c": 3}
        empty_d: dict[str, int] = {}

        self.assertCountEqual(Stream.of_dict_keys(d).to_list(), ["a", "b", "c"])
        self.assertEqual(Stream.of_dict_keys(empty_d).to_list(), [])

        self.assertCountEqual(Stream.of_dict_values(d).to_list(), [1, 2, 3])
        self.assertEqual(Stream.of_dict_values(empty_d).to_list(), [])

        self.assertCountEqual(
            Stream.of_dict_items(d).to_list(),
            [Pair("a", 1), Pair("b", 2), Pair("c", 3)],
        )
        self.assertEqual(Stream.of_dict_items(empty_d).to_list(), [])

    def test_stream_defer(self) -> None:
        supplier_called = False

        def my_iterable_supplier() -> list[int]:
            nonlocal supplier_called
            supplier_called = True
            return [10, 20, 30]

        s = Stream.defer(my_iterable_supplier)
        self.assertFalse(supplier_called, "Supplier should not be called yet")
        self.assertEqual(s.to_list(), [10, 20, 30])
        self.assertTrue(supplier_called, "Supplier should have been called")

        # Test re-iteration
        supplier_called_again = False

        def supplier_two() -> list[int]:
            nonlocal supplier_called_again
            supplier_called_again = True
            return [1, 2]

        s_two = Stream.defer(supplier_two)
        s_two.to_list()  # first consumption
        self.assertTrue(supplier_called_again)
        supplier_called_again = False  # reset
        s_two.to_list()  # second consumption
        self.assertTrue(
            supplier_called_again, "Supplier should be called on re-iteration"
        )

    def test_stream_iterate(self) -> None:
        self.assertEqual(
            Stream.iterate(0, lambda x: x + 2).limit(5).to_list(), [0, 2, 4, 6, 8]
        )

    def test_stream_generate(self) -> None:
        # Generate constant values for predictability
        self.assertEqual(
            Stream.generate(lambda: "val").limit(3).to_list(), ["val", "val", "val"]
        )

    def test_stream_empty(self) -> None:
        self.assertTrue(Stream.empty().is_empty())
        self.assertEqual(Stream.empty().to_list(), [])

    def test_stream_concat_of(self) -> None:
        self.assertEqual(
            Stream.concat_of([1, 2], [3, 4], [5]).to_list(), [1, 2, 3, 4, 5]
        )
        self.assertEqual(Stream.concat_of([1, 2], [], [3]).to_list(), [1, 2, 3])
        self.assertEqual(Stream.concat_of().to_list(), [])
        self.assertEqual(Stream.concat_of([1, 2]).to_list(), [1, 2])

    def test_stream_of_items(self) -> None:
        self.assertEqual(Stream.of_items(1, 2, 3).to_list(), [1, 2, 3])
        self.assertEqual(Stream.of_items().to_list(), [])

    def test_stream_zip_longest(self) -> None:
        s1 = Stream([1, 2])
        s2 = ["a", "b", "c"]
        expected = [Pair(1, "a"), Pair(2, "b"), Pair(None, "c")]
        self.assertEqual(s1.zip_longest(s2).to_list(), expected)

        expected_fill = [Pair(1, "a"), Pair(2, "b"), Pair(-1, "c")]
        self.assertEqual(s1.zip_longest(s2, fillvalue=-1).to_list(), expected_fill)

        self.assertEqual(
            Stream([]).zip_longest(s2, fillvalue=0).to_list(),
            [Pair(0, "a"), Pair(0, "b"), Pair(0, "c")],
        )
        self.assertEqual(
            s1.zip_longest([], fillvalue=0).to_list(), [Pair(1, 0), Pair(2, 0)]
        )
        self.assertEqual(Stream([]).zip_longest([], fillvalue=0).to_list(), [])

    def test_stream_collect(self) -> None:
        it = [1, 2, 3]
        s = Stream(it)
        # collect() returns the original iterable, so it should be the same object
        # or an equivalent one if the stream wraps it in a way that iteration is identical.
        # For simple list, it's often the same.
        collected_it = s.collect()
        self.assertEqual(list(collected_it), it)

    def test_stream_to_dict_variants(self) -> None:
        data = [
            Pair("a", 1),
            Pair("b", 2),
            Pair("c", 1),
        ]  # Note: duplicate value for 'c'
        s = Stream(data)

        self.assertEqual(s.to_dict(Pair.left, Pair.right), {"a": 1, "b": 2, "c": 1})
        # Test key collision - last one wins
        data_collision = [Pair("a", 1), Pair("b", 2), Pair("a", 3)]
        s_collision = Stream(data_collision)
        self.assertEqual(s_collision.to_dict(Pair.left, Pair.right), {"a": 3, "b": 2})

        self.assertEqual(Stream([]).to_dict(Pair.left, Pair.right), {})

        self.assertEqual(
            s.to_dict_as_values(Pair.left),
            {"a": Pair("a", 1), "b": Pair("b", 2), "c": Pair("c", 1)},
        )
        self.assertEqual(
            s_collision.to_dict_as_values(Pair.left),
            {"a": Pair("a", 3), "b": Pair("b", 2)},
        )

        # For to_dict_as_keys, keys must be hashable. Pair objects are if their contents are.
        self.assertEqual(
            s.to_dict_as_keys(Pair.right),
            {Pair("a", 1): 1, Pair("b", 2): 2, Pair("c", 1): 1},
        )

    def test_stream_to_tuple(self) -> None:
        self.assertEqual(Stream([1, 2, 3]).to_tuple(), (1, 2, 3))
        self.assertEqual(Stream([]).to_tuple(), ())

    def test_stream_each(self) -> None:
        items_seen: list[int] = []
        Stream([1, 2, 3]).each(items_seen.append)
        self.assertEqual(items_seen, [1, 2, 3])

    def test_stream_of_type(self) -> None:
        data = [1, "a", 2.0, "b", 3, True]
        self.assertEqual(
            Stream(data).of_type(int).to_list(), [1, 3]
        )  # True is not int here
        self.assertEqual(Stream(data).of_type(str).to_list(), ["a", "b"])
        self.assertEqual(Stream(data).of_type(float).to_list(), [2.0])
        self.assertEqual(Stream(data).of_type(bool).to_list(), [True])
        self.assertEqual(Stream(data).of_type(list).to_list(), [])

    def test_stream_take_until(self) -> None:
        s = Stream([1, 2, 3, 4, 5, 2])
        self.assertEqual(s.take_until(lambda x: x > 3).to_list(), [1, 2, 3])
        self.assertEqual(
            s.take_until(lambda x: x > 3, include_stop_value=True).to_list(),
            [1, 2, 3, 4],
        )
        self.assertEqual(
            Stream([1, 2, 3]).take_until(lambda x: x > 10).to_list(), [1, 2, 3]
        )
        self.assertEqual(
            Stream([1, 2, 3])
            .take_until(lambda x: x == 1, include_stop_value=True)
            .to_list(),
            [1],
        )
        self.assertEqual(Stream([1, 2, 3]).take_until(lambda x: x == 1).to_list(), [])
        self.assertEqual(Stream([]).take_until(lambda x: x > 0).to_list(), [])

    def test_stream_drop_until(self) -> None:
        s = Stream([1, 2, 3, 4, 5, 2])
        self.assertEqual(s.drop_until(lambda x: x > 3).to_list(), [4, 5, 2])
        self.assertEqual(Stream([1, 2, 3]).drop_until(lambda x: x > 10).to_list(), [])
        self.assertEqual(
            Stream([1, 2, 3]).drop_until(lambda x: x == 1).to_list(), [1, 2, 3]
        )
        self.assertEqual(Stream([]).drop_until(lambda x: x > 0).to_list(), [])

    def test_stream_peek(self) -> None:
        items_peeked: list[int] = []

        class MockExcLogger:
            def __init__(self):
                self.logs = []

            def __call__(self, e):
                self.logs.append(e)

        logger = MockExcLogger()

        def peek_action(x: int) -> None:
            if x == 2:
                raise ValueError("Peek error")
            items_peeked.append(x)

        result = Stream([1, 2, 3]).peek(peek_action, logger=logger).to_list()
        self.assertEqual(result, [1, 2, 3])  # Peek does not filter
        self.assertEqual(items_peeked, [1, 3])  # Item 2 caused error
        self.assertEqual(len(logger.logs), 1)
        self.assertIsInstance(logger.logs[0], ValueError)

    def test_stream_count(self) -> None:
        self.assertEqual(Stream([1, 2, 3]).count(), 3)
        self.assertEqual(Stream([]).count(), 0)

    def test_stream_indexed_enumerate(self) -> None:
        s = Stream(["a", "b", "c"])
        expected = [Pair(0, "a"), Pair(1, "b"), Pair(2, "c")]
        self.assertEqual(s.indexed().to_list(), expected)
        self.assertEqual(s.enumerate().to_list(), expected)  # Test alias
        self.assertEqual(Stream([]).indexed().to_list(), [])

    def test_stream_find_last(self) -> None:
        s = Stream([1, 2, 3, 4, 2, 5])
        self.assertEqual(s.find_last(lambda x: x == 2).get_actual(), 2)
        self.assertTrue(s.find_last(lambda x: x == 10).is_empty())
        self.assertTrue(Stream([]).find_last(lambda x: True).is_empty())

    def test_stream_pairwise(self) -> None:
        s = Stream([1, 2, 3, 4])
        expected = [Pair(1, 2), Pair(2, 3), Pair(3, 4)]
        self.assertEqual(s.pairwise().to_list(), expected)
        self.assertEqual(Stream([1, 2]).pairwise().to_list(), [Pair(1, 2)])
        self.assertEqual(Stream([1]).pairwise().to_list(), [])
        self.assertEqual(Stream([]).pairwise().to_list(), [])

    def test_stream_sliding_window(self) -> None:
        s = Stream([1, 2, 3, 4, 5])
        self.assertEqual(
            s.sliding_window(3, 1).to_list(), [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
        )
        self.assertEqual(
            s.sliding_window(2, 2).to_list(), [[1, 2], [3, 4]]
        )  # 5 is dropped
        self.assertEqual(s.sliding_window(5, 1).to_list(), [[1, 2, 3, 4, 5]])
        self.assertEqual(s.sliding_window(6, 1).to_list(), [])  # Not enough elements
        self.assertEqual(Stream([1, 2]).sliding_window(3, 1).to_list(), [])
        self.assertEqual(Stream([]).sliding_window(3, 1).to_list(), [])
        with self.assertRaises(ValueError):
            Stream([]).sliding_window(0, 1)
        with self.assertRaises(ValueError):
            Stream([]).sliding_window(1, 0)

    def test_stream_any_none_none_none(self) -> None:
        self.assertTrue(Stream([1, None, 3]).any_none())
        self.assertFalse(Stream([1, 2, 3]).any_none())
        self.assertFalse(Stream([]).any_none())

        self.assertFalse(Stream([1, None, 3]).none_none())
        self.assertTrue(Stream([1, 2, 3]).none_none())
        self.assertTrue(Stream([]).none_none())

    def test_stream_repeat(self) -> None:
        self.assertEqual(Stream([1, 2]).repeat(n=2).to_list(), [1, 2, 1, 2])
        self.assertEqual(Stream([1, 2]).repeat().limit(5).to_list(), [1, 2, 1, 2, 1])
        self.assertEqual(Stream([]).repeat(n=3).to_list(), [])
        with self.assertRaises(ValueError):
            Stream([1]).repeat(n=0)
        with self.assertRaises(ValueError):
            Stream([1]).repeat(n=-1)

    def test_stream_intersperse(self) -> None:
        self.assertEqual(Stream([1, 2, 3]).intersperse(0).to_list(), [1, 0, 2, 0, 3, 0])
        self.assertEqual(Stream(["a"]).intersperse("-").to_list(), ["a", "-"])
        self.assertEqual(Stream([]).intersperse(0).to_list(), [])

    def test_stream_unfold(self) -> None:
        def counter_generator(current: int) -> Optional[Pair[int, int]]:
            if current >= 5:
                return None
            return Pair(current, current + 1)

        self.assertEqual(Stream.unfold(0, counter_generator).to_list(), [0, 1, 2, 3, 4])

        def empty_generator(seed: int) -> Optional[Pair[int, int]]:
            return None

        self.assertEqual(Stream.unfold(0, empty_generator).to_list(), [])

    def test_stream_scan(self) -> None:
        s = Stream([1, 2, 3])
        self.assertEqual(s.scan(lambda acc, x: acc + x, 0).to_list(), [0, 1, 3, 6])
        self.assertEqual(Stream([]).scan(lambda acc, x: acc + x, 0).to_list(), [0])
        self.assertEqual(s.scan(lambda acc, x: acc * x, 1).to_list(), [1, 1, 2, 6])

    def test_distinct_with_key(self) -> None:
        class MyObj:
            def __init__(self, id_val: int, data: str):
                self.id_val = id_val
                self.data = data

            def __repr__(self) -> str:  # For easier debugging if test fails
                return f"MyObj({self.id_val}, '{self.data}')"

            # No __eq__ or7 __hash__ needed if using key func

        obj1a = MyObj(1, "apple")
        obj1b = MyObj(1, "apricot")
        obj2a = MyObj(2, "banana")

        data = [obj1a, obj2a, obj1b]
        # Distinct based on id_val
        result = Stream(data).distinct(key=lambda x: x.id_val).to_list()
        self.assertEqual(len(result), 2)
        # The first object with id_val=1 should be kept
        self.assertIn(obj1a, result)
        self.assertIn(obj2a, result)
        self.assertNotIn(obj1b, result)  # obj1b has same key as obj1a, obj1a came first

        # Test distinct on empty stream with key
        self.assertEqual(Stream([]).distinct(key=lambda x: x).to_list(), [])

        # Test distinct with all unique keys
        data_unique = [MyObj(1, "a"), MyObj(2, "b")]
        self.assertEqual(
            Stream(data_unique).distinct(key=lambda x: x.id_val).to_list(), data_unique
        )

        # Test distinct with all same keys
        data_same_key = [MyObj(1, "a"), MyObj(1, "b"), MyObj(1, "c")]
        result_same_key = (
            Stream(data_same_key).distinct(key=lambda x: x.id_val).to_list()
        )
        self.assertEqual(len(result_same_key), 1)
        self.assertEqual(result_same_key[0], data_same_key[0])

    def test_stream_of_nullable_with_require_non_null_internally(self) -> None:
        # This test ensures that the internal map(lambda el: require_non_null(el))
        # in of_nullable works as expected.
        # The type checker should also be happy with this.
        s: Stream[int] = Stream.of_nullable([1, None, 2])
        self.assertEqual(s.to_list(), [1, 2])

    def test_stream_zip(self) -> None:
        s1 = Stream([1, 2, 3])
        s2 = ["a", "b"]
        # zip stops at the shortest iterable
        expected = [Pair(1, "a"), Pair(2, "b")]
        self.assertEqual(s1.zip(s2).to_list(), expected)
        expected = [Pair("a", 1), Pair("b", 2)]
        self.assertEqual(
            Stream(s2).zip(s1.to_list()).to_list(), expected
        )  # Order of operands for zip

        self.assertEqual(Stream([1, 2, 3]).zip([]).to_list(), [])
        self.assertEqual(Stream([]).zip([1, 2, 3]).to_list(), [])
        self.assertEqual(Stream([]).zip([]).to_list(), [])
