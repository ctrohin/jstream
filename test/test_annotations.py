from baseTest import BaseTestCase
from jstreams.annotations import getter, setter, builder


class TestAnnotations(BaseTestCase):
    def test_getter(self) -> None:
        @getter()
        class Test:
            var1: str
            var2: int
            var3: str
            _var_private: int = 1

        @getter()
        class OtherTest:
            other_var: str
            other_var2: float

        test_instance = Test()
        test_instance.var1 = "value1"
        test_instance.var2 = 123
        test_instance.var3 = "value3"

        self.assertEqual(test_instance.get_var1(), "value1")
        self.assertEqual(test_instance.get_var2(), 123)
        self.assertEqual(test_instance.get_var3(), "value3")

        other_test_instance = OtherTest()
        other_test_instance.other_var = "test"
        other_test_instance.other_var2 = 2.3

        self.assertEqual(other_test_instance.get_other_var(), "test")
        self.assertEqual(other_test_instance.get_other_var2(), 2.3)

        self.assertRaises(AttributeError, lambda: test_instance.get_unknown())
        self.assertRaises(AttributeError, lambda: test_instance.get__var_private())

    def test_setter(self) -> None:
        @setter()
        class Test:
            var1: str
            var2: int
            var3: str
            _var_private: int = 1

        @setter()
        class OtherTest:
            other_var: str
            other_var2: float

        test_instance = Test()
        test_instance.set_var1("value1")
        test_instance.set_var2(123)
        test_instance.set_var3("value3")

        self.assertEqual(test_instance.var1, "value1")
        self.assertEqual(test_instance.var2, 123)
        self.assertEqual(test_instance.var3, "value3")

        other_test_instance = OtherTest()
        other_test_instance.set_other_var("test")
        other_test_instance.set_other_var2(2.3)

        self.assertEqual(other_test_instance.other_var, "test")
        self.assertEqual(other_test_instance.other_var2, 2.3)
        self.assertRaises(AttributeError, lambda: test_instance.set_unknown(1))
        self.assertRaises(AttributeError, lambda: test_instance.set__var_private(1))

    def test_builder(self) -> None:
        @builder()
        class Test:
            var1: str
            var2: int
            var3: str
            _var_private: int = 1

        @builder()
        class OtherTest:
            other_var: str
            other_var2: float

        test_instance: Test = (
            Test.builder()
            .with_var1("value1")
            .with_var2(123)
            .with_var3("value3")
            .build()
        )

        self.assertEqual(test_instance.var1, "value1")
        self.assertEqual(test_instance.var2, 123)
        self.assertEqual(test_instance.var3, "value3")

        other_test_instance: OtherTest = (
            OtherTest.builder().with_other_var("test").with_other_var2(2.3).build()
        )

        self.assertEqual(other_test_instance.other_var, "test")
        self.assertEqual(other_test_instance.other_var2, 2.3)
        self.assertRaises(
            AttributeError, lambda: Test.builder().with_unknown(1).build()
        )
        self.assertRaises(
            AttributeError, lambda: Test.builder().with__var_private(1).build()
        )
