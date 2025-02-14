from baseTest import BaseTestCase
from jstreams import inject

SUCCESS = "SUCCESS"


class TestInterface:
    def test_function(self) -> str:
        pass


class TestInterfaceImplementation(TestInterface):
    def test_function(self) -> str:
        return SUCCESS


class TestIOC(BaseTestCase):
    def setup_interface_nq(self) -> None:
        inject().provide(TestInterface, TestInterfaceImplementation())

    def setup_interface_q(self) -> TestInterface:
        inject().provide(TestInterface, TestInterfaceImplementation(), "testName")

    def test_ioc_not_qualified(self) -> None:
        """Test dependency injection without qualifier"""
        self.assertThrowsExceptionOfType(
            lambda: inject().get(TestInterface),
            ValueError,
            "Retrieving a non existing object should throw a value error",
        )
        self.setup_interface_nq()
        self.assertIsNotNone(
            inject().find(TestInterface), "Autowired interface should not be null"
        )
        self.assertEqual(inject().get(TestInterface).test_function(), SUCCESS)

    def test_ioc_qualified(self) -> None:
        """Test dependency injection with qualifier"""
        self.assertThrowsExceptionOfType(
            lambda: inject().get(TestInterface, "testName"),
            ValueError,
            "Retrieving a non existing object should throw a value error",
        )

        self.setup_interface_q()
        self.assertIsNotNone(
            inject().find(TestInterface, "testName"),
            "Autowired interface should not be null",
        )
        self.assertEqual(
            inject().get(TestInterface, "testName").test_function(), SUCCESS
        )
