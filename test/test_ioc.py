from baseTest import BaseTestCase
from jstreams import injector
from jstreams.ioc import InjectedDependency, resolveDependencies

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
        injector().provide(TestInterface, TestInterfaceImplementation())

        @resolveDependencies({"testIf": TestInterface})
        class Test:
            testIf: TestInterface

        test = Test()
        self.assertIsNotNone(test.testIf, "Attribute should have been injected")
        self.assertEqual(
            test.testIf.test_function(), SUCCESS, "Method should be properly executed"
        )

    def test_autowire_protected_attr(self) -> None:
        injector().provide(TestInterface, TestInterfaceImplementation())

        @resolveDependencies({"_testIf": TestInterface})
        class Test:
            _testIf: TestInterface

            def getTestIf(self) -> TestInterface:
                return self._testIf

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
