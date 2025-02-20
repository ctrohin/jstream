from baseTest import BaseTestCase
from jstreams import (
    stream,
    Not,
    equalsIgnoreCase,
    strContains,
    isNotNone,
    mapperOf,
    optional,
    predicateOf,
    reducerOf,
    toFloat,
)
from jstreams.predicate import hasKey, hasValue, isKeyIn, isValueIn
from jstreams.utils import identity


class TestPredicate(BaseTestCase):
    def test_predicate_and(self) -> None:
        expected = "Test"
        predicate = predicateOf(isNotNone).And(equalsIgnoreCase("Test"))
        self.assertEqual(
            optional("Test").filter(predicate).get(),
            expected,
            "Expected value should be correct",
        )

    def test_predicate_and2(self) -> None:
        expected = "test value"
        predicate = predicateOf(strContains("test")).And(strContains("value"))
        self.assertEqual(
            optional(expected).filter(predicate).get(),
            expected,
            "Expected value should be correct",
        )

    def test_predicate_and3(self) -> None:
        predicate = predicateOf(strContains("test")).And(Not(strContains("value")))
        self.assertListEqual(
            stream(["test value", "test other", "some value"])
            .filter(predicate)
            .toList(),
            ["test other"],
            "Expected value should be correct",
        )

    def test_predicate_or(self) -> None:
        predicate = predicateOf(strContains("es")).Or(equalsIgnoreCase("Other"))
        self.assertListEqual(
            stream(["Test", "Fest", "other", "Son", "Father"])
            .filter(predicate)
            .toList(),
            ["Test", "Fest", "other"],
            "Expected value should be correct",
        )

    def test_predicate_call(self) -> None:
        predicate = predicateOf(strContains("es"))
        self.assertTrue(
            predicate("test"),
            "Predicate should be callable and return the proper value",
        )

        self.assertTrue(
            predicate.Apply("test"),
            "Predicate should be callable via Apply and return the proper value",
        )
        self.assertFalse(
            predicate("nomatch"),
            "Predicate should be callable and return the proper value",
        )
        self.assertFalse(
            predicate.Apply("nomatch"),
            "Predicate should be callable via Apply and return the proper value",
        )

    def test_mapper_call(self) -> None:
        mapper = mapperOf(toFloat)
        self.assertEqual(
            mapper("1.2"), 1.2, "Mapper should be callable and return the proper value"
        )
        self.assertEqual(
            mapper.Map("1.2"),
            1.2,
            "Mapper should be callable via Map and return the proper value",
        )

    def test_reducer_call(self) -> None:
        reducer = reducerOf(max)
        self.assertEqual(
            reducer(1, 2), 2, "Reducer should be callable and return the proper value"
        )
        self.assertEqual(
            reducer.Reduce(1, 2),
            2,
            "Reducer should be callable via Reduce and return the proper value",
        )

    def test_dict_keys_values(self) -> None:
        dct = {"test": "A"}
        self.assertTrue(hasKey("test")(dct), "Dict should contain key")
        self.assertTrue(hasValue("A")(dct), "Dict should contain value")
        self.assertFalse(hasKey("other")(dct), "Dict should not contain key")
        self.assertFalse(hasValue("B")(dct), "Dict should not contain value")
        self.assertTrue(isKeyIn(dct)("test"), "Dict should contain key")
        self.assertTrue(isValueIn(dct)("A"), "Dict should contain value")
        self.assertFalse(isKeyIn(dct)("other"), "Dict should not contain key")
        self.assertFalse(isValueIn(dct)("B"), "Dict should not contain value")

    def test_identity(self) -> None:
        initial = ["1", "2"]
        self.assertListEqual(
            stream(initial).map(identity).toList(),
            initial,
            "Lists should match after identity mapping",
        )
