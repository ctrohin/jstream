from baseTest import BaseTestCase
from jstreams import stream
from jstreams.predicate import Not, equalsIgnoreCase, strContains
from jstreams.stream import isNotNone, optional, predicateOf


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
