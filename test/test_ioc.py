from typing import Optional

from baseTest import BaseTestCase
from jstreams import Dependency, injector
from jstreams.ioc import (
    InjectedDependency,
    StrVariable,
    inject_args,
    resolve_all,
    resolve_dependencies,
    resolve_variables,
)
from jstreams.predicate import equals
from jstreams.utils import Value

SUCCESS = "SUCCESS"


class TestInterface:
    def test_function(self) -> str:
        pass


class TestInterfaceImplementation(TestInterface):
    def test_function(self) -> str:
        return SUCCESS


class TestIOC(BaseTestCase):
    def setUp(self) -> None:
        injector().clear()

    def setup_interface_nq(self) -> None:
        injector().provide(TestInterface, TestInterfaceImplementation())

    def setup_interface_q(self) -> TestInterface:
        injector().provide(TestInterface, TestInterfaceImplementation(), "testName")

    def test_ioc_not_qualified(self) -> None:
        """Test dependency injection without qualifier"""
        self.assertThrowsExceptionOfType(
            lambda: injector().get(TestInterface),
            ValueError,
            "Retrieving a non existing object should throw a value error",
        )
        self.setup_interface_nq()
        self.assertIsNotNone(
            injector().find(TestInterface), "Autowired interface should not be null"
        )
        self.assertEqual(injector().get(TestInterface).test_function(), SUCCESS)

    def test_ioc_qualified(self) -> None:
        """Test dependency injection with qualifier"""
        self.assertThrowsExceptionOfType(
            lambda: injector().get(TestInterface, "testName"),
            ValueError,
            "Retrieving a non existing object should throw a value error",
        )

        self.setup_interface_q()
        self.assertIsNotNone(
            injector().find(TestInterface, "testName"),
            "Autowired interface should not be null",
        )
        self.assertEqual(
            injector().get(TestInterface, "testName").test_function(), SUCCESS
        )

    def test_autowire_public_attr(self) -> None:
        @resolve_dependencies({"testIf": TestInterface})
        class Test:
            testIf: TestInterface

        injector().provide(TestInterface, TestInterfaceImplementation())

        test = Test()
        self.assertIsNotNone(test.testIf, "Attribute should have been injected")
        self.assertEqual(
            test.testIf.test_function(), SUCCESS, "Method should be properly executed"
        )

    def test_autowire_protected_attr(self) -> None:
        @resolve_dependencies({"_testIf": TestInterface})
        class Test:
            _testIf: TestInterface

            def getTestIf(self) -> TestInterface:
                return self._testIf

        injector().provide(TestInterface, TestInterfaceImplementation())
        test = Test()
        self.assertIsNotNone(test.getTestIf(), "Attribute should have been injected")
        self.assertEqual(
            test.getTestIf().test_function(),
            SUCCESS,
            "Method should be properly executed",
        )

    def test_injected_dependency_class(self) -> None:
        injector().provide(TestInterface, TestInterfaceImplementation())

        class Test:
            def __init__(self):
                self.dep = InjectedDependency(TestInterface)

        test = Test()
        self.assertIsNotNone(test.dep)
        self.assertEqual(test.dep.get().test_function(), SUCCESS)

    def test_injected_dependency_class_fail(self) -> None:
        class Test:
            def __init__(self):
                self.dep = InjectedDependency(TestInterface)

        test = Test()
        self.assertIsNotNone(test.dep)
        self.assertThrowsExceptionOfType(
            test.dep.get,
            ValueError,
            "Should throw error when dependency is forced and not present",
        )

    def test_lazy_dependency(self) -> None:
        val = Value(False)

        def produceHook() -> str:
            val.set(True)
            return "Test"

        injector().provide(str, produceHook)
        self.assertFalse(
            val.get(),
            "Produce hook should not have been called",
        )
        self.assertEqual(injector().get(str), "Test", "Value should be present")
        self.assertTrue(
            val.get(),
            "Produce hook should have been called",
        )

    def test_injector_optional(self) -> None:
        self.assertFalse(
            injector().optional(str).is_present(), "Dependency should not be present"
        )
        injector().provide(str, "Test")
        self.assertTrue(
            injector().optional(str).is_present(), "Dependency should be present"
        )
        self.assertTrue(
            injector().optional(str).filter(equals("Test")).is_present(),
            "Dependency should be correct",
        )

    def test_injected_variable_class_fail(self) -> None:
        @resolve_variables({"val": StrVariable("valKey", True)})
        class Test:
            val: Optional[str]

        test = Test()
        self.assertIsNone(test.val, "Value should be none")

    def test_injected_variable_class_success(self) -> None:
        @resolve_variables({"val": StrVariable("valKey")})
        class Test:
            val: Optional[str]

        injector().provide_var(str, "valKey", "Test")

        test = Test()
        self.assertEqual(test.val, "Test", "Value should be none")

    def test_inject_to_functions(self) -> None:
        @inject_args({"a": int, "b": str})
        def fn(a: int, b: str) -> str:
            return str(a) + "_" + b

        injector().provide(str, "test")
        injector().provide(int, 1)
        self.assertEqual(fn(), "1_test")
        self.assertEqual(fn(a=10), "10_test")
        self.assertEqual(fn(a=10, b="other"), "10_other")
        self.assertEqual(fn(b="other"), "1_other")
        self.assertEqual(fn(10, "other"), "10_other")

    def test_inject_to_functions_with_qualifiers(self) -> None:
        @inject_args({"a": Dependency(int, "a"), "b": str})
        def fn(a: int, b: str) -> str:
            return str(a) + "_" + b

        injector().provide(str, "test")
        injector().provide(int, 1, "a")
        self.assertEqual(fn(), "1_test")
        self.assertEqual(fn(a=10), "10_test")
        self.assertEqual(fn(a=10, b="other"), "10_other")
        self.assertEqual(fn(b="other"), "1_other")
        self.assertEqual(fn(10, "other"), "10_other")

    def test_resolve_all(self) -> None:
        @resolve_all()
        class Test:
            str_val: Optional[str]
            int_val: int
            float_val: float = 7.0
            uncontrolled_float = 6.0
            __bool_val: bool = False

            def get_bool_val(self) -> bool:
                return self.__bool_val

        injector().provide(str, "test")
        injector().provide(int, 1)
        injector().provide(float, 2.0)
        injector().provide(bool, True)
        test = Test()
        self.assertEqual(test.str_val, "test")
        self.assertEqual(test.int_val, 1)
        self.assertEqual(test.float_val, 2.0)
        self.assertEqual(test.uncontrolled_float, 6.0)
        self.assertTrue(test.get_bool_val())
