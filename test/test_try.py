from typing import Any
from baseTest import BaseTestCase
from jstreams import Try
from jstreams.utils import Value


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
        self.assertIsNone(Try(self.throw).mute().and_then(mock.mth1).get().get_actual())
        self.assertFalse(mock.mth1Called)

    def test_try_with_error_on_chain(self) -> None:
        self.assertIsNone(
            Try(self.noThrow).mute().and_then(self.processThrow).get().get_actual()
        )

    def test_try_with_error_on_init_and_onFailure(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.throw)
            .mute()
            .and_then(mock.mth1)
            .on_failure(mock.mth2)
            .get()
            .get_actual()
        )
        self.assertFalse(mock.mth1Called)
        self.assertTrue(mock.mth2Called)

    def test_try_with_error_on_init_and_onFailure_raise(self) -> None:
        mock = CallRegister()
        self.assertThrowsExceptionOfType(
            Try(self.throw)
            .mute()
            .and_then(mock.mth1)
            .on_failure(mock.mth2)
            .on_failure_raise(lambda: ValueError("Test"))
            .get,
            ValueError,
            "Test",
        )
        self.assertFalse(mock.mth1Called)
        self.assertTrue(mock.mth2Called)

    def test_try_with_error_on_chain_and_onFailure(self) -> None:
        mock = CallRegister()
        self.assertIsNone(
            Try(self.noThrow)
            .mute()
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
            .mute()
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
            .mute()
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

    def test_try_recovery(self) -> None:
        self.assertEqual(
            Try(self.throw).mute().recover(lambda e: "Test").get().get(), "Test"
        )

    def test_try_recover_from(self) -> None:
        self.assertEqual(
            Try(self.throw)
            .mute()
            .recover_from(ValueError, lambda _: "Test1")
            .recover(lambda e: "Test")
            .get()
            .get(),
            "Test1",
        )

    def test_try_recover_from_default(self) -> None:
        self.assertEqual(
            Try(self.throw)
            .mute()
            .recover_from(RuntimeError, lambda _: "Test1")
            .recover(lambda e: "Test")
            .get()
            .get(),
            "Test",
        )

    def test_try_logger(self) -> None:
        class MockLogger:
            def __init__(self):
                self.error_called = False
                self.error_message = None

            def error(self, msg, *args, **kwargs):
                self.error_called = True
                self.error_message = msg

        mockLogger = MockLogger()
        Try(self.throw).with_logger(mockLogger).with_error_message("Test").get()
        self.assertTrue(mockLogger.error_called)
        self.assertEqual(mockLogger.error_message, "Test")

    def test_try_with_retries(self) -> None:
        class Mock:
            def __init__(self, tries: int):
                self.tries = tries
                self.current_try = 1
                self.error = None

            def do(self) -> None:
                if self.current_try < self.tries:
                    self.current_try += 1
                    raise ValueError("Test")
                return "TestValue"

            def register_error(self, e: Exception) -> None:
                self.error = e

        mock = Mock(3)

        self.assertEqual(
            Try(mock.do).retry(2, 0.1).on_failure(mock.register_error).get().get(),
            "TestValue",
        )
        self.assertEqual(mock.current_try, 3)
        self.assertIsNone(mock.error)

    def test_try_with_retries_error(self) -> None:
        class Mock:
            def __init__(self, tries: int):
                self.tries = tries
                self.current_try = 0
                self.error = None

            def do(self) -> None:
                self.current_try += 1
                raise ValueError("Test")

            def register_error(self, e: Exception) -> None:
                self.error = e

        mock = Mock(3)

        self.assertIsNone(
            Try(mock.do)
            .mute()
            .retry(2, 0.1)
            .on_failure(mock.register_error)
            .get()
            .get_actual(),
        )
        self.assertEqual(mock.current_try, 3)
        self.assertIsInstance(mock.error, ValueError)
        self.assertEqual(str(mock.error), "Test")

    def test_try_with_resource(self) -> None:
        path = "/tmp/test_file"
        val = Value(None)
        Try.with_resource(lambda: open(path, "w")).and_then(
            lambda f: f.write("Test")
        ).get()
        Try.with_resource(lambda: open(path, "r")).and_then(
            lambda f: val.set(f.read())
        ).get()
        self.assertEqual(val.get(), "Test")

    def test_try_with_resource_controlled(self) -> None:
        class FakeResource:
            def __init__(self):
                self.enter_called = False
                self.exit_called = False

            def __enter__(self):
                self.enter_called = True
                return self

            def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
                self.exit_called = True

        res = FakeResource()
        Try.with_resource(lambda: res).get()
        self.assertTrue(res.enter_called)
        self.assertTrue(res.exit_called)

    def test_try_with_resource_controlled_exception(self) -> None:
        class FakeResource:
            def __init__(self):
                self.enter_called = False
                self.exit_called = False

            def __enter__(self):
                self.enter_called = True
                return self

            def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
                self.exit_called = True

        res = FakeResource()
        Try.with_resource(lambda: res).mute().and_then(lambda _: self.throw()).get()
        self.assertTrue(res.enter_called)
        self.assertTrue(res.exit_called)
