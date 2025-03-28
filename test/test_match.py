from typing import Optional
from baseTest import BaseTestCase
from jstreams import (
    is_none,
    is_not_none,
    case,
    default_case,
    match,
    match_opt,
    is_beween_closed,
    is_higher_than_or_eq,
    is_less_than,
)


class TestMatch(BaseTestCase):
    def test_match_simple(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            case(3, "test3"),
            case(5, "test5"),
        )
        self.assertEqual(val, "test5", "Value should be correct")

    def test_match_out_of_order(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            case(5, "test5"),
            case(3, "test3"),
        )
        self.assertEqual(val, "test5", "Value should be correct")

    def test_match_predicate(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            case(is_beween_closed(3, 6), "testBetween"),
            case(7, "test7"),
        )
        self.assertEqual(val, "testBetween", "Value should be correct")

    def test_match_predicate_supplier(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            case(is_beween_closed(3, 6), lambda: "testBetween"),
            case(7, "test7"),
        )
        self.assertEqual(val, "testBetween", "Value should be correct")

    def test_match_default_case(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            default_case("default"),
        )
        self.assertEqual(val, "default", "Value should be default")

    def test_match_predicates_suppliers(self) -> None:
        val = match(8).of(
            case(is_less_than(5), lambda: str(5)),
            case(is_higher_than_or_eq(5), lambda: str(5) + "H"),
        )
        self.assertEqual(val, "5H", "Value should be correctly mapped")

    def test_match_opt_none(self) -> None:
        v: Optional[str] = None
        val = match_opt(v).of(
            case(is_none, "None"),
            case(is_not_none, "Not none"),
        )
        self.assertEqual(val, "None", "Case should be isNone")

    def test_match_opt_not_none(self) -> None:
        v: Optional[str] = "str"
        val = match_opt(v).of(
            case(is_none, "None"),
            case(is_not_none, "Not none"),
        )
        self.assertEqual(val, "Not none", "Case should be isNotNone")
