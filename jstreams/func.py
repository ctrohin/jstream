from typing import Any, Optional, TypeVar, overload
from collections.abc import Callable
import inspect
from threading import RLock


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
def pipe(f1: Callable[[A], B], f2: Callable[[B], C]) -> Callable[[A], C]: ...


@overload
def pipe(
    f1: Callable[[A], B], f2: Callable[[B], C], f3: Callable[[C], D]
) -> Callable[[A], D]: ...


@overload
def pipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
) -> Callable[[A], E]: ...


@overload
def pipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
) -> Callable[[A], F]: ...


@overload
def pipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
) -> Callable[[A], G]: ...


@overload
def pipe(
    f1: Callable[[A], B],
    f2: Callable[[B], C],
    f3: Callable[[C], D],
    f4: Callable[[D], E],
    f5: Callable[[E], F],
    f6: Callable[[F], G],
    f7: Callable[[G], H],
) -> Callable[[A], H]: ...


@overload
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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
def pipe(
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


def pipe(
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
        >>> from jstreams import pipe
        >>>
        >>> add_one = lambda x: x + 1
        >>> add_two = lambda x: x + 2
        >>> add_three = lambda x: x + 3
        >>> add_four = lambda x: x + 4
        >>> chained = pipe(add_one, add_two, add_three, add_four)
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
    return _pipe_list(fns)


def _pipe_list(fns: list[Optional[Callable[[Any], Any]]]) -> Callable[[Any], Any]:
    def wrap(param: Any) -> Any:
        for f in fns:
            if f is not None:
                param = f(param)
        return param

    return wrap


def partial(func: Callable[..., R], *initial_args: Any) -> Callable[..., R]:
    """
    Creates a partial version of a function.

    The returned function will have some of the initial arguments of the original
    function pre-filled. When the partial function is called, it will be invoked
    with the pre-filled arguments followed by any new arguments provided.

    Example:
        >>> from jstreams import partial
        >>>
        >>> def add(a, b, c):
        ...     return a + b + c
        >>>
        >>> partial_add_5 = partial(add, 5)
        >>> result1 = partial_add_5(10, 15)  # Equivalent to add(5, 10, 15)
        >>> print(result1)
        30
        >>>
        >>> partial_add_5_10 = partial(add, 5, 10)
        >>> result2 = partial_add_5_10(15)   # Equivalent to add(5, 10, 15)
        >>> print(result2)
        30

    Args:
        func (Callable[..., R]): The initial function.
        *initial_args (Any): The initial arguments to pre-fill.

    Returns:
        Callable[..., R]: A new function that, when called, will execute the
                          original function with the pre-filled arguments
                          followed by the arguments passed to the new function.
    """

    def wrapper(*new_args: Any, **new_kwargs: Any) -> R:
        return func(*initial_args, *new_args, **new_kwargs)

    return wrapper


# Cache for storing the number of arguments for functions
_ARG_COUNT_CACHE: dict[Any, int] = {}
_ARG_COUNT_CACHE_LOCK = RLock()


def get_number_of_arguments(func: Callable[..., Any]) -> int:
    """
    Finds the number of arguments a given function accepts, using a cache
    for efficiency on repeated calls with the same function.

    This counts all named parameters in the function's signature,
    including positional, keyword-only, variable positional (*args),
    and variable keyword (**kwargs) parameters. Each of these counts as one.
    Results are cached to avoid repeated expensive introspection.

    Args:
        func: The function to inspect.

    Returns:
        The total number of parameters in the function's signature.

    Raises:
        ValueError: If the signature cannot be determined (e.g., for some built-in functions
                    implemented in C that don't expose their signature).
        TypeError: If the provided 'func' is not a callable object.
    """
    # Optimistic check without lock
    if func in _ARG_COUNT_CACHE:
        return _ARG_COUNT_CACHE[func]

    with _ARG_COUNT_CACHE_LOCK:
        # Double-check if another thread populated the cache while waiting for the lock
        if func in _ARG_COUNT_CACHE:
            return _ARG_COUNT_CACHE[func]

        # If still not in cache, compute, store, and return
        try:
            signature = inspect.signature(func)
            count = len(signature.parameters)
            _ARG_COUNT_CACHE[func] = count
            return count
        except ValueError as e:  # Do not cache errors
            raise ValueError(f"Could not determine signature for {func}: {e}") from e
        except TypeError as e:  # Do not cache errors
            raise TypeError(f"Object {func} is not a callable: {e}") from e


def curry(func: Callable[..., Any], n: int = -1) -> Callable[..., Any]:
    """
    Transforms a function that takes multiple arguments into a sequence of
    functions, each taking a single argument. This process is known as currying.

    The curried function is built by successively applying arguments one at a time.
    Each call with an argument returns a new function that expects the next
    argument, until all `n` arguments have been supplied, at which point the
    original function `func` is executed with all collected arguments.

    Args:
        func: The function to be curried.
        n: The number of arguments to curry.
           If -1 (default), the arity is automatically determined by inspecting
           the signature of `func` (counting all its defined parameters).
           If `func` takes 1 or 0 arguments (or `n` is <= 1), `func` is
           returned directly.

    Returns:
        A curried version of `func`. If `n` > 1, this is a function that
        takes one argument and returns another curried function. If `n` <= 1,
        `func` itself (or a partially applied version if called recursively)
        is returned.

    Example:
        >>> def add_three_numbers(x, y, z):
        ...     return x + y + z
        >>> curried_add = curry(add_three_numbers)
        >>> result = curried_add(1)(2)(3)
        >>> print(result)
        6

        >>> curried_add_two_args = curry(add_three_numbers, 2)
        >>> add_1_and_2 = curried_add_two_args(1)(2) # Returns a function lambda z: 1 + 2 + z
        >>> result_partial = add_1_and_2(10)
        >>> print(result_partial)
        13
    """
    if n == -1:
        n = get_number_of_arguments(func)

    if n <= 1:
        return func
    return lambda arg: curry(partial(func, arg), n - 1)
