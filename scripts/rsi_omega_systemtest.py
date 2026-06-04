"""Minimal frozen Systemtest-compatible BSExpr runtime for RSI omega proofs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple


@dataclass(frozen=True)
class BSVal:
    val: int

    def __str__(self) -> str:
        return str(self.val)


@dataclass(frozen=True)
class BSVar:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class BSArg:
    index: int = 0

    def __str__(self) -> str:
        return f"${self.index}"


@dataclass(frozen=True)
class BSBinOp:
    op: str
    left: Any
    right: Any

    def __str__(self) -> str:
        return f"({self.left}{self.op}{self.right})"


@dataclass(frozen=True)
class BSRecCall:
    arg: Any

    def __str__(self) -> str:
        return f"f({self.arg})"


@dataclass(frozen=True)
class BSCustomOp:
    name: str
    definition: Any
    args: Tuple[Any, ...]

    def __init__(self, name: str, definition: Any, args: Iterable[Any]):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "args", tuple(args))

    def __str__(self) -> str:
        return f"{self.name}({', '.join(str(arg) for arg in self.args)})"


@dataclass(frozen=True)
class BSAbstractionResult:
    body: Any
    arity: int


def _children(expr: Any) -> Tuple[Any, ...]:
    if isinstance(expr, BSBinOp):
        return (expr.left, expr.right)
    if isinstance(expr, BSRecCall):
        return (expr.arg,)
    if isinstance(expr, BSCustomOp):
        return expr.args
    return ()


def bs_expr_complexity(expr: Any) -> int:
    return 1 + sum(bs_expr_complexity(child) for child in _children(expr))


def _max_arg_index(expr: Any) -> int:
    if isinstance(expr, BSArg):
        return expr.index
    return max((_max_arg_index(child) for child in _children(expr)), default=-1)


def _same_leaf(left: Any, right: Any) -> bool:
    return (
        type(left) is type(right)
        and isinstance(left, (BSVal, BSVar, BSArg))
        and left == right
    )


def anti_unify_bs_expr(left: Any, right: Any) -> BSAbstractionResult | None:
    """Return a first-order anti-unification pattern over BSExpr trees."""

    holes: Dict[str, int] = {}

    def hole_for(a: Any, b: Any) -> BSArg:
        key = f"{a!r}\n---\n{b!r}"
        if key not in holes:
            holes[key] = len(holes)
        return BSArg(holes[key])

    def au(a: Any, b: Any) -> Any:
        if _same_leaf(a, b):
            return a
        if isinstance(a, BSBinOp) and isinstance(b, BSBinOp) and a.op == b.op:
            return BSBinOp(a.op, au(a.left, b.left), au(a.right, b.right))
        if isinstance(a, BSRecCall) and isinstance(b, BSRecCall):
            return BSRecCall(au(a.arg, b.arg))
        if isinstance(a, BSCustomOp) and isinstance(b, BSCustomOp) and a.name == b.name and len(a.args) == len(b.args):
            return BSCustomOp(a.name, a.definition, tuple(au(x, y) for x, y in zip(a.args, b.args)))
        return hole_for(a, b)

    body = au(left, right)
    return BSAbstractionResult(body=body, arity=len(holes))


class MetaState:
    """Systemtest-compatible grammar state for learned BSExpr abstractions."""

    def __init__(self):
        self.abstractions: Dict[str, Any] = {}
        self.grammar_version = 0

    def add_abstraction(self, name: str, definition: Any) -> None:
        if name in self.abstractions:
            return
        self.abstractions[name] = definition
        self.grammar_version += 1

    def get_arity(self, name: str) -> int:
        if name not in self.abstractions:
            return 0
        return max(_max_arg_index(self.abstractions[name]) + 1, 0)


class SafeInterpreter:
    """Safe interpreter for recursive integer BSExpr bodies."""

    def __init__(self, limit: int = 20000, max_abs: int = 10**12):
        self.limit = int(limit)
        self.max_abs = int(max_abs)

    def run_recursive(self, body: Any, n: int, base_k: int, base_v: int) -> int:
        steps = [0]
        memo: Dict[int, int] = {}

        def bounded(value: int) -> int:
            if abs(value) > self.max_abs:
                raise OverflowError("interpreter magnitude limit exceeded")
            return value

        def eval_expr(expr: Any, current_n: int, args: Tuple[Any, ...]) -> int:
            steps[0] += 1
            if steps[0] > self.limit:
                raise RuntimeError("interpreter step limit exceeded")
            if isinstance(expr, BSVal):
                return int(expr.val)
            if isinstance(expr, BSVar):
                if expr.name != "n":
                    raise ValueError(f"unknown variable {expr.name}")
                return int(current_n)
            if isinstance(expr, BSArg):
                if expr.index >= len(args):
                    raise ValueError(f"missing abstraction arg {expr.index}")
                return eval_expr(args[expr.index], current_n, args)
            if isinstance(expr, BSBinOp):
                left = eval_expr(expr.left, current_n, args)
                right = eval_expr(expr.right, current_n, args)
                if expr.op == "+":
                    return bounded(left + right)
                if expr.op == "-":
                    return bounded(left - right)
                if expr.op == "*":
                    return bounded(left * right)
                raise ValueError(f"bad operator {expr.op}")
            if isinstance(expr, BSRecCall):
                next_n = eval_expr(expr.arg, current_n, args)
                return rec(next_n)
            if isinstance(expr, BSCustomOp):
                return eval_expr(expr.definition, current_n, expr.args)
            raise ValueError(f"bad expression {expr!r}")

        def rec(current_n: int) -> int:
            if current_n <= base_k:
                return int(base_v)
            if current_n in memo:
                return memo[current_n]
            value = eval_expr(body, current_n, ())
            memo[current_n] = value
            return value

        return rec(int(n))
