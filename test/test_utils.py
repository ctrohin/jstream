from baseTest import BaseTestCase
from jstreams.predicate import allNotNone, default, equals, isBlank, isIn, isNotIn
from jstreams.stream import Stream
from jstreams.utils import isNumber, requireNotNull

class TestHelpers(BaseTestCase):

    def test_requireNotNull(self) -> None:
        """
        Test requireNotNull function
        """
        self.assertEqual(requireNotNull("str"), "str")
        self.assertThrowsExceptionOfType(lambda: requireNotNull(None), ValueError)

    def test_allSatisty(self) -> None:
        """
        Test allSatisfy function
        """
        self.assertFalse(Stream(["A", "B"]).allMatch(lambda e: e is None))
        self.assertFalse(Stream(["A", None]).allMatch(lambda e: e is None))
        self.assertTrue(Stream([None, None]).allMatch(lambda e: e is None))

    def test_areSame(self) -> None:
        """
        Test areSame function
        """
        self.assertTrue(equals([1])([1]), "Int array should be the same")
        self.assertTrue(equals(["str"])(["str"]), "String array should be the same")
        self.assertFalse(equals([1])([2]), "Int array should not be the same")
        self.assertTrue(equals({"a": "b"})({"a": "b"}), "Dict should be the same")
        self.assertTrue(equals({"a": "b", "c": "d"})({"a": "b", "c": "d"}), "Dict should be the same")
        self.assertTrue(equals({"a": "b", "c": "d"})({"c": "d", "a": "b"}), "Dict should be the same")
        self.assertFalse(equals({"a": "b"})({"a": "b1"}), "Dict should not be the same")

    def test_allNotNone(self) -> None:
        self.assertTrue(allNotNone(["A", "B", "C"]), "All should not be none")
        self.assertFalse(allNotNone(["A", "B", None]), "One should contain none")

    def test_isIn(self) -> None:
        self.assertTrue(isIn(["A", "B", "C"])("A"), "A should be in array")
        self.assertFalse(isIn(["A", "B", "C"])("D"), "D should not be in array")

    def test_isNotIn(self) -> None:
        self.assertFalse(isNotIn(["A", "B", "C"])("A"), "A should be in array")
        self.assertTrue(isNotIn(["A", "B", "C"])("D"), "D should not be in array")

    def test_isBlank(self) -> None:
        self.assertFalse(isBlank(["A", "B", "C"]), "Array should not be blank")
        self.assertTrue(isBlank([]), "Array should be blank")
        self.assertTrue(isBlank(None), "Object should be blank")
        self.assertTrue(isBlank(""), "Object should be blank")
        self.assertTrue(isBlank({}), "Dict should be blank")
        self.assertFalse(isBlank("Test"), "String should not be blank")
        self.assertFalse(isBlank({"a": "b"}), "Dict should not be blank")

    def test_defVal(self) -> None:
        self.assertEqual(default("str")(None), "str", "Default value should be applied")
        self.assertEqual(default("str")("str1"), "str1", "Given value should be applied")


    def test_isNumber(self) -> None:
        self.assertTrue(isNumber(10), "10 should be a number")
        self.assertTrue(isNumber(0), "0 should be a number")
        self.assertTrue(isNumber(0.5), "0.5 should be a number")
        self.assertTrue(isNumber("10"), "10 string should be a number")
        self.assertFalse(isNumber(None), "None should not be a number")
