from threading import Lock
from typing import Any, Callable, Generic, Optional, TypeAlias, TypeVar, Union, cast
from jstreams.noop import NoOp, NoOpCls
from jstreams.stream import Opt
from jstreams.utils import isCallable

AnyDict: TypeAlias = dict[str, Any]


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


class ContainerDependency:
    def __init__(self) -> None:
        self.qualifiedDependencies: AnyDict = {}


class VariableDependency:
    def __init__(self) -> None:
        self.qualifiedVariables: AnyDict = {}


T = TypeVar("T")


class _Injector:
    instance: Optional["_Injector"] = None
    instanceLock: Lock = Lock()

    def __init__(self) -> None:
        self.__components: dict[type, ContainerDependency] = {}
        self.__variables: dict[type, VariableDependency] = {}

    def clear(self) -> None:
        self.__components = {}
        self.__variables = {}

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
        foundObj = self._get(className, qualifier)
        return foundObj if foundObj is None else cast(T, foundObj)

    def findOr(
        self,
        className: type[T],
        orCall: Callable[[], T],
        qualifier: Optional[str] = None,
    ) -> T:
        foundObj = self._get(className, qualifier)
        return orCall() if foundObj is None else cast(T, foundObj)

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
        if (varDep := self.__variables.get(className)) is None:
            varDep = VariableDependency()
            self.__variables[className] = varDep
        if qualifier is None:
            qualifier = ""
        varDep.qualifiedVariables[qualifier] = value
        return self

    # Register a component with the container
    def provide(
        self, className: type, comp: Any, qualifier: Optional[str] = None
    ) -> "_Injector":
        if (containerDep := self.__components.get(className)) is None:
            containerDep = ContainerDependency()
            self.__components[className] = containerDep
        if qualifier is None:
            qualifier = ""
        containerDep.qualifiedDependencies[qualifier] = comp
        if isinstance(comp, AutoInit):
            comp.init()
        if isinstance(comp, AutoStart):
            comp.start()

        return self

    # Get a component from the container
    def _get(self, className: type, qualifier: Optional[str]) -> Any:
        if (containerDep := self.__components.get(className)) is None:
            return None
        if qualifier is None:
            qualifier = ""
        foundComponent = containerDep.qualifiedDependencies.get(qualifier, None)
        # We've got a lazy component
        if isCallable(foundComponent):
            # Initialize it
            self.provide(className, foundComponent(), qualifier)
            return self._get(className, qualifier)
        return foundComponent

    def _getVar(self, className: type, qualifier: str) -> Any:
        if (varDep := self.__variables.get(className)) is None:
            return None
        return varDep.qualifiedVariables.get(qualifier, None)

    def provideDependencies(self, dependencies: dict[type, Any]) -> "_Injector":
        for componentClass in dependencies:
            service = dependencies[componentClass]
            self.provide(componentClass, service)
        return self

    def provideVariables(self, variables: list[tuple[type, str, Any]]) -> "_Injector":
        for varClass, qualifier, value in variables:
            self.provideVar(varClass, qualifier, value)
        return self

    def optional(self, className: type[T], qualifier: Optional[str] = None) -> Opt[T]:
        return Opt(self.find(className, qualifier))


Injector = _Injector.getInstance()


def injector() -> _Injector:
    return Injector


def inject(className: type[T], qualifier: Optional[str] = None) -> T:
    return injector().get(className, qualifier)


def var(className: type[T], qualifier: str) -> T:
    return injector().getVar(className, qualifier)


def resolveDependencies(dependencies: dict[str, type]) -> Callable[[type[T]], type[T]]:
    """
    Resolve dependencies decorator.
    Allows class decoration for parameter injection.
    Example:

    @resolveDependencies({"testField": ClassName})
    class TestClass:
        testField: Optional[ClassName]

    Will inject the dependency associated with 'ClassName' into the 'testField' member

    Args:
        dependencies (dict[str, type]): A map of dependencies

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    def wrap(cls: type[T]) -> type[T]:
        for key, typ in dependencies.items():
            if key.startswith("__"):
                raise ValueError(
                    "Cannot inject private attribute. Only public and protected attributes can use injection"
                )
            setattr(cls, key, injector().find(typ))
        return cls

    return wrap


def resolveVariables(
    variables: dict[str, tuple[type, str]],
) -> Callable[[type[T]], type[T]]:
    """
    Resolve varoables decorator.
    Allows class decoration for variables injection.
    Example:

    @resolveVariables({"strValue": (str, "strQualifier"})
    class TestClass:
        strValue: Optional[str]

    Will inject the value associated with 'strQualifier' of type 'str' into the 'strValue' member

    Args:
        variables: dict[str, tuple[type, str]]: A map of variable names to type and key tuple

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    def wrap(cls: type[T]) -> type[T]:
        for key in variables:
            typ, varKey = variables.get(key)
            if key.startswith("__"):
                raise ValueError(
                    "Cannot inject private attribute. Only public and protected attributes can use injection"
                )
            setattr(cls, key, injector().findVar(typ, varKey))
        return cls

    return wrap


class InjectedDependency(Generic[T]):
    __slots__ = ["__typ"]

    def __init__(self, typ: type[T]) -> None:
        self.__typ = typ

    def get(self) -> T:
        return injector().get(self.__typ)


class OptionalInjectedDependency(Generic[T]):
    __slots__ = ["__typ"]

    def __init__(self, typ: type[T]) -> None:
        self.__typ = typ

    def get(self) -> Optional[T]:
        return injector().find(self.__typ)
