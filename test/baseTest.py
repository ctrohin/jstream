from typing import Any, Callable, Optional
import unittest

from jstreams.ioc import injector


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        injector().clear()

    def assertThrowsException(
        self, fn: Callable[[], Any], message: Optional[str] = None
    ) -> None:
        exThrown = False
        try:
            fn()
        except Exception:
            exThrown = True

        self.assertTrue(exThrown, message)

    def assertThrowsExceptionOfType(
        self, fn: Callable[[], Any], exType: type, message: Optional[str] = None
    ) -> None:
        exThrown = False
        try:
            fn()
        except Exception as e:
            exThrown = isinstance(e, exType)

        self.assertTrue(exThrown, message)
