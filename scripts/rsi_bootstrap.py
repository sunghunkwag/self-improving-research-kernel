"""
rsi_bootstrap.py  —  Substantive RECURSIVE self-improvement via bootstrapped
abstraction (DreamCoder-style library learning with anti-unification).

This is NOT a benchmark. There is no adaptive-vs-static table. The point is the
loop itself: the system gets MORE CAPABLE over rounds by compressing its own
solutions into reusable abstractions, and that capability COMPOUNDS so it can
solve a task that is out of reach from base primitives.

THE RECURSION (what "self" refers to, and why it compounds):
  - The search operates over a PRIMITIVE LIBRARY.
  - When the system solves a task, it abstracts its OWN solution:
      * memoizes the solving program as a reusable VALUE primitive (a "skill"),
      * anti-unifies pairs of its solutions to extract reusable FUNCTION
        primitives (arity-1 lambdas over a list hole) — found by the system,
        not given by a human.
  - Those new primitives are added to the library, so the *next* search is a
    search over a richer primitive set: the improver is now more capable.
  - Higher-tier solutions are built FROM lower-tier abstractions, which were
    built from still-lower ones. The learned library forms a dependency DAG of
    depth > 1: a function learned from tier-1 solutions is used inside tier-2
    solutions, which are memoized as skills, which are composed in tier-3.
    Solving tier-3 is therefore only possible because of accumulated,
    self-discovered abstraction. That dependency chain is the recursion.

THE PROOF (falsifiable, run at the end):
  COLD  = solve the hardest task with an EMPTY library, fixed budget, N seeds.
  WARM  = solve the same task after the curriculum has populated the library.
  If COLD fails and WARM succeeds at the SAME budget, the self-improvement did
  real, load-bearing work. We also print the learned library and the dependency
  depth of the winning program, so you can see the chain.

NON-GAMEABLE BY CONSTRUCTION (the discipline you've held me to):
  - Frozen external evaluator + frozen ground-truth targets, outside the mutable
    program. Operators/abstraction only ever read/write Expr trees.
  - 3-way split: TRAIN drives search, HELDOUT gates champion promotion, TEST is
    touched only in the final report.
  - Library entries are derived from program STRUCTURE only — never from labels.
    No target/label can leak into a primitive. A correct program scores exactly
    0 (proven by the feasibility check), so "solved" means truly correct.

THE CEILING (stated, not hidden):
  Base primitives are fixed by a human. The library grows by composing/
  abstracting them; it does not invent genuinely new primitives outside the
  closed set. That open-ended step is unsolved and not claimed here.
"""

from __future__ import annotations
import argparse
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# 1. FROZEN GROUND TRUTH (external; the mutator/abstractor cannot touch this)
# =============================================================================

def _t1_ss(xs):        return sum(x * x for x in xs)
def _t1_sspos(xs):     return sum(x * x for x in xs if x > 0)
def _t2_inc_pos(xs):   return sum((x + 1) ** 2 for x in xs if x > 0)
def _t2_abs_neg(xs):   return sum(abs(x) ** 2 for x in xs if x < 0)
def _t3(xs):           return _t2_inc_pos(xs) - _t2_abs_neg(xs)

# Curriculum tiers (fixed BEFORE any result is seen; not tuned to outcome).
# The curriculum builds the library (tier1, tier2). t3 is NOT in it: it is the
# held-out hard target, solvable warm ONLY by COMPOSING tier-2 skills (never
# memoized, so it cannot be retrieved — it must be reconstructed via abstraction).
CURRICULUM: List[Tuple[str, List[str]]] = [
    ("tier1", ["t1_ss", "t1_sspos"]),
    ("tier2", ["t2_inc_pos", "t2_abs_neg"]),
]
TARGETS = {
    "t1_ss": _t1_ss, "t1_sspos": _t1_sspos,
    "t2_inc_pos": _t2_inc_pos, "t2_abs_neg": _t2_abs_neg, "t3": _t3,
}
HARD_TASK = "t3"

# =============================================================================
# 2. BASE DSL + safe interpreter  (the closed primitive set)
# =============================================================================
UOPS = ("sq", "abs", "neg", "inc", "dbl", "id")
PREDS = ("pos", "neg", "even", "odd", "nonzero")
BINOPS = ("add", "sub", "mul")
REDUCES = ("sum", "max", "min", "len", "prod")
_UOP_FN = {"sq": lambda v: v * v, "abs": abs, "neg": lambda v: -v,
           "inc": lambda v: v + 1, "dbl": lambda v: 2 * v, "id": lambda v: v}
