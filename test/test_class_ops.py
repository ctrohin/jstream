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
