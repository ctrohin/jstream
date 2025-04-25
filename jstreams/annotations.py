import inspect
from threading import RLock
from typing import Any, Callable, TypeVar, cast, get_type_hints

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
