from typing import Any
from baseTest import BaseTestCase
from jstreams.tryOpt import Try


class CallRegister:
    def __init__(self):
        self.mth1Called = False
        self.mth2Called = False
        self.mth3Called = False
        self.mth4Called = False
        self.errorLogged = False

    def mth1(self, e: Any) -> None:
        self.mth1Called = True

    def mth2(self, e: Any) -> None:
        self.mth2Called = True

    def mth3(self, e: Any) -> None:
        self.mth3Called = True

    def mth4(self, e: Any) -> None:
        self.mth4Called = True

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
            Try(self.noThrow).andThen(mock.mth1).andThen(mock.mth2).get().get(),
            "str",
        )
        self.assertTrue(mock.mth1Called)
        self.assertTrue(mock.mth2Called)

    def test_try_with_error_on_initial(self) -> None:
        mock = CallRegister()
        self.assertIsNone(Try(self.throw).andThen(mock.mth1).get().getActual())
        self.assertFalse(mock.mth1Called)

    def test_try_with_error_on_chain(self) -> None:
        self.assertIsNone(
            Try(self.noThrow).andThen(self.processThrow).get().getActual()
        )

    def test_try_with_error_on_init_and_onFailure(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.throw).andThen(mock.mth1).onFailure(mock.mth2).get().getActual()
        )
        self.assertFalse(mock.mth1Called)
        self.assertTrue(mock.mth2Called)

    def test_try_with_error_on_chain_and_onFailure(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.noThrow)
            .andThen(self.processThrow)
            .onFailure(mock.mth1)
            .get()
            .getActual()
        )
        self.assertTrue(mock.mth1Called)

    def test_try_with_error_on_chain_and_onFailureLog(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.noThrow)
            .andThen(self.processThrow)
            .onFailureLog("Test", mock)
            .get()
            .getActual()
        )
        self.assertTrue(mock.errorLogged)
