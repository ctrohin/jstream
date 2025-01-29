from typing import Any


class NoOpCls:
    """No-op that can be put in lieu of almost anything.
    Any actions on that object will be just ignored. You can
    call it, get its atributes, use a a context, anything :)
    Cool feature
    ------------
    NoOp tracks its levels of absurdity.
    Examples
    --------
    >>> from no_op import NoOp as xyz
    # Now all calls to xyz are simply ignored without any exception:
    >>>  print(xyz.get('qwerty').wtf['dupa'].callme('tesla', model='X')[5, ...])
    Just no-op on level 7.

    Copyright
    ---------
    (c) 2021 Maciej J. Mikulski
    Feel free to use it, I put NoOp in public domain.
    """

    def __init__(self, level: int = 0) -> None:
        self.level = level

    def __getattr__(self, attr: Any) -> Any:
        return NoOpCls(self.level + 1)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return NoOpCls(self.level + 1)

    def __getitem__(self, item: Any) -> Any:
        return NoOpCls(self.level + 1)

    def __enter__(self) -> Any:
        return NoOpCls(self.level + 1)

    def __repr__(self) -> str:
        return f"Just no-op on level {self.level}."


NoOp = NoOpCls()


def noop() -> NoOpCls:
    return NoOp


__all__ = ["noop", "NoOpCls"]
