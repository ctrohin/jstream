from jstreams import inject
from baseTest import BaseTestCase
from jstreams.ioc import (
    InjectedDependency,
    InjectedVariable,
    OptionalInjectedDependency,
    StrVariable,
    inject_args,
    injector,
    resolve_dependencies,
    resolve_variables,
    component,
    Strategy,
    service,
)


@resolve_variables(
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


@resolve_dependencies(
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


@resolve_dependencies(
    {
        "label1": str,
    }
)
@resolve_variables(
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
        injector().provide_var(str, "label", "labelValue")
        mock = MockWithVariables(12)
        self.assertEqual(mock.printValues(), "labelValue12")

    def test_resolve_variables_after_instantiation(self) -> None:
        mock = MockWithVariables(12)
        injector().provide_var(str, "label", "labelValue")
        self.assertEqual(mock.printValues(), "labelValue12")

    def test_resolve_dependency(self) -> None:
        injector().provide(str, "labelValue")
        mock = MockWithDependencies(10)
        self.assertEqual(mock.printValues(), "labelValue10")

    def test_resolve_dependency_provision_after_instantiation(self) -> None:
        mock = MockWithDependencies(10)
        injector().provide(str, "labelValue")
        self.assertEqual(mock.printValues(), "labelValue10")

    def test_resolve_variables_and_dependencies(self) -> None:
        injector().provide_var(str, "label", "labelValueVar")
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

    def test_injected_dependency_builder(self) -> None:
        class Test:
            def mock(self) -> str:
                return "test"

        injector().provide(Test, lambda: Test())
        dep = InjectedDependency(Test)
        self.assertEqual(dep().mock(), "test", "Dependency should be injected")

    def test_injected_dependency_later(self) -> None:
        class Test:
            def mock(self) -> str:
                return "test"

        dep = InjectedDependency(Test)
        injector().provide(Test, Test())
        self.assertEqual(dep().mock(), "test", "Dependency should be injected")

    def test_injected_dependency_builder_later(self) -> None:
        class Test:
            def mock(self) -> str:
                return "test"

        dep = InjectedDependency(Test)
        injector().provide(Test, lambda: Test())
        self.assertEqual(dep().mock(), "test", "Dependency should be injected")

    def test_injected_optional_dependency(self) -> None:
        class Test:
            def mock(self) -> str:
                return "test"

        injector().provide(Test, Test())
        dep = OptionalInjectedDependency(Test)
        self.assertEqual(dep().mock(), "test", "Dependency should be injected")

    def test_injected_variable(self) -> None:
        injector().provide_var(str, "test", "string")
        var = InjectedVariable(str, "test")
        self.assertEqual(
            var(), "string", "Variable should have been injected and correct"
        )

    def test_argument_injection(self) -> None:
        injector().provide_dependencies({str: "test", int: 10})

        class Test:
            @inject_args({"a": str, "b": int})
            def __init__(self, a: str, b: int) -> None:
                self.val = a + str(b)

        self.assertEqual(Test().val, "test10")

    def test_argument_injection_lazy_inject(self) -> None:
        class Test:
            @inject_args({"a": str, "b": int})
            def __init__(self, a: str, b: int) -> None:
                self.val = a + str(b)

        injector().provide_dependencies({str: "test", int: 10})
        self.assertEqual(Test().val, "test10")

    def test_argument_injection_lazy_declare(self) -> None:
        class Test:
            @inject_args({"a": str, "b": int})
            def __init__(self, a: str, b: int) -> None:
                self.val = a + str(b)

        injector().provide_dependencies({str: lambda: "test", int: lambda: 10})
        self.assertEqual(Test().val, "test10")

    def test_all_of_type(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @component()
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @component()
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        testString = "AB"
        stream = injector().all_of_type_stream(ValidatorInterface)
        self.assertEqual(len(stream.to_list()), 2)
        valid = stream.all_match(lambda v: v.validate(testString))
        self.assertTrue(valid)

    def test_component_profile(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @component(profiles=["A"])
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @component(profiles=["B"])
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        injector().activate_profile("A")
        stream = injector().all_of_type_stream(ValidatorInterface)
        self.assertEqual(len(stream.to_list()), 1)
        testString = "AAA"
        valid = stream.all_match(lambda v: v.validate(testString))
        self.assertTrue(valid)

    def test_component_profile_alternate_A(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @component(class_name=ValidatorInterface, profiles=["PROFILE_A"])
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @component(class_name=ValidatorInterface, profiles=["PROFILE_B"])
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        injector().activate_profile("PROFILE_A")
        comp = inject(ValidatorInterface)
        self.assertIsInstance(comp, ContainsAValidator)

    def test_component_profile_alternate_B(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @component(class_name=ValidatorInterface, profiles=["A"])
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @component(class_name=ValidatorInterface, profiles=["B"])
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        injector().activate_profile("B")
        comp = inject(ValidatorInterface)
        self.assertIsInstance(comp, ContainsBValidator)

    def test_service_profile(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @service(profiles=["A"])
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @service(profiles=["B"])
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        injector().activate_profile("A")
        stream = injector().all_of_type_stream(ValidatorInterface)
        self.assertEqual(len(stream.to_list()), 1)
        testString = "AAA"
        valid = stream.all_match(lambda v: v.validate(testString))
        self.assertTrue(valid)

    def test_service_profile_alternate_A(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @service(class_name=ValidatorInterface, profiles=["PROFILE_A"])
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @service(class_name=ValidatorInterface, profiles=["PROFILE_B"])
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        injector().activate_profile("PROFILE_A")
        comp = inject(ValidatorInterface)
        self.assertIsInstance(comp, ContainsAValidator)

    def test_service_profile_alternate_B(self) -> None:
        class ValidatorInterface:
            def validate(self, value: str) -> bool:
                pass

        @service(class_name=ValidatorInterface, profiles=["A"])
        class ContainsAValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "A" in value

        @service(class_name=ValidatorInterface, profiles=["B"])
        class ContainsBValidator(ValidatorInterface):
            def validate(self, value: str) -> bool:
                return "B" in value

        injector().activate_profile("B")
        comp = inject(ValidatorInterface)
        self.assertIsInstance(comp, ContainsBValidator)

    def test_resove_deps_with_resolve_vars(self) -> None:
        @component()
        class Service:
            pass

        @resolve_dependencies({"service": Service})
        @resolve_variables({"variable": StrVariable("variable")})
        class Test:
            service: Service
            variable: str

            def mock(self) -> str:
                return "test"

        injector().provide_var(str, "variable", "value")
        test = Test()
        self.assertIsNotNone(test.service)
        self.assertIsNotNone(test.variable)
