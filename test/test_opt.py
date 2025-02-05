from typing import Optional
from baseTest import BaseTestCase
from jstreams import Opt
from jstreams.predicate import equals, isTrue, strLongerThan


class TestOpt(BaseTestCase):
    def test_opt_isPresent(self) -> None:
        """
        Test opt isPresent function
        """

        val: Optional[str] = None
        self.assertFalse(Opt(val).isPresent())

        val = "test"
        self.assertTrue(Opt(val).isPresent())

        self.assertFalse(Opt(None).isPresent())

    def test_opt_get(self) -> None:
        """
        Test opt get function
        """
        self.assertThrowsExceptionOfType(lambda: Opt(None).get(), ValueError)
        self.assertIsNotNone(Opt("str").get())
        self.assertEqual(Opt("str").get(), "str")

    def test_opt_getActual(self) -> None:
        """
        Test opt getActual function
        """
        self.assertIsNotNone(Opt("str").getActual())
        self.assertEqual(Opt("str").getActual(), "str")

    def test_opt_getActual_none(self) -> None:
        """
        Test opt getActual function
        """
        self.assertIsNone(Opt("str").filter(strLongerThan(4)).getActual())

    def test_opt_getOrElse(self) -> None:
        """
        Test opt getOrElse function
        """
        self.assertIsNotNone(Opt(None).getOrElse("str"))
        self.assertEqual(Opt(None).getOrElse("str"), "str")

        self.assertIsNotNone(Opt("test").getOrElse("str"))
        self.assertEqual(Opt("test").getOrElse("str"), "test")

    def test_opt_getOrElseGet(self) -> None:
        """
        Test opt getOrElseGet function
        """
        self.assertIsNotNone(Opt(None).getOrElseGet(lambda: "str"))
        self.assertEqual(Opt(None).getOrElseGet(lambda: "str"), "str")

        self.assertIsNotNone(Opt("test").getOrElseGet(lambda: "str"))
        self.assertEqual(Opt("test").getOrElseGet(lambda: "str"), "test")

    def test_opt_stream(self) -> None:
        """
        Test opt stream function
        """
        self.assertEqual(Opt("A").stream().toList(), ["A"])
        self.assertEqual(Opt(["A"]).stream().toList(), [["A"]])

    def test_opt_flatStream(self) -> None:
        """
        Test opt flatStream function
        """
        self.assertEqual(Opt("A").flatStream().toList(), ["A"])
        self.assertEqual(Opt(["A", "B", "C"]).flatStream().toList(), ["A", "B", "C"])

    def test_opt_orElseThrow(self) -> None:
        """
        Test opt orElseThrow function
        """
        self.assertThrowsExceptionOfType(lambda: Opt(None).orElseThrow(), ValueError)
        self.assertThrowsExceptionOfType(
            lambda: Opt(None).orElseThrowFrom(lambda: Exception("Test")), Exception
        )

    def __callback_test_if_matches(self, calledStr: str) -> None:
        self.test_if_matches_result = calledStr
    
    def test_if_matches(self) -> None:
        """
        Test opt ifMatches function
        """
        Opt("str").ifMatches(equals("str"), self.__callback_test_if_matches)
        self.assertEqual(self.test_if_matches_result, "str")
        
    def test_if_matches_map(self) -> None:
        """
        Test opt ifMatchesMap function
        """
        self.assertEqual(Opt(True).ifMatchesMap(isTrue, lambda _: "success").get(), "success")
        self.assertIsNone(Opt(False).ifMatchesMap(isTrue, lambda _: "success").getActual())