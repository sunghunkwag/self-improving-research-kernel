from scripts import rsi_bootstrap
from scripts.rsi_bootstrap_proof import run_proof


def test_known_bootstrap_targets_are_feasible_under_frozen_evaluator():
    lib = rsi_bootstrap.Library()

    for name, expr in rsi_bootstrap.KNOWN.items():
        task = rsi_bootstrap.Task(name)

        assert task.error(expr, "test", lib) == 0.0


def test_anti_unified_library_chain_solves_hard_task_without_label_leakage():
    lib = rsi_bootstrap.Library()
    tier1_solved = [
        {"task": "t1_ss", "expr": rsi_bootstrap.KNOWN["t1_ss"]},
        {"task": "t1_sspos", "expr": rsi_bootstrap.KNOWN["t1_sspos"]},
    ]
    rsi_bootstrap.abstract(lib, tier1_solved, "tier1")
    square_sum = next(
        name
        for name, info in lib.funcs.items()
        if info["out"] == "scalar" and "map[sq]" in rsi_bootstrap.to_str(info["body"])
    )
    tier2_solved = [
        {
            "task": "t2_inc_pos",
            "expr": ("app", square_sum, ("map", "inc", ("filter", "pos", ("xs",)))),
        },
        {
            "task": "t2_abs_neg",
            "expr": ("app", square_sum, ("map", "abs", ("filter", "neg", ("xs",)))),
        },
    ]
    rsi_bootstrap.abstract(lib, tier2_solved, "tier2")
    hard_expr = ("sub", ("lib", "skill_t2_inc_pos"), ("lib", "skill_t2_abs_neg"))

    hard_task = rsi_bootstrap.Task(rsi_bootstrap.HARD_TASK)

    assert hard_task.error(hard_expr, "test", lib) == 0.0
    assert rsi_bootstrap.expr_dep_depth(hard_expr, lib) >= 2


def test_bootstrap_proof_wrapper_reports_unconfirmed_small_budget_honestly():
    result = run_proof(budget=1, seeds=1, cold_seeds=1)

    assert result["budget"] == 1
    assert result["confirmed"] is False
    assert "VERDICT" in result["output"]
