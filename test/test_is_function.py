from baseTest import BaseTestCase
from jstreams import isCallable


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
        self.assertTrue(isCallable(fn_test), "Should be a function")
        self.assertTrue(isCallable(self.fn), "Should be a method")
        self.assertTrue(isCallable(self.fn1), "Should be a method")
        val = "Test"
        self.assertFalse(isCallable(val), "Should not be a function or method")
        obj = _Class()
        self.assertFalse(isCallable(obj), "Should not be a function or method")
