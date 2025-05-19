import json
from baseTest import BaseTestCase
from jstreams import (
    all_not_none,
    default,
    equals,
    is_blank,
    is_in,
    is_not_in,
    Stream,
    is_number,
    require_non_null,
)
from jstreams.utils import (
    Value,
    as_list,
    cmp_to_key,
    dict_update,
    each,
    extract,
    identity,
    is_empty_or_none,
    is_mth_or_fn,
    is_not_none,
    keys_as_list,
    load_json,
    load_json_ex,
    sort,
    to_float,
    to_int,
    chunk,
    flatten,
    flatten_deep,
    uniq,
    key_by,
    pick,
    omit,
    head,
    tail,
    last,
    initial,  # Added initial as it was in the utils.py diff
)


class SampleClass:
    class_var = "class_variable"

    def __init__(self, instance_var_val):
        self.instance_var = instance_var_val
        self._private_var = "private"

    def instance_method(self):
        return "instance_method_called"

    @staticmethod
    def static_method_func():
        return "static_method_called"

    @classmethod
    def class_method_func(cls):
        return f"class_method_called_on_{cls.__name__}"


def sample_function():
    return "sample_function_called"


lambda_function = lambda x: x * 2


class TestHelpers(BaseTestCase):
    def test_requireNotNull(self) -> None:
        """
        Test requireNotNull function
        """
        self.assertEqual(require_non_null("str"), "str")
        self.assertThrowsExceptionOfType(lambda: require_non_null(None), ValueError)

    def test_allSatisty(self) -> None:
        """
        Test allSatisfy function
        """
        self.assertFalse(Stream(["A", "B"]).all_match(lambda e: e is None))
        self.assertFalse(Stream(["A", None]).all_match(lambda e: e is None))
        self.assertTrue(Stream([None, None]).all_match(lambda e: e is None))

    def test_areSame(self) -> None:
        """
        Test areSame function
        """
        self.assertTrue(equals([1])([1]), "Int array should be the same")
        self.assertTrue(equals(["str"])(["str"]), "String array should be the same")
        self.assertFalse(equals([1])([2]), "Int array should not be the same")
        self.assertTrue(equals({"a": "b"})({"a": "b"}), "Dict should be the same")
        self.assertTrue(
            equals({"a": "b", "c": "d"})({"a": "b", "c": "d"}),
            "Dict should be the same",
        )
        self.assertTrue(
            equals({"a": "b", "c": "d"})({"c": "d", "a": "b"}),
            "Dict should be the same",
        )
        self.assertFalse(equals({"a": "b"})({"a": "b1"}), "Dict should not be the same")

    def test_allNotNone(self) -> None:
        self.assertTrue(all_not_none(["A", "B", "C"]), "All should not be none")
        self.assertFalse(all_not_none(["A", "B", None]), "One should contain none")

    def test_isIn(self) -> None:
        self.assertTrue(is_in(["A", "B", "C"])("A"), "A should be in array")
        self.assertFalse(is_in(["A", "B", "C"])("D"), "D should not be in array")

    def test_isNotIn(self) -> None:
        self.assertFalse(is_not_in(["A", "B", "C"])("A"), "A should be in array")
        self.assertTrue(is_not_in(["A", "B", "C"])("D"), "D should not be in array")

    def test_isBlank(self) -> None:
        self.assertFalse(is_blank(["A", "B", "C"]), "Array should not be blank")
        self.assertTrue(is_blank([]), "Array should be blank")
        self.assertTrue(is_blank(None), "Object should be blank")
        self.assertTrue(is_blank(""), "Object should be blank")
        self.assertTrue(is_blank({}), "Dict should be blank")
        self.assertFalse(is_blank("Test"), "String should not be blank")
        self.assertFalse(is_blank({"a": "b"}), "Dict should not be blank")

    def test_defVal(self) -> None:
        self.assertEqual(default("str")(None), "str", "Default value should be applied")
        self.assertEqual(
            default("str")("str1"), "str1", "Given value should be applied"
        )

    def test_isNumber(self) -> None:
        self.assertTrue(is_number(10), "10 should be a number")
        self.assertTrue(is_number(0), "0 should be a number")
        self.assertTrue(is_number(0.5), "0.5 should be a number")
        self.assertTrue(is_number("10"), "10 string should be a number")
        self.assertFalse(is_number(None), "None should not be a number")

    # Helper class for testing extract and is_mth_or_fn

    def test_is_mth_or_fn(self):
        self.assertTrue(is_mth_or_fn(sample_function))
        self.assertTrue(is_mth_or_fn(lambda_function))

        obj = SampleClass("test")
        self.assertTrue(is_mth_or_fn(obj.instance_method))
        self.assertTrue(is_mth_or_fn(SampleClass.instance_method))  # Unbound method
        self.assertTrue(is_mth_or_fn(SampleClass.static_method_func))
        self.assertTrue(is_mth_or_fn(obj.static_method_func))
        self.assertTrue(is_mth_or_fn(SampleClass.class_method_func))
        self.assertTrue(is_mth_or_fn(obj.class_method_func))

        self.assertFalse(is_mth_or_fn(10))
        self.assertFalse(is_mth_or_fn("string"))
        self.assertFalse(is_mth_or_fn([1, 2]))
        self.assertFalse(is_mth_or_fn({"a": 1}))
        self.assertFalse(is_mth_or_fn(obj))
        self.assertFalse(is_mth_or_fn(SampleClass))

    def test_require_non_null(self):
        self.assertEqual(require_non_null("hello"), "hello")
        self.assertEqual(require_non_null(0), 0)
        self.assertEqual(require_non_null([]), [])

        self.assertThrowsExceptionOfType(
            lambda: require_non_null(None), ValueError, "None object provided"
        )
        self.assertThrowsExceptionOfType(
            lambda: require_non_null(None, "Custom message"),
            ValueError,
            "Custom message",
        )

    def test_is_number(self):
        self.assertTrue(is_number(10))
        self.assertTrue(is_number(0))
        self.assertTrue(is_number(-5))
        self.assertTrue(is_number(3.14))
        self.assertTrue(is_number(0.0))
        self.assertTrue(is_number(-2.5))
        self.assertTrue(is_number("123"))
        self.assertTrue(is_number("0"))
        self.assertTrue(is_number("-45"))
        self.assertTrue(is_number("3.14"))
        self.assertTrue(is_number("0.0"))
        self.assertTrue(is_number("-2.5e-3"))
        self.assertTrue(is_number(True))  # float(True) is 1.0
        self.assertTrue(is_number(False))  # float(False) is 0.0

        self.assertFalse(is_number("abc"))
        self.assertFalse(is_number("12a"))
        self.assertFalse(is_number(None))
        self.assertFalse(is_number([]))
        self.assertFalse(is_number({}))

    def test_to_int(self):
        self.assertEqual(to_int(10), 10)
        self.assertEqual(to_int(3.14), 3)
        self.assertEqual(to_int(3.99), 3)
        self.assertEqual(to_int(-3.14), -3)
        self.assertEqual(to_int("123"), 123)
        self.assertEqual(to_int("-45"), -45)

        self.assertThrowsExceptionOfType(lambda: to_int("3.14"), ValueError)
        self.assertThrowsExceptionOfType(lambda: to_int("abc"), ValueError)
        self.assertThrowsExceptionOfType(lambda: to_int(None), TypeError)
        self.assertThrowsExceptionOfType(lambda: to_int([]), TypeError)

    def test_to_float(self):
        self.assertEqual(to_float(10), 10.0)
        self.assertEqual(to_float(3.14), 3.14)
        self.assertEqual(to_float("123"), 123.0)
        self.assertEqual(to_float("-45"), -45.0)
        self.assertEqual(to_float("3.14"), 3.14)
        self.assertEqual(to_float("-2.5e-3"), -0.0025)

        self.assertThrowsExceptionOfType(lambda: to_float("abc"), ValueError)
        self.assertThrowsExceptionOfType(lambda: to_float(None), TypeError)
        self.assertThrowsExceptionOfType(lambda: to_float([]), TypeError)

    def test_as_list(self):
        self.assertEqual(as_list({}), [])
        d = {"a": 1, "b": 2, "c": 3}
        result = as_list(d)
        self.assertCountEqual(result, [1, 2, 3])
        self.assertEqual(len(result), 3)

    def test_keys_as_list(self):
        self.assertEqual(keys_as_list({}), [])
        d = {"a": 1, "b": 2, "c": 3}
        result = keys_as_list(d)
        self.assertCountEqual(result, ["a", "b", "c"])
        self.assertEqual(len(result), 3)

    def test_load_json(self):
        self.assertEqual(load_json('{"a": 1, "b": "hello"}'), {"a": 1, "b": "hello"})
        self.assertEqual(load_json('[1, 2, "world"]'), [1, 2, "world"])
        self.assertIsNone(load_json("invalid json"))
        self.assertEqual(load_json(b'{"key": "value"}'), {"key": "value"})
        self.assertEqual(
            load_json(bytearray(b'["item1", "item2"]')), ["item1", "item2"]
        )
        self.assertIsNone(load_json(b"invalid bytes"))

    def test_load_json_ex(self):
        self.assertEqual(load_json_ex('{"a": 1}', None), {"a": 1})
        self.assertIsNone(load_json_ex("invalid", None))

        handler_called = False
        exception_caught = None

        def my_handler(ex):
            nonlocal handler_called, exception_caught
            handler_called = True
            exception_caught = ex

        self.assertIsNone(load_json_ex("invalid json", my_handler))
        self.assertTrue(handler_called)
        self.assertIsInstance(exception_caught, json.JSONDecodeError)

        handler_called = False  # Reset
        self.assertEqual(load_json_ex('{"valid": true}', my_handler), {"valid": True})
        self.assertFalse(handler_called)

    def test_identity(self):
        self.assertEqual(identity(10), 10)
        self.assertEqual(identity("hello"), "hello")
        self.assertIsNone(identity(None))
        my_list = [1, 2, 3]
        self.assertIs(identity(my_list), my_list)

    def test_extract(self):
        obj = SampleClass("inst_val")
        data_dict = {
            "a": 10,
            "b": {"c": "nested_str", "d": [1, 2, {"e": "deep"}]},
            "f": obj,
        }
        data_list = [0, data_dict, 20]

        self.assertIsNone(extract(str, None, ["a"]))
        self.assertEqual(extract(str, None, ["a"], "default"), "default")
        self.assertEqual(extract(dict, data_dict, []), data_dict)
        self.assertEqual(extract(str, None, [], "default_val"), "default_val")
        self.assertEqual(extract(str, data_list, [1, "b", "c"]), "nested_str")
        self.assertEqual(extract(str, data_list, [1, "b", "d", 2, "e"]), "deep")
        self.assertIsNone(extract(str, data_list, [5]))
        self.assertEqual(extract(str, data_dict, ["f", "instance_var"]), "inst_val")
        self.assertIsNone(extract(str, obj, ["non_existent_attr"]))
        self.assertEqual(extract(str, obj, ["non_existent_attr"], "default"), "default")
        self.assertEqual(extract(str, data_dict, ["f", "_private_var"]), "private")
        self.assertEqual(extract(int, data_dict, ["a"]), 10)  # Type is for annotation

    def test_is_not_none(self):
        self.assertTrue(is_not_none("hello"))
        self.assertFalse(is_not_none(None))

    def test_is_empty_or_none(self):
        self.assertTrue(is_empty_or_none(None))
        self.assertTrue(is_empty_or_none([]))
        self.assertTrue(is_empty_or_none({}))
        self.assertTrue(is_empty_or_none(""))
        self.assertTrue(is_empty_or_none(set()))
        self.assertTrue(is_empty_or_none(()))

        def empty_gen():
            if False:
                yield 1  # pragma: no cover

        self.assertTrue(is_empty_or_none(empty_gen()))

        def non_empty_gen():
            yield 1

        self.assertFalse(is_empty_or_none(non_empty_gen()))
        self.assertFalse(is_empty_or_none([1]))
        self.assertFalse(is_empty_or_none(10))

    def test_cmp_to_key(self):
        def num_comparator(a: int, b: int) -> int:
            return a - b

        KeyClass = cmp_to_key(num_comparator)
        k1, k2, k3 = KeyClass(10), KeyClass(20), KeyClass(10)

        self.assertTrue(k1 < k2)
        self.assertFalse(k2 < k1)
        self.assertTrue(k2 > k1)
        self.assertTrue(k1 == k3)
        self.assertEqual(k1.__eq__("not a key"), NotImplemented)
        self.assertTrue(k1 <= k2)
        self.assertTrue(k1 <= k3)
        self.assertTrue(k2 >= k1)
        self.assertTrue(k1 >= k3)

    def test_each(self):
        action_called_count = 0

        def my_action_none(x):
            nonlocal action_called_count
            action_called_count += 1  # pragma: no cover

        each(None, my_action_none)
        self.assertEqual(action_called_count, 0)
        each([], my_action_none)
        self.assertEqual(action_called_count, 0)

        items, processed_items = [1, 2, 3], []

        def my_action_collect(x):
            nonlocal action_called_count
            action_called_count += 1
            processed_items.append(x * 2)

        each(items, my_action_collect)
        self.assertEqual(action_called_count, 3)
        self.assertEqual(processed_items, [2, 4, 6])

    def test_dict_update(self):
        my_dict = {"a": 1}
        dict_update(my_dict, "c", 3)
        self.assertEqual(my_dict, {"a": 1, "c": 3})
        dict_update(my_dict, "a", 10)
        self.assertEqual(my_dict, {"a": 10, "c": 3})

    def test_sort(self):
        def comp(a: int, b: int) -> int:
            return a - b

        self.assertEqual(sort([], comp), [])
        data = [3, 1, 4, 1, 5]
        self.assertEqual(sort(list(data), comp), [1, 1, 3, 4, 5])
        original_data = [3, 1, 2]
        sort(original_data, comp)  # sort returns a new list
        self.assertEqual(original_data, [3, 1, 2])  # Original unchanged

    def test_value_class(self):
        v1 = Value(10)
        self.assertEqual(v1.get(), 10)
        v2 = Value(None)
        self.assertIsNone(v2.get())
        v1.set(20)
        self.assertEqual(v1.get(), 20)
        v1.set(None)
        self.assertIsNone(v1.get())

    def test_chunk(self):
        self.assertEqual(chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])
        self.assertEqual(chunk([1, 2, 3, 4], 2), [[1, 2], [3, 4]])
        self.assertEqual(chunk([1, 2, 3], 1), [[1], [2], [3]])
        self.assertEqual(chunk([1, 2, 3], 3), [[1, 2, 3]])
        self.assertEqual(chunk([1, 2, 3], 4), [[1, 2, 3]])
        self.assertEqual(chunk([], 2), [])
        self.assertEqual(chunk(range(5), 2), [[0, 1], [2, 3], [4]])
        self.assertThrowsExceptionOfType(lambda: chunk([1, 2], 0), ValueError)
        self.assertThrowsExceptionOfType(lambda: chunk([1, 2], -1), ValueError)

    def test_flatten(self):
        self.assertEqual(flatten([[1, 2], [3, 4], [5]]), [1, 2, 3, 4, 5])
        self.assertEqual(flatten([[1], [2], [3]]), [1, 2, 3])
        self.assertEqual(flatten([[], [1], [], [2, 3]]), [1, 2, 3])
        self.assertEqual(flatten([]), [])
        self.assertEqual(flatten([[]]), [])
        self.assertEqual(flatten([iter([1, 2]), iter([3, 4])]), [1, 2, 3, 4])

    def test_flatten_deep(self):
        self.assertEqual(
            flatten_deep([1, [2, [3, [4, 5]], 6], 7]), [1, 2, 3, 4, 5, 6, 7]
        )
        self.assertEqual(flatten_deep([[1, 2], [3, 4]]), [1, 2, 3, 4])
        self.assertEqual(flatten_deep([1, 2, 3]), [1, 2, 3])
        self.assertEqual(flatten_deep([]), [])
        self.assertEqual(flatten_deep([[], [[]], [[[]]]]), [])
        self.assertEqual(
            flatten_deep([1, "hello", [2, b"bytes", [3, bytearray(b"ba")]]]),
            [1, "hello", 2, b"bytes", 3, bytearray(b"ba")],
        )
        self.assertEqual(
            flatten_deep([iter([1, 2]), [3, iter([4, 5])]]), [1, 2, 3, 4, 5]
        )

    def test_uniq(self):
        self.assertEqual(uniq([1, 2, 1, 3, 2, 4]), [1, 2, 3, 4])
        self.assertEqual(uniq([1, 1, 1, 1, 1]), [1])
        self.assertEqual(uniq([1, 2, 3]), [1, 2, 3])
        self.assertEqual(uniq([]), [])
        self.assertEqual(uniq(["a", "b", "a", "c"]), ["a", "b", "c"])
        # Test with mixed types (if hashable)
        self.assertEqual(uniq([1, "a", 1, "b", "a"]), [1, "a", "b"])
        self.assertEqual(uniq(iter([1, 2, 1, 3, 2, 4])), [1, 2, 3, 4])

    def test_key_by(self):
        data = [
            {"id": "a", "value": 1},
            {"id": "b", "value": 2},
            {"id": "a", "value": 3},  # This should overwrite the first 'a'
        ]
        self.assertEqual(
            key_by(data, lambda x: x["id"]),
            {
                "a": {"id": "a", "value": 3},
                "b": {"id": "b", "value": 2},
            },
        )
        self.assertEqual(key_by([], lambda x: x["id"]), {})

        class Item:
            def __init__(self, key, val):
                self.key = key
                self.val = val

            def __repr__(self):  # For easier debugging if test fails
                return f"Item({self.key}, {self.val})"

            def __eq__(self, other):
                return (
                    isinstance(other, Item)
                    and self.key == other.key
                    and self.val == other.val
                )

        items = [Item("x", 10), Item("y", 20), Item("x", 30)]
        self.assertEqual(
            key_by(items, lambda item: item.key),
            {
                "x": Item("x", 30),
                "y": Item("y", 20),
            },
        )

    def test_pick(self):
        source = {"a": 1, "b": 2, "c": 3, "d": 4}
        self.assertEqual(pick(source, ["a", "c", "e"]), {"a": 1, "c": 3})
        self.assertEqual(pick(source, ["a", "d"]), {"a": 1, "d": 4})
        self.assertEqual(pick(source, []), {})
        self.assertEqual(pick(source, ["x", "y"]), {})
        self.assertEqual(pick({}, ["a", "b"]), {})
        self.assertEqual(pick(source, iter(["b", "d"])), {"b": 2, "d": 4})

    def test_omit(self):
        source = {"a": 1, "b": 2, "c": 3, "d": 4}
        self.assertEqual(omit(source, ["b", "d", "e"]), {"a": 1, "c": 3})
        self.assertEqual(omit(source, ["a", "c"]), {"b": 2, "d": 4})
        self.assertEqual(omit(source, []), source)
        self.assertEqual(omit(source, ["x", "y"]), source)
        self.assertEqual(omit({}, ["a", "b"]), {})
        self.assertEqual(omit(source, iter(["a", "c"])), {"b": 2, "d": 4})

    def test_head(self):
        self.assertEqual(head([1, 2, 3]), 1)
        self.assertEqual(head(["a", "b"]), "a")
        self.assertEqual(head([10]), 10)
        self.assertIsNone(head([]))
        self.assertEqual(head((1, 2)), 1)  # Test with tuple
        self.assertIsNone(head(()))

    def test_tail(self):
        self.assertEqual(tail([1, 2, 3, 4]), [2, 3, 4])
        self.assertEqual(tail(["a", "b", "c"]), ["b", "c"])
        self.assertEqual(tail([10, 20]), [20])
        self.assertEqual(tail([1]), [])
        self.assertEqual(tail([]), [])
        self.assertEqual(tail((1, 2, 3)), [2, 3])  # Test with tuple
        self.assertEqual(tail((1,)), [])

    def test_last(self):
        self.assertEqual(last([1, 2, 3]), 3)
        self.assertEqual(last(["a", "b"]), "b")
        self.assertEqual(last([10]), 10)
        self.assertIsNone(last([]))
        self.assertEqual(last((1, 2)), 2)  # Test with tuple
        self.assertIsNone(last(()))

    def test_initial(self):
        self.assertEqual(initial([1, 2, 3, 4]), [1, 2, 3])
        self.assertEqual(initial(["a", "b", "c"]), ["a", "b"])
        self.assertEqual(initial([10, 20]), [10])
        self.assertEqual(initial([1]), [])
        self.assertEqual(initial([]), [])
        self.assertEqual(initial((1, 2, 3)), [1, 2])  # Test with tuple
        self.assertEqual(initial((1,)), [])
