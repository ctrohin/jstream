from baseTest import BaseTestCase
from jstreams.predicate import Not, contains, isInInterval, isZero
from jstreams.tuples import leftMatches, middleMatches, pair, rightMatches, triplet


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
        self.assertTrue(leftMatches(contains("es"))(v), "Left should match predicate")
        self.assertFalse(
            leftMatches(contains("as"))(v), "Left should not match predicate"
        )
        self.assertTrue(rightMatches(isZero)(v), "Right should match predicate")
        self.assertFalse(
            rightMatches(Not(isZero))(v), "Right should not match predicate"
        )

    def test_triplet_predicate(self) -> None:
        v = triplet("test", 0, 1.5)
        self.assertTrue(leftMatches(contains("es"))(v), "Left should match predicate")
        self.assertFalse(
            leftMatches(contains("as"))(v), "Left should not match predicate"
        )
        self.assertTrue(middleMatches(isZero)(v), "Middle should match predicate")
        self.assertFalse(
            middleMatches(Not(isZero))(v), "Middle should not match predicate"
        )
        self.assertTrue(
            rightMatches(isInInterval(1, 2))(v), "Right should match predicate"
        )
        self.assertFalse(
            rightMatches(isInInterval(1.6, 2))(v), "Right should not match predicate"
        )
