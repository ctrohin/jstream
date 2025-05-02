from enum import Enum
import importlib
import inspect
from threading import Lock, RLock
from typing import Any, Callable, Generic, Optional, TypeVar, Union, cast

from jstreams.noop import NoOp, NoOpCls
from jstreams.stream import Opt, Stream
from jstreams.utils import is_mth_or_fn, require_non_null


class Strategy(Enum):
    EAGER = 0
    LAZY = 1


class Dependency:
    __slots__ = ["__typ", "__qualifier", "_is_optional"]

    def __init__(self, typ: type, qualifier: Optional[str] = None) -> None:
        self.__typ = typ
        self.__qualifier = qualifier
        self._is_optional = False

    def get_type(self) -> type:
        return self.__typ

    def get_qualifier(self) -> Optional[str]:
        return self.__qualifier

    def is_optional(self) -> bool:
        return self._is_optional


class OptionalDependency(Dependency):
    def __init__(self, typ: type, qualifier: Optional[str] = None) -> None:
        super().__init__(typ, qualifier)
        self._is_optional = True


class Variable:
    __slots__ = ("__typ", "__key", "__is_optional")

    def __init__(self, typ: type, key: str, is_optional: bool = False) -> None:
        self.__typ = typ
        self.__key = key
        self.__is_optional = is_optional

    def get_type(self) -> type:
        return self.__typ

    def get_key(self) -> str:
        return self.__key

    def is_optional(self) -> bool:
        return self.__is_optional


class StrVariable(Variable):
    def __init__(self, key: str, is_optional: bool = False) -> None:
        super().__init__(str, key, is_optional)


class IntVariable(Variable):
    def __init__(self, key: str, is_optional: bool = False) -> None:
        super().__init__(int, key, is_optional)


class FloatVariable(Variable):
    def __init__(self, key: str, is_optional: bool = False) -> None:
        super().__init__(float, key, is_optional)


class ListVariable(Variable):
    def __init__(self, key: str, is_optional: bool = False) -> None:
        super().__init__(list, key, is_optional)


class DictVariable(Variable):
    def __init__(self, key: str, is_optional: bool = False) -> None:
        super().__init__(dict, key, is_optional)


class SetVariable(Variable):
    def __init__(self, key: str, is_optional: bool = False) -> None:
        super().__init__(set, key, is_optional)


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
    __slots__ = ("qualified_dependencies", "lock")

    def __init__(self) -> None:
        self.qualified_dependencies: dict[str, Any] = {}
        self.lock = RLock()


class _VariableDependency:
    __slots__ = ("qualified_variables", "lock")

    def __init__(self) -> None:
        self.qualified_variables: dict[str, Any] = {}


T = TypeVar("T")


