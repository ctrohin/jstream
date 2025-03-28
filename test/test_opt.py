from typing import Optional
from baseTest import BaseTestCase
from jstreams import Opt, equals, is_true, str_longer_than


class TestOpt(BaseTestCase):
    def test_opt_isPresent(self) -> None:
        """
        Test opt isPresent function
        """

        val: Optional[str] = None
        self.assertFalse(Opt(val).is_present())

        val = "test"
        self.assertTrue(Opt(val).is_present())

        self.assertFalse(Opt(None).is_present())

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
        self.assertIsNotNone(Opt("str").get_actual())
        self.assertEqual(Opt("str").get_actual(), "str")

    def test_opt_getActual_none(self) -> None:
        """
        Test opt getActual function
        """
        self.assertIsNone(Opt("str").filter(str_longer_than(4)).get_actual())

    def test_opt_getOrElse(self) -> None:
        """
        Test opt getOrElse function
        """
        self.assertIsNotNone(Opt(None).or_else("str"))
        self.assertEqual(Opt(None).or_else("str"), "str")

        self.assertIsNotNone(Opt("test").or_else("str"))
        self.assertEqual(Opt("test").or_else("str"), "test")

    def test_opt_getOrElseGet(self) -> None:
        """
        Test opt getOrElseGet function
        """
        self.assertIsNotNone(Opt(None).or_else_get(lambda: "str"))
        self.assertEqual(Opt(None).or_else_get(lambda: "str"), "str")

        self.assertIsNotNone(Opt("test").or_else_get(lambda: "str"))
        self.assertEqual(Opt("test").or_else_get(lambda: "str"), "test")

    def test_opt_stream(self) -> None:
        """
        Test opt stream function
        """
        self.assertEqual(Opt("A").stream().to_list(), ["A"])
        self.assertEqual(Opt(["A"]).stream().to_list(), [["A"]])

    def test_opt_flatStream(self) -> None:
        """
        Test opt flatStream function
        """
        self.assertEqual(Opt("A").flat_stream().to_list(), ["A"])
        self.assertEqual(Opt(["A", "B", "C"]).flat_stream().to_list(), ["A", "B", "C"])

    def test_opt_orElseThrow(self) -> None:
        """
        Test opt orElseThrow function
        """
        self.assertThrowsExceptionOfType(lambda: Opt(None).or_else_raise(), ValueError)
        self.assertThrowsExceptionOfType(
            lambda: Opt(None).or_else_raise_from(lambda: Exception("Test")), Exception
        )

    def __callback_test_if_matches(self, calledStr: str) -> None:
        self.test_if_matches_result = calledStr

    def test_if_matches(self) -> None:
        """
        Test opt ifMatches function
        """
        Opt("str").if_matches(equals("str"), self.__callback_test_if_matches)
        self.assertEqual(self.test_if_matches_result, "str")

    def test_if_matches_map(self) -> None:
        """
        Test opt ifMatchesMap function
        """
        self.assertEqual(
            Opt(True).if_matches_map(is_true, lambda _: "success").get(), "success"
        )
        self.assertIsNone(
            Opt(False).if_matches_map(is_true, lambda _: "success").get_actual()
        )
