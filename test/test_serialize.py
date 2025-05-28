from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from baseTest import BaseTestCase
from jstreams.serialize import (
    json_deserialize,
    json_serializable,
    json_serialize,
    json_serialize_return,
    json_standard_serializable,
)


class TestSerialize(BaseTestCase):
    def test_serialize_with_constructor(self) -> None:
        @json_serializable()
        class SerializedClass:
            def __init__(self, a: int, b: str) -> None:
                self.a = a
                self.b = b

        value = SerializedClass(1, "test")
        serialized = json_serialize(value)
        self.assertEqual(serialized, {"a": 1, "b": "test"})

        deserialized = json_deserialize(SerializedClass, serialized)
        self.assertIsInstance(deserialized, SerializedClass)
        self.assertEqual(deserialized.a, 1)
        self.assertEqual(deserialized.b, "test")
        self.assertEqual(value, deserialized)

    def test_serialize_without_constructor(self) -> None:
        @json_serializable()
        class SerializedClass:
            a: Optional[int] = None
            b: Optional[str] = None

        value = SerializedClass()
        value.a = 1
        value.b = "test"
        serialized = json_serialize(value)
        self.assertEqual(serialized, {"a": 1, "b": "test"})

        deserialized = json_deserialize(SerializedClass, serialized)
        self.assertIsInstance(deserialized, SerializedClass)
        self.assertEqual(deserialized.a, 1)
        self.assertEqual(deserialized.b, "test")
        self.assertEqual(value, deserialized)

    def test_serialize_with_default(self) -> None:
        @json_serializable()
        class SerializedClass:
            a: Optional[int] = 1
            b: Optional[str] = "test"

        value = SerializedClass()
        serialized = json_serialize(value)
        self.assertEqual(serialized, {"a": 1, "b": "test"})

        deserialized = json_deserialize(SerializedClass, serialized)
        self.assertIsInstance(deserialized, SerializedClass)
        self.assertEqual(deserialized.a, 1)
        self.assertEqual(deserialized.b, "test")
        self.assertEqual(value, deserialized)

    def test_serialize_nested_objects(self) -> None:
        @json_serializable()
        class NestedClass:
            def __init__(self, a: int, b: str):
                self.a = a
                self.b = b

        @json_serializable()
        class OuterClass:
            def __init__(self, nested: NestedClass, x: Optional[int] = None):
                self.nested = nested
                self.x = x

        value = OuterClass(NestedClass(1, "test"), 42)
        serialized = json_serialize(value)
        self.assertEqual(serialized, {"nested": {"a": 1, "b": "test"}, "x": 42})
        deserialized = json_deserialize(OuterClass, serialized)
        self.assertIsInstance(deserialized, OuterClass)
        self.assertIsInstance(deserialized.nested, NestedClass)
        self.assertEqual(deserialized.nested.a, 1)
        self.assertEqual(deserialized.nested.b, "test")
        self.assertEqual(deserialized.x, 42)
        self.assertEqual(value, deserialized)
        self.assertEqual(value.nested, deserialized.nested)

        partialy_serialized = {"nested": {"a": 1, "b": "test"}}
        deserialized_partial = json_deserialize(OuterClass, partialy_serialized)
        self.assertIsInstance(deserialized_partial, OuterClass)
        self.assertIsInstance(deserialized_partial.nested, NestedClass)
        self.assertEqual(deserialized_partial.nested.a, 1)
        self.assertEqual(deserialized_partial.nested.b, "test")
        self.assertIsNone(deserialized_partial.x)  # x defaults to None
        self.assertEqual(deserialized_partial, OuterClass(NestedClass(1, "test")))

    def test_private_attributes_skipped(self) -> None:
        @json_serializable()
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
        serialized = json_serialize(instance)
        self.assertEqual(serialized, {"public_val": 10})

        deserialized = json_deserialize(
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
        @json_serializable()
        class SlottedClass:
            __slots__ = ("x", "y")

            def __init__(self, x: int, y: str) -> None:
                self.x = x
                self.y = y

        value = SlottedClass(5, "slot_data")
        serialized = json_serialize(value)
        self.assertEqual(serialized, {"x": 5, "y": "slot_data"})

        deserialized = json_deserialize(SlottedClass, serialized)
        self.assertIsInstance(deserialized, SlottedClass)
        self.assertEqual(deserialized.x, 5)
        self.assertEqual(deserialized.y, "slot_data")
        self.assertEqual(value, deserialized)

    def test_list_of_serializable_objects(self) -> None:
        @json_serializable()
        class Item:
            def __init__(self, item_id: int):
                self.item_id = item_id

        @json_serializable()
        class ItemListContainer:
            def __init__(self, items: list[Item]):
                self.items = items

        items_data = [Item(1), Item(2), Item(3)]
        container = ItemListContainer(items_data)
        serialized = json_serialize(container)
        expected_serialized = {
            "items": [{"item_id": 1}, {"item_id": 2}, {"item_id": 3}]
        }
        self.assertEqual(serialized, expected_serialized)

        deserialized = json_deserialize(ItemListContainer, serialized)
        self.assertIsInstance(deserialized, ItemListContainer)
        self.assertEqual(len(deserialized.items), 3)
        for i, item_instance in enumerate(deserialized.items):
            self.assertIsInstance(item_instance, Item)
            self.assertEqual(item_instance.item_id, i + 1)
        self.assertEqual(container, deserialized)

    def test_dict_of_serializable_objects(self) -> None:
        @json_serializable()
        class ConfigValue:
            def __init__(self, value: str):
                self.value = value

        @json_serializable()
        class ConfigContainer:
            def __init__(self, configs: dict[str, ConfigValue]):
                self.configs = configs

        configs_data = {"key1": ConfigValue("val1"), "key2": ConfigValue("val2")}
        container = ConfigContainer(configs_data)
        serialized = json_serialize(container)
        expected_serialized = {
            "configs": {"key1": {"value": "val1"}, "key2": {"value": "val2"}}
        }
        self.assertEqual(serialized, expected_serialized)

        deserialized = json_deserialize(ConfigContainer, serialized)
        self.assertIsInstance(deserialized, ConfigContainer)
        self.assertIn("key1", deserialized.configs)
        self.assertIn("key2", deserialized.configs)
        self.assertIsInstance(deserialized.configs["key1"], ConfigValue)
        self.assertEqual(deserialized.configs["key1"].value, "val1")
        self.assertEqual(container, deserialized)

    def test_optional_attributes_handling(self) -> None:
        @json_serializable(False)
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
        serialized1 = json_serialize(instance1)
        self.assertEqual(
            serialized1,
            {
                "name": "Test1",
                "description": "A test instance",
                "count": 10,
                "status": "active",
            },
        )
        deserialized1 = json_deserialize(ClassWithOptional, serialized1)
        self.assertEqual(instance1, deserialized1)

        # Case 2: Optional value is None (explicitly or by default)
        instance2 = ClassWithOptional("Test2", None)  # description is None
        # count remains its default None, status is not set
        serialized2 = json_serialize(instance2)
        # 'status' won't be in serialized output if not set on instance
        self.assertEqual(
            serialized2, {"name": "Test2", "description": None, "count": None}
        )
        deserialized2 = json_deserialize(ClassWithOptional, serialized2)
        self.assertEqual(deserialized2.name, "Test2")
        self.assertIsNone(deserialized2.description)
        self.assertIsNone(deserialized2.count)
        self.assertFalse(
            hasattr(deserialized2, "status")
        )  # Since it wasn't in serialized data and not set by __init__

        # Case 3: Deserializing with missing optional fields
        data_missing_optional = {"name": "Test3"}
        deserialized3 = json_deserialize(ClassWithOptional, data_missing_optional)
        self.assertEqual(deserialized3.name, "Test3")
        self.assertEqual(
            deserialized3.description, "default_desc"
        )  # from __init__ default
        self.assertIsNone(deserialized3.count)  # from class annotation default
        self.assertFalse(hasattr(deserialized3, "status"))

    def test_equality_method(self) -> None:
        @json_serializable()
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

        @json_serializable()
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
        @json_serializable()
        class Simple:
            val: int

            def __init__(self, val: int):
                self.val = val

            # an_extra_field: Optional[str] = None # If this was here, it would be set

        data_with_extra = {"val": 100, "extra_field": "ignore_me", "another_extra": 123}
        instance = json_deserialize(Simple, data_with_extra)
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
            json_serialize(obj)

        with self.assertRaisesRegex(
            TypeError, "NotSerializable does not have a from_dict method."
        ):
            json_deserialize(NotSerializable, {"a": 1})

        # Test with None
        with self.assertRaisesRegex(
            TypeError, "NoneType does not have a to_dict method."
        ):
            json_serialize(None)
        # deserialize(None, {}) would likely fail earlier at get_type_hints or inspect.signature
        # For deserialize, the first argument must be a type.
        self.assertRaises(AttributeError, lambda: json_deserialize(None, {"a": 1}))

    def test_field_aliases(self) -> None:
        @json_serializable(
            aliases={"python_name": "jsonName", "another_attr": "otherJsonAttr"}
        )
        class AliasedClass:
            def __init__(self, python_name: str, another_attr: int) -> None:
                self.python_name = python_name
                self.another_attr = another_attr

            regular_field: Optional[str] = None

        instance = AliasedClass("value1", 100)
        instance.regular_field = "untouched"

        serialized = json_serialize(instance)
        self.assertEqual(
            serialized,
            {"jsonName": "value1", "otherJsonAttr": 100, "regular_field": "untouched"},
        )

        deserialized = json_deserialize(
            AliasedClass,
            {
                "jsonName": "value2",
                "otherJsonAttr": 200,
                "regular_field": "new_untouched",
            },
        )
        self.assertEqual(deserialized.python_name, "value2")
        self.assertEqual(deserialized.another_attr, 200)
        self.assertEqual(deserialized.regular_field, "new_untouched")
        self.assertEqual(instance.python_name, "value1")  # Original instance unchanged

    def test_omit_none_values(self) -> None:
        @json_serializable(omit_none=True)
        class OmitNoneClass:
            def __init__(
                self,
                name: str,
                value: Optional[int] = None,
                description: Optional[str] = None,
            ) -> None:
                self.name = name
                self.value = value
                self.description = description

        instance_with_none = OmitNoneClass("Test", description="Has description")
        serialized_with_none_omitted = json_serialize(instance_with_none)
        self.assertEqual(
            serialized_with_none_omitted,
            {"name": "Test", "description": "Has description"},
        )

        instance_all_values = OmitNoneClass("TestFull", 123, "Full desc")
        serialized_all_values = json_serialize(instance_all_values)
        self.assertEqual(
            serialized_all_values,
            {"name": "TestFull", "value": 123, "description": "Full desc"},
        )

        @json_serializable(omit_none=False)  # Default behavior
        class KeepNoneClass:
            def __init__(self, name: str, value: Optional[int] = None) -> None:
                self.name = name
                self.value = value

        instance_keep_none = KeepNoneClass("TestKeep")
        serialized_keep_none = json_serialize(instance_keep_none)
        self.assertEqual(serialized_keep_none, {"name": "TestKeep", "value": None})

    def test_datetime_date_uuid_enum_handling(self) -> None:
        class MyEnum(Enum):
            OPTION_A = "val_a"
            OPTION_B = "val_b"

        @json_serializable()
        class AdvancedTypesClass:
            def __init__(
                self,
                dt: datetime,
                d: date,
                u: UUID,
                e: MyEnum,
                e_opt: Optional[MyEnum] = None,
            ) -> None:
                self.dt = dt
                self.d = d
                self.u = u
                self.e = e
                self.e_opt = e_opt

        now = datetime.now()
        today = date.today()
        my_uuid = uuid4()

        instance = AdvancedTypesClass(now, today, my_uuid, MyEnum.OPTION_A)
        serialized = json_serialize(instance)

        self.assertEqual(serialized["dt"], now.isoformat())
        self.assertEqual(serialized["d"], today.isoformat())
        self.assertEqual(serialized["u"], str(my_uuid))
        self.assertEqual(serialized["e"], "val_a")
        self.assertIsNone(serialized["e_opt"])

        deserialized = json_deserialize(AdvancedTypesClass, serialized)
        self.assertEqual(deserialized.dt, now)
        self.assertEqual(deserialized.d, today)
        self.assertEqual(deserialized.u, my_uuid)
        self.assertEqual(deserialized.e, MyEnum.OPTION_A)
        self.assertIsNone(deserialized.e_opt)

        # Test with optional enum present
        instance_with_opt_enum = AdvancedTypesClass(
            now, today, my_uuid, MyEnum.OPTION_A, MyEnum.OPTION_B
        )
        serialized_with_opt_enum = json_serialize(instance_with_opt_enum)
        self.assertEqual(serialized_with_opt_enum["e_opt"], "val_b")
        deserialized_with_opt_enum = json_deserialize(
            AdvancedTypesClass, serialized_with_opt_enum
        )
        self.assertEqual(deserialized_with_opt_enum.e_opt, MyEnum.OPTION_B)

    def test_post_deserialize_hook(self) -> None:
        hook_called_flag = False

        @json_serializable(post_deserialize_hook_name="custom_hook")
        class HookedClass:
            name: str
            derived_value: Optional[str] = None

            def __init__(self, name: str) -> None:
                self.name = name

            def custom_hook(self) -> None:
                nonlocal hook_called_flag
                hook_called_flag = True
                self.derived_value = f"Derived from {self.name}"

        data = {"name": "HookTest"}
        deserialized = json_deserialize(HookedClass, data)

        self.assertTrue(hook_called_flag)
        self.assertEqual(deserialized.name, "HookTest")
        self.assertEqual(deserialized.derived_value, "Derived from HookTest")

    def test_custom_field_serializers_deserializers(self) -> None:
        def custom_int_serializer(value: int) -> str:
            return f"custom_serialized_{value}"

        def custom_int_deserializer(data_value: str) -> int:
            return int(data_value.replace("custom_serialized_", ""))

        def custom_obj_serializer(obj: Any) -> dict:  # Simplified custom object
            return {"wrapper_value": obj.internal_value * 2}

        def custom_obj_deserializer(data: dict) -> Any:  # Simplified custom object
            class TempObj:
                def __init__(self, val):
                    self.internal_value = val

                def __eq__(self, other):
                    return (
                        isinstance(other, TempObj)
                        and self.internal_value == other.internal_value
                    )

            return TempObj(data["wrapper_value"] // 2)

        class MyComplexField:
            def __init__(self, internal_value: int):
                self.internal_value = internal_value

            def __eq__(self, other):
                return (
                    isinstance(other, MyComplexField)
                    and self.internal_value == other.internal_value
                )

        @json_serializable(
            custom_serializers={
                "custom_field_int": custom_int_serializer,
                "complex_obj": custom_obj_serializer,
            },
            custom_deserializers={
                "custom_field_int": custom_int_deserializer,
                "complex_obj": custom_obj_deserializer,
            },
        )
        class CustomHandlerClass:
            regular_field: str
            custom_field_int: int
            complex_obj: MyComplexField

            def __init__(
                self,
                regular_field: str,
                custom_field_int: int,
                complex_obj: MyComplexField,
            ) -> None:
                self.regular_field = regular_field
                self.custom_field_int = custom_field_int
                self.complex_obj = complex_obj

        instance = CustomHandlerClass("hello", 123, MyComplexField(50))
        serialized = json_serialize(instance)

        self.assertEqual(serialized["regular_field"], "hello")
        self.assertEqual(serialized["custom_field_int"], "custom_serialized_123")
        self.assertEqual(serialized["complex_obj"], {"wrapper_value": 100})

        deserialized = json_deserialize(CustomHandlerClass, serialized)
        self.assertEqual(deserialized.regular_field, "hello")
        self.assertEqual(deserialized.custom_field_int, 123)
        self.assertEqual(
            deserialized.complex_obj.internal_value, MyComplexField(50).internal_value
        )

    def test_custom_field_serializers_deserializers_camel(self) -> None:
        def custom_int_serializer(value: int) -> str:
            return f"custom_serialized_{value}"

        def custom_int_deserializer(data_value: str) -> int:
            return int(data_value.replace("custom_serialized_", ""))

        def custom_obj_serializer(obj: Any) -> dict:  # Simplified custom object
            return {"wrapper_value": obj.internal_value * 2}

        def custom_obj_deserializer(data: dict) -> Any:  # Simplified custom object
            class TempObj:
                def __init__(self, val):
                    self.internal_value = val

                def __eq__(self, other):
                    return (
                        isinstance(other, TempObj)
                        and self.internal_value == other.internal_value
                    )

            return TempObj(data["wrapper_value"] // 2)

        class MyComplexField:
            def __init__(self, internal_value: int):
                self.internal_value = internal_value

            def __eq__(self, other):
                return (
                    isinstance(other, MyComplexField)
                    and self.internal_value == other.internal_value
                )

        @json_serializable(
            custom_serializers={
                "custom_field_int": custom_int_serializer,
                "complex_obj": custom_obj_serializer,
            },
            custom_deserializers={
                "custom_field_int": custom_int_deserializer,
                "complex_obj": custom_obj_deserializer,
            },
            translate_snake_to_camel=True,
        )
        class CustomHandlerClass:
            regular_field: str
            custom_field_int: int
            complex_obj: MyComplexField

            def __init__(
                self,
                regular_field: str,
                custom_field_int: int,
                complex_obj: MyComplexField,
            ) -> None:
                self.regular_field = regular_field
                self.custom_field_int = custom_field_int
                self.complex_obj = complex_obj

        instance = CustomHandlerClass("hello", 123, MyComplexField(50))
        serialized = json_serialize(instance)

        self.assertEqual(serialized["regularField"], "hello")
        self.assertEqual(serialized["customFieldInt"], "custom_serialized_123")
        self.assertEqual(serialized["complexObj"], {"wrapper_value": 100})

        deserialized = json_deserialize(CustomHandlerClass, serialized)
        self.assertEqual(deserialized.regular_field, "hello")
        self.assertEqual(deserialized.custom_field_int, 123)
        self.assertEqual(
            deserialized.complex_obj.internal_value, MyComplexField(50).internal_value
        )

    def test_camel_case_deserialize(self) -> None:
        @json_standard_serializable()
        class CamelClass:
            def __init__(self, my_field: str, another_field: int) -> None:
                self.my_field = my_field
                self.another_field = another_field

        data = {"myField": "value", "anotherField": 42}
        instance = json_deserialize(CamelClass, data)
        self.assertEqual(instance.my_field, "value")
        self.assertEqual(instance.another_field, 42)

    def test_json_serialize_return(self) -> None:
        @json_serializable()
        class SimpleClass:
            def __init__(self, value: int) -> None:
                self.value = value

        @json_serialize_return()
        def produce_object() -> SimpleClass:
            return SimpleClass(10)

        serialized = produce_object()
        self.assertEqual(serialized, {"value": 10})
        deserialized = json_deserialize(SimpleClass, serialized)
        self.assertIsInstance(deserialized, SimpleClass)
        self.assertEqual(deserialized.value, 10)
        self.assertEqual(deserialized, SimpleClass(10))
