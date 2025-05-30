from typing import Any, Mapping
from collections.abc import Sized
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
    Predicate,
    PredicateWith,
    contains,
    default,
    equals,
    has_key,
    has_length,
    has_value,
    is_beween,
    is_beween_closed,
    is_beween_closed_end,
    is_beween_closed_start,
    is_blank,
    is_even,
    is_false,
    is_falsy,
    is_higher_than,
    is_higher_than_or_eq,
    is_identity,
    is_in,
    is_in_interval,
    is_in_open_interval,
    is_instance,
    is_int,
    is_key_in,
    is_less_than,
    is_less_than_or_eq,
    is_negative,
    is_none,
    is_not_blank,
    is_not_in,
    is_odd,
    is_positive,
    is_true,
    is_truthy,
    is_value_in,
    is_zero,
    not_equals,
    not_strict,
    str_contains_ignore_case,
    str_ends_with,
    str_ends_with_ignore_case,
    str_fullmatch,
    str_is_alnum,
    str_is_alpha,
    str_is_digit,
    str_is_lower,
    str_is_space,
    str_is_title,
    str_is_upper,
    str_longer_than,
    str_longer_than_or_eq,
    str_matches,
    str_not_matches,
    str_shorter_than,
    str_shorter_than_or_eq,
    str_starts_with,
    str_starts_with_ignore_case,
)
from jstreams.stream_predicates import all_none, all_not_none, any_of, none_of, all_of
from jstreams.utils import identity


# Helper for Sized test
class MySized(Sized):
    def __init__(self, length: int):
        self._length = length

    def __len__(self) -> int:
        return self._length


class MyNonSized:
    pass


class ParentClass:
    pass


