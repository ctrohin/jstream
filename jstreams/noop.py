from typing import Any


class NoOpCls:
    """
    A No-Operation object that does nothing when its methods are called
    and returns itself for method chaining.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes the Noop object (does nothing)."""
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Allows the Noop object to be called as a function (does nothing)."""
        return self

    def __getattr__(self, name: str) -> Any:
        """Returns itself for any attribute access, enabling method chaining."""
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        """Ignores attribute setting."""
        pass

    def __delattr__(self, name: str) -> None:
        """Ignores attribute deletion."""
        pass

    def __repr__(self) -> str:
        """Returns a string representation of the Noop object."""
        return "<Noop>"

    def __str__(self) -> str:
        """Returns a string representation of the Noop object."""
        return "<Noop>"

    def __bool__(self) -> bool:
        """Returns False, as a Noop object has no meaningful value."""
        return False

    def __eq__(self, other: Any) -> bool:
        """Returns True if the other object is also a Noop, False otherwise."""
        return isinstance(other, NoOpCls)

    def __ne__(self, other: Any) -> bool:
        """Returns True if the other object is not a Noop, False otherwise."""
        return not isinstance(other, NoOpCls)

    def __enter__(self) -> Any:
        return self


NoOp = NoOpCls()


def noop() -> NoOpCls:
    return NoOp
