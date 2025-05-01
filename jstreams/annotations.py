import inspect
from threading import Lock, RLock
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from jstreams import Predicate

NoneType = type(None)
T = TypeVar("T")


def builder() -> Callable[[type[T]], type[T]]:
    """
    A decorator that adds builder methods to a class.

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class.
    """

    def decorator(cls: type[T]) -> type[T]:
        class Builder:
            def __init__(self) -> None:
                self._instance = cls.__new__(cls)
                self._fields: dict[str, Any] = {}

            def build(self) -> T:
                """
                Builds the object.

                Returns:
                    The built object.
                """
                for name, value in self._fields.items():
                    setattr(self._instance, name, value)
                return self._instance

            def __getattr__(self, name: str) -> Callable[[Any], "Builder"]:
                if name.startswith("with_"):
                    field_name = name[5:]
                    if field_name.startswith("_"):
                        raise AttributeError(
                            f"'{cls.__name__}.{type(self).__name__}' cannot access private field '{field_name}'"
                        )
                    if field_name in get_type_hints(cls):

                        def setter(value: Any) -> "Builder":
                            self._fields[field_name] = value
                            return self

                        return setter

                raise AttributeError(
                    f"'{cls.__name__}.{type(self).__name__}' object has no attribute '{name}'"
                )

        def get_builder() -> Builder:
            return Builder()

        setattr(cls, "builder", staticmethod(get_builder))
        return cls

    return decorator


def getter() -> Callable[[type[T]], type[T]]:
    """
    A decorator that adds getter methods directly to a class.

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class.
    """

    def decorator(cls: type[T]) -> type[T]:
        for field_name, field_type in get_type_hints(cls).items():
            if not field_name.startswith("_"):

                def getter_method(self: Any, name: str = field_name) -> Any:
                    return getattr(self, name)

                setattr(cls, f"get_{field_name}", getter_method)

        return cls

    return decorator


def setter() -> Callable[[type[T]], type[T]]:
    """
    A decorator that adds setter methods directly to a class.

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class.
    """

    def decorator(cls: type[T]) -> type[T]:
        for field_name, field_type in get_type_hints(cls).items():
            if not field_name.startswith("_"):

                def setter_method(
                    self: Any, value: Any, name: str = field_name
                ) -> None:
                    setattr(self, name, value)

                setattr(cls, f"set_{field_name}", setter_method)

        return cls

    return decorator