class _Injector:
    instance: Optional["_Injector"] = None
    instance_lock: Lock = Lock()
    provide_lock: Lock = Lock()
    load_modules_lock: Lock = Lock()

    def __init__(self) -> None:
        self.__components: dict[type, _ContainerDependency] = {}
        self.__variables: dict[type, _VariableDependency] = {}
        self.__default_qualifier: str = "__DEFAULT_QUALIFIER__"
        self.__default_profile: str = "__DEFAULT_PROFILE__"
        self.__profile: Optional[str] = None
        self.__modules_to_scan: list[str] = []
        self.__modules_scanned = False
        self.__raise_beans_error = False

    def scan_modules(self, modules_to_scan: list[str]) -> "_Injector":
        self.__modules_to_scan = modules_to_scan
        return self

    def __retrieve_components(self) -> None:
        if self.__modules_scanned:
            return
        with self.load_modules_lock:
            if self.__modules_scanned:
                return
            self.__modules_scanned = True
            for module in self.__modules_to_scan:
                importlib.import_module(module)

    def __get_profile_str(self) -> str:
        if self.__profile is None:
            return self.__default_profile
        return self.__profile

    def __compute_profile(self, profile: Optional[str]) -> str:
        return profile if profile is not None else self.__default_profile

    def activate_profile(self, profile: str) -> None:
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

    def get_active_profile(self) -> Optional[str]:
        return self.__profile

    def raise_bean_errors(self, flag: bool) -> "_Injector":
        self.__raise_beans_error = flag
        return self

    def handle_bean_error(self, message: str) -> None:
        if self.__raise_beans_error:
            raise TypeError(message)
        print(message)

    def clear(self) -> None:
        self.__components = {}
        self.__variables = {}
        self.__profile = None
        self.__modules_scanned = False
        self.__modules_to_scan = []

    def get(self, class_name: type[T], qualifier: Optional[str] = None) -> T:
        if (found_obj := self.find(class_name, qualifier)) is None:
            raise ValueError("No object found for class " + str(class_name))
        return found_obj

    def get_var(self, class_name: type[T], qualifier: str) -> T:
        if (found_var := self.find_var(class_name, qualifier)) is None:
            raise ValueError(
                "No variable found for class "
                + str(class_name)
                + " and qualifier "
                + qualifier
            )
        return found_var

    def find_var(self, class_name: type[T], qualifier: str) -> Optional[T]:
        found_var = self._get_var(class_name, qualifier)
        if found_var is None:
            found_var = self._get_var(
                class_name,
                self.__get_component_key_with_profile(
                    qualifier or self.__default_qualifier, self.__default_profile
                ),
                True,
            )

        return found_var if found_var is None else cast(T, found_var)

    def find_var_or(
        self, class_name: type[T], qualifier: str, or_val: T
    ) -> Optional[T]:
        found_var = self.find_var(class_name, qualifier)
        return or_val if found_var is None else found_var

    def find(self, class_name: type[T], qualifier: Optional[str] = None) -> Optional[T]:
        # Try to get the dependency using the active profile
        found_obj = self._get(class_name, qualifier)
        if found_obj is None:
            # or get it for the default profile
            found_obj = self._get(
                class_name,
                self.__get_component_key_with_profile(
                    qualifier or self.__default_qualifier, self.__default_profile
                ),
                True,
            )
        return found_obj if found_obj is None else cast(T, found_obj)

    def find_or(
        self,
        class_name: type[T],
        or_call: Callable[[], T],
        qualifier: Optional[str] = None,
    ) -> T:
        found_obj = self.find(class_name, qualifier)
        return or_call() if found_obj is None else found_obj

    def find_noop(
        self, class_name: type[T], qualifier: Optional[str] = None
    ) -> Union[T, NoOpCls]:
        if (found_obj := self.find(class_name, qualifier)) is None:
            return NoOp
        return found_obj

    @staticmethod
    def get_instance() -> "_Injector":
        # If the instance is not initialized
        if _Injector.instance is None:
            # Lock for instantiation
            with _Injector.instance_lock:
                # Check if the instance was not already initialized before acquiring the lock
                if _Injector.instance is None:
                    # Initialize
                    _Injector.instance = _Injector()
        return _Injector.instance

    def provide_var_if_not_null(
        self, class_name: type, qualifier: str, value: Any
    ) -> "_Injector":
        if value is not None:
            self.provide_var(class_name, qualifier, value)
        return self

    def provide_var(
        self,
        class_name: type,
        qualifier: str,
        value: Any,
        profiles: Optional[list[str]] = None,
    ) -> "_Injector":
        with self.provide_lock:
            if (var_dep := self.__variables.get(class_name)) is None:
                var_dep = _VariableDependency()
                self.__variables[class_name] = var_dep
            if profiles is not None:
                for profile in profiles:
                    var_dep.qualified_variables[
                        self.__get_component_key_with_profile(
                            qualifier, self.__compute_profile(profile)
                        )
                    ] = value
            else:
                var_dep.qualified_variables[
                    self.__get_component_key_with_profile(
                        qualifier, self.__compute_profile(None)
                    )
                ] = value

        return self

    def provide(
        self,
        class_name: type,
        comp: Union[Any, Callable[[], Any]],
        qualifier: Optional[str] = None,
        profiles: Optional[list[str]] = None,
    ) -> "_Injector":
        self.__provide(class_name, comp, qualifier, profiles, False)
        return self

    def __compute_full_qualifier(
        self, qualifier: str, override_qualifier: bool, profile: Optional[str]
    ) -> str:
        return (
            qualifier
            if override_qualifier
            else self.__get_component_key_with_profile(
                qualifier, self.__compute_profile(profile)
            )
        )

    # Register a component with the container
    def __provide(
        self,
        class_name: type,
        comp: Union[Any, Callable[[], Any]],
        qualifier: Optional[str] = None,
        profiles: Optional[list[str]] = None,
        override_qualifier: bool = False,
    ) -> "_Injector":
        with self.provide_lock:
            if (container_dep := self.__components.get(class_name)) is None:
                container_dep = _ContainerDependency()
                self.__components[class_name] = container_dep
            if qualifier is None:
                qualifier = self.__default_qualifier
            if profiles is not None:
                for profile in profiles:
                    full_qualifier = self.__compute_full_qualifier(
                        qualifier, override_qualifier, profile
                    )
                    container_dep.qualified_dependencies[full_qualifier] = comp
            else:
                full_qualifier = self.__compute_full_qualifier(
                    qualifier, override_qualifier, None
                )
                container_dep.qualified_dependencies[full_qualifier] = comp
            self.__init_meta(comp)

        return self

    def _get_all(self, class_name: type[T]) -> list[T]:
        elements: list[T] = []
        for key in self.__components:
            dep = self.__components[key]
            for dependency_key in dep.qualified_dependencies:
                if self.__is_dependency_active(dependency_key):
                    comp = self._get(key, dependency_key, True)
                    if isinstance(comp, class_name):
                        elements.append(comp)
        return elements

    def __is_dependency_active(self, dependency_key: str) -> bool:
        return (
            self.__profile is None
            or dependency_key.startswith(self.__default_profile)
            or dependency_key.startswith(self.__profile)
        )

    def __get_component_key(self, qualifier: str) -> str:
        return self.__get_profile_str() + qualifier

    def __get_component_key_with_profile(self, qualifier: str, profile: str) -> str:
        return profile + qualifier

    def __get_full_qualifier(
        self, qualifier: Optional[str], override_qualifier: bool
    ) -> str:
        if qualifier is None:
            qualifier = self.__default_qualifier
        return qualifier if override_qualifier else self.__get_component_key(qualifier)

    def __initialize_and_get(
        self, container_dep: _ContainerDependency, full_qualifier: str
    ) -> Any:
        found_component = container_dep.qualified_dependencies.get(
            full_qualifier,
            None,
        )

        if is_mth_or_fn(found_component):
            comp = found_component()
            # Remove the old dependency
            container_dep.qualified_dependencies[full_qualifier] = self.__init_meta(
                comp
            )
            return comp
        return found_component

    # Get a component from the container
    def _get(
        self,
        class_name: type,
        qualifier: Optional[str],
        override_qualifier: bool = False,
    ) -> Any:
        self.__retrieve_components()
        if (container_dep := self.__components.get(class_name)) is None:
            return None
        full_qualifier = self.__get_full_qualifier(qualifier, override_qualifier)
        found_component = container_dep.qualified_dependencies.get(
            full_qualifier,
            None,
        )

        if found_component is None:
            return None

        # We've got a lazy component
        if is_mth_or_fn(found_component):
            # We need to lock in the instantiation, so it will only happen once.
            with container_dep.lock:
                # Once we've got the lock, get the component again, and make sure no other thread has already instatiated it
                return self.__initialize_and_get(container_dep, full_qualifier)

        return found_component

    def _get_var(
        self, class_name: type, qualifier: str, override_qualifier: bool = False
    ) -> Any:
        self.__retrieve_components()

        if (var_dep := self.__variables.get(class_name)) is None:
            return None

        full_qualifier = (
            qualifier if override_qualifier else self.__get_component_key(qualifier)
        )

        return var_dep.qualified_variables.get(full_qualifier, None)

    def __init_meta(self, comp: Any) -> Any:
        if isinstance(comp, AutoInit):
            comp.init()
        if isinstance(comp, AutoStart):
            comp.start()
        return comp

    def provide_dependencies(
        self, dependencies: dict[type, Any], profiles: Optional[list[str]] = None
    ) -> "_Injector":
        for component_class in dependencies:
            svc = dependencies[component_class]
            self.provide(component_class, svc, profiles=profiles)
        return self

    def provide_variables(
        self, variables: list[tuple[type, str, Any]], profiles: Optional[list[str]]
    ) -> "_Injector":
        for var_class, qualifier, value in variables:
            self.provide_var(var_class, qualifier, value, profiles)
        return self

    def optional(self, class_name: type[T], qualifier: Optional[str] = None) -> Opt[T]:
        return Opt(self.find(class_name, qualifier))

    def var_optional(self, class_name: type[T], qualifier: str) -> Opt[T]:
        return Opt(self.find_var(class_name, qualifier))

    def all_of_type(self, class_name: type[T]) -> list[T]:
        """
        Returns a list of all objects that have or subclass the given type,
        regardless of their actual declared class or qualifiers.

        This method is useful, for example, when retrieving a dynamic list
        of validators that implement the same interface.

        Args:
            class_name (type[T]): The class or parent class

        Returns:
            list[T]: The list of dependencies available
        """
        return self._get_all(class_name)

    def all_of_type_stream(self, class_name: type[T]) -> Stream[T]:
        """
        Returns a stream of all objects that have or subclass the given type,
        regardless of their actual declared class or qualifiers.

        This method is useful, for example, when retrieving a dynamic list
        of validators that implement the same interface.

        Args:
            class_name (type[T]): The class or parent class

        Returns:
            Stream[T]: A stream of the dependencies available
        """
        return Stream(self.all_of_type(class_name))


