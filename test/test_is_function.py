from baseTest import BaseTestCase
from jstreams import is_mth_or_fn


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
        self.assertTrue(is_mth_or_fn(fn_test), "Should be a function")
        self.assertTrue(is_mth_or_fn(self.fn), "Should be a method")
        self.assertTrue(is_mth_or_fn(self.fn1), "Should be a method")
        val = "Test"
        self.assertFalse(is_mth_or_fn(val), "Should not be a function or method")
        obj = _Class()
        self.assertFalse(is_mth_or_fn(obj), "Should not be a function or method")
