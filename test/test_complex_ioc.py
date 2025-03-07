from baseTest import BaseTestCase
from jstreams.ioc import (
    InjectedDependency,
    InjectedVariable,
    OptionalInjectedDependency,
    StrVariable,
    injector,
    resolveDependencies,
    resolveVariables,
    component,
    Strategy,
)


@resolveVariables(
    {
        "label": StrVariable("label"),
    }
)
class MockWithVariables:
    label: str

    def __init__(self, value: int) -> None:
        self.value = value

    def printValues(self) -> str:
        return self.label + str(self.value)


@resolveDependencies(
    {
        "label": str,
    }
)
class MockWithDependencies:
    label: str

    def __init__(self, value: int) -> None:
        self.value = value

    def printValues(self) -> str:
        return self.label + str(self.value)


@resolveDependencies(
    {
        "label1": str,
    }
)
@resolveVariables(
    {
        "label2": StrVariable("label"),
    }
)
class MockWithDependenciesAndVariables:
    label1: str
    label2: str

    def __init__(self, value: int) -> None:
        self.value = value

    def printValues(self) -> str:
        return self.label1 + str(self.value) + self.label2


EAGER_TEST_INIT_CALLED = False
LAZY_TEST_INIT_CALLED = False


class TestComplexIoc(BaseTestCase):
    def test_resolve_variables(self) -> None:
        injector().provideVar(str, "label", "labelValue")
        mock = MockWithVariables(12)
        self.assertEqual(mock.printValues(), "labelValue12")

    def test_resolve_dependency(self) -> None:
        injector().provide(str, "labelValue")
        mock = MockWithDependencies(10)
        self.assertEqual(mock.printValues(), "labelValue10")

    def test_resolve_variables_and_dependencies(self) -> None:
        injector().provideVar(str, "label", "labelValueVar")
        injector().provide(str, "labelValueDep")
        mock = MockWithDependenciesAndVariables(7)
        self.assertEqual(mock.printValues(), "labelValueDep7labelValueVar")

    def test_component_eager(self) -> None:
        @component(Strategy.EAGER)
        class EagerTest:
            def __init__(self) -> None:
                global EAGER_TEST_INIT_CALLED
                EAGER_TEST_INIT_CALLED = True

        self.assertTrue(EAGER_TEST_INIT_CALLED, "Init should have been called")
        self.assertIsNotNone(
            injector().get(EagerTest), "Test class should have been injected"
        )

    def test_component_lazy(self) -> None:
        @component(Strategy.LAZY)
        class LazyTest:
            def __init__(self) -> None:
                global LAZY_TEST_INIT_CALLED
                LAZY_TEST_INIT_CALLED = True

        self.assertFalse(LAZY_TEST_INIT_CALLED, "Init should not have been called")
        self.assertIsNotNone(
            injector().get(LazyTest), "Test class should have been injected"
        )
        self.assertTrue(LAZY_TEST_INIT_CALLED, "Init should have been called")

    def test_injected_dependency(self) -> None:
        class Test:
            def mock(self) -> str:
                return "test"

        injector().provide(Test, Test())
        dep = InjectedDependency(Test)
        self.assertEqual(dep().mock(), "test", "Dependency should be injected")

    def test_injected_optional_dependency(self) -> None:
        class Test:
            def mock(self) -> str:
                return "test"

        injector().provide(Test, Test())
        dep = OptionalInjectedDependency(Test)
        self.assertEqual(dep().mock(), "test", "Dependency should be injected")

    def test_injected_variable(self) -> None:
        injector().provideVar(str, "test", "string")
        var = InjectedVariable(str, "test")
        self.assertEqual(
            var(), "string", "Variable should have been injected and correct"
        )
