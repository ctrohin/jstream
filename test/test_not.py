from baseTest import BaseTestCase
from jstreams import is_none, is_not_none, not_, predicate_of


class TestNot(BaseTestCase):
    def test_not_fn(self) -> None:
        self.assertFalse(
            not_(is_none)(None), "Not isNone applied to None should be False"
        )
        self.assertTrue(
            not_(is_not_none)(None), "Not isNotNone applied to None should be True"
        )

    def test_not_predicate(self) -> None:
        self.assertFalse(
            not_(predicate_of(is_none))(None),
            "Not isNone applied to None should be False",
        )
        self.assertTrue(
            not_(predicate_of(is_not_none))(None),
            "Not isNotNone applied to None should be True",
        )
