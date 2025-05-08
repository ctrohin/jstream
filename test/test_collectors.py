from typing import Any, Callable, Generator

from baseTest import BaseTestCase
from jstreams.collectors import grouping_by, grouping_by_mapping, joining, Collectors
from jstreams.stream import Opt


class TestCollectors(BaseTestCase):
    def test_grouping_by_standalone(self):
        # Test with an empty iterable
        self.assertEqual(grouping_by(lambda x: x, []), {})

        # Test grouping numbers by parity
        data_nums = [1, 2, 3, 4, 5, 6]
        expected_nums = {1: [1, 3, 5], 0: [2, 4, 6]}
        self.assertEqual(grouping_by(lambda x: x % 2, data_nums), expected_nums)

        # Test grouping strings by first letter
        data_strs = ["apple", "banana", "apricot", "blueberry", "cherry"]
        expected_strs = {
            "a": ["apple", "apricot"],
            "b": ["banana", "blueberry"],
            "c": ["cherry"],
        }
        result_strs = grouping_by(lambda s: s[0], data_strs)
        # Sort lists for consistent comparison as order within groups is preserved
        for key in result_strs:
            result_strs[key].sort()
        for key in expected_strs:
            expected_strs[key].sort()
        self.assertEqual(result_strs, expected_strs)

        # Test with a generator
        def num_gen() -> Generator[int, None, None]:
            yield 1
            yield 2
            yield 3

        self.assertEqual(grouping_by(lambda x: x % 2, num_gen()), {1: [1, 3], 0: [2]})

    def test_grouping_by_mapping_standalone(self):
        # Test with an empty iterable
        self.assertEqual(grouping_by_mapping(lambda x: x, [], lambda x: x * 2), {})

        # Test grouping numbers by parity and mapping to their squares
        data_nums = [1, 2, 3, 4]
        expected_nums = {1: [1, 9], 0: [4, 16]}  # 1*1, 3*3 and 2*2, 4*4
        self.assertEqual(
            grouping_by_mapping(lambda x: x % 2, data_nums, lambda x: x * x),
            expected_nums,
        )

        # Test grouping strings by first letter and mapping to uppercase
        data_strs = ["apple", "banana", "apricot"]
        expected_strs = {"a": ["APPLE", "APRICOT"], "b": ["BANANA"]}
        result_strs = grouping_by_mapping(lambda s: s[0], data_strs, str.upper)
        for key in result_strs:
            result_strs[key].sort()
        for key in expected_strs:
            expected_strs[key].sort()
        self.assertEqual(result_strs, expected_strs)

    def test_joining_standalone(self):
        # Test with an empty iterable
        self.assertEqual(joining(",", []), "")

        # Test with a single element
        self.assertEqual(joining(",", ["hello"]), "hello")

        # Test with multiple elements and a separator
        self.assertEqual(joining("-", ["a", "b", "c"]), "a-b-c")

        # Test with an empty string separator
        self.assertEqual(joining("", ["a", "b", "c"]), "abc")

        # Test with a generator
        def str_gen() -> Generator[str, None, None]:
            yield "x"
            yield "y"

        self.assertEqual(joining("|", str_gen()), "x|y")

    def test_collectors_to_list(self):
        collector = Collectors.to_list()
        self.assertEqual(collector([]), [])
        self.assertEqual(collector([1, 2, 3]), [1, 2, 3])
        self.assertEqual(collector(iter([1, 2, 3])), [1, 2, 3])

    def test_collectors_to_set(self):
        collector = Collectors.to_set()
        self.assertEqual(collector([]), set())
        self.assertEqual(collector([1, 2, 2, 3]), {1, 2, 3})
        self.assertEqual(collector(iter([1, 2, 2, 3])), {1, 2, 3})

    def test_collectors_grouping_by(self):
        collector = Collectors.grouping_by(lambda x: x % 2)
        self.assertEqual(collector([1, 2, 3, 4]), {1: [1, 3], 0: [2, 4]})
        self.assertEqual(collector([]), {})

    def test_collectors_grouping_by_mapping(self):
        collector = Collectors.grouping_by_mapping(lambda x: x % 2, lambda x: x * 10)
        self.assertEqual(collector([1, 2, 3, 4]), {1: [10, 30], 0: [20, 40]})
        self.assertEqual(collector([]), {})

    def test_collectors_joining(self):
        collector_default = Collectors.joining()
        collector_custom = Collectors.joining("-")

        self.assertEqual(collector_default(["a", "b", "c"]), "abc")
        self.assertEqual(collector_default([]), "")
        self.assertEqual(collector_custom(["a", "b", "c"]), "a-b-c")
        self.assertEqual(collector_custom([]), "")
        self.assertEqual(collector_custom(["a"]), "a")

    def test_collectors_partitioning_by(self):
        collector = Collectors.partitioning_by(lambda x: x > 2)
        self.assertEqual(collector([1, 2, 3, 4, 5]), {False: [1, 2], True: [3, 4, 5]})
        self.assertEqual(collector([1, 2]), {False: [1, 2]})
        self.assertEqual(collector([3, 4]), {True: [3, 4]})
        self.assertEqual(collector([]), {})

    def test_collectors_partitioning_by_mapping(self):
        collector = Collectors.partitioning_by_mapping(
            lambda x: x > 2, lambda x: x * 10
        )
        self.assertEqual(
            collector([1, 2, 3, 4, 5]), {False: [10, 20], True: [30, 40, 50]}
        )
        self.assertEqual(collector([1, 2]), {False: [10, 20]})
        self.assertEqual(collector([3, 4]), {True: [30, 40]})
        self.assertEqual(collector([]), {})

    def test_collectors_counting(self):
        collector = Collectors.counting()
        self.assertEqual(collector([]), 0)
        self.assertEqual(collector([1, 2, 3]), 3)
        self.assertEqual(collector(iter([1, "a", None, 4.5])), 4)

    def test_collectors_summing_int(self):
        collector = Collectors.summing_int()
        self.assertEqual(collector([]), 0)
        self.assertEqual(collector([1, 2, 3]), 6)
        self.assertEqual(collector([-1, 0, 1, 5]), 5)

    def test_collectors_averaging_float(self):
        collector = Collectors.averaging_float()
        self.assertIsNone(collector([]))
        self.assertEqual(collector([1.0, 2.0, 3.0]), 2.0)
        self.assertEqual(collector([10.0]), 10.0)
        self.assertEqual(collector([1.5, 2.5, 3.5]), 2.5)
        self.assertEqual(collector([-1.0, 1.0]), 0.0)

    def test_collectors_max_by(self):
        # Comparator for numbers: standard difference
        num_comparator: Callable[[int, int], int] = lambda a, b: a - b
        collector_num = Collectors.max_by(num_comparator)

        self.assertEqual(collector_num([]), Opt(None))
        self.assertEqual(collector_num([1, 5, 2, 8, 3]), Opt(8))
        self.assertEqual(collector_num([-1, -5, -2]), Opt(-1))
        self.assertEqual(collector_num([5]), Opt(5))

        # Comparator for strings by length
        str_len_comparator: Callable[[str, str], int] = lambda a, b: len(a) - len(b)
        collector_str_len = Collectors.max_by(str_len_comparator)

        self.assertEqual(collector_str_len([]), Opt(None))
        self.assertEqual(collector_str_len(["a", "bbb", "cc", "ddddd"]), Opt("ddddd"))
        self.assertEqual(
            collector_str_len(["apple", "fig", "elderberry"]), Opt("elderberry")
        )
        # Test tie-breaking (max usually returns the first one encountered in a tie)
        # This depends on Python's max behavior with a key.
        # For `cmp_to_key`, if lengths are equal, comparator returns 0.
        # `max` behavior for equal keys is to return the first one.
        self.assertEqual(collector_str_len(["long", "word", "same"]), Opt("long"))

    def test_collectors_min_by(self):
        # Comparator for numbers: standard difference
        num_comparator: Callable[[int, int], int] = lambda a, b: a - b
        collector_num = Collectors.min_by(num_comparator)

        self.assertEqual(collector_num([]), Opt(None))
        self.assertEqual(collector_num([1, 5, 0, 8, 3]), Opt(0))
        self.assertEqual(collector_num([-1, -5, -2]), Opt(-5))
        self.assertEqual(collector_num([5]), Opt(5))

        # Comparator for strings by length
        str_len_comparator: Callable[[str, str], int] = lambda a, b: len(a) - len(b)
        collector_str_len = Collectors.min_by(str_len_comparator)

        self.assertEqual(collector_str_len([]), Opt(None))
        self.assertEqual(collector_str_len(["apple", "fig", "kiwi"]), Opt("fig"))
        # Test tie-breaking (min usually returns the first one encountered in a tie)
        self.assertEqual(
            collector_str_len(["short", "tiny", "word"]), Opt("tiny")
        )  # "tiny" and "word" have same length

    def test_collectors_to_tuple(self):
        collector = Collectors.to_tuple()
        self.assertEqual(collector([]), ())
        self.assertEqual(collector([1, 2, 3]), (1, 2, 3))
        self.assertEqual(collector(iter([1, 2, 3])), (1, 2, 3))

    def test_collectors_summing_float(self):
        collector = Collectors.summing_float()
        self.assertEqual(collector([]), 0.0)
        self.assertEqual(collector([1.0, 2.5, 3.0]), 6.5)
        self.assertEqual(collector([-1.0, 0.0, 1.0, 5.5]), 5.5)

    def test_collectors_averaging_int(self):
        collector = Collectors.averaging_int()
        self.assertIsNone(collector([]))
        self.assertEqual(collector([1, 2, 3]), 2.0)
        self.assertEqual(collector([10]), 10.0)
        self.assertEqual(collector([1, 2]), 1.5)
        self.assertEqual(collector([-1, 0, 1]), 0.0)

    # Additional tests for edge cases or specific behaviors

    def test_grouping_by_standalone_custom_keys(self):
        class MyKey:
            def __init__(self, val):
                self.val = val

            def __hash__(self):
                return hash(self.val)

            def __eq__(self, other):
                return isinstance(other, MyKey) and self.val == other.val

        data = [("a", 10), ("b", 20), ("a", 30)]
        # Group by MyKey(item[0])
        result = grouping_by(lambda item: MyKey(item[0]), data)

        # Expected keys are MyKey('a') and MyKey('b')
        key_a = MyKey("a")
        key_b = MyKey("b")

        self.assertIn(key_a, result)
        self.assertIn(key_b, result)
        self.assertEqual(result[key_a], [("a", 10), ("a", 30)])
        self.assertEqual(result[key_b], [("b", 20)])

    def test_grouping_by_mapping_standalone_output_types(self):
        # Group by int, map to string length
        data = [(1, "hello"), (2, "hi"), (1, "world")]
        result = grouping_by_mapping(
            lambda item: item[0], data, lambda item: len(item[1])
        )
        expected = {
            1: [5, 5],  # len("hello"), len("world")
            2: [2],  # len("hi")
        }
        self.assertEqual(result, expected)

    def test_collectors_partitioning_by_empty_groups(self):
        # All true
        collector_all_true = Collectors.partitioning_by(lambda x: x > 0)
        self.assertEqual(collector_all_true([1, 2, 3]), {True: [1, 2, 3]})

        # All false
        collector_all_false = Collectors.partitioning_by(lambda x: x < 0)
        self.assertEqual(collector_all_false([1, 2, 3]), {False: [1, 2, 3]})

    def test_collectors_averaging_float_single_element(self):
        collector = Collectors.averaging_float()
        self.assertEqual(collector([5.5]), 5.5)

    def test_collectors_averaging_int_single_element(self):
        collector = Collectors.averaging_int()
        self.assertEqual(collector([7]), 7.0)

    def test_collectors_max_by_with_generator(self):
        num_comparator: Callable[[int, int], int] = lambda a, b: a - b
        collector_num = Collectors.max_by(num_comparator)

        def gen_nums():
            yield 1
            yield 5
            yield 2

        self.assertEqual(collector_num(gen_nums()), Opt(5))

    def test_collectors_min_by_with_generator(self):
        num_comparator: Callable[[int, int], int] = lambda a, b: a - b
        collector_num = Collectors.min_by(num_comparator)

        def gen_nums():
            yield 10
            yield 5
            yield 12

        self.assertEqual(collector_num(gen_nums()), Opt(5))

    def test_collectors_summing_int_empty_generator(self):
        collector = Collectors.summing_int()

        def empty_gen() -> Generator[int, None, None]:
            if False:  # Never yields
                yield 0

        self.assertEqual(collector(empty_gen()), 0)

    def test_collectors_summing_float_empty_generator(self):
        collector = Collectors.summing_float()

        def empty_gen() -> Generator[float, None, None]:
            if False:  # Never yields
                yield 0.0

        self.assertEqual(collector(empty_gen()), 0.0)

    def test_collectors_counting_empty_generator(self):
        collector = Collectors.counting()

        def empty_gen() -> Generator[Any, None, None]:
            if False:  # Never yields
                yield 0

        self.assertEqual(collector(empty_gen()), 0)