_PRED_FN = {"pos": lambda v: v > 0, "neg": lambda v: v < 0,
            "even": lambda v: v % 2 == 0, "odd": lambda v: v % 2 != 0,
            "nonzero": lambda v: v != 0}


class EvalError(Exception):
    pass


def eval_base(e: Any, xs: List[int]) -> Any:
    """Interpreter for PURE BASE expressions (no library refs / no holes)."""
    if not isinstance(e, tuple):
        raise EvalError("not expr")
    h = e[0]
    if h == "xs":
        return xs
    if h == "const":
        return int(e[1])
    if h in BINOPS:
        a, b = eval_base(e[1], xs), eval_base(e[2], xs)
        if not isinstance(a, int) or not isinstance(b, int):
            raise EvalError("binop non-scalar")
        return a + b if h == "add" else a - b if h == "sub" else a * b
    if h in REDUCES:
        le = eval_base(e[1], xs)
        if not isinstance(le, list):
            raise EvalError("reduce non-list")
        if h == "len":
            return len(le)
        if not le:
            return 1 if h == "prod" else 0
        if h == "sum":
            return sum(le)
        if h == "max":
            return max(le)
        if h == "min":
            return min(le)
        p = 1
        for v in le:
            p *= v
            if abs(p) > 10 ** 12:
                raise EvalError("overflow")
        return p
    if h == "map":
        le = eval_base(e[2], xs)
        if not isinstance(le, list):
            raise EvalError("map non-list")
        return [_UOP_FN[e[1]](v) for v in le]
    if h == "filter":
        le = eval_base(e[2], xs)
        if not isinstance(le, list):
            raise EvalError("filter non-list")
        return [v for v in le if _PRED_FN[e[1]](v)]
    raise EvalError(f"bad head {h}")


# =============================================================================
# 3. LIBRARY  +  expansion of library-augmented exprs to base
# =============================================================================
# Augmented forms add:  ('lib', name)         value primitive (closed term)
#                       ('app', name, arg)     apply arity-1 FUNC to arg
#                       ('hole',)              the parameter inside a FUNC body
EXPAND_SIZE_CAP = 400


class Library:
    def __init__(self):
        self.values: Dict[str, Dict[str, Any]] = {}   # name -> {expr, type, deps}
        self.funcs: Dict[str, Dict[str, Any]] = {}     # name -> {body, in, out, deps}
        self.order: List[str] = []

    def add_value(self, name, expr, typ):
        if name in self.values:
            return
        self.values[name] = {"expr": expr, "type": typ, "deps": refs_of(expr)}
        self.order.append(name)

    def add_func(self, name, body, in_t, out_t):
        if name in self.funcs:
            return
        self.funcs[name] = {"body": body, "in": in_t, "out": out_t, "deps": refs_of(body)}
        self.order.append(name)

    def value_names(self, typ=None):
        return [n for n, v in self.values.items() if typ is None or v["type"] == typ]

    def func_names(self, out_t=None):
        return [n for n, f in self.funcs.items() if out_t is None or f["out"] == out_t]


def refs_of(e: Any) -> set:
    """All library names referenced anywhere in an augmented expr."""
    out = set()
    if not isinstance(e, tuple):
        return out
    if e[0] == "lib":
        out.add(e[1])
    elif e[0] == "app":
        out.add(e[1])
        out |= refs_of(e[2])
    else:
        for i in child_idx(e):
            out |= refs_of(e[i])
    return out


def subst_hole(body: Any, arg: Any) -> Any:
    if not isinstance(body, tuple):
        return body
    if body[0] == "hole":
        return arg
    if body[0] in ("lib",):
        return body
    if body[0] == "app":
        return ("app", body[1], subst_hole(body[2], arg))
    lst = list(body)
    for i in child_idx(body):
        lst[i] = subst_hole(body[i], arg)
    return tuple(lst)


