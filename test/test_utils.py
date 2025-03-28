from baseTest import BaseTestCase
from jstreams import (
    all_not_none,
    default,
    equals,
    is_blank,
    is_in,
    is_not_in,
    Stream,
    is_number,
    require_non_null,
)


class TestHelpers(BaseTestCase):
    def test_requireNotNull(self) -> None:
        """
        Test requireNotNull function
        """
        self.assertEqual(require_non_null("str"), "str")
        self.assertThrowsExceptionOfType(lambda: require_non_null(None), ValueError)

    def test_allSatisty(self) -> None:
        """
        Test allSatisfy function
        """
        self.assertFalse(Stream(["A", "B"]).all_match(lambda e: e is None))
        self.assertFalse(Stream(["A", None]).all_match(lambda e: e is None))
        self.assertTrue(Stream([None, None]).all_match(lambda e: e is None))

    def test_areSame(self) -> None:
        """
        Test areSame function
        """
        self.assertTrue(equals([1])([1]), "Int array should be the same")
        self.assertTrue(equals(["str"])(["str"]), "String array should be the same")
        self.assertFalse(equals([1])([2]), "Int array should not be the same")
        self.assertTrue(equals({"a": "b"})({"a": "b"}), "Dict should be the same")
        self.assertTrue(
            equals({"a": "b", "c": "d"})({"a": "b", "c": "d"}),
            "Dict should be the same",
        )
        self.assertTrue(
            equals({"a": "b", "c": "d"})({"c": "d", "a": "b"}),
            "Dict should be the same",
        )
        self.assertFalse(equals({"a": "b"})({"a": "b1"}), "Dict should not be the same")

    def test_allNotNone(self) -> None:
        self.assertTrue(all_not_none(["A", "B", "C"]), "All should not be none")
        self.assertFalse(all_not_none(["A", "B", None]), "One should contain none")

    def test_isIn(self) -> None:
        self.assertTrue(is_in(["A", "B", "C"])("A"), "A should be in array")
        self.assertFalse(is_in(["A", "B", "C"])("D"), "D should not be in array")

    def test_isNotIn(self) -> None:
        self.assertFalse(is_not_in(["A", "B", "C"])("A"), "A should be in array")
        self.assertTrue(is_not_in(["A", "B", "C"])("D"), "D should not be in array")

    def test_isBlank(self) -> None:
        self.assertFalse(is_blank(["A", "B", "C"]), "Array should not be blank")
        self.assertTrue(is_blank([]), "Array should be blank")
        self.assertTrue(is_blank(None), "Object should be blank")
        self.assertTrue(is_blank(""), "Object should be blank")
        self.assertTrue(is_blank({}), "Dict should be blank")
        self.assertFalse(is_blank("Test"), "String should not be blank")
        self.assertFalse(is_blank({"a": "b"}), "Dict should not be blank")

    def test_defVal(self) -> None:
        self.assertEqual(default("str")(None), "str", "Default value should be applied")
        self.assertEqual(
            default("str")("str1"), "str1", "Given value should be applied"
        )

    def test_isNumber(self) -> None:
        self.assertTrue(is_number(10), "10 should be a number")
        self.assertTrue(is_number(0), "0 should be a number")
        self.assertTrue(is_number(0.5), "0.5 should be a number")
        self.assertTrue(is_number("10"), "10 string should be a number")
        self.assertFalse(is_number(None), "None should not be a number")
