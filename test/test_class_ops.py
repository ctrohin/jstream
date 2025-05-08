from jstreams.class_operations import ClassOps
from baseTest import BaseTestCase


class TestClassOperations(BaseTestCase):
    def test_type_equals(self) -> None:
        self.assertTrue(ClassOps(str).type_equals("test"))
        self.assertTrue(ClassOps(int).type_equals(1))
        self.assertFalse(ClassOps(int).type_equals("test"))
        self.assertFalse(ClassOps(str).type_equals(1))

    def test_type_equals_derived(self) -> None:
        class BaseClass:
            pass

        class DerivedClass(BaseClass):
            pass

        self.assertTrue(ClassOps(DerivedClass).type_equals(DerivedClass()))
        self.assertFalse(ClassOps(BaseClass).type_equals(DerivedClass()))
        self.assertFalse(ClassOps(DerivedClass).type_equals(BaseClass()))
        self.assertTrue(ClassOps(BaseClass).type_equals(BaseClass()))

    def test_instance_of_derived(self) -> None:
        class BaseClass:
            pass

        class DerivedClass(BaseClass):
            pass

        self.assertTrue(ClassOps(DerivedClass).instance_of(DerivedClass()))
        self.assertTrue(ClassOps(BaseClass).instance_of(DerivedClass()))
        self.assertFalse(ClassOps(DerivedClass).instance_of(BaseClass()))
        self.assertTrue(ClassOps(BaseClass).instance_of(BaseClass()))

    def test_get_name(self) -> None:
        class BaseClass:
            pass

        self.assertEqual(ClassOps(BaseClass).get_name(), "BaseClass")
        self.assertEqual(ClassOps(str).get_name(), "str")
        self.assertEqual(ClassOps(int).get_name(), "int")

    def test_has_attribute(self) -> None:
        class BaseClass:
            attr = 1
            pass

        self.assertTrue(ClassOps(BaseClass).has_attribute("attr"))
        self.assertFalse(ClassOps(BaseClass).has_attribute("attr2"))

    def test_subclass_of(self) -> None:
        class BaseClass:
            pass

        class DerivedClass(BaseClass):
            pass

        self.assertFalse(ClassOps(DerivedClass).subclass_of(BaseClass))
        self.assertTrue(ClassOps(BaseClass).subclass_of(DerivedClass))
        self.assertTrue(ClassOps(BaseClass).subclass_of(BaseClass))
        self.assertTrue(ClassOps(DerivedClass).subclass_of(DerivedClass))

    def test_is_same_type(self) -> None:
        class BaseClass:
            pass

        class DerivedClass(BaseClass):
            pass

        self.assertFalse(ClassOps(DerivedClass).is_same_type(BaseClass))
        self.assertFalse(ClassOps(BaseClass).is_same_type(DerivedClass))
        self.assertTrue(ClassOps(BaseClass).is_same_type(BaseClass))
        self.assertTrue(ClassOps(DerivedClass).is_same_type(DerivedClass))