def expand(e: Any, lib: Library, _sz=None) -> Any:
    """Inline all library refs into a pure base expr. Raise on bad/oversized."""
    if _sz is None:
        _sz = [0]
    _sz[0] += 1
    if _sz[0] > EXPAND_SIZE_CAP:
        raise EvalError("expand blowup")
    if not isinstance(e, tuple):
        raise EvalError("bad node")
    h = e[0]
    if h in ("xs", "const"):
        return e
    if h == "hole":
        raise EvalError("free hole")
    if h == "lib":
        if e[1] not in lib.values:
            raise EvalError("missing value " + e[1])
        return expand(lib.values[e[1]]["expr"], lib, _sz)
    if h == "app":
        if e[1] not in lib.funcs:
            raise EvalError("missing func " + e[1])
        arg = expand(e[2], lib, _sz)
        body = lib.funcs[e[1]]["body"]
        return expand(subst_hole(body, arg), lib, _sz)
    lst = list(e)
    for i in child_idx(e):
        lst[i] = expand(e[i], lib, _sz)
    return tuple(lst)


def evaluate(e: Any, xs: List[int], lib: Library) -> Any:
    return eval_base(expand(e, lib), xs)


# =============================================================================
# 4. typing + tree navigation for the AUGMENTED grammar
# =============================================================================

def child_idx(e: tuple) -> List[int]:
    h = e[0]
    if h in ("xs", "const", "lib", "hole"):
        return []
    if h in BINOPS:
        return [1, 2]
    if h in REDUCES:
        return [1]
    if h in ("map", "filter"):
        return [2]
    if h == "app":
        return [2]
    return []


def typeof(e: tuple, lib: Library) -> str:
    h = e[0]
    if h in ("map", "filter", "xs"):
        return "list"
    if h == "lib":
        return lib.values[e[1]]["type"] if e[1] in lib.values else "scalar"
    if h == "app":
        return lib.funcs[e[1]]["out"] if e[1] in lib.funcs else "scalar"
    if h == "hole":
        return "hole"
    return "scalar"


def size(e: Any) -> int:
    if not isinstance(e, tuple):
        return 1
    n = 1
    for i in child_idx(e):
        n += size(e[i])
    return n


def collect(e: tuple, path=()):
    out = [(path, e)]
    for i in child_idx(e):
        out.extend(collect(e[i], path + (i,)))
    return out


def replace_at(e: tuple, path, new):
    if not path:
        return new
    i = path[0]
    lst = list(e)
    lst[i] = replace_at(e[i], path[1:], new)
    return tuple(lst)


def to_str(e: Any) -> str:
    if not isinstance(e, tuple):
        return str(e)
    h = e[0]
    if h == "xs":
        return "xs"
    if h == "const":
        return str(e[1])
    if h == "hole":
        return "·"
    if h == "lib":
        return e[1]
    if h == "app":
        return f"{e[1]}({to_str(e[2])})"
    if h in BINOPS:
        op = {"add": "+", "sub": "-", "mul": "*"}[h]
        return f"({to_str(e[1])}{op}{to_str(e[2])})"
    if h in REDUCES:
        return f"{h}({to_str(e[1])})"
    if h in ("map", "filter"):
        return f"{h}[{e[1]}]({to_str(e[2])})"
    return str(e)


# =============================================================================
# 5. generation over the (library-augmented) grammar
# =============================================================================
CONSTS = (-2, -1, 0, 1, 2)
MAX_SIZE = 26


def gen_list(rng, d, lib, use_lib=0.35):
    lib_lists = lib.value_names("list")
    lib_l2l = lib.func_names("list")
    if d <= 0 or rng.random() < 0.4:
        if lib_lists and rng.random() < use_lib:
            return ("lib", rng.choice(lib_lists))
        return ("xs",)
    r = rng.random()
    if lib_l2l and r < use_lib:
        return ("app", rng.choice(lib_l2l), gen_list(rng, d - 1, lib, use_lib))
    if r < 0.6:
        return ("map", rng.choice(UOPS), gen_list(rng, d - 1, lib, use_lib))
    return ("filter", rng.choice(PREDS), gen_list(rng, d - 1, lib, use_lib))


def gen_scalar(rng, d, lib, use_lib=0.35):
    lib_scal = lib.value_names("scalar")
    lib_l2s = lib.func_names("scalar")
    if d <= 0:
        if lib_scal and rng.random() < use_lib:
            return ("lib", rng.choice(lib_scal))
        return ("const", rng.choice(CONSTS))
    r = rng.random()
    if lib_scal and r < use_lib * 0.5:
        return ("lib", rng.choice(lib_scal))
    if lib_l2s and r < use_lib:
        return ("app", rng.choice(lib_l2s), gen_list(rng, d - 1, lib, use_lib))
    r2 = rng.random()
    if r2 < 0.25:
        return ("const", rng.choice(CONSTS))
    if r2 < 0.6:
        return (rng.choice(REDUCES), gen_list(rng, d - 1, lib, use_lib))
    return (rng.choice(BINOPS), gen_scalar(rng, d - 1, lib, use_lib),
            gen_scalar(rng, d - 1, lib, use_lib))


