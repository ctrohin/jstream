from typing import Any
from baseTest import BaseTestCase
from jstreams import Try


class CallRegister:
    def __init__(self):
        self.mth1Called = False
        self.mth2Called = False
        self.mth3Called = False
        self.mth4Called = False
        self.mth5Called = False
        self.mth6Called = False
        self.errorLogged = False

    def mth1(self, e: Any) -> None:
        self.mth1Called = True

    def mth2(self, e: Any) -> None:
        self.mth2Called = True

    def mth3(self, e: Any) -> None:
        self.mth3Called = True

    def mth4(self, e: Any) -> None:
        self.mth4Called = True

    def mth5(self, e: Any) -> None:
        self.mth5Called = True

    def mth6(self, e: Any) -> None:
        self.mth6Called = True

    def error(self, msg, *args, **kwargs):
        self.errorLogged = True


class TestTry(BaseTestCase):
    def noThrow(self) -> str:
        return "str"

    def throw(self) -> str:
        raise ValueError("Test")

    def processThrow(self, e: str) -> None:
        raise ValueError("Test")

    def test_try(self) -> None:
        mock = CallRegister()
        self.assertEqual(
            Try(self.noThrow).and_then(mock.mth1).and_then(mock.mth2).get().get(),
            "str",
        )
        self.assertTrue(mock.mth1Called)
        self.assertTrue(mock.mth2Called)

    def test_try_with_error_on_initial(self) -> None:
        mock = CallRegister()
        self.assertIsNone(Try(self.throw).and_then(mock.mth1).get().get_actual())
        self.assertFalse(mock.mth1Called)

    def test_try_with_error_on_chain(self) -> None:
        self.assertIsNone(
            Try(self.noThrow).and_then(self.processThrow).get().get_actual()
        )

    def test_try_with_error_on_init_and_onFailure(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.throw).and_then(mock.mth1).on_failure(mock.mth2).get().get_actual()
        )
        self.assertFalse(mock.mth1Called)
        self.assertTrue(mock.mth2Called)

    def test_try_with_error_on_chain_and_onFailure(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.noThrow)
            .and_then(self.processThrow)
            .on_failure(mock.mth1)
            .get()
            .get_actual()
        )
        self.assertTrue(mock.mth1Called)

    def test_try_with_error_on_chain_and_onFailureLog(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.noThrow)
            .and_then(self.processThrow)
            .on_failure_log("Test", mock)
            .get()
            .get_actual()
        )
        self.assertTrue(mock.errorLogged)

    def test_try_with_error_multiple_on_fail_and_finally(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.throw)
            .on_failure(mock.mth1)
            .on_failure(mock.mth2)
            .and_finally(mock.mth3)
            .and_finally(mock.mth4)
            .get()
            .get_actual()
        )
        self.assertTrue(mock.mth1Called)
        self.assertTrue(mock.mth2Called)
        self.assertTrue(mock.mth3Called)
        self.assertTrue(mock.mth4Called)

    def test_try_with_no_error_multiple_on_fail_and_finally(self) -> None:
        mock = CallRegister()
        self.assertIsNotNone(
            Try(self.noThrow)
            .on_failure(mock.mth1)
            .on_failure(mock.mth2)
            .and_then(mock.mth3)
            .and_finally(mock.mth4)
            .and_finally(mock.mth5)
            .get()
            .get_actual()
        )
        self.assertFalse(mock.mth1Called)
        self.assertFalse(mock.mth2Called)
        self.assertTrue(mock.mth3Called)
        self.assertTrue(mock.mth4Called)
        self.assertTrue(mock.mth5Called)
