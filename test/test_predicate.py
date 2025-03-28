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
from jstreams.predicate import has_key, has_value, is_key_in, is_value_in
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
