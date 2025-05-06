from baseTest import BaseTestCase
from jstreams.state import default_state, null_state, use_state
from jstreams.utils import Value


class TestState(BaseTestCase):
    def test_use_state_simple(self) -> None:
        (getValue, setValue) = use_state("test", "A")
        self.assertEqual(getValue(), "A", "State value should be A")
        setValue("B")
        self.assertEqual(getValue(), "B", "State value should be B")

    def test_use_state_with_on_change(self) -> None:
        val = Value(None)
        old_val = Value(None)

        def callback_test_use_state_with_on_change(value: str, oldValue: str) -> None:
            val.set(value)
            old_val.set(oldValue)

        (getValue, setValue) = use_state(
            "test2", "A", callback_test_use_state_with_on_change
        )
        self.assertEqual(getValue(), "A", "State value should be A")
        setValue("B")
        self.assertEqual(getValue(), "B", "State value should be B")
        self.assertEqual(
            val.get(),
            "B",
            "Callback should have been called with the correct new value",
        )
        self.assertEqual(
            old_val.get(),
            "A",
            "Callback should have been called with the correct old value",
        )

    def test_use_state_multiple(self) -> None:
        (getValue, setValue) = use_state("test3", "A")
        (getValue1, setValue1) = use_state("test3", "A")
        self.assertEqual(getValue(), "A", "State value should be A")
        self.assertEqual(getValue1(), "A", "State value should be A")
        setValue("B")
        self.assertEqual(getValue(), "B", "State value should be B")
        self.assertEqual(getValue1(), "B", "State value should be B")

    def test_use_state_none_default(self) -> None:
        (getValue, setValue) = use_state("test4", default_state(str))
        self.assertIsNone(getValue(), "State value should be None")
        setValue("Test")
        self.assertEqual(getValue(), "Test", "State value should be Test")

    def test_use_state_null_state(self) -> None:
        (getValue, setValue) = use_state("test5", null_state(str))
        self.assertIsNone(getValue(), "State value should be None")
        setValue("Test")
        self.assertEqual(getValue(), "Test", "State value should be Test")
