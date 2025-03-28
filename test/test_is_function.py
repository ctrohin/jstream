from baseTest import BaseTestCase
from jstreams import is_callable


class _Class:
    pass


def fn_test() -> None:
    pass


class TestIsCallable(BaseTestCase):
    def fn(self) -> None:
        pass

    def fn1(self, strArg: str) -> bool:
        return False

    def test_is_function(self) -> None:
        self.assertTrue(is_callable(fn_test), "Should be a function")
        self.assertTrue(is_callable(self.fn), "Should be a method")
        self.assertTrue(is_callable(self.fn1), "Should be a method")
        val = "Test"
        self.assertFalse(is_callable(val), "Should not be a function or method")
        obj = _Class()
        self.assertFalse(is_callable(obj), "Should not be a function or method")
