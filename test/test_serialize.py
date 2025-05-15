from typing import Optional
from baseTest import BaseTestCase
from jstreams.serialize import deserialize, serializable, serialize


class TestSerialize(BaseTestCase):
    def test_serialize_with_constructor(self) -> None:
        @serializable()
        class SerializedClass:
            def __init__(self, a: int, b: str) -> None:
                self.a = a
                self.b = b

        value = SerializedClass(1, "test")
        serialized = serialize(value)
        self.assertEqual(serialized, {"a": 1, "b": "test"})

        deserialized = deserialize(SerializedClass, serialized)
        self.assertIsInstance(deserialized, SerializedClass)
        self.assertEqual(deserialized.a, 1)
        self.assertEqual(deserialized.b, "test")
        self.assertEqual(value, deserialized)

    def test_serialize_without_constructor(self) -> None:
        @serializable()
        class SerializedClass:
            a: Optional[int] = None
            b: Optional[str] = None

        value = SerializedClass()
        value.a = 1
        value.b = "test"
        serialized = serialize(value)
        self.assertEqual(serialized, {"a": 1, "b": "test"})

        deserialized = deserialize(SerializedClass, serialized)
        self.assertIsInstance(deserialized, SerializedClass)
        self.assertEqual(deserialized.a, 1)
        self.assertEqual(deserialized.b, "test")
        self.assertEqual(value, deserialized)

    def test_serialize_with_default(self) -> None:
        @serializable()
        class SerializedClass:
            a: Optional[int] = 1
            b: Optional[str] = "test"

        value = SerializedClass()
        print(value.a, value.b)
        serialized = serialize(value)
        self.assertEqual(serialized, {"a": 1, "b": "test"})

        deserialized = deserialize(SerializedClass, serialized)
        self.assertIsInstance(deserialized, SerializedClass)
        self.assertEqual(deserialized.a, 1)
        self.assertEqual(deserialized.b, "test")
        self.assertEqual(value, deserialized)

    def test_serialize_nested_objects(self) -> None:
        @serializable()
        class NestedClass:
            def __init__(self, a: int, b: str):
                self.a = a
                self.b = b

        @serializable()
        class OuterClass:
            def __init__(self, nested: NestedClass, x: Optional[int] = None):
                self.nested = nested
                self.x = x

        value = OuterClass(NestedClass(1, "test"), 42)
        serialized = serialize(value)
        self.assertEqual(serialized, {"nested": {"a": 1, "b": "test"}, "x": 42})
        deserialized = deserialize(OuterClass, serialized)
        self.assertIsInstance(deserialized, OuterClass)
        self.assertIsInstance(deserialized.nested, NestedClass)
        self.assertEqual(deserialized.nested.a, 1)
        self.assertEqual(deserialized.nested.b, "test")
        self.assertEqual(deserialized.x, 42)
        self.assertEqual(value, deserialized)
        self.assertEqual(value.nested, deserialized.nested)

        partialy_serialized = {"nested": {"a": 1, "b": "test"}}
        deserialized_partial = deserialize(OuterClass, partialy_serialized)
        self.assertIsInstance(deserialized_partial, OuterClass)
        self.assertIsInstance(deserialized_partial.nested, NestedClass)
        self.assertEqual(deserialized_partial.nested.a, 1)
        self.assertEqual(deserialized_partial.nested.b, "test")
        self.assertIsNone(deserialized_partial.x)  # x defaults to None
        self.assertEqual(deserialized_partial, OuterClass(NestedClass(1, "test")))

    def test_private_attributes_skipped(self) -> None:
        @serializable()
        class ClassWithPrivate:
            def __init__(
                self, public_val: int, private_val: Optional[str] = None
            ) -> None:
                self.public_val = public_val
                self._private_val = private_val
                self.__mangled_private = "mangled"

            def get_mangled(self):  # Helper to check mangled value
                return self.__mangled_private

        instance = ClassWithPrivate(10, "secret")
        serialized = serialize(instance)
        self.assertEqual(serialized, {"public_val": 10})

        deserialized = deserialize(
            ClassWithPrivate,
            {
                "public_val": 20,
                "_private_val": "attempted_set",
                "__mangled_private": "attempt_mangled",
            },
        )
        self.assertEqual(deserialized.public_val, 20)
        # For __mangled_private, it depends on whether it's in __init__ or settable.
        # If it's not in __init__ and not a public attribute, it won't be set from extra_data.
        # The current implementation of from_dict would try to set it if it's a known attribute (e.g. via annotations or slots)
        # but since it's mangled and not in __init__, it's tricky.
        # Let's assume for now it's not set if not explicitly handled by __init__.
        # To be absolutely sure, one might need to check the mangled name.
        self.assertEqual(
            deserialized.get_mangled(), "mangled"
        )  # Should retain original if not overwritten by __init__

    def test_slots_serialization(self) -> None:
        @serializable()
        class SlottedClass:
            __slots__ = ("x", "y")

            def __init__(self, x: int, y: str) -> None:
                self.x = x
                self.y = y

        value = SlottedClass(5, "slot_data")
        serialized = serialize(value)
        self.assertEqual(serialized, {"x": 5, "y": "slot_data"})

        deserialized = deserialize(SlottedClass, serialized)
        self.assertIsInstance(deserialized, SlottedClass)
        self.assertEqual(deserialized.x, 5)
        self.assertEqual(deserialized.y, "slot_data")
        self.assertEqual(value, deserialized)

    def test_list_of_serializable_objects(self) -> None:
        @serializable()
        class Item:
            def __init__(self, item_id: int):
                self.item_id = item_id

        @serializable()
        class ItemListContainer:
            def __init__(self, items: list[Item]):
                self.items = items

        items_data = [Item(1), Item(2), Item(3)]
        container = ItemListContainer(items_data)
        serialized = serialize(container)
        expected_serialized = {
            "items": [{"item_id": 1}, {"item_id": 2}, {"item_id": 3}]
        }
        self.assertEqual(serialized, expected_serialized)

        deserialized = deserialize(ItemListContainer, serialized)
        self.assertIsInstance(deserialized, ItemListContainer)
        self.assertEqual(len(deserialized.items), 3)
        for i, item_instance in enumerate(deserialized.items):
            self.assertIsInstance(item_instance, Item)
            self.assertEqual(item_instance.item_id, i + 1)
        self.assertEqual(container, deserialized)

    def test_dict_of_serializable_objects(self) -> None:
        @serializable()
        class ConfigValue:
            def __init__(self, value: str):
                self.value = value

        @serializable()
        class ConfigContainer:
            def __init__(self, configs: dict[str, ConfigValue]):
                self.configs = configs

        configs_data = {"key1": ConfigValue("val1"), "key2": ConfigValue("val2")}
        container = ConfigContainer(configs_data)
        serialized = serialize(container)
        expected_serialized = {
            "configs": {"key1": {"value": "val1"}, "key2": {"value": "val2"}}
        }
        self.assertEqual(serialized, expected_serialized)

        deserialized = deserialize(ConfigContainer, serialized)
        self.assertIsInstance(deserialized, ConfigContainer)
        self.assertIn("key1", deserialized.configs)
        self.assertIn("key2", deserialized.configs)
        self.assertIsInstance(deserialized.configs["key1"], ConfigValue)
        self.assertEqual(deserialized.configs["key1"].value, "val1")
        self.assertEqual(container, deserialized)

    def test_optional_attributes_handling(self) -> None:
        @serializable(False)
        class ClassWithOptional:
            # In __init__
            name: str
            # In __init__, optional
            description: Optional[str]
            # Only in annotations, optional
            count: Optional[int] = None
            # Only in annotations, no default in annotation, but class might set it
            status: Optional[str]

            def __init__(self, name: str, description: Optional[str] = "default_desc"):
                self.name = name
                self.description = description
                # status is not set in __init__

        # Case 1: Optional value provided
        instance1 = ClassWithOptional("Test1", "A test instance")
        instance1.count = 10
        instance1.status = "active"
        serialized1 = serialize(instance1)
        self.assertEqual(
            serialized1,
            {
                "name": "Test1",
                "description": "A test instance",
                "count": 10,
                "status": "active",
            },
        )
        deserialized1 = deserialize(ClassWithOptional, serialized1)
        self.assertEqual(instance1, deserialized1)

        # Case 2: Optional value is None (explicitly or by default)
        instance2 = ClassWithOptional("Test2", None)  # description is None
        # count remains its default None, status is not set
        serialized2 = serialize(instance2)
        # 'status' won't be in serialized output if not set on instance
        self.assertEqual(
            serialized2, {"name": "Test2", "description": None, "count": None}
        )
        deserialized2 = deserialize(ClassWithOptional, serialized2)
        self.assertEqual(deserialized2.name, "Test2")
        self.assertIsNone(deserialized2.description)
        self.assertIsNone(deserialized2.count)
        self.assertFalse(
            hasattr(deserialized2, "status")
        )  # Since it wasn't in serialized data and not set by __init__

        # Case 3: Deserializing with missing optional fields
        data_missing_optional = {"name": "Test3"}
        deserialized3 = deserialize(ClassWithOptional, data_missing_optional)
        self.assertEqual(deserialized3.name, "Test3")
        self.assertEqual(
            deserialized3.description, "default_desc"
        )  # from __init__ default
        self.assertIsNone(deserialized3.count)  # from class annotation default
        self.assertFalse(hasattr(deserialized3, "status"))

    def test_equality_method(self) -> None:
        @serializable()
        class Point:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y

        p1 = Point(1, 2)
        p2 = Point(1, 2)
        p3 = Point(3, 4)

        self.assertTrue(p1 == p2)
        self.assertEqual(p1, p2)  # Same as above, but more conventional for unittest
        self.assertFalse(p1 == p3)
        self.assertNotEqual(p1, p3)

        @serializable()
        class AnotherPoint:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y

        ap1 = AnotherPoint(1, 2)
        self.assertFalse(p1 == ap1)  # Different types
        self.assertNotEqual(p1, ap1)

        self.assertFalse(p1 == "not a point")  # Different types
        self.assertNotEqual(p1, "not a point")

    def test_from_dict_extra_fields_in_data(self) -> None:
        @serializable()
        class Simple:
            val: int

            def __init__(self, val: int):
                self.val = val

            # an_extra_field: Optional[str] = None # If this was here, it would be set

        data_with_extra = {"val": 100, "extra_field": "ignore_me", "another_extra": 123}
        instance = deserialize(Simple, data_with_extra)
        self.assertEqual(instance.val, 100)
        # The current implementation of from_dict will attempt to setattr for extra_data
        # if the attribute exists on the instance (e.g. from __annotations__ or __slots__).
        # If 'extra_field' is not an attribute of Simple, setattr will fail silently or raise if strict.
        # Let's assume they are not attributes of Simple.
        self.assertFalse(hasattr(instance, "extra_field"))
        self.assertFalse(hasattr(instance, "another_extra"))

    def test_serialize_deserialize_error_cases(self) -> None:
        class NotSerializable:
            pass

        obj = NotSerializable()
        with self.assertRaisesRegex(
            TypeError, "NotSerializable does not have a to_dict method."
        ):
            serialize(obj)

        with self.assertRaisesRegex(
            TypeError, "NotSerializable does not have a from_dict method."
        ):
            deserialize(NotSerializable, {"a": 1})

        # Test with None
        with self.assertRaisesRegex(
            TypeError, "NoneType does not have a to_dict method."
        ):
            serialize(None)
        # deserialize(None, {}) would likely fail earlier at get_type_hints or inspect.signature
        # For deserialize, the first argument must be a type.
        self.assertRaises(AttributeError, lambda: deserialize(None, {"a": 1}))
