from baseTest import BaseTestCase
from jstreams.noop import noop


class TestNoop(BaseTestCase):
    def test_method_calls(self) -> None:
        obj = noop()
        self.assertEqual(obj.get_something(), obj)
        self.assertEqual(obj._get_something(), obj)

    def test_member_calls(self) -> None:
        obj = noop()
        self.assertEqual(obj.something, obj)
        self.assertEqual(obj._something, obj)

    def test_levels_calls(self) -> None:
        obj = noop()
        self.assertEqual(obj.something.get_something(), obj)
        self.assertEqual(obj.something.get_something().test, obj)
        self.assertEqual(obj.get_something().something, obj)
        self.assertEqual(obj.get_something().get_something(), obj)