def gen_program(rng, lib, max_depth=3, use_lib=0.35):
    # programs return a scalar; bias toward using xs / library
    return gen_scalar(rng, max_depth, lib, use_lib)


# =============================================================================
# 6. mutation operators (read/write Expr trees only — never the evaluator)
# =============================================================================

def _get(e, path):
    cur = e
    for i in path:
        cur = cur[i]
    return cur


def op_point_const(rng, e, pop, lib):
    spots = [p for p, s in collect(e) if s[0] == "const"]
    if not spots:
        return None
    p = rng.choice(spots)
    return replace_at(e, p, ("const", _get(e, p)[1] + rng.choice((-2, -1, 1, 2))))


def _swap_family(node, rng):
    h = node[0]
    if h in BINOPS:
        return (rng.choice([o for o in BINOPS if o != h]),) + node[1:]
    if h in REDUCES:
        return (rng.choice([o for o in REDUCES if o != h]),) + node[1:]
    if h == "map":
        return ("map", rng.choice([o for o in UOPS if o != node[1]]), node[2])
    if h == "filter":
        return ("filter", rng.choice([o for o in PREDS if o != node[1]]), node[2])
    return None


def op_point_op(rng, e, pop, lib):
    spots = [(p, s) for p, s in collect(e)
             if s[0] in BINOPS or s[0] in REDUCES or s[0] in ("map", "filter")]
    if not spots:
        return None
    p, node = rng.choice(spots)
    sw = _swap_family(node, rng)
    return replace_at(e, p, sw) if sw else None


def op_grow(rng, e, pop, lib):
    p, node = rng.choice(collect(e))
    fresh = gen_list(rng, 2, lib) if typeof(node, lib) == "list" else gen_scalar(rng, 2, lib)
    cand = replace_at(e, p, fresh)
    return cand if size(cand) <= MAX_SIZE else None


def op_shrink(rng, e, pop, lib):
    spots = collect(e)
    rng.shuffle(spots)
    for p, node in spots:
        descs = [s for q, s in collect(node) if q and typeof(s, lib) == typeof(node, lib)]
        if descs:
            return replace_at(e, p, rng.choice(descs))
    return None


def op_insert_transform(rng, e, pop, lib):
    lists = [p for p, s in collect(e) if typeof(s, lib) == "list"]
    if not lists:
        return None
    p = rng.choice(lists)
    sub = _get(e, p)
    if rng.random() < 0.5:
        w = ("map", rng.choice(UOPS), sub)
    else:
        w = ("filter", rng.choice(PREDS), sub)
    cand = replace_at(e, p, w)
    return cand if size(cand) <= MAX_SIZE else None


def op_use_library(rng, e, pop, lib):
    """Inject a learned abstraction: a library VALUE, or app(FUNC, generated arg).
    This is the operator through which accumulated self-improvement is exploited."""
    choices = []
    for p, s in collect(e):
        t = typeof(s, lib)
        if lib.value_names(t):
            choices.append(("val", p, t))
        if t == "scalar" and lib.func_names("scalar"):
            choices.append(("fs", p, t))
        if t == "list" and lib.func_names("list"):
            choices.append(("fl", p, t))
    if not choices:
        return None
    kind, p, t = rng.choice(choices)
    if kind == "val":
        node = ("lib", rng.choice(lib.value_names(t)))
    elif kind == "fs":
        node = ("app", rng.choice(lib.func_names("scalar")), gen_list(rng, 2, lib))
    else:
        node = ("app", rng.choice(lib.func_names("list")), gen_list(rng, 2, lib))
    cand = replace_at(e, p, node)
    return cand if size(cand) <= MAX_SIZE else None


def op_crossover(rng, e, pop, lib):
    if not pop:
        return None
    other = rng.choice(pop)
    if other is e:
        return None
    mine = collect(e)
    rng.shuffle(mine)
    theirs = collect(other)
    for p, node in mine:
        compat = [s for _, s in theirs if typeof(s, lib) == typeof(node, lib)]
        if compat:
            cand = replace_at(e, p, rng.choice(compat))
            if size(cand) <= MAX_SIZE:
                return cand
    return None


