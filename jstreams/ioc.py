from enum import Enum
from random import choice
from string import ascii_letters, digits
from threading import Lock, RLock
from typing import Any, Callable, Generic, Optional, TypeVar, Union, cast

from jstreams import Stream
from jstreams.noop import NoOp, NoOpCls
from jstreams.stream import Opt, each
from jstreams.utils import isCallable


class Strategy(Enum):
    EAGER = 0
    LAZY = 1


class Provided:
    __slots__ = ("__component", "__profiles")

    def __init__(self, component: Any, profiles: list[str]) -> None:
        self.__component = component
        self.__profiles = profiles

    def getComponent(self) -> Any:
        return self.__component

    def getProfiles(self) -> list[str]:
        return self.__profiles


class Dependency:
    __slots__ = ("__typ", "__qualifier", "_isOptional")

    def __init__(self, typ: type, qualifier: Optional[str] = None) -> None:
        self.__typ = typ
        self.__qualifier = qualifier
        self._isOptional = False

    def getType(self) -> type:
        return self.__typ

    def getQualifier(self) -> Optional[str]:
        return self.__qualifier

    def isOptional(self) -> bool:
        return self._isOptional


class OptionalDependency(Dependency):
    def __init__(self, typ: type, qualifier: Optional[str] = None) -> None:
        super().__init__(typ, qualifier)
        self._isOptional = True


class Variable:
    __slots__ = ("__typ", "__key", "__isOptional")

    def __init__(self, typ: type, key: str, isOptional: bool = False) -> None:
        self.__typ = typ
        self.__key = key
        self.__isOptional = isOptional

    def getType(self) -> type:
        return self.__typ

    def getKey(self) -> str:
        return self.__key

    def isOptional(self) -> bool:
        return self.__isOptional


class StrVariable(Variable):
    def __init__(self, key: str, isOptional: bool = False) -> None:
        super().__init__(str, key, isOptional)


class IntVariable(Variable):
    def __init__(self, key: str, isOptional: bool = False) -> None:
        super().__init__(int, key, isOptional)


class FloatVariable(Variable):
    def __init__(self, key: str, isOptional: bool = False) -> None:
        super().__init__(float, key, isOptional)


class ListVariable(Variable):
    def __init__(self, key: str, isOptional: bool = False) -> None:
        super().__init__(list, key, isOptional)


class DictVariable(Variable):
    def __init__(self, key: str, isOptional: bool = False) -> None:
        super().__init__(dict, key, isOptional)


class AutoStart:
    __slots__ = ()
    """
    Interface notifying the container that a component must be started as soon as it
    is added to the container.
    """

    def start(self) -> None:
        pass


class AutoInit:
    __slots__ = ()
    """
    Interface notifying the container that a component must be initialized by calling the 'init' method
    as soon as it is added to the container.
    """

    def init(self) -> None:
        pass


class _ContainerDependency:
    __slots__ = ("qualifiedDependencies", "lock")

    def __init__(self) -> None:
        self.qualifiedDependencies: dict[str, Any] = {}
        self.lock = RLock()


class _VariableDependency:
    __slots__ = ("qualifiedVariables", "lock")

    def __init__(self) -> None:
        self.qualifiedVariables: dict[str, Any] = {}
        self.lock = RLock()


T = TypeVar("T")


