from baseTest import BaseTestCase
from jstreams import Stream


class TestStream(BaseTestCase):
    def test_stream_map(self) -> None:
        """
        Test stream map function
        """
        self.assertEqual(
            Stream(["Test", "Best", "Lest"]).map(str.upper).toList(),
            ["TEST", "BEST", "LEST"],
        )

    def test_stream_filter(self) -> None:
        """
        Test stream filter function
        """
        self.assertEqual(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .toList(),
            ["Test"],
        )
        self.assertFalse(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .isEmpty()
        )
        self.assertTrue(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("T"))
            .isNotEmpty()
        )

        self.assertEqual(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("X"))
            .toList(),
            [],
        )

        self.assertTrue(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("X"))
            .isEmpty()
        )

        self.assertFalse(
            Stream(["Test", "Best", "Lest"])
            .filter(lambda s: s.startswith("X"))
            .isNotEmpty()
        )

    def test_stream_anyMatch(self) -> None:
        """
        Test stream anyMatch function
        """
        self.assertFalse(
            Stream(["Test", "Best", "Lest"]).anyMatch(lambda s: s.startswith("X"))
        )

        self.assertTrue(
            Stream(["Test", "Best", "Lest"]).anyMatch(lambda s: s.startswith("T"))
        )

    def test_stream_allMatch(self) -> None:
        """
        Test stream allMatch function
        """
        self.assertTrue(
            Stream(["Test", "Best", "Lest"]).allMatch(lambda s: s.endswith("est"))
        )

        self.assertFalse(
            Stream(["Test", "Best", "Lest1"]).allMatch(lambda s: s.endswith("est"))
        )

    def test_stream_noneMatch(self) -> None:
        """
        Test stream noneMatch function
        """
        self.assertFalse(
            Stream(["Test", "Best", "Lest"]).noneMatch(lambda s: s.endswith("est"))
        )

        self.assertTrue(
            Stream(["Test", "Best", "Lest1"]).noneMatch(lambda s: s.endswith("xx"))
        )

    def test_stream_findFirst(self) -> None:
        """
        Test stream findFirst function
        """

        self.assertEqual(
            Stream(["Test", "Best", "Lest"])
            .findFirst(lambda s: s.startswith("L"))
            .getActual(),
            "Lest",
        )

    def test_stream_first(self) -> None:
        """
        Test stream first function
        """

        self.assertEqual(
            Stream(["Test", "Best", "Lest"]).first().getActual(),
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
            .getActual(),
            "Test1",
        )

    def test_stream_flatMap(self) -> None:
        """
        Test stream flatMap function
        """

        self.assertEqual(
            Stream([["a", "b"], ["c", "d"]]).flatMap(list).toList(),
            ["a", "b", "c", "d"],
        )

    def test_stream_skip(self) -> None:
        """
        Test stream skip function
        """

        self.assertEqual(
            Stream(["a", "b", "c", "d"]).skip(2).toList(),
            ["c", "d"],
        )

    def test_stream_limit(self) -> None:
        """
        Test stream limit function
        """

        self.assertEqual(
            Stream(["a", "b", "c", "d"]).limit(2).toList(),
            ["a", "b"],
        )

    def test_stream_takeWhile(self) -> None:
        """
        Test stream takeWhile function
        """

        self.assertEqual(
            Stream(["a1", "a2", "a3", "b", "c", "d"])
            .takeWhile(lambda e: e.startswith("a"))
            .toList(),
            ["a1", "a2", "a3"],
        )

    def test_stream_reduce(self) -> None:
        """
        Test stream reduce function
        """

        self.assertEqual(
            Stream(["aaa", "aa", "aaaa", "b", "c", "d"])
            .reduce(lambda el1, el2: el1 if len(el1) > len(el2) else el2)
            .getActual(),
            "aaaa",
        )

    def test_stream_reduce_integers(self) -> None:
        """
        Test stream reduce function
        """

        self.assertEqual(
            Stream([1, 2, 3, 4, 20, 5, 6]).reduce(max).getActual(),
            20,
        )

    def test_stream_nonNull(self) -> None:
        """
        Test stream nonNull function
        """

        self.assertEqual(
            Stream(["A", None, "B", None, None, "C", None, None]).nonNull().toList(),
            ["A", "B", "C"],
        )

    def str_len_cmp(self, a: str, b: str) -> int:
        return len(b) - len(a)

    def test_stream_sort(self) -> None:
        """
        Test stream sort function
        """

        self.assertEqual(
            Stream(["1", "333", "22", "4444", "55555"]).sort(self.str_len_cmp).toList(),
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
            .toList(),
            ["1", "22", "333", "4444", "55555"],
        )

    def test_stream_distinct(self) -> None:
        """
        Test stream distinct function
        """

        self.assertEqual(
            Stream(["1", "1", "2", "3", "3", "4"]).distinct().toList(),
            ["1", "2", "3", "4"],
        )

    def test_stream_dropWhile(self) -> None:
        """
        Test stream dropWhile function
        """

        self.assertEqual(
            Stream(["a1", "a2", "a3", "b", "c", "d"])
            .dropWhile(lambda e: e.startswith("a"))
            .toList(),
            ["b", "c", "d"],
        )

        self.assertEqual(
            Stream(["a1", "a2", "a3", "a4", "a5", "a6"])
            .dropWhile(lambda e: e.startswith("a"))
            .toList(),
            [],
        )

    def test_stream_concat(self) -> None:
        """
        Test stream concat function
        """

        self.assertEqual(
            Stream(["a", "b", "c", "d"]).concat(Stream(["e", "f"])).toList(),
            ["a", "b", "c", "d", "e", "f"],
        )