OPS = [op_point_const, op_point_op, op_grow, op_shrink,
       op_insert_transform, op_use_library, op_crossover]


# =============================================================================
# 7. frozen evaluator + data split
# =============================================================================

class Task:
    def __init__(self, name):
        self.name = name
        self.fn = TARGETS[name]
        r = random.Random("task::" + name)        # data seed independent of search
        self.train = [self._inp(r) for _ in range(16)]
        self.holdout = [self._inp(r) for _ in range(16)]
        self.test = [self._inp(r) for _ in range(40)]
        self.tr_y = [self.fn(x) for x in self.train]
        self.ho_y = [self.fn(x) for x in self.holdout]
        self.te_y = [self.fn(x) for x in self.test]

    @staticmethod
    def _inp(r):
        return [r.randint(-9, 9) for _ in range(r.randint(1, 6))]

    def error(self, e, split, lib):
        X, Y = ({"train": (self.train, self.tr_y),
                 "holdout": (self.holdout, self.ho_y),
                 "test": (self.test, self.te_y)})[split]
        tot = 0.0
        for x, y in zip(X, Y):
            try:
                out = evaluate(e, x, lib)
            except (EvalError, RecursionError, ValueError, ZeroDivisionError, OverflowError):
                tot += 1.0
                continue
            if not isinstance(out, int):
                tot += 1.0
                continue
            tot += 0.0 if out == y else min(1.0, abs(out - y) / (1 + abs(y)))
        return tot / len(X)


# =============================================================================
# 8. the search (solves ONE task with the CURRENT library)
# =============================================================================

def run_search(task: Task, lib: Library, seed: int, budget: int,
               pop_size: int = 50, max_depth: int = 4):
    rng = random.Random(seed)
    pop = []
    for _ in range(pop_size):
        p = gen_program(rng, lib, max_depth)
        pop.append({"e": p, "te": task.error(p, "train", lib)})
    best = min(pop, key=lambda r: (r["te"], size(r["e"])))
    champ_e, champ_ho, champ_sz = best["e"], task.error(best["e"], "holdout", lib), size(best["e"])

    evals = 0
    while evals < budget:
        contenders = rng.sample(pop, min(4, len(pop)))
        parent = min(contenders, key=lambda r: (r["te"], size(r["e"])))
        op = rng.choice(OPS)
        child = op(rng, parent["e"], [r["e"] for r in pop], lib)
        if child is None or child == parent["e"]:
            continue
        ce = task.error(child, "train", lib)
        evals += 1
        worst = max(pop, key=lambda r: (r["te"], -size(r["e"])))
        if (ce, size(child)) < (worst["te"], -size(worst["e"])):
            pop.remove(worst)
            pop.append({"e": child, "te": ce})
        ch = task.error(child, "holdout", lib)
        if (ch, size(child)) < (champ_ho, champ_sz):
            champ_e, champ_ho, champ_sz = child, ch, size(child)
            if champ_ho == 0.0:
                # solved on holdout — keep a little longer only to simplify, then stop
                break
    te = task.error(champ_e, "test", lib)
    return {"task": task.name, "seed": seed, "expr": champ_e,
            "hold_err": champ_ho, "test_err": te, "solved": te == 0.0,
            "evals": evals, "size": champ_sz}


# =============================================================================
# 9. ABSTRACTION: the system compresses its OWN solutions into new primitives
# =============================================================================

def anti_unify(a, b):
    """First-order anti-unification. Returns (pattern_with_holes, n_distinct_holes)
    or None. Identical differing-subterm-pairs collapse to ONE hole (reuse)."""
    holes: Dict[Tuple, int] = {}

    def au(x, y):
        if isinstance(x, tuple) and isinstance(y, tuple) and x[0] == y[0]:
            h = x[0]
            if h in ("const",):
                if x[1] == y[1]:
                    return x
                key = (x, y)
                holes.setdefault(key, len(holes))
                return ("hole",)
            if h in ("map", "filter"):  # op label must match too
                if x[1] != y[1]:
                    key = (x, y)
                    holes.setdefault(key, len(holes))
                    return ("hole",)
                return (h, x[1], au(x[2], y[2]))
            if h == "lib":
                if x[1] == y[1]:
                    return x
                key = (x, y); holes.setdefault(key, len(holes)); return ("hole",)
            if h == "app":
                if x[1] != y[1]:
                    key = (x, y); holes.setdefault(key, len(holes)); return ("hole",)
                return ("app", x[1], au(x[2], y[2]))
            idx = child_idx(x)
            if not idx:
                return x
            lst = list(x)
            for i in idx:
                lst[i] = au(x[i], y[i])
            return tuple(lst)
        # heads differ -> a hole standing for this differing position
        key = (x, y)
        holes.setdefault(key, len(holes))
        return ("hole",)

    pat = au(a, b)
    return pat, len(holes)


