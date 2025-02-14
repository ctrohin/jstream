from typing import Optional
from baseTest import BaseTestCase
from jstreams import (
    isNone,
    isNotNone,
    case,
    defaultCase,
    match,
    matchOpt,
    isBeweenClosed,
    isHigherThanOrEqual,
    isLessThan,
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
            case(isBeweenClosed(3, 6), "testBetween"),
            case(7, "test7"),
        )
        self.assertEqual(val, "testBetween", "Value should be correct")

    def test_match_predicate_supplier(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            case(isBeweenClosed(3, 6), lambda: "testBetween"),
            case(7, "test7"),
        )
        self.assertEqual(val, "testBetween", "Value should be correct")

    def test_match_default_case(self) -> None:
        val = match(5).of(
            case(1, "test1"),
            case(2, "test2"),
            defaultCase("default"),
        )
        self.assertEqual(val, "default", "Value should be default")

    def test_match_predicates_suppliers(self) -> None:
        val = match(8).of(
            case(isLessThan(5), lambda: str(5)),
            case(isHigherThanOrEqual(5), lambda: str(5) + "H"),
        )
        self.assertEqual(val, "5H", "Value should be correctly mapped")

    def test_match_opt_none(self) -> None:
        v: Optional[str] = None
        val = matchOpt(v).of(
            case(isNone, "None"),
            case(isNotNone, "Not none"),
        )
        self.assertEqual(val, "None", "Case should be isNone")

    def test_match_opt_not_none(self) -> None:
        v: Optional[str] = "str"
        val = matchOpt(v).of(
            case(isNone, "None"),
            case(isNotNone, "Not none"),
        )
        self.assertEqual(val, "Not none", "Case should be isNotNone")
