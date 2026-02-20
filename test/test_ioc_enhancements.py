from baseTest import BaseTestCase
from jstreams.ioc import injector, component, Scope, AutoClose, inject


class TestIocEnhancements(BaseTestCase):
    def setUp(self) -> None:
        injector().clear()

    def test_prototype_scope(self) -> None:
        @component(scope=Scope.PROTOTYPE)
        class PrototypeComponent:
            pass

        instance1 = inject(PrototypeComponent)
        instance2 = inject(PrototypeComponent)

        self.assertNotEqual(
            instance1, instance2, "Prototype components should return new instances"
        )
        self.assertIsInstance(instance1, PrototypeComponent)
        self.assertIsInstance(instance2, PrototypeComponent)

    def test_singleton_scope(self) -> None:
        @component(scope=Scope.SINGLETON)
        class SingletonComponent:
            pass

        instance1 = inject(SingletonComponent)
        instance2 = inject(SingletonComponent)

        self.assertEqual(
            instance1, instance2, "Singleton components should return the same instance"
        )

    def test_auto_close(self) -> None:
        closed_flag = {"closed": False}

        @component()
        class CloseableComponent(AutoClose):
            def close(self) -> None:
                closed_flag["closed"] = True

        # Ensure component is created
        inject(CloseableComponent)

        # Clear injector to trigger close
        injector().clear()

        self.assertTrue(
            closed_flag["closed"],
            "AutoClose component should be closed on injector clear",
        )

    def test_prototype_not_closed(self) -> None:
        closed_flag = {"closed": False}

        @component(scope=Scope.PROTOTYPE)
        class PrototypeCloseable(AutoClose):
            def close(self) -> None:
                closed_flag["closed"] = True

        inject(PrototypeCloseable)
        injector().clear()

        self.assertFalse(
            closed_flag["closed"],
            "Prototype components should not be managed/closed by container",
        )