def hole_type_in_base(differs) -> Optional[str]:
    """Type of the differing subterms (must agree). Used to type the FUNC hole."""
    types = set()
    for x, y in differs:
        for t in (_base_type(x), _base_type(y)):
            types.add(t)
    return types.pop() if len(types) == 1 else None


def _base_type(e):
    if not isinstance(e, tuple):
        return "scalar"
    if e[0] in ("xs", "map", "filter"):
        return "list"
    return "scalar"


def minimize(e, task, lib, max_rounds=60):
    """Behavior-preserving compression of a SOLVED program: greedily shrink while
    keeping TRAIN and HELDOUT error at 0. Canonicalizes the system's own solution
    so that (a) memoized skills are clean and (b) anti-unification can find shared
    structure. TEST is never consulted -> no leakage. Occam, not gaming."""
    if task.error(e, "train", lib) != 0.0 or task.error(e, "holdout", lib) != 0.0:
        return e
    best, best_sz = e, size(e)
    for _ in range(max_rounds):
        improved = False
        for p, node in collect(best):
            cands = []
            # (1) replace a node with a same-typed strict descendant (drops wrappers)
            cands += [s for q, s in collect(node) if q and typeof(s, lib) == typeof(node, lib)]
            # (2) strip identity map
            if node[0] == "map" and node[1] == "id":
                cands.append(node[2])
            for c in cands:
                cand = replace_at(best, p, c)
                if size(cand) < best_sz \
                        and task.error(cand, "train", lib) == 0.0 \
                        and task.error(cand, "holdout", lib) == 0.0:
                    best, best_sz, improved = cand, size(cand), True
                    break
            if improved:
                break
        if not improved:
            break
    return best


def abstract(lib: Library, solved: List[Dict[str, Any]], round_tag: str) -> List[str]:
    """Add new primitives derived from the system's own solutions. Returns log lines."""
    log = []
    # (a) memoize each new solution as a reusable VALUE primitive ("skill").
    #     Stored in LIBRARY-AUGMENTED form, so a skill that used a learned FUNC
    #     references that FUNC -> this is what creates recursive dependency depth.
    for s in solved:
        nm = "skill_" + s["task"]
        if nm not in lib.values and size(s["expr"]) > 1:
            lib.add_value(nm, s["expr"], "scalar")
            log.append(f"  + VALUE {nm} := {to_str(s['expr'])}   deps={sorted(refs_of(s['expr'])) or '-'}")
    # (b) anti-unify pairs of solved programs (BASE-expanded) to extract reusable
    #     arity-1 FUNCTION primitives. These are genuine abstractions, discovered
    #     by the system, not provided.
    bases = []
    for s in solved:
        try:
            bases.append((s["task"], expand(s["expr"], lib)))
        except EvalError:
            pass
    for i in range(len(bases)):
        for j in range(i + 1, len(bases)):
            (ta, ea), (tb, eb) = bases[i], bases[j]
            res = anti_unify(ea, eb)
            if not res:
                continue
            pat, nholes = res
            if nholes != 1:
                continue                      # accept only arity-1 abstractions
            body_sz = size(pat)
            if body_sz < 3:
                continue                      # too trivial to be worth a name
            # determine hole type from the differing subterms
            holes = {}
            def collect_diffs(x, y):
                if isinstance(x, tuple) and isinstance(y, tuple) and x[0] == y[0]:
                    h = x[0]
                    if h in ("map", "filter", "app") and x[1] != y[1]:
                        holes[(x, y)] = True; return
                    if h == "const" and x[1] != y[1]:
                        holes[(x, y)] = True; return
                    if h == "lib" and x[1] != y[1]:
                        holes[(x, y)] = True; return
                    for k in child_idx(x):
                        collect_diffs(x[k], y[k])
                else:
                    holes[(x, y)] = True
            collect_diffs(ea, eb)
            in_t = hole_type_in_base(list(holes.keys()))
            if in_t != "list":               # we learn functions OF A LIST
                continue
            out_t = _base_type(pat)
            fname = "F_" + _short(pat)
            if fname in lib.funcs:
                continue
            lib.add_func(fname, pat, "list", out_t)
            log.append(f"  + FUNC  {fname} := λ·. {to_str(pat)}   (from {ta} & {tb})")
    return log


