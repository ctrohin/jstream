from enum import Enum
import importlib
from random import choice
from string import ascii_letters, digits
from threading import Lock, RLock
from typing import Any, Callable, Generic, Optional, TypeVar, Union, cast

from jstreams.noop import NoOp, NoOpCls
from jstreams.stream import Opt, Stream
from jstreams.utils import isCallable, requireNotNull


class Strategy(Enum):
    EAGER = 0
    LAZY = 1


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


class SetVariable(Variable):
    def __init__(self, key: str, isOptional: bool = False) -> None:
        super().__init__(set, key, isOptional)


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
        self.__modulesToScan: list[str] = []
        self.__modulesScanned = False
        self.__raiseBeansError = False

    def scanModules(self, modulesToScan: list[str]) -> "_Injector":
        self.__modulesToScan = modulesToScan
        return self

    def __retrieveComponents(self) -> None:
        self.__modulesScanned = True
        for module in self.__modulesToScan:
            importlib.import_module(module)

    def __getProfileStr(self) -> str:
        if self.__profile is None:
            return self.__defaultProfile
        return self.__profile

    def __computeProfile(self, profile: Optional[str]) -> str:
        return profile if profile is not None else self.__defaultProfile

    def activateProfile(self, profile: str) -> None:
        """
        Activates the given injection profile.
        Only components that use the given profile or no profile will be available once a profile is activated.

        Args:
            profile (str): The profile

        Raises:
            ValueError: When a profile is already active.
        """
        if self.__profile is not None:
            raise ValueError(f"Profile ${self.__profile} is already active")
        self.__profile = profile

    def raiseBeanErrors(self, raiseBeanErrors: bool) -> "_Injector":
        self.__raiseBeansError = raiseBeanErrors
        return self

    def handleBeanError(self, message: str) -> None:
        if self.__raiseBeansError:
            raise TypeError(message)
        print(message)

    def clear(self) -> None:
        self.__components = {}
        self.__variables = {}
        self.__profile = None
        self.__modulesScanned = False
        self.__modulesToScan = []

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

    def provideVar(
        self,
        className: type,
        qualifier: str,
        value: Any,
        profiles: Optional[list[str]] = None,
    ) -> "_Injector":
        with self.provideLock:
            if (varDep := self.__variables.get(className)) is None:
                varDep = _VariableDependency()
                self.__variables[className] = varDep
            if profiles is not None:
                for profile in profiles:
                    varDep.qualifiedVariables[
                        self.__getComponentKeyWithProfile(
                            qualifier, self.__computeProfile(profile)
                        )
                    ] = value
            else:
                varDep.qualifiedVariables[
                    self.__getComponentKeyWithProfile(
                        qualifier, self.__computeProfile(None)
                    )
                ] = value

        return self

    def provide(
        self,
        className: type,
        comp: Union[Any, Callable[[], Any]],
        qualifier: Optional[str] = None,
        profiles: Optional[list[str]] = None,
    ) -> "_Injector":
        self.__provide(className, comp, qualifier, profiles, False)
        return self

    def __computeFullQualifier(
        self, qualifier: str, overrideQualifier: bool, profile: Optional[str]
    ) -> str:
        return (
            qualifier
            if overrideQualifier
            else self.__getComponentKeyWithProfile(
                qualifier, self.__computeProfile(profile)
            )
        )

    # Register a component with the container
    def __provide(
        self,
        className: type,
        comp: Union[Any, Callable[[], Any]],
        qualifier: Optional[str] = None,
        profiles: Optional[list[str]] = None,
        overrideQualifier: bool = False,
    ) -> "_Injector":
        with self.provideLock:
            if (containerDep := self.__components.get(className)) is None:
                containerDep = _ContainerDependency()
                self.__components[className] = containerDep
            if qualifier is None:
                qualifier = self.__defaultQualifier
            if profiles is not None:
                for profile in profiles:
                    fullQualifier = self.__computeFullQualifier(
                        qualifier, overrideQualifier, profile
                    )
                    containerDep.qualifiedDependencies[fullQualifier] = comp
            else:
                fullQualifier = self.__computeFullQualifier(
                    qualifier, overrideQualifier, None
                )
                containerDep.qualifiedDependencies[fullQualifier] = comp
            self.__initMeta(comp)

        return self

    def _getAll(self, className: type[T]) -> list[T]:
        elements: list[T] = []
        for key in self.__components:
            dep = self.__components[key]
            for dependencyKey in dep.qualifiedDependencies:
                if self.__isDependencyActive(dependencyKey):
                    comp = self._get(key, dependencyKey, True)
                    if isinstance(comp, className):
                        elements.append(comp)
        return elements

    def __isDependencyActive(self, dependencyKey: str) -> bool:
        return (
            self.__profile is None
            or dependencyKey.startswith(self.__defaultProfile)
            or dependencyKey.startswith(self.__profile)
        )

    def __getComponentKey(self, qualifier: str) -> str:
        return self.__getProfileStr() + qualifier

    def __getComponentKeyWithProfile(self, qualifier: str, profile: str) -> str:
        return profile + qualifier

    # Get a component from the container
    def _get(
        self, className: type, qualifier: Optional[str], overrideQualifier: bool = False
    ) -> Any:
        if not self.__modulesScanned:
            self.__retrieveComponents()
        if (containerDep := self.__components.get(className)) is None:
            return None
        with containerDep.lock:
            if qualifier is None:
                qualifier = self.__defaultQualifier
            fullQualifier = (
                qualifier if overrideQualifier else self.__getComponentKey(qualifier)
            )
            foundComponent = containerDep.qualifiedDependencies.get(
                fullQualifier,
                None,
            )
            # We've got a lazy component
            if isCallable(foundComponent):
                comp = foundComponent()
                # Remove the old dependency
                containerDep.qualifiedDependencies[fullQualifier] = self.__initMeta(
                    comp
                )

                return comp
            return foundComponent

    def __initMeta(self, comp: Any) -> Any:
        if isinstance(comp, AutoInit):
            comp.init()
        if isinstance(comp, AutoStart):
            comp.start()
        return comp

    def _getVar(self, className: type, qualifier: str) -> Any:
        if (varDep := self.__variables.get(className)) is None:
            return None
        with varDep.lock:
            return varDep.qualifiedVariables.get(
                self.__getComponentKey(qualifier), None
            )

    def provideDependencies(
        self, dependencies: dict[type, Any], profiles: Optional[list[str]] = None
    ) -> "_Injector":
        for componentClass in dependencies:
            service = dependencies[componentClass]
            self.provide(componentClass, service, profiles=profiles)
        return self

    def provideVariables(
        self, variables: list[tuple[type, str, Any]], profiles: Optional[list[str]]
    ) -> "_Injector":
        for varClass, qualifier, value in variables:
            self.provideVar(varClass, qualifier, value, profiles)
        return self

    def optional(self, className: type[T], qualifier: Optional[str] = None) -> Opt[T]:
        return Opt(self.find(className, qualifier))

    def varOptional(self, className: type[T], qualifier: str) -> Opt[T]:
        return Opt(self.findVar(className, qualifier))

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


