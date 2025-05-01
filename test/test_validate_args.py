from typing import Optional, Union, Any, List

from jstreams.annotations import default_on_error, validate_args
from baseTest import BaseTestCase
from jstreams.predicate import is_higher_than


# --- Test Functions ---
# Define these globally or within the class if preferred, but global is simpler here.


@validate_args()
def basic_types(name: str, age: int) -> str:
    return f"{name} is {age}"


@validate_args()
def optional_type(value: Optional[int]) -> str:
    return f"Value: {value}"


@validate_args()
def union_type(value: Union[str, float]) -> str:
    return f"Value: {value}"


@validate_args()
def union_with_none(value: Union[str, None]) -> str:
    return f"Value: {value}"


@validate_args()
def any_type(value: Any) -> str:
    return f"Any value: {value}"


@validate_args()
def no_hint(value) -> str:
    return f"No hint value: {value}"


@validate_args()
def default_arg(name: str, count: int = 0) -> str:
    return f"{name} count: {count}"


@validate_args()
def list_hint(items: list) -> int:
    return len(items)


@validate_args()
def list_specific_hint(items: List[int]) -> int:
    # Note: validate_args only checks isinstance(items, list), not contents
    return len(items)


class ForwardRefClass:
    pass


@validate_args()
def forward_ref_hint(obj: "ForwardRefClass") -> str:
    return "Got ForwardRefClass"


class TestOnMethod:
    @validate_args()
    def concat_str(self, a: int, b: str) -> str:
        return str(a) + b

    @validate_args({"b": is_higher_than(0)})
    def divide(self, a: float, b: float) -> float:
        return a / b

    @default_on_error(-1.0, [TypeError])
    @validate_args({"b": is_higher_than(0)})
    def divide_with_default(self, a: float, b: float) -> float:
        return a / b


# --- Test Class ---


class TestValidateArgs(BaseTestCase):
    def test_basic_types_valid(self):
        self.assertEqual(basic_types("Alice", 30), "Alice is 30")
        self.assertEqual(basic_types(name="Bob", age=40), "Bob is 40")

    def test_basic_types_invalid(self):
        with self.assertRaisesRegex(
            TypeError, "Argument 'name'.*expected type <class 'str'>, but got int"
        ):
            basic_types(123, 30)  # type: ignore
        with self.assertRaisesRegex(
            TypeError, "Argument 'age'.*expected type <class 'int'>, but got str"
        ):
            basic_types("Alice", "thirty")  # type: ignore
        # Test missing argument (error comes from signature binding)
        with self.assertRaisesRegex(TypeError, "missing a required argument: 'age'"):
            basic_types("Alice")  # type: ignore

    def test_optional_type_valid(self):
        self.assertEqual(optional_type(10), "Value: 10")
        self.assertEqual(optional_type(None), "Value: None")
        self.assertEqual(optional_type(value=20), "Value: 20")
        self.assertEqual(optional_type(value=None), "Value: None")

    def test_optional_type_invalid(self):
        with self.assertRaisesRegex(
            TypeError,
            "Argument 'value'.*expected type typing.Optional\\[int\\].*but got str",
        ):
            optional_type("hello")  # type: ignore

    def test_union_type_valid(self):
        self.assertEqual(union_type("hello"), "Value: hello")
        self.assertEqual(union_type(3.14), "Value: 3.14")

    def test_union_type_invalid(self):
        with self.assertRaisesRegex(
            TypeError,
            "Argument 'value'.*expected type typing.Union\\[str, float\\].*but got int",
        ):
            union_type(123)  # type: ignore

    def test_union_with_none_valid(self):
        self.assertEqual(union_with_none("hello"), "Value: hello")
        self.assertEqual(union_with_none(None), "Value: None")

    def test_union_with_none_invalid(self):
        self.assertRaises(TypeError, lambda: union_with_none(123))  # type: ignore

    def test_any_type_valid(self):
        self.assertEqual(any_type(123), "Any value: 123")
        self.assertEqual(any_type("string"), "Any value: string")
        self.assertEqual(any_type(None), "Any value: None")
        self.assertEqual(any_type([1, 2]), "Any value: [1, 2]")

    def test_no_hint_valid(self):
        self.assertEqual(no_hint(123), "No hint value: 123")
        self.assertEqual(no_hint("string"), "No hint value: string")
        self.assertEqual(no_hint(None), "No hint value: None")

    def test_default_arg_valid(self):
        self.assertEqual(default_arg("Test"), "Test count: 0")  # Uses default
        self.assertEqual(default_arg("Test", 5), "Test count: 5")

    def test_default_arg_invalid(self):
        with self.assertRaisesRegex(
            TypeError, "Argument 'count'.*expected type <class 'int'>, but got str"
        ):
            default_arg("Test", "five")  # type: ignore

    def test_list_hint_valid(self):
        self.assertEqual(list_hint([1, 2, 3]), 3)
        self.assertEqual(list_hint([]), 0)

    def test_list_hint_invalid(self):
        with self.assertRaisesRegex(
            TypeError, "Argument 'items'.*expected type <class 'list'>, but got str"
        ):
            list_hint("not a list")  # type: ignore

    def test_list_specific_hint_valid(self):
        # validate_args only checks the outer type (list), not the inner type (int)
        self.assertEqual(list_specific_hint([1, 2, 3]), 3)
        self.assertEqual(list_specific_hint(["a", "b"]), 2)  # Passes validation

    def test_list_specific_hint_invalid(self):
        with self.assertRaisesRegex(
            TypeError,
            "Argument 'items'.*expected type typing.List\\[int\\].*but got tuple",
        ):
            list_specific_hint((1, 2))  # type: ignore

    def test_forward_ref_valid(self):
        instance = ForwardRefClass()
        self.assertEqual(forward_ref_hint(instance), "Got ForwardRefClass")

    def test_forward_ref_invalid(self):
        with self.assertRaisesRegex(
            TypeError, "Argument 'obj'.*expected type .*ForwardRefClass.*but got str"
        ):
            forward_ref_hint("not the right class")  # type: ignore

    def test_on_method(self) -> None:
        t = TestOnMethod()
        self.assertEqual(t.concat_str(123, "abc"), "123abc")
        self.assertRaises(TypeError, lambda: t.concat_str("abc", 123))

    def test_on_method_rules(self) -> None:
        t = TestOnMethod()
        self.assertEqual(t.divide(1.0, 1.0), 1)
        self.assertRaises(TypeError, lambda: t.divide(1.0, 0.0))
        self.assertEqual(t.divide_with_default(1.0, 0.0), -1)
