from baseTest import BaseTestCase
from jstreams.state import defaultState, nullState, useState


class TestState(BaseTestCase):
    def test_use_state_simple(self) -> None:
        (getValue, setValue) = useState("test", "A")
        self.assertEqual(getValue(), "A", "State value should be A")
        setValue("B")
        self.assertEqual(getValue(), "B", "State value should be B")

    def __callback_test_use_state_with_on_change(self, value: str) -> None:
        self.callback_test_use_state_with_on_change = value

    def test_use_state_with_on_change(self) -> None:
        (getValue, setValue) = useState(
            "test2", "A", self.__callback_test_use_state_with_on_change
        )
        self.assertEqual(getValue(), "A", "State value should be A")
        setValue("B")
        self.assertEqual(getValue(), "B", "State value should be B")
        self.assertEqual(
            self.callback_test_use_state_with_on_change,
            "B",
            "Callback should have been called with the correct value",
        )

    def test_use_state_multiple(self) -> None:
        (getValue, setValue) = useState("test3", "A")
        (getValue1, setValue1) = useState("test3", "A")
        self.assertEqual(getValue(), "A", "State value should be A")
        self.assertEqual(getValue1(), "A", "State value should be A")
        setValue("B")
        self.assertEqual(getValue(), "B", "State value should be B")
        self.assertEqual(getValue1(), "B", "State value should be B")

    def test_use_state_none_default(self) -> None:
        (getValue, setValue) = useState("test3", defaultState(str))
        self.assertIsNone(getValue(), "State value should be None")
        setValue("Test")
        self.assertEqual(getValue(), "Test", "State value should be Test")

    def test_use_state_null_state(self) -> None:
        (getValue, setValue) = useState("test3", nullState(str))
        self.assertIsNone(getValue(), "State value should be None")
        setValue("Test")
        self.assertEqual(getValue(), "Test", "State value should be Test")