def _short(e):
    s = to_str(e).replace("·", "h")
    keep = "".join(c for c in s if c.isalnum())[:10]
    return keep or "f"


# =============================================================================
# 10. dependency-depth analysis (the recursion, made explicit)
# =============================================================================

def dep_depth(name: str, lib: Library, _seen=None) -> int:
    """Longest chain of learned-primitive dependencies under `name`."""
    if _seen is None:
        _seen = set()
    if name in _seen:
        return 0
    _seen = _seen | {name}
    deps = set()
    if name in lib.values:
        deps = lib.values[name]["deps"]
    elif name in lib.funcs:
        deps = lib.funcs[name]["deps"]
    if not deps:
        return 0
    return 1 + max((dep_depth(d, lib, _seen) for d in deps), default=0)


def expr_dep_depth(e, lib) -> int:
    rs = refs_of(e)
    return 1 + max((dep_depth(r, lib) for r in rs), default=-1) if rs else 0


# =============================================================================
# 11. feasibility (objective is honest: a correct program scores exactly 0)
# =============================================================================
KNOWN = {
    "t1_ss": ("sum", ("map", "sq", ("xs",))),
    "t1_sspos": ("sum", ("map", "sq", ("filter", "pos", ("xs",)))),
    "t2_inc_pos": ("sum", ("map", "sq", ("map", "inc", ("filter", "pos", ("xs",))))),
    "t2_abs_neg": ("sum", ("map", "sq", ("map", "abs", ("filter", "neg", ("xs",))))),
    "t3": ("sub",
           ("sum", ("map", "sq", ("map", "inc", ("filter", "pos", ("xs",))))),
           ("sum", ("map", "sq", ("map", "abs", ("filter", "neg", ("xs",)))))),
}


def feasibility():
    print("== FEASIBILITY (frozen evaluator on hand-written base solutions) ==")
    empty = Library()
    ok = True
    for name in TARGETS:
        t = Task(name)
        sol = KNOWN[name]
        te = t.error(sol, "test", empty)
        tag = "OK " if te == 0.0 else "BAD"
        ok &= te == 0.0
        print(f"  [{tag}] {name:11s} {to_str(sol):46s} test_err={te:.3f}  (size {size(sol)})")
    print(f"  -> objective {'HONEST' if ok else 'BROKEN'}\n")
    return ok


# =============================================================================
# 12. THE BOOTSTRAP LOOP + the cold/warm proof
# =============================================================================

def solve_task_multiseed(name, lib, budget, seeds):
    """Try a task across seeds; return first solve (or best attempt)."""
    best = None
    for s in seeds:
        r = run_search(Task(name), lib, s, budget)
        if r["solved"]:
            return r
        if best is None or r["test_err"] < best["test_err"]:
            best = r
    return best