Injector = _Injector.get_instance()


def injector() -> _Injector:
    return Injector


def inject(class_name: type[T], qualifier: Optional[str] = None) -> T:
    return injector().get(class_name, qualifier)


def var(class_name: type[T], qualifier: str) -> T:
    return injector().get_var(class_name, qualifier)


def service(
    class_name: Optional[type] = None,
    qualifier: Optional[str] = None,
    profiles: Optional[list[str]] = None,
) -> Callable[[type[T]], type[T]]:
    """
    Proxy for @component with the strategy always set to Strategy.LAZY
    """
    return component(Strategy.LAZY, class_name, qualifier, profiles)


def component(
    strategy: Strategy = Strategy.LAZY,
    class_name: Optional[type] = None,
    qualifier: Optional[str] = None,
    profiles: Optional[list[str]] = None,
) -> Callable[[type[T]], type[T]]:
    """
    Decorates a component for container injection.

    Args:
        strategy (Strategy, optional): The strategy used for instantiation: EAGER means instantiate as soon as possible, LAZY means instantiate when needed. Defaults to Strategy.LAZY.
        class_name (Optional[type], optional): Specify which class to use with the container. Defaults to declared class.
        qualifier (Optional[str], optional): Specify the qualifer to be used for the dependency. Defaults to None.
        profiles (Optional[list[str]], optional): Specify the profiles for which this dependency should be available. Defaults to None.

    Returns:
        Callable[[type[T]], type[T]]: The decorated class
    """

    def wrap(cls: type[T]) -> type[T]:
        injector().provide(
            class_name if class_name is not None else cls,
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
        @provide(str)
        def strBean(self) -> str: # Produces a str dependency that can be accessed by inject(str)
            return "test"

    Args:
        profiles (Optional[list[str]], optional): The profiles for which the defined dependencies will be available for. Defaults to None.

    Returns:
        Callable[[type[T]], type[T]]: The decorated class
    """

    def run_bean(obj: Any, attr: str) -> None:
        try:
            getattr(obj, attr)(profiles=profiles)
        except TypeError as _:
            message = (
                "Dependency "
                + str(attr)
                + " of class "
                + str(type(obj))
                + " is not properly decorated. In a configuration class, each public method must produce a dependency decorated with the @provide decorator. For internal logic, please use protected _method or private __method."
            )
            injector().handle_bean_error(message)

    def wrap(cls: type[T]) -> type[T]:
        obj = cls()
        (
            Stream(dir(obj))
            .filter(lambda s: not s.startswith("_"))
            .filter(lambda s: is_mth_or_fn(getattr(obj, s)))
            .each(lambda s: run_bean(obj, s))
        )
        return cls

    return wrap


def provide(
    class_name: type[T], qualifier: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., None]]:
    """
    Provide decorator. Used for methods inside @configuration classes.
    This decorator is meant to be used in @configuration classes, in order to mark the methods that
    define injected dependencies.

    Args:
        class_name (type[T]): The dependency class
        qualifier (Optional[str], optional): Optional dependency qualifier. Defaults to None.

    Returns:
        Callable[[Callable[..., T]], Callable[..., None]]: The decorated method
    """

    def wrapper(func: Callable[..., T]) -> Callable[..., None]:
        def wrapped(*args: Any, **kwds: Any) -> None:
            profiles: Optional[list[str]] = None
            if "profiles" in kwds:
                profiles = kwds.pop("profiles")

            injector().provide(class_name, lambda: func(*args), qualifier, profiles)

        return wrapped

    return wrapper


def provide_variable(
    class_name: type[T], qualifier: str
) -> Callable[[Callable[..., T]], Callable[..., None]]:
    """
    Provide variable decorator. Used for methods inside @configuration classes.
    This decorator is meant to be used in @configuration classes, in order to mark the methods that
    define injected variables.

    Args:
        class_name (type[T]): The dependency class
        qualifier (str): Mandatory variable qualifier. Defaults to None.

    Returns:
        Callable[[Callable[..., T]], Callable[..., None]]: The decorated method
    """

    def wrapper(func: Callable[..., T]) -> Callable[..., None]:
        def wrapped(*args: Any, **kwds: Any) -> None:
            profiles: Optional[list[str]] = None
            if "profiles" in kwds:
                profiles = kwds.pop("profiles")

            injector().provide_var(class_name, qualifier, func(*args), profiles)

        return wrapped

    return wrapper


def validate_dependencies(dependencies: dict[str, Any]) -> None:
    for key in dependencies:
        if key.startswith("__"):
            raise ValueError(
                "Private attributes cannot be injected. Offending dependency "
                + str(key)
            )


def resolve_dependencies(
    dependencies: dict[str, Union[type, Dependency]],
) -> Callable[[type[T]], type[T]]:
    """
    Resolve dependencies decorator.
    Allows class decoration for parameter injection.
    Example:

    @resolve_dependencies({"test_field": ClassName})
    class TestClass:
        test_field: Optional[ClassName]

    Will inject the dependency associated with 'ClassName' into the 'test_field' member

    Args:
        dependencies (dict[str, Union[type, Dependency]]): A map of dependencies

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """
    return resolve(cast(dict[str, Union[type, Dependency, Variable]], dependencies))


def resolve(
    dependencies: dict[str, Union[type, Dependency, Variable]],
) -> Callable[[type[T]], type[T]]:
    """
    Resolve dependencies decorator.
    Allows class decoration for parameter injection.
    Example:

    @resolve({"test_field": ClassName, "str_value": Variable(str, "strQualifier", True)})
    class TestClass:
        test_field: Optional[ClassName]
        str_value: Optional[str]

    Will inject the dependency associated with 'ClassName' into the 'test_field' member,
    and the variable associated with 'strQualifier' into the 'str_value' member

    Args:
        dependencies (dict[str, Union[type, Dependency, Variable]]): A map of dependencies

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    validate_dependencies(dependencies)

    def wrap(cls: type[T]) -> type[T]:
        original_get_attribute = cls.__getattribute__

        def __getattribute__(self, attr_name: str) -> Any:  # type: ignore[no-untyped-def]
            if attr_name in dependencies:
                quali = dependencies.get(attr_name, NoOpCls)
                dep = _get_dep(quali)
                if dep is not None:
                    # If a dependency has been resolved, set it as an attribute of the class
                    setattr(cls, attr_name, dep)
                    # The remove it from the dependencies map
                    dependencies.pop(attr_name)
                return dep
            return original_get_attribute(self, attr_name)

        cls.__getattribute__ = __getattribute__  # type: ignore[method-assign]
        return cls

    return wrap


def resolve_variables(
    variables: dict[str, Variable],
) -> Callable[[type[T]], type[T]]:
    """
    Resolve variables decorator.
    Allows class decoration for variables injection.
    Example:

    @resolve_variables({"str_value": Variable(str, "strQualifier", True)})
    class TestClass:
        str_value: Optional[str]

    Will inject the value associated with 'strQualifier' of type 'str' into the 'str_value' member

    Args:
        variables: dict[str, Variable]: A map of variable names to Variable definition

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    return resolve(cast(dict[str, Union[type, Dependency, Variable]], variables))


def _get_dep(dep: Union[type, Dependency, Variable]) -> Any:
    qualifier: Optional[str] = None
    is_optional = False
    is_variable = False
    if isinstance(dep, Dependency):
        qualifier = dep.get_qualifier()
        typ = dep.get_type()
        is_optional = dep.is_optional()
    elif isinstance(dep, Variable):
        qualifier = dep.get_key()
        typ = dep.get_type()
        is_variable = True
        is_optional = dep.is_optional()
    else:
        typ = dep

    return (
        (
            injector().find_var(typ, require_non_null(qualifier))
            if is_optional
            else injector().get_var(typ, require_non_null(qualifier))
        )
        if is_variable
        else (
            injector().find(typ, qualifier) if is_optional else inject(typ, qualifier)
        )
    )


def inject_args(
    dependencies: dict[str, Union[type, Dependency, Variable]],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Injects dependencies/variables into function/method arguments if they are not already provided by the caller.

    This decorator inspects the function signature and the arguments passed during the call.
    For each argument name specified in the `dependencies` dictionary, if that argument
    was *not* provided by the caller (either positionally or by keyword), the corresponding
    dependency or variable is resolved from the injector and passed as a keyword argument.

    Example:
        injector().provide(str, "default_string")
        injector().provide(int, 100, qualifier="special_int")
        injector().provide_var(float, "some.float.key", 3.14)

        @inject_args({
            "arg1": str,
            "arg2": Dependency(int, qualifier="special_int"),
            "arg3": Variable(float, "some.float.key")
        })
        def my_function(arg1: str, arg2: int, arg3: float, arg4: bool = True):
            print(f"{arg1=}, {arg2=}, {arg3=}, {arg4=}")

        # Variable("some.float.key") resolves to 3.14
        my_function(arg4=False)
        # Output: arg1='default_string', arg2=100, arg3=3.14, arg4=False

        my_function("explicit_string", arg4=False)
        # Output: arg1='explicit_string', arg2=100, arg3=3.14, arg4=False

        my_function("explicit_string", 50, arg4=False) # arg3 still injected
        # Output: arg1='explicit_string', arg2=50, arg3=3.14, arg4=False

        my_function("explicit", 50, 9.99, False) # Nothing injected
        # Output: arg1='explicit', arg2=50, arg3=9.99, arg4=False

    Args:
        dependencies (dict[str, Union[type, Dependency, Variable]]):
            A dictionary mapping argument names to their corresponding dependency type,
            Dependency object, or Variable object.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: The decorated function or method.

    Raises:
        ValueError: If a required dependency/variable cannot be resolved by the injector.
        TypeError: If the arguments passed during the call are fundamentally incompatible
                    with the function signature (e.g., too many positional arguments).
    """
    validate_dependencies(dependencies)  # Keep validation

    def wrapper(func: Callable[..., T]) -> Callable[..., T]:
        sig = inspect.signature(func)

        def wrapped(*args: Any, **kwds: Any) -> T:
            try:
                # Bind provided arguments to see what's missing
                # Use bind_partial as not all args might be provided yet (we inject the rest)
                bound_args = sig.bind_partial(*args, **kwds)
                # Consider arguments with defaults as "provided" for injection purposes
                bound_args.apply_defaults()
            except TypeError as e:
                # Reraise if basic binding fails (e.g., too many positional args)
                raise TypeError(
                    f"Error binding arguments for {func.__qualname__}: {e}"
                ) from e

            # Prepare keyword arguments for injection
            injected_kwds = {}
            for param_name, dep_info in dependencies.items():
                # Check if the argument was already provided by the caller or has a default
                if param_name not in bound_args.arguments:
                    try:
                        # Resolve the dependency/variable
                        resolved_dep = _get_dep(dep_info)
                        injected_kwds[param_name] = resolved_dep
                    except ValueError as e:
                        # Dependency not found - re-raise with more context
                        raise ValueError(
                            f"Failed to inject argument '{param_name}' for {func.__qualname__}: {e}"
                        ) from e
                    except Exception as e:
                        # Catch other potential errors during resolution
                        raise RuntimeError(
                            f"Unexpected error injecting argument '{param_name}' for {func.__qualname__}: {e}"
                        ) from e

            # Combine original kwds and injected kwds.
            # Caller's explicit kwds take precedence over injected ones.
            final_kwds = {**injected_kwds, **kwds}

            # Call the original function with original args and combined kwds
            return func(*args, **final_kwds)

        # Preserve original function metadata for introspection and debugging
        wrapped.__name__ = func.__name__
        wrapped.__qualname__ = func.__qualname__
        wrapped.__doc__ = func.__doc__

        return wrapped

    return wrapper


# def inject_args(
#     dependencies: dict[str, Union[type, Dependency, Variable]],
# ) -> Callable[[Callable[..., T]], Callable[..., T]]:
#     """
#     Injects dependencies to a function, method or constructor using args and kwargs.
#     Example:

#     IMPORTANT: For constructors, kw arg overriding is not available. When overriding arguments, all arguments must be specified, and their order must be exact (see below TestArgInjection)

#     # Example 1:
#     injector().provide(str, "test")
#     injector().provide(int, 10)
#     injector().provide_var(str, "var1", "var1Value")

#     @inject_args({"param1": str, "param2": int})
#     def fn(param1: str, param2: int) -> None:
#         print(param1 + "_" + param2)

#     fn() # will print out "test_10"
#     fn(param1="test2") # will print out "test2_10" as param1 is overriden by the actual call
#     fn(param1="test2", param2=1) # will print out "test2_1" as both param1 and param2 are overriden by the actual call
#     fn(param2=1) # will print out "test_1" as only param2 is overriden by the actual call

#     # CAUTION: It is possible to also call decorated functions with positional arguments, but in
#     # this case, all parameters must be provided.
#     fn("test2", 1) # will print out "test2_1" as both param1 and param2 are provided by the actual call
#     fn("test2") # will result in an ERROR as not all params are provided by the positional arguments

#     class TestArgInjection:
#         @inject_args({"a": str, "b": int, "c": StrVariable("var1)})
#         def __init__(self, a: str, b: int, c: str) -> None:
#             self.a = a
#             self.b = b
#             self.c = c

#         def print(self) -> None:
#             print(a + str(b) + c)

#     TestArgInjection().print() # Will print out "test10var1Value" as all three arguments are injected into the constructor
#     TestArgInjection("other", 5).print() # Will print out "other5" as all args are overriden

#         Args:
#         dependencies (dict[str, Union[type, Dependency, Variable]]): A dictionary of dependecies that specify the argument name and the dependency or variable mapping.

#     Returns:
#         Callable[[Callable[..., T]], Callable[..., T]]: The decorated function or method
#     """
#     validate_dependencies(dependencies)

#     def wrapper(func: Callable[..., T]) -> Callable[..., T]:
#         def wrapped(*args: Any, **kwds: Any) -> T:
#             if func.__name__ == "__init__":
#                 # We are dealing with a constructor, and must provide positional arguments
#                 for key in dependencies:
#                     dep = dependencies[key]
#                     args = args + (_get_dep(dep),)
#             elif len(args) == 0:
#                 for key in dependencies:
#                     if kwds.get(key) is None:
#                         dep = dependencies[key]
#                         kwds[key] = _get_dep(dep)
#             return func(*args, **kwds)

#         wrapped.__name__ = func.__name__
#         wrapped.__qualname__ = func.__qualname__
#         return wrapped

#     return wrapper


def autowired(
    class_name: type[T], qualifier: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that replaces the decorated function's body entirely.
    When the decorated function is called, it will instead retrieve and return
    a mandatory dependency of `class_name` with the optional `qualifier`.

    Useful for creating simple getter methods or properties backed by injected dependencies.

    Example:
        class ServiceClient:
            @property
            @autowired(HttpClient) # Decorate the property's getter
            def http_client(self) -> HttpClient:
                # This body is replaced by the injector call
                return return_wired(HttpClient) # Use return_wired for type hinting

    Args:
        class_name (type[T]): The type of the dependency to inject.
        qualifier (Optional[str], optional): The qualifier name. Defaults to None.

    Returns:
        Callable[[Callable[..., T]], Callable[..., T]]: The decorator function.
    """

    def wrapper(func: Callable[..., T]) -> Callable[..., T]:
        def wrapped(*args: Any, **kwds: Any) -> T:
            return injector().get(class_name, qualifier)

        return wrapped

    return wrapper


def return_wired(class_name: type[T]) -> T:
    """
    Placeholder function used for type hinting within methods decorated with `@autowired`.
    It signals that the method's return value will be provided by the injector.
    This function's body is never actually executed when used with `@autowired`.

    Args:
        class_name (type[T]): The type that will be injected.

    Returns:
        T: A placeholder value (currently `NoOp`), primarily for type checking.
    """
    return cast(T, NoOp)


def return_wired_optional(class_name: type[T]) -> Optional[T]:
    """
    Placeholder function used for type hinting within methods decorated with `@autowired_optional`.
    It signals that the method's return value will be provided by the injector and might be None.
    This function's body is never actually executed when used with `@autowired_optional`.

    Args:
        class_name (type[T]): The type that will be injected.

    Returns:
        Optional[T]: A placeholder value (None), primarily for type checking.
    """
    return None


def autowired_optional(
    class_name: type[T], qualifier: Optional[str] = None
) -> Callable[[Callable[..., Optional[T]]], Callable[..., Optional[T]]]:
    """
    Decorator that replaces the decorated function's body entirely.
    When the decorated function is called, it will instead retrieve and return
    an optional dependency of `class_name` with the optional `qualifier`.

    Useful for creating simple getter methods or properties for optional dependencies.

    Example:
        class ServiceClient:
            @property
            @autowired_optional(Logger, qualifier="request_logger")
            def logger(self) -> Optional[Logger]:
                # This body is replaced by the injector call
                return return_wired_optional(Logger) # Use return_wired_optional for type hinting

    Args:
        class_name (type[T]): The type of the dependency to inject.
        qualifier (Optional[str], optional): The qualifier name. Defaults to None.

    Returns:
        Callable[[Callable[..., Optional[T]]], Callable[..., Optional[T]]]: The decorator function.
    """

    def wrapper(func: Callable[..., Optional[T]]) -> Callable[..., Optional[T]]:
        def wrapped(*args: Any, **kwds: Any) -> Optional[T]:
            return injector().find(class_name, qualifier)

        return wrapped

    return wrapper


class InjectedDependency(Generic[T]):
    """
    A wrapper that holds a request for a mandatory dependency.

    The dependency is retrieved from the injector only when the wrapper instance
    is called (`wrapper()`) or its `get()` method is called. This allows deferring
    injection until the dependency is actually needed, useful when the dependency
    might not be available at the time the wrapper is created.

    Example:
        class NeedsDbLater:
            def __init__(self):
                # Request the dependency, but don't inject yet
                self.db_conn_provider = InjectedDependency(DatabaseConnection)

            def execute_query(self, query: str):
                # Inject the dependency when needed
                conn = self.db_conn_provider() # or self.db_conn_provider.get()
                conn.execute(query)
    """

    __slots__ = ["__typ", "__quali", "__actual_value"]

    def __init__(self, typ: type[T], qualifier: Optional[str] = None) -> None:
        """
        Initializes the dependency request wrapper.

        Args:
            typ (type[T]): The type of the dependency.
            qualifier (Optional[str], optional): The qualifier name. Defaults to None.
        """
        self.__typ = typ
        self.__quali = qualifier
        self.__actual_value: Optional[T] = None

    def get(self) -> T:
        """
        Retrieves the mandatory dependency from the injector.

        Returns:
            T: The dependency instance.

        Raises:
            ValueError: If the dependency is not found.
        """
        if self.__actual_value is not None:
            return self.__actual_value
        # Cache the value
        self.__actual_value = injector().get(self.__typ, self.__quali)
        return self.__actual_value

    def __call__(self) -> T:
        """
        Retrieves the mandatory dependency from the injector. Syntactic sugar for `get()`.

        Returns:
            T: The dependency instance.

        Raises:
            ValueError: If the dependency is not found.
        """
        return self.get()


class OptionalInjectedDependency(Generic[T]):
    """
    A wrapper that holds a request for an optional dependency.

    The dependency is retrieved from the injector only when the wrapper instance
    is called (`wrapper()`) or its `get()` method is called. Returns None if the
    dependency is not found.

    Example:
        class MaybeNeedsLogger:
            def __init__(self):
                self.logger_provider = OptionalInjectedDependency(Logger)

            def log_message(self, msg: str):
                logger = self.logger_provider() # or self.logger_provider.get()
                if logger:
                    logger.info(msg)
    """

    __slots__ = ["__typ", "__quali", "__actual_value"]

    def __init__(self, typ: type[T], qualifier: Optional[str] = None) -> None:
        """
        Initializes the optional dependency request wrapper.

        Args:
            typ (type[T]): The type of the dependency.
            qualifier (Optional[str], optional): The qualifier name. Defaults to None.
        """
        self.__typ = typ
        self.__quali = qualifier
        self.__actual_value: Optional[T] = None

    def get(self) -> Optional[T]:
        """
        Retrieves the optional dependency from the injector.

        Returns:
            Optional[T]: The dependency instance if found, otherwise None.
        """
        if self.__actual_value is not None:
            return self.__actual_value
        # Cache the value
        self.__actual_value = injector().find(self.__typ, self.__quali)
        return self.__actual_value

    def __call__(self) -> Optional[T]:
        """
        Retrieves the optional dependency from the injector. Syntactic sugar for `get()`.

        Returns:
            Optional[T]: The dependency instance if found, otherwise None.
        """
        return self.get()


class InjectedVariable(Generic[T]):
    """
    A wrapper that holds a request for a mandatory configuration variable.

    The variable is retrieved from the injector only when the wrapper instance
    is called (`wrapper()`) or its `get()` method is called.

    Example:
        class ConfigReader:
            def __init__(self):
                self.api_key_provider = InjectedVariable(str, "api.secret_key")

            def get_key(self) -> str:
                return self.api_key_provider() # or self.api_key_provider.get()
    """

    __slots__ = ["__typ", "__quali", "__actual_value"]

    def __init__(self, typ: type[T], qualifier: str) -> None:
        """
        Initializes the variable request wrapper.

        Args:
            typ (type[T]): The expected type of the variable.
            qualifier (str): The key (name) of the variable.
        """
        self.__typ = typ
        self.__quali = qualifier  # Qualifier here means the variable key
        self.__actual_value: Optional[T] = None

    def get(self) -> T:
        """
        Retrieves the mandatory variable from the injector.

        Returns:
            T: The variable value.

        Raises:
            ValueError: If the variable is not found.
        """
        if self.__actual_value is not None:
            return self.__actual_value
        # Cache the value
        self.__actual_value = injector().get_var(self.__typ, self.__quali)
        return self.__actual_value

    def __call__(self) -> T:
        """
        Retrieves the mandatory variable from the injector. Syntactic sugar for `get()`.

        Returns:
            T: The variable value.

        Raises:
            ValueError: If the variable is not found.
        """
        return self.get()


class _InspectedElement:
    def __init__(
        self, element_name: str, element_type: type, is_optional: bool
    ) -> None:
        self.element_name = element_name
        self.element_type = element_type
        self.is_optional = is_optional


def _get_class_attributes(cls: type) -> list[_InspectedElement]:
    boring = dir(type("dummy", (object,), {}))
    return_members: list[_InspectedElement] = []
    member_list = [item for item in inspect.getmembers(cls) if item[0] not in boring]
    for member in member_list:
        if not isinstance(member[1], dict):
            continue
        member_dict: dict[str, Any] = member[1]

        for var_name, var_type in member_dict.items():
            inspected_element: Optional[_InspectedElement] = None
            if isinstance(var_type, type):
                inspected_element = _InspectedElement(var_name, var_type, False)
            elif str(var_type).startswith("typing.Optional"):
                inspected_element = _InspectedElement(
                    var_name, var_type.__args__[0], True
                )
            else:
                continue
            return_members.append(inspected_element)
    return return_members


def resolve_all() -> Callable[[type[T]], type[T]]:
    """
    Resolve all dependencies decorator.
    Allows class decoration for parameter injection.
    This decorator will attempt to inject all defined class dependencies by inspecting the type hint annotations.
    It is important to note, that all the fields that need to be injected must declared in the class with either
    a type annotation or an Optional annotation. Fields without type annotations will be ignored by the injection
    mechanusm
    Example:

    @resolve_all()
    class TestClass:
        test_field: Optional[ClassName]
        str_value: Optional[str]
        int_value = 7

    Will inject the dependency associated with 'ClassName' into the 'test_field' member,
    and the dependency associated with 'str' into the 'str_value' member, while 'int_value' will be left as is.

    Returns:
        Callable[[type[T]], type[T]]: The decorated class constructor
    """

    def wrap(cls: type[T]) -> type[T]:
        original_get_attribute = cls.__getattribute__
        dependencies_list = _get_class_attributes(cls)
        dependencies: dict[str, Union[type, Dependency, Variable]] = {}
        for element in dependencies_list:
            dependencies[element.element_name] = (
                element.element_type
                if not element.is_optional
                else OptionalDependency(element.element_type)
            )

        def __getattribute__(self, attr_name: str) -> Any:  # type: ignore[no-untyped-def]
            if attr_name in dependencies:
                quali = dependencies.get(attr_name, NoOpCls)
                dep = _get_dep(quali)
                if dep is not None:
                    # If a dependency has been resolved, set it as an attribute of the class
                    setattr(cls, attr_name, dep)
                    # Then remove it from the dependencies map
                    dependencies.pop(attr_name)
                return dep
            return original_get_attribute(self, attr_name)

        cls.__getattribute__ = __getattribute__  # type: ignore[method-assign]
        return cls

    return wrap
