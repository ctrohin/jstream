from baseTest import BaseTestCase
from jstreams import Stream
from jstreams.collectors import Collectors


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
            Stream(["a1", "a2", "a3", "b", "c", "d"])
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