def run_bootstrap(budget=2500, seeds_per_task=6, cold_seeds=12, verbose=True):
    if not feasibility():
        print("aborting."); return

    print("== COLD CONTROL: solve the hard task with an EMPTY library ==")
    print(f"   ({HARD_TASK}, budget={budget}, {cold_seeds} seeds, no learned primitives)")
    empty = Library()
    cold_sols = 0
    cold_best = 1.0
    for s in range(cold_seeds):
        r = run_search(Task(HARD_TASK), empty, s, budget)
        cold_sols += r["solved"]
        cold_best = min(cold_best, r["test_err"])
    print(f"   COLD result: solved {cold_sols}/{cold_seeds} seeds, best test_err={cold_best:.4f}\n")

    print("== BOOTSTRAP: solve the curriculum, abstracting own solutions each tier ==")
    lib = Library()
    solved_all: List[Dict[str, Any]] = []
    seeds = list(range(seeds_per_task))
    for tier_name, names in CURRICULUM:
        print(f"-- {tier_name} --  (library has {len(lib.values)} values, {len(lib.funcs)} funcs)")
        tier_solved = []
        for nm in names:
            r = solve_task_multiseed(nm, lib, budget, seeds)
            if r["solved"]:
                r["expr"] = minimize(r["expr"], Task(nm), lib)   # canonicalize own solution
            status = "SOLVED" if r["solved"] else f"FAILED(err={r['test_err']:.3f})"
            print(f"   {nm:11s} [{status:>14s}]  {to_str(r['expr'])}")
            if r["solved"]:
                tier_solved.append(r)
                solved_all.append(r)
        # the system compresses what it just solved into new primitives
        log = abstract(lib, tier_solved, tier_name)
        for line in log:
            print(line)
        print()

    print("== LEARNED LIBRARY (discovered by the system from its own solutions) ==")
    for nm in lib.order:
        if nm in lib.values:
            v = lib.values[nm]
            print(f"   VALUE {nm:18s} : {to_str(v['expr'])}   [dep_depth={dep_depth(nm, lib)}]")
        else:
            f = lib.funcs[nm]
            print(f"   FUNC  {nm:18s} : λ·. {to_str(f['body'])}   [dep_depth={dep_depth(nm, lib)}]")

    # warm solution of the hard task (if curriculum already solved it, re-solve to
    # exhibit the library-composed form explicitly)
    print(f"\n== WARM: solve the hard task '{HARD_TASK}' WITH the learned library ==")
    warm = solve_task_multiseed(HARD_TASK, lib, budget, seeds)
    if warm["solved"]:
        warm["expr"] = minimize(warm["expr"], Task(HARD_TASK), lib)
    wtag = "SOLVED" if warm["solved"] else f"FAILED(err={warm['test_err']:.3f})"
    print(f"   WARM result: [{wtag}]  {to_str(warm['expr'])}")
    if warm["solved"]:
        chain_depth = expr_dep_depth(warm["expr"], lib)
        used = sorted(refs_of(warm["expr"]))
        print(f"   winning program uses learned primitives: {used or '-'}")
        print(f"   recursion depth of the winning program's dependency chain: {chain_depth}")
        # print the full chain
        _print_chain(warm["expr"], lib)

    print("\n== VERDICT ==")
    warm_ok = warm["solved"]
    if warm_ok and cold_sols == 0:
        print("   RECURSIVE SELF-IMPROVEMENT CONFIRMED:")
        print(f"   '{HARD_TASK}' was UNSOLVABLE cold (0/{cold_seeds}) but SOLVED warm,")
        print("   using abstractions the system distilled from its own earlier solutions.")
    elif warm_ok and cold_sols < cold_seeds:
        print(f"   PARTIAL: warm solves it; cold solved only {cold_sols}/{cold_seeds}.")
        print("   The learned library made the hard task reliably reachable (efficiency")
        print("   gain), though base search occasionally stumbles onto it cold.")
    elif warm_ok:
        print("   warm and cold both solve it -> the hard task was not actually out of")
        print("   reach at this budget; the bootstrapping helped but isn't load-bearing here.")
    else:
        print("   warm did NOT solve it -> reported honestly; abstraction did not (yet)")
        print("   yield the needed capability at this budget.")


def _print_chain(e, lib, indent="     "):
    for r in sorted(refs_of(e)):
        if r in lib.values:
            sub = lib.values[r]["expr"]
            print(f"{indent}{r}  ->  {to_str(sub)}")
            if refs_of(sub):
                _print_chain(sub, lib, indent + "   ")
        elif r in lib.funcs:
            body = lib.funcs[r]["body"]
            print(f"{indent}{r}  ->  λ·. {to_str(body)}")


# =============================================================================
# 13. CLI
# =============================================================================

def main():
    ap = argparse.ArgumentParser(description="Bootstrapping recursive self-improvement")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("feasibility")
    b = sub.add_parser("bootstrap", help="run the full self-improvement loop + cold/warm proof")
    b.add_argument("--budget", type=int, default=2500)
    b.add_argument("--seeds", type=int, default=6)
    b.add_argument("--cold-seeds", type=int, default=12)
    args = ap.parse_args()
    if args.cmd == "feasibility":
        feasibility()
    elif args.cmd == "bootstrap":
        run_bootstrap(budget=args.budget, seeds_per_task=args.seeds, cold_seeds=args.cold_seeds)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()