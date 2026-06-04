from scripts import rsi_omega
from scripts.rsi_omega_proof import run_proof


def test_omega_known_recursive_bodies_are_frozen_evaluator_feasible():
    for name, body in rsi_omega.KNOWN.items():
        assert rsi_omega.error(body, rsi_omega.N_TEST, rsi_omega.TARGETS[name]) == 0.0


def test_omega_anti_unification_grows_reusable_accumulator_operator():
    meta = rsi_omega.MetaState()
    solved = [
        {"task": "tri", "body": rsi_omega.KNOWN["tri"], "solved": True},
        {"task": "sqsum", "body": rsi_omega.KNOWN["sqsum"], "solved": True},
    ]

    log = rsi_omega.learn_abstractions(meta, solved, "tier1")
    hard_body = rsi_omega.constructed_warm_body(meta)

    assert log
    assert meta.grammar_version == 1
    assert rsi_omega.error(hard_body, rsi_omega.N_TEST, rsi_omega.TARGETS[rsi_omega.HARD_TASK]) == 0.0
    assert list(meta.abstractions)[0] in rsi_omega.to_s(hard_body)


def test_omega_rejects_non_decreasing_recursive_candidates_before_interpretation():
    unsafe = rsi_omega.BSRecCall(rsi_omega.BSVar("n"))

    assert not rsi_omega.has_safe_recursion(unsafe)
    assert rsi_omega.eval_body(unsafe, 5) is None


def test_omega_proof_reports_bounded_small_budget_result_honestly():
    result = run_proof(budget=1, seeds=1, cold_seeds=1)

    assert result["budget"] == 1
    assert "VERDICT" in result["output"]
    assert "bounded Systemtest BSExpr DSL" in result["output"]
    assert result["warm_source"] in {"search", "constructed_operator_reuse"}
    assert isinstance(result["confirmed"], bool)
