import inspect
from threading import Lock, RLock
from typing import Any, Callable, Optional, TypeVar, cast, get_type_hints

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


def synchronized(lock_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator to synchronize access to a function or method using a reentrant lock.

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
