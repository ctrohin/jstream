from baseTest import BaseTestCase
from jstreams.ioc import Injector

SUCCESS = "SUCCESS"


class TestInterface:
    def test_function(self) -> str:
        pass


class TestInterfaceImplementation(TestInterface):
    def test_function(self) -> str:
        return SUCCESS


class TestIOC(BaseTestCase):
    def setup_interface_nq(self) -> None:
        Injector.provide(TestInterface, TestInterfaceImplementation())

    def setup_interface_q(self) -> TestInterface:
        Injector.provide(TestInterface, TestInterfaceImplementation(), "testName")

    def test_ioc_not_qualified(self) -> None:
        """Test dependency injection without qualifier"""
        self.assertThrowsExceptionOfType(
            lambda: Injector.get(TestInterface),
            ValueError,
            "Retrieving a non existing object should throw a value error",
        )
        self.setup_interface_nq()
        self.assertIsNotNone(Injector.find(TestInterface), "Autowired interface should not be null")
        self.assertEqual(Injector.get(TestInterface).test_function(), SUCCESS)

    def test_ioc_qualified(self) -> None:
        """Test dependency injection with qualifier"""
        self.assertThrowsExceptionOfType(
            lambda: Injector.get(TestInterface, "testName"),
            ValueError,
            "Retrieving a non existing object should throw a value error",
        )

        self.setup_interface_q()
        self.assertIsNotNone(
            Injector.find(TestInterface, "testName"),
            "Autowired interface should not be null",
        )
        self.assertEqual(Injector.get(TestInterface, "testName").test_function(), SUCCESS)