def locked() -> Callable[[type[T]], type[T]]:
    """
    A class decorator that makes instances of the decorated class thread-safe.

    It wraps attribute access (__getattr__, __setattr__, __delattr__) and
    method calls with a threading.RLock to ensure that only one thread
    can access or modify the instance's state at a time.

    Args:
        cls: The class to decorate.

    Returns:
        The wrapped, thread-safe class.
    """

    def decorator(cls: type[T]) -> type[T]:
        # Store original methods needed for the wrapper
        original_init = cls.__init__
        original_getattr = getattr(
            cls, "__getattr__", None
        )  # Handle classes without custom __getattr__
        original_setattr = cls.__setattr__
        original_delattr = cls.__delattr__

        class ThreadSafeWrapper:
            """Wraps the original class instance and manages the lock."""

            # Use __slots__ for minor optimization if appropriate, but be cautious
            # if the original class relies heavily on dynamic attribute creation.
            # __slots__ = ('_lock', '_original_instance')

            def __init__(self, *args: Any, **kwargs: Any) -> None:
                """
                Initializes the wrapper, creates the lock, creates the original
                instance, and calls its __init__ within the lock.
                """
                # Crucial: Initialize lock *before* creating the original instance
                # Use object.__setattr__ to avoid triggering our wrapped __setattr__
                object.__setattr__(self, "_lock", RLock())
                object.__setattr__(self, "_original_instance", cls.__new__(cls))

                # Call original __init__ under lock protection
                with self._lock:
                    try:
                        original_init(self._original_instance, *args, **kwargs)
                    except Exception as e:
                        # Ensure lock is released even if original __init__ fails
                        # Re-raise the exception to maintain original behavior
                        raise e

            def __getattr__(self, name: str) -> Any:
                """
                Gets an attribute or method from the original instance, acquiring the lock.
                If the attribute is a method, it returns a wrapped method that also
                acquires the lock before execution.
                """
                with self._lock:
                    try:
                        # Try getting the attribute from the original instance
                        value = getattr(self._original_instance, name)

                        # If it's a bound method of the original instance, wrap it
                        if (
                            inspect.ismethod(value)
                            and getattr(value, "__self__", None)
                            is self._original_instance
                        ):

                            def wrapped_method(*args: Any, **kwargs: Any) -> Any:
                                # Method execution also needs the lock
                                with self._lock:
                                    return value(*args, **kwargs)

                            return wrapped_method
                        else:
                            # If it's a regular attribute or a non-bound method/function, return directly
                            return value
                    except AttributeError:
                        # If getattr on original fails, try the original class's __getattr__ if it exists
                        if original_getattr is not None:
                            # Call the original __getattr__ within the lock
                            return original_getattr(self._original_instance, name)
                        else:
                            # If no original __getattr__, raise the AttributeError
                            raise AttributeError(
                                f"'{cls.__name__}' object (wrapped) has no attribute '{name}'"
                            )

            def __setattr__(self, name: str, value: Any) -> None:
                """Sets an attribute on the original instance, acquiring the lock."""
                # Use object.__setattr__ for the wrapper's own attributes
                if name in ("_lock", "_original_instance"):
                    object.__setattr__(self, name, value)
                else:
                    # Set attribute on the original instance under lock protection
                    with self._lock:
                        # Use original setattr logic of the wrapped class
                        original_setattr(self._original_instance, name, value)

            def __delattr__(self, name: str) -> None:
                """Deletes an attribute from the original instance, acquiring the lock."""
                with self._lock:
                    # Use original delattr logic of the wrapped class
                    original_delattr(self._original_instance, name)

            # --- Optional: Delegate common special methods ---
            # You might want to explicitly delegate other special methods if needed,
            # although __getattr__ will handle many cases if they are called.
            def __str__(self) -> str:
                with self._lock:
                    return str(self._original_instance)

            def __repr__(self) -> str:
                with self._lock:
                    # Indicate that it's a wrapped instance
                    return f"ThreadSafeWrapper({repr(self._original_instance)})"

            # Add others like __len__, __getitem__, __setitem__ etc. if required
            # Example:
            # def __len__(self) -> int:
            #     with self._lock:
            #         return len(self._original_instance) # type: ignore

        # --- End Wrapper Class ---

        # Preserve original class name and docstring if possible
        ThreadSafeWrapper.__name__ = f"ThreadSafe{cls.__name__}"
        ThreadSafeWrapper.__doc__ = f"Thread-safe wrapper around {cls.__name__}.\n\nOriginal docstring:\n{cls.__doc__}"
        # Return the wrapper class, effectively replacing the original class definition
        # Use cast to satisfy the type checker about the return type
        return cast(type[T], ThreadSafeWrapper)

    return decorator


# Type variable for the decorated function, bound to Callable
F = TypeVar("F", bound=Callable[..., Any])

# --- Lock Management ---

# --- Synchronized Decorator ---

# Global registry for named locks (maps lock name string to RLock)
# Now holds both explicitly named locks and default generated named locks.
_lock_registry: dict[str, RLock] = {}
# Lock to protect access to the registry during lock creation/retrieval
_registry_access_lock = Lock()