class _Injector:
    instance: Optional["_Injector"] = None
    instanceLock: Lock = Lock()
    provideLock: Lock = Lock()

    def __init__(self) -> None:
        self.__components: dict[type, _ContainerDependency] = {}
        self.__variables: dict[type, _VariableDependency] = {}
        self.__defaultQualifier: str = "".join(
            choice(digits + ascii_letters) for i in range(64)
        )
        self.__defaultProfile = "".join(
            choice(digits + ascii_letters) for i in range(16)
        )
        self.__profile: Optional[str] = None

    def __getProfileStr(self) -> str:
        if self.__profile is None:
            return self.__defaultProfile
        return self.__profile

    def __computeProfile(self, profile: Optional[str]) -> str:
        return profile if profile is not None else self.__defaultProfile

    def activateProfile(self, profile: str) -> None:
        if self.__profile is not None:
            raise ValueError(f"Profile ${self.__profile} is already active")
        self.__profile = profile

    def clear(self) -> None:
        self.__components = {}
        self.__variables = {}
        self.__profile = None

    def get(self, className: type[T], qualifier: Optional[str] = None) -> T:
        if (foundObj := self.find(className, qualifier)) is None:
            raise ValueError("No object found for class " + str(className))
        return foundObj

    def getVar(self, className: type[T], qualifier: str) -> T:
        if (foundVar := self.findVar(className, qualifier)) is None:
            raise ValueError(
                "No variable found for class "
                + str(className)
                + " and qualifier "
                + qualifier
            )
        return foundVar

    def findVar(self, className: type[T], qualifier: str) -> Optional[T]:
        foundVar = self._getVar(className, qualifier)
        return foundVar if foundVar is None else cast(T, foundVar)

    def findVarOr(self, className: type[T], qualifier: str, orVal: T) -> Optional[T]:
        foundVar = self._getVar(className, qualifier)
        return orVal if foundVar is None else cast(T, foundVar)

    def find(self, className: type[T], qualifier: Optional[str] = None) -> Optional[T]:
        # Try to get the dependency using the active profile
        foundObj = self._get(className, qualifier)
        if foundObj is None:
            # or get it for the default profile
            foundObj = self._get(
                className,
                self.__getComponentKeyWithProfile(
                    qualifier or self.__defaultQualifier, self.__defaultProfile
                ),
                True,
            )
        return foundObj if foundObj is None else cast(T, foundObj)

    def findOr(
        self,
        className: type[T],
        orCall: Callable[[], T],
        qualifier: Optional[str] = None,
    ) -> T:
        foundObj = self.find(className, qualifier)
        return orCall() if foundObj is None else foundObj

    def findNoOp(
        self, className: type[T], qualifier: Optional[str] = None
    ) -> Union[T, NoOpCls]:
        if (foundObj := self.find(className, qualifier)) is None:
            return NoOp
        return foundObj

    @staticmethod
    def getInstance() -> "_Injector":
        # If the instance is not initialized
        if _Injector.instance is None:
            # Lock for instantiation
            with _Injector.instanceLock:
                # Check if the instance was not already initialized before acquiring the lock
                if _Injector.instance is None:
                    # Initialize
                    _Injector.instance = _Injector()
        return _Injector.instance

    def provideVarIfNotNull(
        self, className: type, qualifier: str, value: Any
    ) -> "_Injector":
        if value is not None:
            self.provideVar(className, qualifier, value)
        return self

    def provideVar(self, className: type, qualifier: str, value: Any) -> "_Injector":
        with self.provideLock:
            if (varDep := self.__variables.get(className)) is None:
                varDep = _VariableDependency()
                self.__variables[className] = varDep
            varDep.qualifiedVariables[qualifier] = value
        return self

    # Register a component with the container
    def provide(
        self,
        className: type,
        comp: Any,
        qualifier: Optional[str] = None,
        profiles: Optional[list[str]] = None,
    ) -> "_Injector":
        with self.provideLock:
            if (containerDep := self.__components.get(className)) is None:
                containerDep = _ContainerDependency()
                self.__components[className] = containerDep
            if qualifier is None:
                qualifier = self.__defaultQualifier
            if profiles is not None:
                for profile in profiles:
                    containerDep.qualifiedDependencies[
                        self.__getComponentKeyWithProfile(
                            qualifier, self.__computeProfile(profile)
                        )
                    ] = comp
            else:
                containerDep.qualifiedDependencies[
                    self.__getComponentKeyWithProfile(
                        qualifier, self.__computeProfile(None)
                    )
                ] = comp

            if isinstance(comp, AutoInit):
                comp.init()
            if isinstance(comp, AutoStart):
                comp.start()

        return self

    def _getAll(self, className: type[T]) -> list[T]:
        elements: list[T] = []
        for key in self.__components:
            dep = self.__components[key]
            for dependencyKey in dep.qualifiedDependencies:
                component = self._get(key, dependencyKey, True)
                if isinstance(component, className):
                    elements.append(component)
        return elements

    def __getComponentKey(self, qualifier: str) -> str:
        return self.__getProfileStr() + qualifier

    def __getComponentKeyWithProfile(self, qualifier: str, profile: str) -> str:
        return profile + qualifier

    # Get a component from the container
    def _get(
        self, className: type, qualifier: Optional[str], overrideQualifier: bool = False
    ) -> Any:
        if (containerDep := self.__components.get(className)) is None:
            return None
        with containerDep.lock:
            if qualifier is None:
                qualifier = self.__defaultQualifier
            foundComponent = containerDep.qualifiedDependencies.get(
                qualifier if overrideQualifier else self.__getComponentKey(qualifier),
                None,
            )
            # We've got a lazy component
            if isCallable(foundComponent):
                # Initialize it
                self.provide(className, foundComponent(), qualifier)
                return self._get(className, qualifier, overrideQualifier)
            return foundComponent

    def _getVar(self, className: type, qualifier: str) -> Any:
        if (varDep := self.__variables.get(className)) is None:
            return None
        with varDep.lock:
            return varDep.qualifiedVariables.get(qualifier, None)

    def provideDependencies(
        self, dependencies: dict[type, Any], profiles: Optional[list[str]] = None
    ) -> "_Injector":
        for componentClass in dependencies:
            service = dependencies[componentClass]
            self.provide(componentClass, service, profiles)
        return self

    def provideVariables(self, variables: list[tuple[type, str, Any]]) -> "_Injector":
        for varClass, qualifier, value in variables:
            self.provideVar(varClass, qualifier, value)
        return self

    def optional(self, className: type[T], qualifier: Optional[str] = None) -> Opt[T]:
        return Opt(self.find(className, qualifier))

    def allOfType(self, className: type[T]) -> list[T]:
        """
        Returns a list of all objects that have or subclass the given type,
        regardless of their actual declared class or qualifiers.

        This method is useful, for example, when retrieving a dynamic list
        of validators that implement the same interface.

        Args:
            className (type[T]): The class or parent class

        Returns:
            list[T]: The list of dependencies available
        """
        return self._getAll(className)

    def allOfTypeStream(self, className: type[T]) -> Stream[T]:
        """
        Returns a stream of all objects that have or subclass the given type,
        regardless of their actual declared class or qualifiers.

        This method is useful, for example, when retrieving a dynamic list
        of validators that implement the same interface.

        Args:
            className (type[T]): The class or parent class

        Returns:
            Stream[T]: A stream of the dependencies available
        """
        return Stream(self.allOfType(className))


