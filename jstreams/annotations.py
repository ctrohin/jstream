from typing import Any, Callable, TypeVar, get_type_hints

T = TypeVar("T")


def builder(cls: type[T]) -> type[T]:
    """
    A decorator that adds builder methods to a class.

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class.
    """

    class Builder:
        def __init__(self):
            self._instance = cls.__new__(cls)
            self._fields = {}

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


def getter(cls: type[T]) -> type[T]:
    """
    A decorator that adds getter methods directly to a class.

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class.
    """
    for field_name, field_type in get_type_hints(cls).items():
        if not field_name.startswith("_"):

            def getter_method(self, field_name=field_name) -> Any:
                return getattr(self, field_name)

            setattr(cls, f"get_{field_name}", getter_method)

    return cls


def setter(cls: type[T]) -> type[T]:
    """
    A decorator that adds setter methods directly to a class.

    Args:
        cls: The class to decorate.

    Returns:
        The decorated class.
    """
    for field_name, field_type in get_type_hints(cls).items():
        if not field_name.startswith("_"):

            def setter_method(self, value: Any, field_name=field_name) -> None:
                setattr(self, field_name, value)

            setattr(cls, f"set_{field_name}", setter_method)

    return cls