def _get_or_create_lock(func: Callable[..., Any], lock_name: Optional[str]) -> RLock:
    """
    Retrieves or creates the appropriate RLock for the given function and lock name.

    Uses a global registry, protected by a lock for thread-safe creation.
    If lock_name is None, a default name is generated based on the function's
    module and qualified name.

    Args:
        func: The function object being decorated (used to generate default lock name).
        lock_name: The optional name specified for the lock.

    Returns:
        The threading.RLock instance to use for synchronization.
    """
    final_lock_name: str
    if lock_name is not None:
        final_lock_name = lock_name
    else:
        # Generate default lock name based on function's context
        # Example: my_module.MyClass.my_method or my_module.my_function
        final_lock_name = f"{func.__module__}.{func.__qualname__}"

    # Use the single registry for all locks
    with _registry_access_lock:
        # Check if lock exists, create if not
        if final_lock_name not in _lock_registry:
            _lock_registry[final_lock_name] = RLock()
        # Return the existing or newly created lock
        return _lock_registry[final_lock_name]


def synchronized_static(lock_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator to synchronize access to a function or method using a static reentrant lock.

    Ensures that only one thread can execute the decorated function (or any other
    function sharing the same lock name) at a time. Uses threading.RLock for
    reentrancy, allowing a thread that already holds the lock to acquire it again
    without deadlocking (e.g., if a synchronized method calls another synchronized
    method using the same lock).

    Args:
        lock_name (Optional[str]): An optional name for the lock.
            - If provided (e.g., `@synchronized("my_resource_lock")`), all functions
                decorated with the *same* `lock_name` string will share the same
                underlying RLock. This synchronizes access across all those functions,
                treating them as a critical section for a shared resource.
            - If None (default, e.g., `@synchronized()`), a default lock name is
                generated based on the function's module and qualified name
                (e.g., "my_module.MyClass.my_method"). This lock is shared across
                all calls to functions/methods that generate the *same* default name.
                For instance methods, this means all instances of the class will share
                the same lock for that specific method.

    Returns:
        Callable[[F], F]: A decorator that wraps the input function `F`, returning
                        a new function with the same signature but added locking.
    """

    def decorator(func: F) -> F:
        # Determine and retrieve/create the lock *once* when the function is decorated.
        # This lock instance will be captured by the 'wrapper' closure below.
        lock = _get_or_create_lock(func, lock_name)
        # Store the determined lock name for potential introspection
        actual_lock_name = (
            lock_name
            if lock_name is not None
            else f"{func.__module__}.{func.__qualname__}"
        )

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            The replacement function that acquires the lock, executes the original
            function, and ensures the lock is released.
            """
            # The 'with' statement elegantly handles lock acquisition and release,
            # even if the original function raises an exception.
            with lock:
                # Execute the original function with its arguments
                result = func(*args, **kwargs)
            # Return the result obtained from the original function
            return result

        # Optional: Attach the lock information to the wrapper for introspection/debugging
        setattr(wrapper, "_synchronized_lock", lock)
        setattr(wrapper, "_synchronized_lock_name", actual_lock_name)

        # Cast is necessary because the type checker doesn't automatically infer
        # that 'wrapper' has the same signature as 'func' even after using @functools.wraps.
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        return cast(F, wrapper)

    # Return the actual decorator function
    return decorator


# Global lock ONLY for protecting the lazy creation of lock attributes on instances
_instance_lock_creation_lock = Lock()

# Default attribute name if none is specified by the user
DEFAULT_INSTANCE_LOCK_ATTR = "_default_instance_sync_lock"


def synchronized(
    lock_attribute_name: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator to synchronize access to an instance method using an instance-specific reentrant lock.

    Ensures that only one thread can execute the decorated method *on the same instance*
    (or any other method on that instance sharing the same lock attribute name) at a time.
    Uses threading.RLock for reentrancy.

    This differs from `@synchronized` in that the lock is tied to the object instance (`self`),
    not the class method definition or a global name. Calls to the same method on *different*
    instances can execute concurrently.

    Args:
        lock_attribute_name (Optional[str]): An optional name for the attribute on the instance
            that will hold the lock.
            - If provided (e.g., `@instance_synchronized("_my_resource_lock")`), this specific
                attribute name will be used to store the RLock on the instance. All methods
                on the *same instance* decorated with the *same* `lock_attribute_name` will
                share that instance's lock. Choose a name unlikely to clash with existing attributes.
            - If None (default, e.g., `@instance_synchronized()`), a default attribute name
              (`_default_instance_sync_lock`) is used. All methods on the *same instance*
                decorated with the default name will share that instance's default lock.
            - Using different `lock_attribute_name` values allows for multiple independent
                instance-level locks within the same object (e.g., one for reading, one for writing).

    Returns:
        Callable[[F], F]: A decorator that wraps the input method `F`, returning
                        a new method with the same signature but added instance-level locking.

    Raises:
        TypeError: If the decorator is applied to something that doesn't look like an
                instance method (i.e., doesn't receive `self` as the first argument)
                or if the lock attribute cannot be set (e.g., due to `__slots__`
                without including the lock attribute name).
    """
    # Determine the actual attribute name to use ONCE during decoration
    attr_name = (
        lock_attribute_name
        if lock_attribute_name is not None
        else DEFAULT_INSTANCE_LOCK_ATTR
    )

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            The replacement method that acquires the instance-specific lock, executes
            the original method, and ensures the lock is released.
            """
            # 1. Check if used on an instance method and get the instance ('self')
            if not args:
                raise TypeError(
                    f"@{synchronized.__name__} requires 'self' (instance) argument. "
                    f"Decorator applied to '{func.__qualname__}' which seems to be a non-method function or static/class method."
                )
            instance = args[0]
            # A more robust check might involve inspect.isclass(type(instance)),
            # but let's rely on convention for 'self' being the first arg.

            # 2. Try to get the instance-specific lock attribute
            lock: Optional[RLock] = getattr(instance, attr_name, None)

            # 3. Lazy, thread-safe lock creation if it doesn't exist on the instance yet
            if lock is None:
                # Acquire global lock *only* for the creation phase
                with _instance_lock_creation_lock:
                    # Double-check if another thread created it while waiting for the lock
                    lock = getattr(instance, attr_name, None)
                    if lock is None:
                        # Create a new RLock for this instance and this lock name
                        lock = RLock()
                        try:
                            # Store the lock on the instance using the determined attribute name
                            setattr(instance, attr_name, lock)
                        except AttributeError as e:
                            # Handle cases where attribute setting might fail (e.g., __slots__)
                            raise TypeError(
                                f"Could not set lock attribute '{attr_name}' on instance of {type(instance).__name__}. "
                                f"Does the class use __slots__ without including '{attr_name}'?"
                            ) from e

            # 4. Execute original function under the instance lock
            # 'lock' is now guaranteed to be a valid RLock for this instance
            with lock:
                result = func(*args, **kwargs)
            return result

        # Optional: Attach introspection info to the wrapper
        setattr(wrapper, "_instance_synchronized_lock_attr", attr_name)

        return cast(F, wrapper)

    return decorator


def _args(require_all: bool) -> Callable[[type[T]], type[T]]:
    """
    A decorator that adds a static method called 'required' to a class.
    This method constructs an object of the class using only the required
    (non-Optional) members declared in the class.
    """

    def decorator(cls: type[T]) -> type[T]:
        required_members: dict[str, type] = {}
        null_members: set[str] = set()

        for name, type_hint in get_type_hints(cls).items():
            if name.startswith("_"):
                continue

            if repr(type_hint).startswith("<class"):
                required_members[name] = type_hint
            else:
                if require_all:
                    required_members[name] = type_hint.__args__[0]
                else:
                    null_members.add(name)

        def constructor(*args: Any, **kwargs: Any) -> T:
            """
            Constructs an object of the decorated class using the required members.
            """
            if len(args) + len(kwargs) != len(required_members):
                raise TypeError(
                    f"Class requires arguments: {list(required_members.keys())} and received {len(args) + len(kwargs)} arguments"
                )

            call_kwargs: dict[str, Any] = {}
            arg_index = 0
            for param_name, param_type in required_members.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                else:
                    if arg_index >= len(args):
                        raise TypeError("too few arguments")
                    value = args[arg_index]
                    arg_index += 1

                if not isinstance(value, param_type):
                    raise TypeError(
                        f"argument '{param_name}' should be of type {param_type}, received type: {type(value)}"
                    )

                call_kwargs[param_name] = value

            instance = cls.__new__(cls)
            for name, value in call_kwargs.items():
                setattr(instance, name, value)
            for name in null_members:
                setattr(instance, name, None)
            return instance

        constructor.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
            parameters=[
                inspect.Parameter(
                    name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=required_members[name],
                )
                for name in required_members
            ]
        )

        setattr(
            cls, "required" if not require_all else "all", staticmethod(constructor)
        )
        return cls

    return decorator


def required_args() -> Callable[[type[T]], type[T]]:
    """
    A decorator that adds a static method called 'required' to a class.
    This method constructs an object of the class using only the required
    (non-Optional) public members declared in the class. The parameters can be
    passed to the 'required' method either as positional or keyword arguments.
    If positional arguments are used, then they must be specified in the order
    they were declared.
    """
    return _args(False)


def all_args() -> Callable[[type[T]], type[T]]:
    """
    A decorator that adds a static method called 'all' to a class.
    This method constructs an object of the class using all public
    members declared in the class, including Optionals. The parameters can be
    passed to the 'all' method either as positional or keyword arguments.
    If positional arguments are used, then they must be specified in the order
    they were declared.
    """

    return _args(True)


def validate_args(
    rules: Optional[dict[str, Predicate[Any]]] = None,
) -> Callable[[F], F]:
    """
    Decorator to validate function arguments against their type hints at runtime.

    Checks if the type of each argument passed to the decorated function matches
    the corresponding type hint in the function's signature. Raises a TypeError
    if a mismatch is found.

    Supports basic types, `typing.Optional`, and `typing.Union`.
    Skips validation for parameters without type hints or hinted with `typing.Any`.
    Does not perform deep validation of collection contents (e.g., list[int]).

    Example:
        @validate_args()
        def process_data(name: str, age: Optional[int] = None, tags: list = []):
            print(f"Processing {name} ({age}) with tags {tags}")

        process_data("Alice", 30)       # OK
        process_data("Bob", None)       # OK (Optional[int] allows None)
        process_data("Charlie", "twenty") # Raises TypeError (age should be int or None)
        process_data(123, 40)           # Raises TypeError (name should be str)

    Returns:
        Callable[[F], F]: A decorator function.
    """

    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        # Use get_type_hints for better resolution of forward references etc.
        # include_extras=False is default but good to be aware of
        try:
            type_hints = get_type_hints(func)
        except Exception:
            # Handle potential errors during type hint resolution (e.g., NameError)
            # In this case, we might choose to skip validation or log a warning.
            # For simplicity, we'll skip validation if hints can't be resolved.
            type_hints = {}

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Bind provided arguments to parameter names
            try:
                bound_args = sig.bind(*args, **kwargs)
            except TypeError as e:
                # Reraise if basic binding fails (e.g., wrong number of args)
                raise TypeError(
                    f"Error binding arguments for {func.__qualname__}: {e}"
                ) from e

            # Apply default values for parameters not provided in the call
            bound_args.apply_defaults()

            # Validate arguments against type hints
            for param_name, value in bound_args.arguments.items():
                if param_name not in type_hints:
                    # Skip validation if no type hint is available
                    continue

                expected_type = type_hints[param_name]

                if expected_type is Any:
                    # Skip validation if hinted as Any
                    continue

                origin = get_origin(expected_type)
                args_types = get_args(expected_type)

                is_valid = False
                if (
                    origin is Union
                ):  # Handles Union and Optional (Optional[T] is Union[T, NoneType])
                    # Check if the value's type is one of the types in the Union
                    for type_arg in args_types:
                        # Special handling for NoneType in Optional/Union
                        if type_arg is NoneType and value is None:
                            is_valid = True
                            break
                        # isinstance() doesn't work directly with NoneType before 3.10
                        if type_arg is not NoneType and isinstance(value, type_arg):
                            is_valid = True
                            break
                elif origin is not None:
                    # Handle other generic types like list, dict, etc.
                    # Basic check: validate the origin type (e.g., list, dict)
                    # Deeper validation (e.g., checking list contents) is complex and skipped here.
                    if isinstance(value, origin):
                        is_valid = True
                else:
                    # Simple, non-generic type hint
                    if isinstance(value, expected_type):
                        is_valid = True

                # Check predicates, if available
                if rules is not None and param_name in rules:
                    rule = rules.get(param_name)
                    if rule is not None and not rule(value):
                        raise TypeError(
                            f"Argument '{param_name}' for {func.__qualname__} does not match the given predicate"
                        )

                if not is_valid:
                    raise TypeError(
                        f"Argument '{param_name}' for {func.__qualname__} "
                        f"expected type {expected_type}, but got {type(value).__name__}."
                    )

            # If all validations pass, call the original function
            return func(*bound_args.args, **bound_args.kwargs)

        return cast(F, wrapper)

    return decorator


# Type variable for the return type (used in default_on_error)
R = TypeVar("R")


def default_on_error(
    default_value: R,
    catch_exceptions: Optional[list[type]] = None,
    logger: Optional[
        Any
    ] = None,  # Using Any for logger to avoid strict logging dependency
    log_message: str = "Caught exception in {func_name} ({exception}), returning default value.",
) -> Callable[[F], F]:
    """
    Decorator factory: returns a default value if the decorated function raises specific exceptions.

    Args:
        default_value (R): The value to return if a specified exception is caught.
        catch_exceptions (Optional[list[Type[E]]]): A list of exception types to catch.
            If None or empty, catches all `Exception` subclasses. Defaults to None.
        logger (Optional[Any]): Logger-like object with an `error` or `warning` method
            to log the exception. If None, no logging occurs. Defaults to None.
        log_message (str): Format string for the log message. Available placeholders:
            {func_name}, {exception}, {args}, {kwargs}. Defaults to a standard message.

    Returns:
        Callable[[F], F]: The decorator.

    Example:
        @default_on_error(default_value=-1, catch_exceptions=[ValueError, TypeError])
        def parse_int(value: str) -> int:
            return int(value)

        parse_int("10")  # Returns 10
        parse_int("abc") # Returns -1 (ValueError caught)
        parse_int(None)  # Returns -1 (TypeError caught)

        @default_on_error(default_value=0.0) # Catches any Exception
        def safe_divide(a, b):
            return a / b

        safe_divide(10, 2) # Returns 5.0
        safe_divide(10, 0) # Returns 0.0 (ZeroDivisionError caught)
    """
    # Determine which exceptions to catch
    exceptions_to_catch: list[type]
    if catch_exceptions is None or not catch_exceptions:
        exceptions_to_catch = [BaseException]  # Catch any standard exception
    else:
        exceptions_to_catch = catch_exceptions

    def decorator(func: F) -> F:
        def wrapper(
            *args: Any, **kwargs: Any
        ) -> Any:  # Return Any as it could be original or default
            try:
                return func(*args, **kwargs)
            except BaseException as e:
                if type(e) not in exceptions_to_catch:
                    raise e
                if logger and hasattr(
                    logger, "warning"
                ):  # Basic check for logger capability
                    formatted_message = log_message.format(
                        func_name=func.__qualname__,
                        exception=e,
                        args=args,
                        kwargs=kwargs,
                    )
                    logger.warning(formatted_message, exc_info=e)  # Log with traceback
                return default_value
            # Let other exceptions (if specific types were requested) propagate

        return cast(F, wrapper)  # Keep original signature for type checking

    return decorator
