from baseTest import BaseTestCase
from jstreams.iterable_operations import (
    find_first,
    find_last,
    matching,
    reduce,
    drop_until,
    drop_while,
    take_until,
    take_while,
)
from jstreams.predicate import is_not_blank
from jstreams.utils import is_not_none


class TestIterableOperations(BaseTestCase):
    def test_find_first(self):
        self.assertEqual(find_first([1, 2, 3, 4], lambda x: x > 2), 3)
        self.assertEqual(find_first([1, 2, 3, 4], lambda x: x == 1), 1)
        self.assertEqual(find_first([1, 2, 3, 4], lambda x: x == 4), 4)
        self.assertIsNone(find_first([1, 2, 3, 4], lambda x: x > 5))
        self.assertIsNone(find_first([], lambda x: x > 0))
        self.assertEqual(find_first([1, 3, 5, 2, 4, 6], lambda x: x % 2 == 0), 2)

    def test_find_last(self):
        self.assertEqual(
            find_last([1, 2, 3, 4, 3, 5], lambda x: x == 3), 3
        )  # The second 3
        self.assertEqual(find_last([1, 2, 3, 4], lambda x: x > 2), 4)
        self.assertEqual(find_last([1, 2, 3, 4], lambda x: x == 1), 1)
        self.assertEqual(find_last([1, 2, 3, 4], lambda x: x == 4), 4)
        self.assertIsNone(find_last([1, 2, 3, 4], lambda x: x > 5))
        self.assertIsNone(find_last([], lambda x: x > 0))
        self.assertEqual(find_last([1, 3, 5, 2, 4, 6], lambda x: x % 2 != 0), 5)

    def test_matching(self):
        self.assertEqual(list(matching([1, 2, 3, 4, 5], lambda x: x % 2 == 0)), [2, 4])
        self.assertEqual(list(matching([1, 2, 3, 4, 5], lambda x: x > 5)), [])
        self.assertEqual(list(matching([], lambda x: x > 0)), [])
        self.assertEqual(list(matching([1, 3, 5], lambda x: x % 2 != 0)), [1, 3, 5])
        # Test with predicate being None (if it implies truthiness)
        # Assuming None predicate filters out falsy values by default if that's the design
        # If None predicate is not allowed or has specific behavior, adjust this test
        # For now, assuming it works like filter(None, ...)
        self.assertEqual(
            list(matching([0, 1, None, 2, False, 3, ""], is_not_none)),
            [0, 1, 2, False, 3, ""],
        )
        self.assertEqual(
            list(matching([0, 1, None, 2, False, 3, ""], is_not_blank)),
            [0, 1, 2, False, 3],
        )

    def test_reduce(self):
        # Test with initial value
        self.assertEqual(reduce([1, 2, 3, 4], lambda acc, x: acc + x), 10)
        self.assertEqual(reduce([], lambda acc, x: acc + x), None)
        self.assertEqual(reduce(["a", "b", "c"], lambda acc, x: acc + x), "abc")

        # Test without initial value
        self.assertEqual(reduce([1, 2, 3, 4], lambda acc, x: acc + x), 10)
        self.assertEqual(
            reduce([5], lambda acc, x: acc + x), 5
        )  # Single element, no initial
        self.assertEqual(reduce(["a", "b", "c"], lambda acc, x: acc + x), "abc")

    def test_drop_until(self):
        self.assertEqual(list(drop_until([1, 2, 3, 4, 5], lambda x: x == 3)), [3, 4, 5])
        self.assertEqual(
            list(drop_until([1, 2, 3, 4, 5], lambda x: x == 1)), [1, 2, 3, 4, 5]
        )
        self.assertEqual(list(drop_until([1, 2, 3, 4, 5], lambda x: x == 5)), [5])
        self.assertEqual(list(drop_until([1, 2, 3, 4, 5], lambda x: x > 5)), [])
        self.assertEqual(list(drop_until([], lambda x: x > 0)), [])
        self.assertEqual(
            list(drop_until([1, 2, 3], lambda x: x < 0)), []
        )  # Predicate never true
        self.assertEqual(
            list(drop_until([1, 2, 3], lambda x: x > 0)), [1, 2, 3]
        )  # Predicate true for first

    def test_drop_while(self):
        self.assertEqual(list(drop_while([1, 2, 3, 4, 5], lambda x: x < 3)), [3, 4, 5])
        self.assertEqual(
            list(drop_while([1, 2, 3, 4, 5], lambda x: x < 1)), [1, 2, 3, 4, 5]
        )  # Predicate false for first
        self.assertEqual(
            list(drop_while([1, 2, 3, 4, 5], lambda x: x < 0)), [1, 2, 3, 4, 5]
        )  # Predicate always false
        self.assertEqual(
            list(drop_while([1, 2, 3, 4, 5], lambda x: x < 6)), []
        )  # Predicate always true
        self.assertEqual(list(drop_while([], lambda x: x > 0)), [])
        self.assertEqual(
            list(drop_while([2, 4, 6, 1, 3, 5], lambda x: x % 2 == 0)), [1, 3, 5]
        )

    def test_take_until(self):
        self.assertEqual(list(take_until([1, 2, 3, 4, 5], lambda x: x == 3)), [1, 2])
        self.assertEqual(list(take_until([1, 2, 3, 4, 5], lambda x: x == 1)), [])
        self.assertEqual(
            list(take_until([1, 2, 3, 4, 5], lambda x: x == 5)), [1, 2, 3, 4]
        )
        self.assertEqual(
            list(take_until([1, 2, 3, 4, 5], lambda x: x > 5)), [1, 2, 3, 4, 5]
        )  # Predicate never true
        self.assertEqual(list(take_until([], lambda x: x > 0)), [])
        self.assertEqual(
            list(take_until([1, 2, 3], lambda x: x < 0)), [1, 2, 3]
        )  # Predicate never true
        self.assertEqual(
            list(take_until([1, 2, 3], lambda x: x > 0)), []
        )  # Predicate true for first

    def test_take_while(self):
        self.assertEqual(list(take_while([1, 2, 3, 4, 5], lambda x: x < 3)), [1, 2])
        self.assertEqual(
            list(take_while([1, 2, 3, 4, 5], lambda x: x < 1)), []
        )  # Predicate false for first
        self.assertEqual(
            list(take_while([1, 2, 3, 4, 5], lambda x: x < 0)), []
        )  # Predicate always false
        self.assertEqual(
            list(take_while([1, 2, 3, 4, 5], lambda x: x < 6)), [1, 2, 3, 4, 5]
        )  # Predicate always true
        self.assertEqual(list(take_while([], lambda x: x > 0)), [])
        self.assertEqual(
            list(take_while([2, 4, 6, 1, 3, 5], lambda x: x % 2 == 0)), [2, 4, 6]
        )

    def test_find_first_on_generator(self):
        gen = (x for x in [1, 2, 3, 4])
        self.assertEqual(find_first(gen, lambda x: x > 2), 3)
        # After finding, the generator is partially consumed
        self.assertEqual(list(gen), [4])

    def test_find_last_on_generator(self):
        # find_last will consume the generator
        gen = (x for x in [1, 2, 3, 4, 3, 5])
        self.assertEqual(find_last(gen, lambda x: x == 3), 3)
        self.assertEqual(list(gen), [])  # Generator fully consumed

    def test_reduce_on_generator(self):
        gen = (x for x in [1, 2, 3, 4])
        self.assertEqual(reduce(gen, lambda acc, x: acc + x), 10)
        self.assertEqual(list(gen), [])  # Original generator consumed

        gen2 = (x for x in [1, 2, 3, 4])
        self.assertEqual(reduce(gen2, lambda acc, x: acc + x), 10)
        self.assertEqual(list(gen2), [])  # Original generator consumed

    def test_drop_until_on_generator(self):
        gen = (x for x in [1, 2, 3, 4, 5])
        dropped_gen = drop_until(gen, lambda x: x == 3)
        self.assertEqual(list(dropped_gen), [3, 4, 5])
        # The original generator 'gen' is consumed up to the point where drop_until stopped.
        # The remaining elements of 'gen' are those yielded by 'dropped_gen'.
        # So, if 'dropped_gen' is fully consumed, 'gen' will also be fully consumed.
        # If 'dropped_gen' is partially consumed, 'gen' will be partially consumed.
        # This behavior is standard for iterator chaining.

    def test_drop_while_on_generator(self):
        gen = (x for x in [1, 2, 3, 4, 5])
        dropped_gen = drop_while(gen, lambda x: x < 3)
        self.assertEqual(list(dropped_gen), [3, 4, 5])

    def test_take_until_on_generator(self):
        gen = (x for x in [1, 2, 3, 4, 5])
        taken_gen = take_until(gen, lambda x: x == 3)
        self.assertEqual(list(taken_gen), [1, 2])
        # Original generator 'gen' will be consumed up to '3' (inclusive, as it needs to check it)
        self.assertEqual(list(gen), [4, 5])

    def test_take_while_on_generator(self):
        gen = (x for x in [1, 2, 3, 4, 5])
        taken_gen = take_while(gen, lambda x: x < 3)
        self.assertEqual(list(taken_gen), [1, 2])
        # Original generator 'gen' will be consumed up to '3' (inclusive, as it needs to check it)
        self.assertEqual(list(gen), [4, 5])
