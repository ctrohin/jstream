from baseTest import BaseTestCase
from jstreams import isNone, isNotNone, not_
from jstreams.stream import predicateOf


class TestNot(BaseTestCase):
    def test_not_fn(self) -> None:
        self.assertFalse(
            not_(isNone)(None), "Not isNone applied to None should be False"
        )
        self.assertTrue(
            not_(isNotNone)(None), "Not isNotNone applied to None should be True"
        )

    def test_not_predicate(self) -> None:
        self.assertFalse(
            not_(predicateOf(isNone))(None),
            "Not isNone applied to None should be False",
        )
        self.assertTrue(
            not_(predicateOf(isNotNone))(None),
            "Not isNotNone applied to None should be True",
        )
