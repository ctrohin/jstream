from jstreams import inject
from baseTest import BaseTestCase
from jstreams.ioc import injector


class TestProfile(BaseTestCase):
    def test_profile(self) -> None:
        injector().provide(str, "Test1", profiles=["1"])
        injector().provide(str, "Test2", profiles=["2"])
        injector().activateProfile("1")
        self.assertEqual(
            inject(str), "Test1", "Value for profile 1 should have been selected"
        )

    def test_profile_2(self) -> None:
        injector().provide(str, "Test1", profiles=["1"])
        injector().provide(str, "Test2", profiles=["2"])
        injector().activateProfile("2")
        self.assertEqual(
            inject(str), "Test2", "Value for profile 2 should have been selected"
        )

    def test_profile_3(self) -> None:
        injector().provide(str, "Test1", profiles=["1"])
        injector().provide(int, 0, profiles=["2"])
        injector().activateProfile("1")
        self.assertEqual(
            injector().find(str),
            "Test1",
            "Value for profile 1 should have been selected",
        )
        self.assertIsNone(injector().find(int), "Value for int should not be injected")

    def test_profile_4(self) -> None:
        injector().provide(str, "Test1", profiles=["1"])
        injector().provide(int, 0, profiles=["2"])
        injector().activateProfile("2")
        self.assertIsNone(
            injector().find(str), "Value for profile 1 should not have been selected"
        )
        self.assertEqual(injector().find(int), 0, "Value for int should be injected")

    def test_profile_var_1(self) -> None:
        injector().provideVar(str, "varStr", "Test1", profiles=["1"])
        injector().provideVar(int, "varInt", 0, profiles=["2"])
        injector().activateProfile("2")
        self.assertIsNone(
            injector().findVar(str, "varStr"),
            "Value for profile 2 should not have been selected",
        )
        self.assertEqual(
            injector().findVar(int, "varInt"), 0, "Value for int should be injected"
        )

    def test_profile_var_2(self) -> None:
        injector().provideVar(str, "varStr", "Test1", profiles=["1"])
        injector().provideVar(int, "varInt", 0, profiles=["2"])
        injector().activateProfile("1")
        self.assertEqual(
            injector().findVar(str, "varStr"),
            "Test1",
            "Value for profile 1 should not have been selected",
        )
        self.assertIsNone(
            injector().findVar(int, "varInt"), "Value for int should be injected"
        )

    def test_profile_var_3(self) -> None:
        injector().provideVar(str, "varStr", "Test1", profiles=["1"])
        injector().provideVar(str, "varStr", "Test2", profiles=["2"])
        injector().activateProfile("1")
        self.assertEqual(
            injector().findVar(str, "varStr"),
            "Test1",
            "Value for profile 1 should not have been selected",
        )

    def test_profile_var_4(self) -> None:
        injector().provideVar(str, "varStr", "Test1", profiles=["1"])
        injector().provideVar(str, "varStr", "Test2", profiles=["2"])
        injector().activateProfile("2")
        self.assertEqual(
            injector().findVar(str, "varStr"),
            "Test2",
            "Value for profile 2 should not have been selected",
        )