def service(
    className: Optional[type] = None,
    qualifier: Optional[str] = None,
    profiles: Optional[list[str]] = None,
) -> Callable[[type[T]], type[T]]:
    """
    Proxy for @component with the strategy always set to Strategy.LAZY
    """
    return component(Strategy.LAZY, className, qualifier, profiles)


def component(
    strategy: Strategy = Strategy.LAZY,
    className: Optional[type] = None,
    qualifier: Optional[str] = None,
    profiles: Optional[list[str]] = None,
) -> Callable[[type[T]], type[T]]:
    """
    Decorates a component for container injection.

    Args:
        strategy (Strategy, optional): The strategy used for instantiation: EAGER means instantiate as soon as possible, LAZY means instantiate when needed. Defaults to Strategy.LAZY.
        className (Optional[type], optional): Specify which class to use with the container. Defaults to declared class.
        qualifier (Optional[str], optional): Specify the qualifer to be used for the dependency. Defaults to None.
        profiles (Optional[list[str]], optional): Specify the profiles for which this dependency should be available. Defaults to None.

    Returns:
        Callable[[type[T]], type[T]]: The decorated class
    """

    def wrap(cls: type[T]) -> type[T]:
        injector().provide(
            className if className is not None else cls,
            cls() if strategy == Strategy.EAGER else lambda: cls(),
            qualifier,
            profiles,
        )
        return cls

    return wrap


def configuration(profiles: Optional[list[str]] = None) -> Callable[[type[T]], type[T]]:
    """
    Configuration decorator.
    A class can be decorated as a configuration if that class provides one or multiple injection beans.
    Each public method from a decorated class should return a bean decorated with the @bean decoration.
    Example:

    @configuration()
    class Config:
        @bean(str)
        def strBean(self) -> str: # Produces a str bean that can be accessed by inject(str)
            return "test"

    Args:
        profiles (Optional[list[str]], optional): The profiles for which the defined beans will be available for. Defaults to None.

    Returns:
        Callable[[type[T]], type[T]]: The decorated class
    """

    def runBean(obj: Any, attr: str) -> None:
        try:
            getattr(obj, attr)(profiles=profiles)
        except TypeError as _:
            message = (
                "Bean "
                + str(attr)
                + " of class "
                + str(type(obj))
                + " is not properly decorated. In a configuration class, each public method must produce a bean decorated with the @bean decorator. For internal logic, please use protected _method or private __method."
            )
            injector().handleBeanError(message)

    def wrap(cls: type[T]) -> type[T]:
        obj = cls()
        (
            Stream(dir(obj))
            .filter(lambda s: not s.startswith("_"))
            .filter(lambda s: isCallable(getattr(obj, s)))
            .each(lambda s: runBean(obj, s))
        )
        return cls

    return wrap


