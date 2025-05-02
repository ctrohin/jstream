from baseTest import BaseTestCase
from jstreams.stream import pair_stream
from jstreams.stream_factories import triplet_stream
from jstreams.predicate import not_, contains, is_in_interval, is_zero
from jstreams.tuples import (
    Pair,
    Triplet,
    left_matches,
    middle_matches,
    pair,
    right_matches,
    triplet,
)


class TestTuples(BaseTestCase):
    def test_pair(self) -> None:
        v = pair("a", 0)
        self.assertEqual(v.left(), "a", "Left should be correct")
        self.assertEqual(v.right(), 0, "Right should be correct")

    def test_triplet(self) -> None:
        v = triplet("test", 1, None)
        self.assertEqual(v.left(), "test", "Left should be correct")
        self.assertEqual(v.middle(), 1, "Middle should be correct")
        self.assertIsNone(v.right(), "Right should be None")

    def test_pair_predicate(self) -> None:
        v = pair("test", 0)
        self.assertTrue(left_matches(contains("es"))(v), "Left should match predicate")
        self.assertFalse(
            left_matches(contains("as"))(v), "Left should not match predicate"
        )
        self.assertTrue(right_matches(is_zero)(v), "Right should match predicate")
        self.assertFalse(
            right_matches(not_(is_zero))(v), "Right should not match predicate"
        )

    def test_triplet_predicate(self) -> None:
        v = triplet("test", 0, 1.5)
        self.assertTrue(left_matches(contains("es"))(v), "Left should match predicate")
        self.assertFalse(
            left_matches(contains("as"))(v), "Left should not match predicate"
        )
        self.assertTrue(middle_matches(is_zero)(v), "Middle should match predicate")
        self.assertFalse(
            middle_matches(not_(is_zero))(v), "Middle should not match predicate"
        )
        self.assertTrue(
            right_matches(is_in_interval(1, 2))(v), "Right should match predicate"
        )
        self.assertFalse(
            right_matches(is_in_interval(1.6, 2))(v), "Right should not match predicate"
        )

    def test_pair_stream(self) -> None:
        list1 = ["A", "B", "C"]
        list2 = [0, 1, 2]

        expected = [Pair("A", 0), Pair("B", 1), Pair("C", 2)]

        self.assertListEqual(
            pair_stream(list1, list2).to_list(),
            expected,
            "Pairs should be produced as expected",
        )

    def test_pair_stream_uneven_first(self) -> None:
        list1 = ["A", "B", "C", "D"]
        list2 = [0, 1, 2]

        expected = [Pair("A", 0), Pair("B", 1), Pair("C", 2)]

        self.assertListEqual(
            pair_stream(list1, list2).to_list(),
            expected,
            "Pairs should be produced as expected. Last pair should not exist since it is incomplete",
        )

    def test_pair_stream_uneven_second(self) -> None:
        list1 = ["A", "B", "C"]
        list2 = [0, 1, 2, 3]

        expected = [Pair("A", 0), Pair("B", 1), Pair("C", 2)]

        self.assertListEqual(
            pair_stream(list1, list2).to_list(),
            expected,
            "Pairs should be produced as expected. Last pair should not exist since it is incomplete",
        )

    def test_triplet_stream(self) -> None:
        list1 = ["A", "B", "C"]
        list2 = [0, 1, 2]
        list3 = [0.5, 1.2, 1.3]

        expected = [Triplet("A", 0, 0.5), Triplet("B", 1, 1.2), Triplet("C", 2, 1.3)]

        self.assertListEqual(
            triplet_stream(list1, list2, list3).to_list(),
            expected,
            "Triplets should be produced as expected",
        )

    def test_triplet_stream_uneven_left(self) -> None:
        list1 = ["A", "B", "C", "D"]
        list2 = [0, 1, 2]
        list3 = [0.5, 1.2, 1.3]

        expected = [Triplet("A", 0, 0.5), Triplet("B", 1, 1.2), Triplet("C", 2, 1.3)]

        self.assertListEqual(
            triplet_stream(list1, list2, list3).to_list(),
            expected,
            "Triplets should be produced as expected",
        )

    def test_triplet_stream_uneven_right(self) -> None:
        list1 = ["A", "B", "C"]
        list2 = [0, 1, 2]
        list3 = [0.5, 1.2, 1.3, 5]

        expected = [Triplet("A", 0, 0.5), Triplet("B", 1, 1.2), Triplet("C", 2, 1.3)]

        self.assertListEqual(
            triplet_stream(list1, list2, list3).to_list(),
            expected,
            "Triplets should be produced as expected",
        )
