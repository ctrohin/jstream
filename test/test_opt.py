from typing import Optional
from baseTest import BaseTestCase
from jstreams import Opt, equals, is_true, str_longer_than
from jstreams.utils import Value


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

    def test_if_matches(self) -> None:
        """
        Test opt ifMatches function
        """
        val = Value(None)
        Opt("str").if_matches(equals("str"), val.set)
        self.assertEqual(val.get(), "str")

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

    def test_flat_map(self) -> None:
        """
        Test opt flat_map function
        """
        self.assertEqual(
            Opt(True).map(lambda v: Opt(v)).flat_map(lambda v: v).get(), True
        )

    def test_opt_empty_factory(self) -> None:
        empty_opt1 = Opt.empty()
        empty_opt2 = Opt.empty()
        self.assertTrue(empty_opt1.is_empty())
        self.assertIs(
            empty_opt1, empty_opt2, "Opt.empty() should return a cached instance"
        )

    def test_opt_when_factory(self) -> None:
        self.assertEqual(
            Opt.when(True, "value").get_actual(), Opt("value").get_actual()
        )
        self.assertIsNone(Opt.when(False, "value").get_actual())
        self.assertTrue(Opt.when(False, "value").is_empty())

    def test_opt_when_supplied_factory(self) -> None:
        supplier_called = False

        def supplier() -> str:
            nonlocal supplier_called
            supplier_called = True
            return "supplied_value"

        # Condition is True
        opt1 = Opt.when_supplied(True, supplier)
        self.assertEqual(opt1.get_actual(), "supplied_value")
        self.assertTrue(
            supplier_called, "Supplier should be called when condition is True"
        )

        # Reset and test False condition
        supplier_called = False
        opt2 = Opt.when_supplied(False, supplier)
        self.assertIsNone(opt2.get_actual())
        self.assertTrue(opt2.is_empty())
        self.assertFalse(
            supplier_called, "Supplier should not be called when condition is False"
        )

    def test_opt_try_or_empty_factory(self) -> None:
        def successful_call() -> str:
            return "success"

        def raises_value_error() -> str:
            raise ValueError("Test error")

        def raises_type_error() -> str:
            raise TypeError("Another error")

        # Successful call
        self.assertEqual(Opt.try_or_empty(successful_call).get_actual(), "success")

        # Catches specified exception (ValueError)
        self.assertIsNone(Opt.try_or_empty(raises_value_error, ValueError).get_actual())
        self.assertTrue(Opt.try_or_empty(raises_value_error, ValueError).is_empty())

        # Does not catch unspecified exception if others are specified
        with self.assertRaises(TypeError):
            Opt.try_or_empty(raises_type_error, ValueError)

        # Catches default Exception if no specific exceptions are provided
        self.assertEqual(Opt.try_or_empty(raises_value_error), Opt.empty())
        self.assertEqual(Opt.try_or_empty(raises_type_error), Opt.empty())

        # Catches multiple specified exceptions
        self.assertEqual(
            Opt.try_or_empty(raises_value_error, ValueError, TypeError), Opt.empty()
        )
        self.assertEqual(
            Opt.try_or_empty(raises_type_error, ValueError, TypeError), Opt.empty()
        )

    def test_opt_first_present_factory(self) -> None:
        opt_a = Opt("a")
        opt_b = Opt("b")
        empty1 = Opt.empty()
        empty2 = Opt.empty()

        self.assertEqual(Opt.first_present(empty1, opt_a, opt_b), opt_a)
        self.assertEqual(Opt.first_present(opt_a, empty1, opt_b), opt_a)
        self.assertEqual(Opt.first_present(empty1, empty2, opt_b), opt_b)
        self.assertEqual(Opt.first_present(empty1, empty2), Opt.empty())
        self.assertTrue(Opt.first_present(empty1, empty2).is_empty())
        self.assertEqual(Opt.first_present(), Opt.empty())
        self.assertEqual(Opt.first_present(opt_a), opt_a)

    def test_or_else_raise(self) -> None:
        self.assertEqual(Opt("value").or_else_raise(), "value")
        self.assertRaises(ValueError, lambda: Opt(None).or_else_raise())
        self.assertRaises(
            RuntimeError,
            lambda: Opt(None).or_else_raise_from(lambda: RuntimeError("Test error")),
        )

    def test_if_present_or_else(self) -> None:
        present_action_called = False
        empty_action_called = False

        def present_action(val: str) -> None:
            nonlocal present_action_called
            present_action_called = True
            self.assertEqual(val, "value")

        def empty_action() -> None:
            nonlocal empty_action_called
            empty_action_called = True

        Opt("value").if_present_or_else(present_action, empty_action)
        self.assertTrue(present_action_called)
        self.assertFalse(empty_action_called)

        present_action_called = False  # Reset
        Opt.empty().if_present_or_else(present_action, empty_action)
        self.assertFalse(present_action_called)
        self.assertTrue(empty_action_called)

    def test_or_else_opt(self) -> None:
        self.assertEqual(Opt("value").or_else_opt("other"), "value")
        self.assertEqual(Opt.empty().or_else_opt("other"), "other")
        self.assertIsNone(
            Opt.empty().or_else_opt(None),
        )

    def test_or_else_get_opt(self) -> None:
        supplier_called = False

        def supplier() -> Optional[str]:
            nonlocal supplier_called
            supplier_called = True
            return "supplied_opt"

        self.assertEqual(Opt("value").or_else_get_opt(supplier), "value")
        self.assertFalse(supplier_called)

        self.assertEqual(Opt.empty().or_else_get_opt(supplier), "supplied_opt")
        self.assertTrue(supplier_called)

        supplier_called = False  # Reset

        def empty_supplier() -> Optional[str]:
            nonlocal supplier_called
            supplier_called = True
            return None

        self.assertIsNone(Opt.empty().or_else_get_opt(empty_supplier))
        self.assertTrue(supplier_called)
