from baseTest import BaseTestCase
from jstreams import (
    stream,
    not_,
    equals_ignore_case,
    str_contains,
    is_not_none,
    mapper_of,
    optional,
    predicate_of,
    reducer_of,
    to_float,
)
from jstreams.predicate import (
    has_key,
    has_value,
    is_even,
    is_key_in,
    is_odd,
    is_positive,
    is_value_in,
)
from jstreams.stream_predicates import all_none, all_not_none, any_of, none_of, all_of
from jstreams.utils import identity


class TestPredicate(BaseTestCase):
    def test_predicate_and(self) -> None:
        expected = "Test"
        predicate = predicate_of(is_not_none).and_(equals_ignore_case("Test"))
        self.assertEqual(
            optional("Test").filter(predicate).get(),
            expected,
            "Expected value should be correct",
        )

    def test_predicate_and2(self) -> None:
        expected = "test value"
        predicate = predicate_of(str_contains("test")).and_(str_contains("value"))
        self.assertEqual(
            optional(expected).filter(predicate).get(),
            expected,
            "Expected value should be correct",
        )

    def test_predicate_and3(self) -> None:
        predicate = predicate_of(str_contains("test")).and_(not_(str_contains("value")))
        self.assertListEqual(
            stream(["test value", "test other", "some value"])
            .filter(predicate)
            .to_list(),
            ["test other"],
            "Expected value should be correct",
        )

    def test_predicate_or(self) -> None:
        predicate = predicate_of(str_contains("es")).or_(equals_ignore_case("Other"))
        self.assertListEqual(
            stream(["Test", "Fest", "other", "Son", "Father"])
            .filter(predicate)
            .to_list(),
            ["Test", "Fest", "other"],
            "Expected value should be correct",
        )

    def test_predicate_call(self) -> None:
        predicate = predicate_of(str_contains("es"))
        self.assertTrue(
            predicate("test"),
            "Predicate should be callable and return the proper value",
        )

        self.assertTrue(
            predicate.apply("test"),
            "Predicate should be callable via Apply and return the proper value",
        )
        self.assertFalse(
            predicate("nomatch"),
            "Predicate should be callable and return the proper value",
        )
        self.assertFalse(
            predicate.apply("nomatch"),
            "Predicate should be callable via Apply and return the proper value",
        )

    def test_mapper_call(self) -> None:
        mapper = mapper_of(to_float)
        self.assertEqual(
            mapper("1.2"), 1.2, "Mapper should be callable and return the proper value"
        )
        self.assertEqual(
            mapper.map("1.2"),
            1.2,
            "Mapper should be callable via Map and return the proper value",
        )

    def test_reducer_call(self) -> None:
        reducer = reducer_of(max)
        self.assertEqual(
            reducer(1, 2), 2, "Reducer should be callable and return the proper value"
        )
        self.assertEqual(
            reducer.reduce(1, 2),
            2,
            "Reducer should be callable via Reduce and return the proper value",
        )

    def test_dict_keys_values(self) -> None:
        dct = {"test": "A"}
        self.assertTrue(has_key("test")(dct), "Dict should contain key")
        self.assertTrue(has_value("A")(dct), "Dict should contain value")
        self.assertFalse(has_key("other")(dct), "Dict should not contain key")
        self.assertFalse(has_value("B")(dct), "Dict should not contain value")
        self.assertTrue(is_key_in(dct)("test"), "Dict should contain key")
        self.assertTrue(is_value_in(dct)("A"), "Dict should contain value")
        self.assertFalse(is_key_in(dct)("other"), "Dict should not contain key")
        self.assertFalse(is_value_in(dct)("B"), "Dict should not contain value")

    def test_identity(self) -> None:
        initial = ["1", "2"]
        self.assertListEqual(
            stream(initial).map(identity).to_list(),
            initial,
            "Lists should match after identity mapping",
        )

    def test_all_none(self) -> None:
        self.assertTrue(all_none([]), "Empty list should be all None")
        self.assertTrue(all_none([None, None]), "List of Nones should be all None")
        self.assertFalse(all_none([1, None]), "Mixed list should not be all None")
        self.assertFalse(all_none([1, 2]), "List of non-Nones should not be all None")

    def test_all_not_none(self) -> None:
        self.assertTrue(all_not_none([]), "Empty list should be all not None")
        self.assertTrue(
            all_not_none([1, 2]), "List of non-Nones should be all not None"
        )
        self.assertFalse(
            all_not_none([1, None]), "Mixed list should not be all not None"
        )
        self.assertFalse(
            all_not_none([None, None]), "List of Nones should not be all not None"
        )

    def test_all_of(self) -> None:
        # Test with no predicates (vacuously true)
        self.assertTrue(all_of([])(5), "all_of with no predicates should be True")

        # Test with functions
        pred_all_func = all_of([is_positive, is_even])
        self.assertTrue(pred_all_func(4), "4 is positive and even")
        self.assertFalse(pred_all_func(3), "3 is positive but not even")
        self.assertFalse(pred_all_func(-2), "-2 is even but not positive")
        self.assertFalse(pred_all_func(-3), "-3 is not positive and not even")

        # Test with Predicate objects
        pred_all_obj = all_of([predicate_of(is_positive), predicate_of(is_even)])
        self.assertTrue(pred_all_obj(4), "4 is positive and even (Predicate objects)")
        self.assertFalse(
            pred_all_obj(3), "3 is positive but not even (Predicate objects)"
        )

        # Test short-circuiting (implicitly, by checking one failing predicate is enough)
        # is_positive fails first
        self.assertFalse(all_of([is_positive, lambda x: x > 1000])(-5))
        # is_even fails first
        self.assertFalse(all_of([is_even, lambda x: x < 0])(3))

    def test_any_of(self) -> None:
        # Test with no predicates
        self.assertFalse(any_of([])(5), "any_of with no predicates should be False")

        # Test with functions
        pred_any_func = any_of([is_positive, is_even])
        self.assertTrue(pred_any_func(4), "4 is positive or even (both)")
        self.assertTrue(pred_any_func(3), "3 is positive or even (positive)")
        self.assertTrue(pred_any_func(-2), "-2 is positive or even (even)")
        self.assertFalse(pred_any_func(-3), "-3 is not positive nor even")

        # Test with Predicate objects
        pred_any_obj = any_of([predicate_of(is_positive), predicate_of(is_even)])
        self.assertTrue(pred_any_obj(3), "3 is positive or even (Predicate objects)")
        self.assertFalse(
            pred_any_obj(-3), "-3 is not positive nor even (Predicate objects)"
        )

        # Test short-circuiting (implicitly, by checking one succeeding predicate is enough)
        # is_positive is true
        self.assertTrue(any_of([is_positive, lambda x: x > 1000])(5))
        # is_even is true
        self.assertTrue(any_of([is_odd, is_even])(2))

    def test_none_of(self) -> None:
        # Test with no predicates (vacuously true)
        self.assertTrue(none_of([])(5), "none_of with no predicates should be True")

        # Test with functions
        pred_none_func = none_of([is_positive, is_even])
        self.assertFalse(pred_none_func(4), "4 matches is_positive and is_even")
        self.assertFalse(pred_none_func(3), "3 matches is_positive")
        self.assertFalse(pred_none_func(-2), "-2 matches is_even")
        self.assertTrue(
            pred_none_func(-3), "-3 matches neither is_positive nor is_even"
        )

        # Test with Predicate objects
        pred_none_obj = none_of([predicate_of(is_positive), predicate_of(is_even)])
        self.assertTrue(
            pred_none_obj(-3),
            "-3 matches neither is_positive nor is_even (Predicate objects)",
        )
        self.assertFalse(pred_none_obj(3), "3 matches is_positive (Predicate objects)")

        # Test short-circuiting (implicitly, by checking one succeeding predicate is enough to fail none_of)
        # is_positive is true
        self.assertFalse(none_of([is_positive, lambda x: x > 1000])(5))
        # is_even is true
        self.assertFalse(none_of([is_odd, is_even])(2))

        # Test where all predicates fail (so none_of should be true)
        self.assertTrue(
            none_of([is_positive, is_even])(-1)
        )  # -1 is not positive and not even
        self.assertTrue(none_of([lambda x: x > 10, lambda x: x < 0])(5))