Injector = _Injector.getInstance()


def injector() -> _Injector:
    return Injector


def inject(className: type[T], qualifier: Optional[str] = None) -> T:
    return injector().get(className, qualifier)


def var(className: type[T], qualifier: str) -> T:
    return injector().getVar(className, qualifier)


def component(
    strategy: Strategy = Strategy.EAGER,
    className: Optional[type] = None,
    qualifier: Optional[str] = None,
) -> Callable[[type[T]], type[T]]:
    """
    Decorates a component for container injection.

    Args:
        strategy (Strategy, optional): The strategy used for instantiation: EAGER means instantiate as soon as possible, LAZY means instantiate when needed. Defaults to Strategy.EAGER.
        className (Optional[type], optional): Specify which class to use with the container. Defaults to declared class.
        qualifier (Optional[str], optional): Specify the qualifer to be used for the dependency. Defaults to None.

    Returns:
        Callable[[type[T]], type[T]]: The decorated class
    """

    def wrap(cls: type[T]) -> type[T]:
        if strategy == Strategy.EAGER:
            injector().provide(
                className if className is not None else cls, cls(), qualifier
            )
        elif strategy == Strategy.LAZY:
            injector().provide(
                className if className is not None else cls, lambda: cls(), qualifier
            )
        return cls

    return wrap


def validateDependencies(dependencies: dict[str, Any]) -> None:
    for key in dependencies:
        if key.startswith("__"):
            raise ValueError(
                "Private attributes cannot be injected. Offending dependency "
                + str(key)
            )


def resolveDependencies(
    dependencies: dict[str, Union[type, Dependency]],
) -> Callable[[type[T]], type[T]]:
    """
    Resolve dependencies decorator.
    Allows class decoration for parameter injection.
    Example:

    @resolveDependencies({"testField": ClassName})
    class TestClass:
        testField: Optional[ClassName]

    Will inject the dependency associated with 'ClassName' into the 'testField' member

    Args:
        dependencies (Union[type, Dependency]]): A map of dependencies

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    validateDependencies(dependencies)

    def wrap(cls: type[T]) -> type[T]:
        originalGetAttribute = cls.__getattribute__

        def __getattribute__(self, attrName: str) -> Any:  # type: ignore[no-untyped-def]
            if attrName in dependencies:
                quali = dependencies.get(attrName, NoOpCls)
                isOptional = False
                if isinstance(quali, Dependency):
                    typ = quali.getType()
                    qualifier = quali.getQualifier()
                    isOptional = quali.isOptional()
                else:
                    typ = quali
                    qualifier = None
                return (
                    injector().find(typ, qualifier)
                    if isOptional
                    else inject(typ, qualifier)
                )
            return originalGetAttribute(self, attrName)

        cls.__getattribute__ = __getattribute__  # type: ignore[method-assign]
        return cls

    return wrap


def resolveVariables(
    variables: dict[str, Variable],
) -> Callable[[type[T]], type[T]]:
    """
    Resolve variables decorator.
    Allows class decoration for variables injection.
    Example:

    @resolveVariables({"strValue": Variable(str, "strQualifier", True)})
    class TestClass:
        strValue: Optional[str]

    Will inject the value associated with 'strQualifier' of type 'str' into the 'strValue' member

    Args:
        variables: dict[str, dict[str, Variable]]: A map of variable names to type and key tuple

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    validateDependencies(variables)

    def wrap(cls: type[T]) -> type[T]:
        originalGetAttribute = cls.__getattribute__

        def __getattribute__(self, attrName: str) -> Any:  # type: ignore[no-untyped-def]
            if attrName in variables:
                variable = variables.get(attrName)
                if variable is None:
                    return originalGetAttribute(self, attrName)
                return (
                    injector().findVar(variable.getType(), variable.getKey())
                    if variable.isOptional()
                    else injector().getVar(variable.getType(), variable.getKey())
                )
            return originalGetAttribute(
                self, attrName
            )  # Call the original __getattribute__

        cls.__getattribute__ = __getattribute__  # type: ignore[method-assign]
        return cls

    return wrap


