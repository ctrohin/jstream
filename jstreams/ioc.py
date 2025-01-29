from threading import Lock
from typing import Any, Callable, Optional, TypeAlias, TypeVar, Union, cast
from jstreams.noop import NoOp, NoOpCls

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
        return self

    # Get a component from the container
    def _get(self, className: type, qualifier: Optional[str]) -> Any:
        if (containerDep := self.__components.get(className)) is None:
            return None
        if qualifier is None:
            qualifier = ""
        return containerDep.qualifiedDependencies.get(qualifier, None)

    def _getVar(self, className: type, qualifier: str) -> Any:
        if (varDep := self.__variables.get(className)) is None:
            return None
        return varDep.qualifiedVariables.get(qualifier, None)

    def provideDependencies(self, dependencies: dict[type, Any]) -> "_Injector":
        for componentClass in dependencies:
            service = dependencies[componentClass]
            self.provide(componentClass, service)
            if isinstance(service, AutoInit):
                service.init()
            if isinstance(service, AutoStart):
                service.start()
        return self

    def provideVariables(self, variables: list[tuple[type, str, Any]]) -> "_Injector":
        for varClass, qualifier, value in variables:
            self.provideVar(varClass, qualifier, value)
        return self


Injector = _Injector.getInstance()


def injector() -> _Injector:
    return Injector


def inject(className: type[T], qualifier: Optional[str] = None) -> T:
    return injector().get(className, qualifier)


def var(className: type[T], qualifier: str) -> T:
    return injector().getVar(className, qualifier)


__all__ = ["Injector", "AutoStart", "AutoInit", "injector", "inject", "var"]
