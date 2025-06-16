import unittest
from jstreams import pipe, partial, curry, get_number_of_arguments
from baseTest import BaseTestCase
from typing import Any


# --- Helper functions for testing ---
def add(x: int, y: int) -> int:
    return x + y


def multiply(x: int, y: int) -> int:
    return x * y


def power(base: float, exp: float) -> float:
    return base**exp


def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"


def sum_all(*args: int) -> int:
    return sum(args)


def describe_person(name: str, age: int, *hobbies: str, **details: Any) -> dict:
    return {"name": name, "age": age, "hobbies": hobbies, "details": details}


def identity_func(x: Any) -> Any:
    return x


def str_to_int(s: str) -> int:
    return int(s)


def int_to_bool(i: int) -> bool:
    return i > 0


class TestFuncUtilities(BaseTestCase):
    # --- Tests for pipe ---
    def test_pipe_two_functions(self):
        add_one = lambda x: x + 1
        multiply_by_two = lambda x: x * 2
        composed_func = pipe(add_one, multiply_by_two)
        self.assertEqual(composed_func(5), 12)  # (5+1)*2 = 12

    def test_pipe_multiple_functions(self):
        add_one = lambda x: x + 1
        multiply_by_two = lambda x: x * 2
        subtract_three = lambda x: x - 3
        composed_func = pipe(add_one, multiply_by_two, subtract_three)
        self.assertEqual(composed_func(5), 9)  # ((5+1)*2)-3 = 9

    def test_pipe_type_change(self):
        to_str = lambda x: str(x)
        append_text = lambda x: x + " apples"
        composed_func = pipe(to_str, append_text)
        self.assertEqual(composed_func(5), "5 apples")

    def test_pipe_single_function(self):
        multiply_by_ten = lambda x: x * 10
        composed_func = pipe(multiply_by_ten)
        self.assertEqual(composed_func(5), 50)

    def test_pipe_with_exception(self):
        divide_by_zero = lambda x: x / 0
        add_one = lambda x: x + 1
        composed_func = pipe(identity_func, divide_by_zero, add_one)
        with self.assertRaises(ZeroDivisionError):
            composed_func(5)

    def test_pipe_with_none_return(self):
        return_none = lambda x: None
        process_none = lambda x: f"Processed: {x}"
        composed_func = pipe(return_none, process_none)
        self.assertEqual(composed_func(5), "Processed: None")

    def test_pipe_complex_chain(self):
        f1 = lambda x: x * 2  # 10
        f2 = lambda x: str(x)  # "10"
        f3 = lambda x: x + "0"  # "100"
        f4 = lambda x: int(x)  # 100
        f5 = lambda x: x / 5  # 20.0
        composed = pipe(f1, f2, f3, f4, f5)
        self.assertEqual(composed(5), 20.0)

    # --- Tests for partial ---
    def test_partial_one_arg(self):
        add_10 = partial(add, 10)
        self.assertEqual(add_10(5), 15)
        self.assertEqual(add_10(y=20), 30)  # add(10, y=20)

    def test_partial_multiple_args(self):
        # describe_person(name: str, age: int, *hobbies: str, **details: Any)
        partial_alice = partial(describe_person, "Alice", 30)
        result = partial_alice("reading", "coding", city="New York", employed=True)
        expected = {
            "name": "Alice",
            "age": 30,
            "hobbies": ("reading", "coding"),
            "details": {"city": "New York", "employed": True},
        }
        self.assertEqual(result, expected)

    def test_partial_all_args_prefilled(self):
        add_10_and_5 = partial(add, 10, 5)
        self.assertEqual(add_10_and_5(), 15)
        with self.assertRaises(
            TypeError
        ):  # add() takes 2 positional arguments but 3 were given (10, 5, then another if passed)
            add_10_and_5(1)  # This would be add(10, 5, 1)

    def test_partial_with_kwargs_in_call(self):
        greet_bob = partial(greet, "Bob")
        self.assertEqual(
            greet_bob(greeting="Hola"), "Hola, Bob!"
        )  # Overrides default "Hello"
        self.assertEqual(greet_bob(), "Hello, Bob!")  # Uses default "Hello"

    def test_partial_with_default_args(self):
        # greet(name: str, greeting: str = "Hello")
        partial_greet_alice = partial(greet, "Alice")
        self.assertEqual(
            partial_greet_alice(), "Hello, Alice!"
        )  # Uses default greeting

    def test_partial_with_star_args_and_kwargs(self):
        # describe_person(name, age, *hobbies, **details)
        partial_bob = partial(describe_person, "Bob", 25, "skiing")
        result = partial_bob("coding", country="USA", sport="Snowboarding")
        # "skiing" is from partial, "coding" from call.
        # "sport" in details will be "Snowboarding"
        expected = {
            "name": "Bob",
            "age": 25,
            "hobbies": ("skiing", "coding"),
            "details": {"country": "USA", "sport": "Snowboarding"},
        }
        self.assertEqual(result, expected)

        partial_charlie = partial(describe_person, "Charlie", 22)
        result2 = partial_charlie("music", sport="football")
        expected2 = {
            "name": "Charlie",
            "age": 22,
            "hobbies": ("music",),
            "details": {"sport": "football"},
        }
        self.assertEqual(result2, expected2)

    # --- Tests for curry ---
    def test_curry_basic_three_args(self):
        add3 = lambda x, y, z: x + y + z
        curried_add3 = curry(add3)
        self.assertEqual(curried_add3(1)(2)(3), 6)

    def test_curry_one_arg_func(self):
        double = lambda x: x * 2
        curried_double = curry(double)  # n will be 1
        self.assertEqual(curried_double(5), 10)
        # Ensure it's the same function or equivalent
        self.assertEqual(curry(double).__code__, double.__code__)

    def test_curry_zero_arg_func(self):
        get_42 = lambda: 42
        curried_get_42 = curry(get_42)  # n will be 0
        self.assertEqual(curried_get_42(), 42)
        self.assertEqual(curry(get_42).__code__, get_42.__code__)

    def test_curry_with_default_args(self):
        # greet(name: str, greeting: str = "Hello")
        # get_number_of_arguments(greet) is 2
        curried_greet = curry(greet)
        greet_dev = curried_greet("Dev")
        self.assertEqual(greet_dev(), "Hello, Dev!")  # Calls greet("Dev")
        self.assertEqual(greet_dev("Hi"), "Hi, Dev!")  # Calls greet("Dev", "Hi")

    def test_curry_with_keyword_only_args_limitation(self):
        def f_kw_only(*, x):
            return x

        # get_number_of_arguments(f_kw_only) is 1
        curried_f = curry(f_kw_only)
        # curry(f_kw_only) returns f_kw_only because n=1
        # Calling curried_f(1) is like f_kw_only(1), which is a TypeError
        with self.assertRaises(TypeError):
            curried_f(1)
        self.assertEqual(curried_f(x=10), 10)  # Calling the original way

        def f_pos_then_kw_only(a, *, b):
            return a + b

        # get_number_of_arguments is 2
        curried_f_pk = curry(f_pos_then_kw_only)
        call_with_a = curried_f_pk(1)  # This is partial(f_pos_then_kw_only, 1)
        # Now calling call_with_a(2) would be partial(f_pos_then_kw_only, 1)(2)
        # which is f_pos_then_kw_only(1, 2) -> TypeError because b is keyword-only
        with self.assertRaises(TypeError):
            call_with_a(2)
        self.assertEqual(call_with_a(b=5), 6)  # f_pos_then_kw_only(1, b=5)

    # --- Tests for get_number_of_arguments (more direct) ---
    def test_get_number_of_arguments(self):
        def f0():
            pass

        def f1(a):
            pass

        def f2(a, b):
            pass

        def f3(a, b, c=0):
            pass

        def f_starargs(a, *args):
            pass

        def f_kwargs(a, **kwargs):
            pass

        def f_kwonly(a, *, b):
            pass

        def f_all(a, b=1, *args, c=2, **kwargs):
            pass

        self.assertEqual(get_number_of_arguments(f0), 0)
        self.assertEqual(get_number_of_arguments(f1), 1)
        self.assertEqual(get_number_of_arguments(f2), 2)
        self.assertEqual(get_number_of_arguments(f3), 3)
        self.assertEqual(get_number_of_arguments(f_starargs), 2)  # a, *args
        self.assertEqual(get_number_of_arguments(f_kwargs), 2)  # a, **kwargs
        self.assertEqual(get_number_of_arguments(f_kwonly), 2)  # a, b
        self.assertEqual(get_number_of_arguments(f_all), 5)  # a, b, *args, c, **kwargs

        self.assertEqual(get_number_of_arguments(lambda: 0), 0)
        self.assertEqual(get_number_of_arguments(lambda x, y: x + y), 2)

        # Test caching (indirectly by calling twice)
        self.assertEqual(get_number_of_arguments(f_all), 5)


if __name__ == "__main__":
    unittest.main()