def injectArgs(
    dependencies: dict[str, Union[type, Dependency]],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Injects dependencies to a function, method or constructor using args and kwargs.
    Example:

    # Example 1:
    injector().provide(str, "test")
    injector().provide(int, 10)

    @injectArgs({"param1": str, "param2": int})
    def fn(param1: str, param2: int) -> None:
        print(param1 + "_" + param2)

    fn() # will print out "test_10"
    fn(param1="test2") # will print out "test2_10" as param1 is overriden by the actual call
    fn(param1="test2", param2=1) # will print out "test2_1" as both param1 and param2 are overriden by the actual call
    fn(param2=1) # will print out "test_1" as only param2 is overriden by the actual call

    CAUTION: It is possible to also call decorated functions with positional arguments, but in
    this case, all parameters must be provided.
    fn("test2", 1) # will print out "test2_1" as both param1 and param2 are provided by the actual call
    fn("test2") # will result in an ERROR as not all params are provided by the positional arguments

    class TestArgInjection:
    @injectArgs({"a": str, "b": int})
    def __init__(self, a: str, b: int) -> None:
        self.a = a
        self.b = b

    def print(self) -> None:
        print(a + str(b))

    TestArgInjection().print() # Will print out "test10" as both arguments are injected into the constructor
    # IMPORTANT: For constructors, kw arg overriding is not available. When overriding arguments, all arguments must be specified
    TestArgInjection("other", 5).print() # Will print out "other5" as all args are overriden

        Args:
        dependencies (dict[str, Union[type, Dependency]]): A dictionary of dependecies that specify the argument name and the dependency mapping.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: The decorated function or method
    """
    validateDependencies(dependencies)

    def wrapper(func: Callable[..., T]) -> Callable[..., T]:
        def wrapped(*args: Any, **kwds: Any) -> T:
            if func.__name__ == "__init__":
                # We are dealing with a constructor, and must provide positional arguments
                for key in dependencies:
                    dep = dependencies[key]
                    qualif: Optional[str] = None
                    isOptional = False
                    if isinstance(dep, Dependency):
                        qualif = dep.getQualifier()
                        typ = dep.getType()
                        isOptional = dep.isOptional()
                    else:
                        typ = dep
                    args = args + (
                        (
                            injector().find(typ, qualif)
                            if isOptional
                            else inject(typ, qualif)
                        ),
                    )
            elif len(args) == 0:
                for key in dependencies:
                    if kwds.get(key) is None:
                        dep = dependencies[key]
                        quali: Optional[str] = None
                        isOptional = False
                        if isinstance(dep, Dependency):
                            quali = dep.getQualifier()
                            typ = dep.getType()
                            isOptional = dep.isOptional()
                        else:
                            typ = dep
                        kwds[key] = (
                            injector().find(typ, quali)
                            if isOptional
                            else inject(typ, quali)
                        )
            return func(*args, **kwds)

        return wrapped

    return wrapper


class InjectedDependency(Generic[T]):
    __slots__ = ["__typ", "__quali"]

    def __init__(self, typ: type[T], qualifier: Optional[str] = None) -> None:
        self.__typ = typ
        self.__quali = qualifier

    def get(self) -> T:
        return injector().get(self.__typ, self.__quali)

    def __call__(self) -> T:
        return self.get()


class OptionalInjectedDependency(Generic[T]):
    __slots__ = ["__typ", "__quali"]

    def __init__(self, typ: type[T], qualifier: Optional[str] = None) -> None:
        self.__typ = typ
        self.__quali = qualifier

    def get(self) -> Optional[T]:
        return injector().find(self.__typ, self.__quali)

    def __call__(self) -> Optional[T]:
        return self.get()


class InjectedVariable(Generic[T]):
    __slots__ = ["__typ", "__quali"]

    def __init__(self, typ: type[T], qualifier: str) -> None:
        self.__typ = typ
        self.__quali = qualifier

    def get(self) -> T:
        return injector().getVar(self.__typ, self.__quali)

    def __call__(self) -> T:
        return self.get()
