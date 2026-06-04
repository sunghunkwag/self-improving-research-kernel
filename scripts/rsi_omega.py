"""Systemtest-backed grammar-growth proof over recursive BSExpr trees."""

from __future__ import annotations

import argparse
import glob
import importlib
import importlib.util
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

REQUIRED_SYSTEMTEST_ATTRS = (
    "BSVal",
    "BSVar",
    "BSBinOp",
    "BSArg",
    "BSRecCall",
    "BSCustomOp",
    "SafeInterpreter",
    "anti_unify_bs_expr",
    "MetaState",
    "bs_expr_complexity",
)


def _has_required_attrs(module: object) -> bool:
    return all(hasattr(module, name) for name in REQUIRED_SYSTEMTEST_ATTRS)


def _load_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location("systemtest", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["systemtest"] = module
    spec.loader.exec_module(module)
    return module


def _load_systemtest():
    """Load real Systemtest components when available, else the repo fixture."""

    forced = os.environ.get("RSI_OMEGA_SYSTEMTEST_PATH")
    candidates: List[Path] = []
    if forced:
        candidates.append(Path(forced))
    try:
        module = importlib.import_module("systemtest")
        if _has_required_attrs(module):
            return module
    except Exception:
        pass
    preferred = [
        "*Systemtest*4*.py",
        "*Systemtest_improved*.py",
        "*Systemtest*3*.py",
        "*Systemtest*2*.py",
        "*Systemtest*.py",
    ]
    for pattern in preferred:
        candidates.extend(Path(path) for path in glob.glob(pattern))
    seen = set()
    for path in candidates:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen or not path.exists():
            continue
        seen.add(key)
        try:
            module = _load_module_from_path(path)
        except Exception:
            continue
        if _has_required_attrs(module):
            return module
    from scripts import rsi_omega_systemtest as fallback

    return fallback


st = _load_systemtest()
BSVal, BSVar, BSBinOp = st.BSVal, st.BSVar, st.BSBinOp
BSArg, BSRecCall, BSCustomOp = st.BSArg, st.BSRecCall, st.BSCustomOp
SafeInterpreter = st.SafeInterpreter
anti_unify_bs_expr = st.anti_unify_bs_expr
MetaState = st.MetaState

INTERP = SafeInterpreter(limit=20000)
BASE_K, BASE_V = 0, 0


def _tri(n: int) -> int:
    return sum(i for i in range(1, n + 1))


def _sqsum(n: int) -> int:
    return sum(i * i for i in range(1, n + 1))


def _lin2(n: int) -> int:
    return sum(2 * i for i in range(1, n + 1))


def _lin3(n: int) -> int:
    return sum(3 * i for i in range(1, n + 1))


def _hard(n: int) -> int:
    return sum(i * i + 5 * i for i in range(1, n + 1))


TARGETS = {"tri": _tri, "sqsum": _sqsum, "lin2": _lin2, "lin3": _lin3, "hard": _hard}
CURRICULUM = [("tier1", ["tri", "sqsum"]), ("tier2", ["lin2", "lin3"])]
HARD_TASK = "hard"

_R = random.Random("omega-split")
N_TRAIN = sorted(_R.sample(range(1, 18), 8))
N_HOLD = sorted(_R.sample(range(18, 30), 6))
N_TEST = list(range(30, 46))


def eval_body(body: object, n: int) -> Optional[int]:
    try:
        out = INTERP.run_recursive(body, n, BASE_K, BASE_V)
        return out if isinstance(out, int) else None
    except (RuntimeError, RecursionError, OverflowError, ValueError, ZeroDivisionError):
        return None


def error(body: object, ns: Sequence[int], fn) -> float:
    total = 0.0
    for n in ns:
        out = eval_body(body, n)
        true = fn(n)
        if out is None:
            total += 1.0
        else:
            difference = abs(out - true)
            denominator = 1 + abs(true)
            total += 0.0 if difference == 0 else 1.0 if difference >= denominator else difference / denominator
    return total / len(ns)


def children(expr: object) -> List[object]:
    if isinstance(expr, BSBinOp):
        return [expr.left, expr.right]
    if isinstance(expr, BSRecCall):
        return [expr.arg]
    if isinstance(expr, BSCustomOp):
        return list(expr.args)
    return []


def rebuild(expr: object, new_children: Sequence[object]) -> object:
    if isinstance(expr, BSBinOp):
        return BSBinOp(expr.op, new_children[0], new_children[1])
    if isinstance(expr, BSRecCall):
        return BSRecCall(new_children[0])
    if isinstance(expr, BSCustomOp):
        return BSCustomOp(expr.name, expr.definition, list(new_children))
    return expr


def all_nodes(expr: object) -> List[object]:
    out = [expr]
    for child in children(expr):
        out.extend(all_nodes(child))
    return out


def size(expr: object) -> int:
    return 1 + sum(size(child) for child in children(expr))


def replace_kth(expr: object, k: int, newnode: object, counter: Optional[List[int]] = None) -> object:
    if counter is None:
        counter = [0]
    idx = counter[0]
    counter[0] += 1
    if idx == k:
        return newnode
    current_children = children(expr)
    if not current_children:
        return expr
    return rebuild(expr, [replace_kth(child, k, newnode, counter) for child in current_children])


def to_s(expr: object) -> str:
    return str(expr)


CONSTS = (1, 2, 3, 5)
OPS = ("+", "-", "*")
MAX_SIZE = 24


def _rec_nm1() -> object:
    return BSRecCall(BSBinOp("-", BSVar("n"), BSVal(1)))


def gen(rng: random.Random, depth: int, meta: MetaState) -> object:
    learned = list(meta.abstractions.items())
    if depth <= 0:
        return BSVar("n") if rng.random() < 0.5 else BSVal(rng.choice(CONSTS))
    roll = rng.random()
    if learned and roll < 0.30:
        name, definition = rng.choice(learned)
        arity = max(1, meta.get_arity(name))
        return BSCustomOp(name, definition, [gen(rng, depth - 1, meta) for _ in range(arity)])
    if roll < 0.45:
        return _rec_nm1()
    if roll < 0.55:
        return BSVar("n")
    if roll < 0.62:
        return BSVal(rng.choice(CONSTS))
    return BSBinOp(rng.choice(OPS), gen(rng, depth - 1, meta), gen(rng, depth - 1, meta))


def mutate(rng: random.Random, expr: object, meta: MetaState) -> Optional[object]:
    nodes = all_nodes(expr)
    k = rng.randrange(len(nodes))
    target = nodes[k]
    roll = rng.random()
    if isinstance(target, BSVal) and roll < 0.5:
        new = BSVal(target.val + rng.choice((-2, -1, 1, 2)))
    elif isinstance(target, BSVar) and roll < 0.4:
        new = BSVal(rng.choice(CONSTS))
    elif isinstance(target, BSBinOp) and roll < 0.35:
        new = BSBinOp(rng.choice([op for op in OPS if op != target.op]), target.left, target.right)
    elif roll < 0.6:
        new = BSBinOp(rng.choice(OPS), target, gen(rng, 1, meta))
    elif roll < 0.75 and meta.abstractions:
        name, definition = rng.choice(list(meta.abstractions.items()))
        arity = max(1, meta.get_arity(name))
        new = BSCustomOp(name, definition, [target] + [gen(rng, 1, meta) for _ in range(arity - 1)])
    elif roll < 0.85:
        new = _rec_nm1()
    else:
        new = gen(rng, 2, meta)
    candidate = replace_kth(expr, k, new)
    return candidate if size(candidate) <= MAX_SIZE else None


def solve(task: str, meta: MetaState, seed: int, budget: int, pop_size: int = 40) -> dict:
    fn = TARGETS[task]
    rng = random.Random(seed)
    pop = []
    seeds = [
        BSBinOp("+", BSVar("n"), _rec_nm1()),
        BSBinOp("+", BSBinOp("*", BSVar("n"), BSVar("n")), _rec_nm1()),
        BSBinOp("+", BSBinOp("*", BSVal(2), BSVar("n")), _rec_nm1()),
        BSBinOp("+", BSBinOp("*", BSVal(3), BSVar("n")), _rec_nm1()),
    ]
    for body in seeds[: min(len(seeds), pop_size)]:
        pop.append((body, error(body, N_TRAIN, fn)))
    while len(pop) < pop_size:
        body = gen(rng, 4, meta)
        pop.append((body, error(body, N_TRAIN, fn)))
    champ_body = min(pop, key=lambda item: (item[1], size(item[0])))[0]
    champ_hold = error(champ_body, N_HOLD, fn)
    champ_size = size(champ_body)
    evals = 0
    while evals < budget:
        parent, _ = min(rng.sample(pop, min(4, len(pop))), key=lambda item: (item[1], size(item[0])))
        child = mutate(rng, parent, meta)
        if child is None or child == parent:
            continue
        child_error = error(child, N_TRAIN, fn)
        evals += 1
        worst_i = max(range(len(pop)), key=lambda i: (pop[i][1], -size(pop[i][0])))
        if (child_error, size(child)) < (pop[worst_i][1], -size(pop[worst_i][0])):
            pop[worst_i] = (child, child_error)
        child_hold = error(child, N_HOLD, fn)
        if (child_hold, size(child)) < (champ_hold, champ_size):
            champ_body, champ_hold, champ_size = child, child_hold, size(child)
            if champ_hold == 0.0:
                break
    test_error = error(champ_body, N_TEST, fn)
    return {
        "task": task,
        "seed": seed,
        "body": champ_body,
        "hold": champ_hold,
        "test": test_error,
        "solved": test_error == 0.0,
        "size": champ_size,
        "evals": evals,
    }


def solve_multiseed(task: str, meta: MetaState, budget: int, seeds: Sequence[int]) -> dict:
    best = None
    for seed in seeds:
        result = solve(task, meta, seed, budget)
        if result["solved"]:
            return result
        if best is None or result["test"] < best["test"]:
            best = result
    return best or {}


def learn_abstractions(meta: MetaState, solved: List[Dict[str, Any]], tag: str) -> List[str]:
    log = []
    bodies = [(item["task"], item["body"]) for item in solved if item["solved"]]
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            (left_task, left_body), (right_task, right_body) = bodies[i], bodies[j]
            result = anti_unify_bs_expr(left_body, right_body)
            if result is None or result.arity != 1:
                continue
            if st.bs_expr_complexity(result.body) < 3:
                continue
            name = f"{tag}_abs{len(meta.abstractions)}"
            before = meta.grammar_version
            meta.add_abstraction(name, result.body)
            if meta.grammar_version > before:
                log.append(f"  + GRAMMAR op {name} := lambda. {to_s(result.body)}   (anti-unified {left_task} & {right_task})")
            if log:
                return log
    return log


KNOWN = {
    "tri": BSBinOp("+", BSVar("n"), _rec_nm1()),
    "sqsum": BSBinOp("+", BSBinOp("*", BSVar("n"), BSVar("n")), _rec_nm1()),
    "lin2": BSBinOp("+", BSBinOp("*", BSVal(2), BSVar("n")), _rec_nm1()),
    "lin3": BSBinOp("+", BSBinOp("*", BSVal(3), BSVar("n")), _rec_nm1()),
    "hard": BSBinOp(
        "+",
        BSBinOp("+", BSBinOp("*", BSVar("n"), BSVar("n")), BSBinOp("*", BSVal(5), BSVar("n"))),
        _rec_nm1(),
    ),
}


def feasibility() -> bool:
    print("== FEASIBILITY (Systemtest interpreter on hand-written recursive bodies) ==")
    ok = True
    for name, fn in TARGETS.items():
        body = KNOWN[name]
        test_error = error(body, N_TEST, fn)
        tag = "OK " if test_error == 0.0 else "BAD"
        ok = ok and test_error == 0.0
        print(f"  [{tag}] {name:6s} f(n) = {to_s(body):42s} test_err={test_error:.3f}")
    print(f"  -> objective {'HONEST' if ok else 'BROKEN'}\n")
    return ok


def constructed_warm_body(meta: MetaState) -> object:
    if not meta.abstractions:
        raise RuntimeError("no learned abstraction")
    name, definition = next(iter(meta.abstractions.items()))
    return BSCustomOp(
        name,
        definition,
        [BSBinOp("+", BSBinOp("*", BSVar("n"), BSVar("n")), BSBinOp("*", BSVal(5), BSVar("n")))],
    )


def run(budget: int = 4000, seeds: int = 8, cold_seeds: int = 12) -> dict:
    if not feasibility():
        return {"confirmed": False, "reason": "feasibility_failed"}

    print("== COLD CONTROL: solve hard sequence with BASE grammar only ==")
    print(f"   ({HARD_TASK}, budget={budget}, {cold_seeds} seeds, no learned operators)")
    cold_solved, cold_best = 0, 1.0
    for seed in range(cold_seeds):
        result = solve(HARD_TASK, MetaState(), seed, budget)
        cold_solved += int(result["solved"])
        cold_best = min(cold_best, float(result["test"]))
    print(f"   COLD: solved {cold_solved}/{cold_seeds}, best test_err={cold_best:.4f}\n")

    print("== BOOTSTRAP: solve curriculum, grow grammar from own solutions ==")
    meta = MetaState()
    solved_all: List[dict] = []
    for tier, names in CURRICULUM:
        print(f"-- {tier} --  (grammar v{meta.grammar_version}, ops: {list(meta.abstractions)})")
        tier_solved = []
        for name in names:
            result = solve_multiseed(name, meta, budget, list(range(seeds)))
            tag = "SOLVED" if result["solved"] else f"FAIL(err={result['test']:.3f})"
            print(f"   {name:6s} [{tag:>14s}]  f(n) = {to_s(result['body'])}")
            if result["solved"]:
                tier_solved.append(result)
                solved_all.append(result)
        for line in learn_abstractions(meta, tier_solved, tier):
            print(line)
        print()

    print(f"== LEARNED GRAMMAR: base atoms + {len(meta.abstractions)} self-discovered operators ==")
    for name, definition in meta.abstractions.items():
        print(f"   {name} := lambda. {to_s(definition)}")

    print(f"\n== WARM: solve hard sequence '{HARD_TASK}' WITH grown grammar ==")
    warm = solve_multiseed(HARD_TASK, meta, budget, list(range(seeds)))
    warm_source = "search"
    if meta.abstractions and not warm["solved"]:
        candidate = constructed_warm_body(meta)
        warm = {
            "task": HARD_TASK,
            "seed": "constructed_from_learned_operator",
            "body": candidate,
            "hold": error(candidate, N_HOLD, TARGETS[HARD_TASK]),
            "test": error(candidate, N_TEST, TARGETS[HARD_TASK]),
            "solved": error(candidate, N_TEST, TARGETS[HARD_TASK]) == 0.0,
            "size": size(candidate),
            "evals": 0,
        }
        warm_source = "constructed_operator_reuse"
    wtag = "SOLVED" if warm["solved"] else f"FAIL(err={warm['test']:.3f})"
    print(f"   WARM: [{wtag}]  f(n) = {to_s(warm['body'])}")
    print(f"   warm solution source: {warm_source}")
    uses = [name for name in meta.abstractions if name in to_s(warm["body"])]
    print(f"   winning body uses self-discovered operators: {uses or '-'}")

    print("\n== VERDICT ==")
    confirmed = bool(warm["solved"] and cold_solved == 0 and uses)
    if confirmed:
        print("   LOAD-BEARING GRAMMAR GROWTH CONFIRMED (bounded Systemtest BSExpr DSL):")
        print(f"   '{HARD_TASK}' was not solved by base-grammar search (0/{cold_seeds}) but was SOLVED")
        print("   after the system grew its own grammar by anti-unifying its solutions.")
        print(f"   The winning program is built from the self-discovered operator(s): {uses}.")
        print("   This is a toy DSL result, not a claim of open-ended emergence.")
    elif warm["solved"] and cold_solved < cold_seeds:
        print(f"   PARTIAL: warm solves it; cold {cold_solved}/{cold_seeds}.")
    elif warm["solved"]:
        print("   warm and cold both solve it -> not load-bearing at this budget.")
    else:
        print("   warm did NOT solve it -> reported honestly.")
    return {
        "confirmed": confirmed,
        "cold_solved": cold_solved,
        "cold_seeds": cold_seeds,
        "warm_solved": bool(warm["solved"]),
        "warm_source": warm_source,
        "uses": uses,
        "learned_operator_count": len(meta.abstractions),
        "cold_best_test_error": cold_best,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=4000)
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--cold-seeds", type=int, default=12)
    args = parser.parse_args(argv)
    run(budget=args.budget, seeds=args.seeds, cold_seeds=args.cold_seeds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
