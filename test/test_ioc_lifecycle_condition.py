from baseTest import BaseTestCase
from jstreams.ioc import (
    injector,
    component,
    post_construct,
    pre_destroy,
    inject_optional,
    configuration,
    provide,
)


class TestIocLifecycleCondition(BaseTestCase):
    def setUp(self) -> None:
        injector().clear()

    def test_lifecycle_decorators(self) -> None:
        lifecycle_log = []

        @component()
        class LifecycleBean:
            @post_construct
            def init(self) -> None:
                lifecycle_log.append("init")

            @pre_destroy
            def destroy(self) -> None:
                lifecycle_log.append("destroy")

        # Trigger creation
        injector().get(LifecycleBean)
        self.assertEqual(lifecycle_log, ["init"])

        # Trigger destruction
        injector().clear()
        self.assertEqual(lifecycle_log, ["init", "destroy"])

    def test_conditional_component_true(self) -> None:
        @component(condition=lambda: True)
        class ConditionalBeanTrue:
            pass

        self.assertIsNotNone(inject_optional(ConditionalBeanTrue))

    def test_conditional_component_false(self) -> None:
        @component(condition=lambda: False)
        class ConditionalBeanFalse:
            pass

        self.assertIsNone(inject_optional(ConditionalBeanFalse))

    def test_conditional_provide_true(self) -> None:
        @configuration()
        class ConfigTrue:
            @provide(str, qualifier="cond_true", condition=lambda: True)
            def provide_string(self) -> str:
                return "exists"

        self.assertEqual(injector().get(str, "cond_true"), "exists")

    def test_conditional_provide_false(self) -> None:
        @configuration()
        class ConfigFalse:
            @provide(str, qualifier="cond_false", condition=lambda: False)
            def provide_string(self) -> str:
                return "should not exist"

        self.assertIsNone(injector().find(str, "cond_false"))
