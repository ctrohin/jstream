from typing import Any, Callable, Optional, TypeVar, overload

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
E = TypeVar("E")
F = TypeVar("F")
G = TypeVar("G")
H = TypeVar("H")
I_ = TypeVar("I_")
J = TypeVar("J")
K = TypeVar("K")
L = TypeVar("L")
M = TypeVar("M")
N = TypeVar("N")
O_ = TypeVar("O_")
P = TypeVar("P")
Q = TypeVar("Q")
R = TypeVar("R")
S = TypeVar("S")


@overload
def fpipe(f1: Callable[[A], B], f2: Callable[[B], C]) -> Callable[[A], C]: ...


@overload
def fpipe(
    f1: Callable[[A], B], f2: Callable[[B], C], f3: Callable[[C], D]
) -> Callable[[A], D]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
) -> Callable[[A], E]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
) -> Callable[[A], F]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
) -> Callable[[A], G]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
) -> Callable[[A], H]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
) -> Callable[[A], I_]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
) -> Callable[[A], J]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
) -> Callable[[A], K]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
) -> Callable[[A], L]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
    f12: Callable[[L], M],
) -> Callable[[A], M]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
    f12: Callable[[L], M],
    f13: Callable[[M], N],
) -> Callable[[A], N]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
    f12: Callable[[L], M],
    f13: Callable[[M], N],
    f14: Callable[[N], O_],
) -> Callable[[A], O_]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
    f12: Callable[[L], M],
    f13: Callable[[M], N],
    f14: Callable[[N], O_],
    f15: Callable[[O_], P],
) -> Callable[[A], P]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
    f12: Callable[[L], M],
    f13: Callable[[M], N],
    f14: Callable[[N], O_],
    f15: Callable[[O_], P],
    f16: Callable[[P], Q],
) -> Callable[[A], Q]: ...


@overload
def fpipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
    f8: Callable[[H], I_],
    f9: Callable[[I_], J],
    f10: Callable[[J], K],
    f11: Callable[[K], L],
    f12: Callable[[L], M],
    f13: Callable[[M], N],
    f14: Callable[[N], O_],
    f15: Callable[[O_], P],
    f16: Callable[[P], Q],
    f17: Callable[[Q], R],
) -> Callable[[A], R]: ...


def fpipe(
    f1: Callable[[A], B],
    f2: Optional[Callable[[B], C]] = None,
    f3: Optional[Callable[[C], D]] = None,
    f4: Optional[Callable[[D], E]] = None,
    f5: Optional[Callable[[E], F]] = None,
    f6: Optional[Callable[[F], G]] = None,
    f7: Optional[Callable[[G], H]] = None,
    f8: Optional[Callable[[H], I_]] = None,
    f9: Optional[Callable[[I_], J]] = None,
    f10: Optional[Callable[[J], K]] = None,
    f11: Optional[Callable[[K], L]] = None,
    f12: Optional[Callable[[L], M]] = None,
    f13: Optional[Callable[[M], N]] = None,
    f14: Optional[Callable[[N], O_]] = None,
    f15: Optional[Callable[[O_], P]] = None,
    f16: Optional[Callable[[P], Q]] = None,
    f17: Optional[Callable[[Q], R]] = None,
    f18: Optional[Callable[[R], S]] = None,
) -> Callable[[A], S]:
    """
    Creates a function from the given function arguments, that accepts as the
    parameter the value of the parameter of the first function in the chain, and returns the value of the
    last function in the chain. The piping works by applying each function
    in the chain to the result of the previous function (except for the first function
    for which the parameter must be provided).

    This function is useful for multi function composition.

    Example:
        >>> from jstreams import fpipe
        >>>
        >>> add_one = lambda x: x + 1
        >>> add_two = lambda x: x + 2
        >>> add_three = lambda x: x + 3
        >>> add_four = lambda x: x + 4
        >>> chained = fpipe(add_one, add_two, add_three, add_four)
        >>> chained(1)
        11

    """
    fns: list[Optional[Callable[[Any], Any]]] = [
        f1,
        f2,
        f3,
        f4,
        f5,
        f6,
        f7,
        f8,
        f9,
        f10,
        f11,
        f12,
        f13,
        f14,
        f15,
        f16,
        f17,
        f18,
    ]

    def wrap(param: A) -> S:
        for f in fns:
            if f is not None:
                param = f(param)
        return param  # type: ignore[return-value]

    return wrap
