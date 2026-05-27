from shared.capability_benchmarks import (
    DEFAULT_CAPABILITY_CASES,
    capability_delta_from_evaluations,
    evaluate_capability_cases,
    extract_failure_residue,
    synthesize_operator_specs,
)
from shared.capability_primitives import (
    apply_grid_action,
    dedupe_preserve_order,
    infer_linear_rule,
    rotate_grid_clockwise,
    run_length_encode,
)


def test_capability_cases_cover_requested_families():
    families = {case.family for case in DEFAULT_CAPABILITY_CASES}

    assert {
        "algorithm_synthesis",
        "symbolic_reasoning",
        "grid_transformation",
        "bug_repair",
        "planning_state_transition",
    } <= families
    assert {case.split for case in DEFAULT_CAPABILITY_CASES} == {"public", "hidden"}


def test_capability_evaluator_scores_public_and_hidden_cases():
    evaluations = evaluate_capability_cases(
        {
            "run_length_encode": run_length_encode,
            "infer_linear_rule": infer_linear_rule,
            "rotate_grid_clockwise": rotate_grid_clockwise,
            "dedupe_preserve_order": dedupe_preserve_order,
            "apply_grid_action": apply_grid_action,
        }
    )
    delta = capability_delta_from_evaluations(
        evaluations,
        reused_operators=("run_length_encode", "run_length_encode", "rotate_grid_clockwise"),
        regression_failures=0,
        compute_cost=3.0,
    )

    assert all(result.solved for result in evaluations)
    assert delta.solved_new_tasks == len(DEFAULT_CAPABILITY_CASES)
    assert delta.hidden_transfer == 5
    assert delta.regression_protection == 1
    assert delta.operator_reuse == 2
    assert delta.score > 10.0


def test_operator_synthesis_specs_include_validation_plan_kinds():
    specs = synthesize_operator_specs("algorithm_synthesis", "run_length_encode")

    assert {spec.kind for spec in specs} == {
        "solver_primitive",
        "search_heuristic",
        "evaluator_mutation",
        "counterexample_test",
    }
    assert all(spec.validation_plan.executable() for spec in specs)


def test_failure_residue_extracts_missing_operator_and_overfit_signal():
    residue = extract_failure_residue(
        "candidate_x",
        [
            {
                "label": "candidate_x_focused",
                "exit_code": 0,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "label": "candidate_x_root_broad",
                "exit_code": 1,
                "stdout_tail": "ImportError: cannot import name 'missing_solver'",
                "stderr_tail": "",
            },
        ],
        error="RuntimeError: one or more validation gates failed",
    )

    assert residue.missing_operator == "missing_solver"
    assert residue.failed_evaluator == "candidate_x_root_broad"
    assert residue.overfit_signal == "focused_passed_broad_failed"