class ChildClass(ParentClass):
    pass


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

    def test_predicate_of_and_call(self):
        p_gt0 = Predicate.of(lambda x: x > 0)
        self.assertIsInstance(p_gt0, Predicate)
        self.assertTrue(p_gt0(5))
        self.assertFalse(p_gt0(-1))
        self.assertTrue(p_gt0.apply(1))  # Test apply directly

        # Test Predicate.of with an existing Predicate instance
        p_gt0_again = Predicate.of(p_gt0)
        self.assertIs(p_gt0_again, p_gt0)  # Should return the same instance

    def test_predicate_or2(self):
        p_is_even = Predicate.of(lambda x: x % 2 == 0)
        p_is_gt10 = Predicate.of(lambda x: x > 10)
        p_or = p_is_even.or_(p_is_gt10)

        self.assertTrue(p_or(4))  # even
        self.assertTrue(p_or(12))  # > 10 and even
        self.assertTrue(p_or(11))  # > 10
        self.assertFalse(p_or(5))  # not even, not > 10

        # Test with a callable
        p_or_callable = p_is_even.or_(lambda x: x > 10)
        self.assertTrue(p_or_callable(11))

    def test_predicate_and2(self):
        p_is_even = Predicate.of(lambda x: x % 2 == 0)
        p_is_gt10 = Predicate.of(lambda x: x > 10)
        p_and = p_is_even.and_(p_is_gt10)

        self.assertFalse(p_and(4))  # even, but not > 10
        self.assertTrue(p_and(12))  # > 10 and even
        self.assertFalse(p_and(11))  # > 10, but not even
        self.assertFalse(p_and(5))  # not even, not > 10

        # Test with a callable
        p_and_callable = p_is_even.and_(lambda x: x > 10)
        self.assertTrue(p_and_callable(12))

    def test_predicate_with_of_and_call(self):
        pw_sum_eq_target = PredicateWith.of(lambda x, y, target: x + y == target)
        self.assertIsInstance(pw_sum_eq_target, PredicateWith)
        # This predicate actually takes 3 args, let's adjust for PredicateWith[T, K]
        pw_first_plus_second_eq_third = PredicateWith.of(
            lambda x, k_tuple: x + k_tuple[0] == k_tuple[1]
        )
        self.assertTrue(pw_first_plus_second_eq_third(5, (5, 10)))  # 5 + 5 == 10
        self.assertFalse(pw_first_plus_second_eq_third(5, (6, 10)))  # 5 + 6 != 10

        # Test PredicateWith.of with an existing PredicateWith instance
        pw_again = PredicateWith.of(pw_first_plus_second_eq_third)
        self.assertIs(pw_again, pw_first_plus_second_eq_third)

    def test_predicate_with_or(self):
        pw1 = PredicateWith.of(lambda t, k: isinstance(t, str) and isinstance(k, str))
        pw2 = PredicateWith.of(lambda t, k: len(str(t)) == len(str(k)))
        pw_or = pw1.or_(pw2)

        self.assertTrue(pw_or("a", "b"))  # Both true
        self.assertTrue(pw_or("a", 1))  # pw1 false, pw2 true (len("a")==len(str(1)))
        self.assertTrue(pw_or(1, "b"))  # pw1 false, pw2 true (len(str(1))==len("b"))
        self.assertTrue(pw_or("aa", "b"))  # pw1 true, pw2 false
        self.assertFalse(pw_or(1, 2.0))  # Both false

    def test_predicate_with_and(self):
        pw1 = PredicateWith.of(lambda t, k: isinstance(t, str) and isinstance(k, str))
        pw2 = PredicateWith.of(lambda t, k: len(t) == len(k))
        pw_and = pw1.and_(pw2)

        self.assertTrue(pw_and("a", "b"))  # Both true
        self.assertFalse(pw_and("a", 1))  # pw1 false
        self.assertFalse(pw_and("aa", "b"))  # pw2 false
        self.assertFalse(pw_and(1, 2.0))  # Both false

    def test_is_true_false(self):
        self.assertTrue(is_true(True))
        self.assertFalse(is_true(False))
        self.assertFalse(is_false(True))
        self.assertTrue(is_false(False))

    def test_is_none(self):
        self.assertTrue(is_none(None))
        self.assertFalse(is_none("something"))
        self.assertFalse(is_none(0))

    def test_is_in_and_is_not_in(self):
        my_list = [1, 2, 3, "a"]
        my_set = {1, 2, 3, "a"}
        my_tuple = (1, 2, 3, "a")

        for collection in [my_list, my_set, my_tuple]:
            p_in = is_in(collection)
            p_not_in = is_not_in(collection)

            self.assertTrue(p_in(1))
            self.assertTrue(p_in("a"))
            self.assertFalse(p_in(4))
            self.assertFalse(p_in("b"))

            self.assertFalse(p_not_in(1))
            self.assertFalse(p_not_in("a"))
            self.assertTrue(p_not_in(4))
            self.assertTrue(p_not_in("b"))

        self.assertFalse(is_in([])(1))
        self.assertTrue(is_not_in([])(1))

    def test_equals_and_not_equals(self):
        p_eq_5 = equals(5)
        p_neq_5 = not_equals(5)

        self.assertTrue(p_eq_5(5))
        self.assertFalse(p_eq_5(6))
        self.assertFalse(p_eq_5(None))

        self.assertFalse(p_neq_5(5))
        self.assertTrue(p_neq_5(6))
        self.assertTrue(p_neq_5(None))

        p_eq_none = equals(None)
        p_neq_none = not_equals(None)

        self.assertTrue(p_eq_none(None))
        self.assertFalse(p_eq_none(5))
        self.assertFalse(p_neq_none(None))
        self.assertTrue(p_neq_none(5))

    def test_is_blank_and_is_not_blank(self):
        # is_blank
        self.assertTrue(is_blank(None))
        self.assertTrue(is_blank(""))
        self.assertTrue(is_blank([]))
        self.assertTrue(is_blank({}))
        self.assertTrue(is_blank(MySized(0)))

        self.assertFalse(is_blank("text"))
        self.assertFalse(is_blank([1]))
        self.assertFalse(is_blank({"a": 1}))
        self.assertFalse(is_blank(MySized(1)))
        self.assertFalse(is_blank(MyNonSized()))  # Not None, Not Sized -> False
        self.assertFalse(
            is_blank(0)
        )  # Not None, Not Sized (int is not Sized in this context) -> False

        # is_not_blank
        self.assertFalse(is_not_blank(None))
        self.assertFalse(is_not_blank(""))
        self.assertFalse(is_not_blank([]))
        self.assertFalse(is_not_blank({}))
        self.assertFalse(is_not_blank(MySized(0)))

        self.assertTrue(is_not_blank("text"))
        self.assertTrue(is_not_blank([1]))
        self.assertTrue(is_not_blank({"a": 1}))
        self.assertTrue(is_not_blank(MySized(1)))
        self.assertTrue(is_not_blank(MyNonSized()))
        self.assertTrue(is_not_blank(0))

    def test_default_utility(self):
        default_to_zero = default(0)
        self.assertEqual(default_to_zero(None), 0)
        self.assertEqual(default_to_zero(5), 5)
        self.assertEqual(default_to_zero(0), 0)

        default_to_hello = default("hello")
        self.assertEqual(default_to_hello(None), "hello")
        self.assertEqual(default_to_hello("world"), "world")

    def test_contains(self):
        p_contains_test = contains("test")
        self.assertTrue(p_contains_test("this is a test string"))
        self.assertFalse(p_contains_test("no match here"))
        self.assertFalse(p_contains_test(None))

        p_contains_3 = contains(3)
        self.assertTrue(p_contains_3([1, 2, 3, 4]))
        self.assertFalse(p_contains_3([1, 2, 4, 5]))
        self.assertFalse(p_contains_3(None))
        p_contains_3 = contains("3")
        self.assertFalse(p_contains_3("1245"))  # 'in' for string means substring

    def test_str_predicates_case_sensitive(self):
        # str_contains
        self.assertTrue(str_contains("test")("testing"))
        self.assertFalse(str_contains("Test")("testing"))
        self.assertFalse(str_contains("test")(None))

        # str_starts_with
        self.assertTrue(str_starts_with("test")("testing"))
        self.assertFalse(str_starts_with("Test")("testing"))
        self.assertFalse(str_starts_with("test")(None))
        self.assertFalse(str_starts_with("long")("short"))

        # str_ends_with
        self.assertTrue(str_ends_with("ing")("testing"))
        self.assertFalse(str_ends_with("ING")("testing"))
        self.assertFalse(str_ends_with("ing")(None))
        self.assertFalse(str_ends_with("long")("short"))

    def test_str_predicates_ignore_case(self):
        # str_contains_ignore_case
        p_contains_test_ic = str_contains_ignore_case("Test")
        self.assertTrue(p_contains_test_ic("this is a testing string"))
        self.assertTrue(p_contains_test_ic("TESTING"))
        self.assertFalse(p_contains_test_ic("no match"))
        self.assertFalse(p_contains_test_ic(None))

        # str_starts_with_ignore_case
        p_starts_test_ic = str_starts_with_ignore_case("Test")
        self.assertTrue(p_starts_test_ic("Testing 123"))
        self.assertTrue(p_starts_test_ic("testing 123"))
        self.assertFalse(p_starts_test_ic(" TesTing"))  # Leading space
        self.assertFalse(p_starts_test_ic(None))

        # str_ends_with_ignore_case
        p_ends_test_ic = str_ends_with_ignore_case("Test")
        self.assertTrue(p_ends_test_ic("This is a Test"))
        self.assertTrue(p_ends_test_ic("This is a test"))
        self.assertFalse(p_ends_test_ic("Test this"))
        self.assertFalse(p_ends_test_ic(None))

        # equals_ignore_case
        p_eq_test_ic = equals_ignore_case("Test")
        self.assertTrue(p_eq_test_ic("test"))
        self.assertTrue(p_eq_test_ic("Test"))
        self.assertTrue(p_eq_test_ic("TEST"))
        self.assertFalse(p_eq_test_ic("Test1"))
        self.assertFalse(p_eq_test_ic(None))
        self.assertFalse(equals_ignore_case("Test")(None))  # Test with None directly
        self.assertFalse(equals_ignore_case("")(None))
        self.assertTrue(equals_ignore_case("")(""))

    def test_str_regex_predicates(self):
        # str_matches (re.match - from beginning)
        p_matches_digits = str_matches(r"\d+")
        self.assertTrue(p_matches_digits("123abc"))
        self.assertFalse(p_matches_digits("abc123"))
        self.assertFalse(p_matches_digits(None))
        self.assertFalse(p_matches_digits(""))  # Empty string does not match \d+

        # str_not_matches
        p_not_matches_digits = str_not_matches(r"\d+")
        self.assertFalse(p_not_matches_digits("123abc"))
        self.assertTrue(p_not_matches_digits("abc123"))
        self.assertTrue(
            p_not_matches_digits(None)
        )  # not (None matches) -> not (False) -> True

        # str_fullmatch (re.fullmatch - entire string)
        p_fullmatch_digits = str_fullmatch(r"\d+")
        self.assertTrue(p_fullmatch_digits("123"))
        self.assertFalse(p_fullmatch_digits("123abc"))
        self.assertFalse(p_fullmatch_digits("abc123"))
        self.assertFalse(p_fullmatch_digits(None))
        self.assertFalse(p_fullmatch_digits(""))
        self.assertTrue(str_fullmatch(r"")(""))  # Empty pattern matches empty string

    def test_str_length_predicates(self):
        s = "hello"  # len 5
        self.assertTrue(str_longer_than(4)(s))
        self.assertFalse(str_longer_than(5)(s))
        self.assertFalse(str_longer_than(4)(None))

        self.assertTrue(str_shorter_than(6)(s))
        self.assertFalse(str_shorter_than(5)(s))
        self.assertFalse(str_shorter_than(6)(None))

        self.assertTrue(str_longer_than_or_eq(5)(s))
        self.assertTrue(str_longer_than_or_eq(4)(s))
        self.assertFalse(str_longer_than_or_eq(6)(s))
        self.assertFalse(str_longer_than_or_eq(5)(None))

        self.assertTrue(str_shorter_than_or_eq(5)(s))
        self.assertTrue(str_shorter_than_or_eq(6)(s))
        self.assertFalse(str_shorter_than_or_eq(4)(s))
        self.assertFalse(str_shorter_than_or_eq(5)(None))

    def test_numeric_simple_predicates(self):
        self.assertTrue(is_even(2))
        self.assertFalse(is_even(3))
        self.assertTrue(is_even(0))
        self.assertTrue(is_even(-2))
        self.assertFalse(is_even(None))

        self.assertTrue(is_odd(3))
        self.assertFalse(is_odd(2))
        self.assertTrue(is_odd(-3))
        self.assertFalse(is_odd(None))

        self.assertTrue(is_positive(5.0))
        self.assertTrue(is_positive(0.1))
        self.assertFalse(is_positive(0.0))
        self.assertFalse(is_positive(-5.0))
        self.assertFalse(is_positive(None))

        self.assertTrue(is_negative(-5.0))
        self.assertTrue(is_negative(-0.1))
        self.assertFalse(is_negative(0.0))
        self.assertFalse(is_negative(5.0))
        self.assertFalse(is_negative(None))

        self.assertTrue(is_zero(0))
        self.assertTrue(is_zero(0.0))
        self.assertFalse(is_zero(0.001))
        self.assertFalse(is_zero(None))

        self.assertTrue(is_int(5.0))
        self.assertTrue(is_int(0.0))
        self.assertTrue(is_int(-3.0))
        self.assertFalse(is_int(5.1))
        self.assertFalse(is_int(None))

    def test_numeric_interval_predicates(self):
        # is_beween_closed / is_in_interval
        p_closed_1_5 = is_beween_closed(1.0, 5.0)  # Alias: is_in_interval
        self.assertTrue(p_closed_1_5(1.0))
        self.assertTrue(p_closed_1_5(3.0))
        self.assertTrue(p_closed_1_5(5.0))
        self.assertFalse(p_closed_1_5(0.9))
        self.assertFalse(p_closed_1_5(5.1))
        self.assertFalse(p_closed_1_5(None))
        self.assertTrue(is_in_interval(1.0, 5.0)(3.0))

        # is_beween / is_in_open_interval
        p_open_1_5 = is_beween(1.0, 5.0)  # Alias: is_in_open_interval
        self.assertFalse(p_open_1_5(1.0))
        self.assertTrue(p_open_1_5(3.0))
        self.assertFalse(p_open_1_5(5.0))
        self.assertFalse(p_open_1_5(0.9))
        self.assertFalse(p_open_1_5(5.1))
        self.assertFalse(p_open_1_5(None))
        self.assertTrue(is_in_open_interval(1.0, 5.0)(3.0))

        # is_beween_closed_start (start <= val < end)
        p_closed_start_1_5 = is_beween_closed_start(1.0, 5.0)
        self.assertTrue(p_closed_start_1_5(1.0))
        self.assertTrue(p_closed_start_1_5(4.9))
        self.assertFalse(p_closed_start_1_5(5.0))
        self.assertFalse(p_closed_start_1_5(0.9))
        self.assertFalse(p_closed_start_1_5(None))

        # is_beween_closed_end (start < val <= end)
        p_closed_end_1_5 = is_beween_closed_end(1.0, 5.0)
        self.assertFalse(p_closed_end_1_5(1.0))
        self.assertTrue(p_closed_end_1_5(1.1))
        self.assertTrue(p_closed_end_1_5(5.0))
        self.assertFalse(p_closed_end_1_5(5.1))
        self.assertFalse(p_closed_end_1_5(None))

    def test_numeric_comparison_predicates(self):
        self.assertTrue(is_higher_than(5.0)(6.0))
        self.assertFalse(is_higher_than(5.0)(5.0))
        self.assertFalse(is_higher_than(5.0)(None))

        self.assertTrue(is_higher_than_or_eq(5.0)(5.0))
        self.assertTrue(is_higher_than_or_eq(5.0)(6.0))
        self.assertFalse(is_higher_than_or_eq(5.0)(4.0))
        self.assertFalse(is_higher_than_or_eq(5.0)(None))

        self.assertTrue(is_less_than(5.0)(4.0))
        self.assertFalse(is_less_than(5.0)(5.0))
        self.assertFalse(is_less_than(5.0)(None))

        self.assertTrue(is_less_than_or_eq(5.0)(5.0))
        self.assertTrue(is_less_than_or_eq(5.0)(4.0))
        self.assertFalse(is_less_than_or_eq(5.0)(6.0))
        self.assertFalse(is_less_than_or_eq(5.0)(None))

    def test_higher_order_predicates(self):
        p_is_none = Predicate.of(is_none)
        p_not_is_none = not_(p_is_none)  # not_ can take Predicate or callable
        self.assertTrue(p_not_is_none("value"))
        self.assertFalse(p_not_is_none(None))

        p_not_is_none_direct = not_(is_none)  # Test with callable directly
        self.assertTrue(p_not_is_none_direct("value"))

        # not_strict
        p_gt0_strict = Predicate.of(lambda x: x > 0)  # Expects non-Optional T
        p_not_gt0_strict = not_strict(p_gt0_strict)
        self.assertTrue(p_not_gt0_strict(-5))
        self.assertFalse(p_not_gt0_strict(5))
        # Calling p_not_gt0_strict(None) would be a type error if type-checked,
        # and may or may not raise at runtime depending on the wrapped predicate.
        # Here, (lambda x: x > 0)(None) would raise TypeError.
        with self.assertRaises(TypeError):
            p_not_gt0_strict(None)

    def test_mapping_predicates(self):
        my_dict = {"a": 1, "b": 2, None: 3}
        empty_dict: Mapping[Any, Any] = {}

        # has_key
        p_has_key_a = has_key("a")
        self.assertTrue(p_has_key_a(my_dict))
        self.assertFalse(p_has_key_a(empty_dict))
        self.assertFalse(p_has_key_a(None))
        self.assertTrue(has_key(None)(my_dict))  # Test None as key

        # has_value
        p_has_value_1 = has_value(1)
        self.assertTrue(p_has_value_1(my_dict))
        self.assertFalse(p_has_value_1(empty_dict))
        self.assertFalse(p_has_value_1(None))
        self.assertFalse(has_value(4)(my_dict))

        # is_key_in
        p_is_key_in_my_dict = is_key_in(my_dict)
        self.assertTrue(p_is_key_in_my_dict("a"))
        self.assertFalse(p_is_key_in_my_dict("c"))
        self.assertTrue(p_is_key_in_my_dict(None))  # Test None as key

        # is_value_in
        p_is_value_in_my_dict = is_value_in(my_dict)
        self.assertTrue(p_is_value_in_my_dict(1))
        self.assertFalse(p_is_value_in_my_dict(4))

    def test_truthy_falsy_identity(self):
        self.assertTrue(is_truthy(1))
        self.assertTrue(is_truthy("text"))
        self.assertTrue(is_truthy([1]))
        self.assertFalse(is_truthy(0))
        self.assertFalse(is_truthy(""))
        self.assertFalse(is_truthy([]))
        self.assertFalse(is_truthy(None))

        self.assertFalse(is_falsy(1))
        self.assertTrue(is_falsy(0))
        self.assertTrue(is_falsy(None))

        obj1 = MyNonSized()
        obj2 = MyNonSized()
        p_is_obj1 = is_identity(obj1)
        self.assertTrue(p_is_obj1(obj1))
        self.assertFalse(p_is_obj1(obj2))
        self.assertFalse(p_is_obj1(None))
        self.assertTrue(is_identity(None)(None))

    def test_has_length(self):
        p_len_3 = has_length(3)
        self.assertTrue(p_len_3("abc"))
        self.assertTrue(p_len_3([1, 2, 3]))
        self.assertFalse(p_len_3("ab"))
        self.assertFalse(p_len_3(None))
        self.assertFalse(p_len_3(MySized(0)))  # has_length(3) applied to MySized(0)

    def test_is_instance(self):
        p_is_str = is_instance(str)
        self.assertTrue(p_is_str("hello"))
        self.assertFalse(p_is_str(123))
        self.assertFalse(p_is_str(None))

        p_is_parent = is_instance(ParentClass)
        self.assertTrue(p_is_parent(ParentClass()))
        self.assertTrue(p_is_parent(ChildClass()))  # Subclass is instance of parent

    def test_str_type_predicates(self):
        self.assertTrue(str_is_alpha("abc"))
        self.assertFalse(str_is_alpha("abc1"))
        self.assertFalse(str_is_alpha(None))

        self.assertTrue(str_is_digit("123"))
        self.assertFalse(str_is_digit("123a"))
        self.assertFalse(str_is_digit(None))

        self.assertTrue(str_is_alnum("abc123"))
        self.assertFalse(str_is_alnum("abc 123"))  # space is not alnum
        self.assertFalse(str_is_alnum(None))

        self.assertTrue(str_is_lower("abc"))
        self.assertFalse(str_is_lower("aBc"))
        self.assertTrue(str_is_lower("abc1"))  # non-cased chars are ignored
        self.assertFalse(str_is_lower(None))

        self.assertTrue(str_is_upper("ABC"))
        self.assertFalse(str_is_upper("ABc"))
        self.assertTrue(str_is_upper("ABC1"))
        self.assertFalse(str_is_upper(None))

        self.assertTrue(str_is_space("   \t\n"))
        self.assertFalse(str_is_space(" a "))
        self.assertFalse(str_is_space(None))
        self.assertFalse(str_is_space(""))  # Empty string is not all space

        self.assertTrue(str_is_title("This Is A Title String"))
        self.assertFalse(str_is_title("This is a title string"))
        self.assertFalse(str_is_title(None))
