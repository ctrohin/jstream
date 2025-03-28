from baseTest import BaseTestCase
from jstreams.predicate import not_, contains, is_in_interval, is_zero
from jstreams.tuples import left_matches, middle_matches, pair, right_matches, triplet


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