def bean(
    className: type[T], qualifier: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., None]]:
    """
    Bean decorator. Used for methods inside @configuration classes.
    This decorator is meant to be used in @configuration classes, in order to mark the methods that
    define injected dependencies.

    Args:
        className (type[T]): The dependency class
        qualifier (Optional[str], optional): Optional bean qualifier. Defaults to None.

    Returns:
        Callable[[Callable[..., T]], Callable[..., None]]: The decorated method
    """

    def wrapper(func: Callable[..., T]) -> Callable[..., None]:
        def wrapped(*args: Any, **kwds: Any) -> None:
            profiles: Optional[list[str]] = None
            if "profiles" in kwds:
                profiles = kwds.pop("profiles")

            injector().provide(className, lambda: func(*args), qualifier, profiles)

        return wrapped

    return wrapper


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
                return _getDep(quali)
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
                return _getDep(variable)
            return originalGetAttribute(
                self, attrName
            )  # Call the original __getattribute__

        cls.__getattribute__ = __getattribute__  # type: ignore[method-assign]
        return cls

    return wrap


def _getDep(dep: Union[type, Dependency, Variable]) -> Any:
    qualif: Optional[str] = None
    isOptional = False
    isVariable = False
    if isinstance(dep, Dependency):
        qualif = dep.getQualifier()
        typ = dep.getType()
        isOptional = dep.isOptional()
    elif isinstance(dep, Variable):
        qualif = dep.getKey()
        typ = dep.getType()
        isVariable = True
        isOptional = dep.isOptional()
    else:
        typ = dep

    return (
        (
            injector().findVar(typ, requireNotNull(qualif))
            if isOptional
            else injector().getVar(typ, requireNotNull(qualif))
        )
        if isVariable
        else (injector().find(typ, qualif) if isOptional else inject(typ, qualif))
    )


def injectArgs(
    dependencies: dict[str, Union[type, Dependency, Variable]],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Injects dependencies to a function, method or constructor using args and kwargs.
    Example:

    IMPORTANT: For constructors, kw arg overriding is not available. When overriding arguments, all arguments must be specified, and their order must be exact (see below TestArgInjection)

    # Example 1:
    injector().provide(str, "test")
    injector().provide(int, 10)
    injector().provideVar(str, "var1", "var1Value")

    @injectArgs({"param1": str, "param2": int})
    def fn(param1: str, param2: int) -> None:
        print(param1 + "_" + param2)

    fn() # will print out "test_10"
    fn(param1="test2") # will print out "test2_10" as param1 is overriden by the actual call
    fn(param1="test2", param2=1) # will print out "test2_1" as both param1 and param2 are overriden by the actual call
    fn(param2=1) # will print out "test_1" as only param2 is overriden by the actual call

    # CAUTION: It is possible to also call decorated functions with positional arguments, but in
    # this case, all parameters must be provided.
    fn("test2", 1) # will print out "test2_1" as both param1 and param2 are provided by the actual call
    fn("test2") # will result in an ERROR as not all params are provided by the positional arguments

    class TestArgInjection:
        @injectArgs({"a": str, "b": int, "c": StrVariable("var1)})
        def __init__(self, a: str, b: int, c: str) -> None:
            self.a = a
            self.b = b
            self.c = c

        def print(self) -> None:
            print(a + str(b) + c)

    TestArgInjection().print() # Will print out "test10var1Value" as all three arguments are injected into the constructor
    TestArgInjection("other", 5).print() # Will print out "other5" as all args are overriden

        Args:
        dependencies (dict[str, Union[type, Dependency, Variable]]): A dictionary of dependecies that specify the argument name and the dependency or variable mapping.

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
                    args = args + (_getDep(dep),)
            elif len(args) == 0:
                for key in dependencies:
                    if kwds.get(key) is None:
                        dep = dependencies[key]
                        kwds[key] = _getDep(dep)
            return func(*args, **kwds)

        return wrapped

    return wrapper


def autowired(
    className: type[T], qualifier: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def wrapper(func: Callable[..., T]) -> Callable[..., T]:
        def wrapped(*args: Any, **kwds: Any) -> T:
            return injector().get(className, qualifier)

        return wrapped

    return wrapper


def returnWired(className: type[T]) -> T:
    return cast(T, NoOp)


def returnWiredOptional(className: type[T]) -> Optional[T]:
    return None


def autowiredOptional(
    className: type[T], qualifier: Optional[str] = None
) -> Callable[[Callable[..., Optional[T]]], Callable[..., Optional[T]]]:
    def wrapper(func: Callable[..., Optional[T]]) -> Callable[..., Optional[T]]:
        def wrapped(*args: Any, **kwds: Any) -> Optional[T]:
            return injector().find(className, qualifier)

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
