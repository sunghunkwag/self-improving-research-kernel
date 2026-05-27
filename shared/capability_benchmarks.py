"""Executable capability benchmark primitives for RSI experiments.

The benchmark layer is intentionally small and deterministic. It gives the
closed loop concrete task families beyond schema-query repair, plus structured
evidence objects for scoring, failure residue, and synthesized operators.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class CapabilityCase:
    """One executable capability benchmark case."""

    name: str
    family: str
    operator: str
    inputs: Tuple[object, ...]
    expected: object
    split: str = "public"
    tags: Tuple[str, ...] = ()
    cost: float = 1.0


@dataclass(frozen=True)
class CapabilityEvaluation:
    """Outcome for one benchmark case."""

    case_name: str
    family: str
    operator: str
    split: str
    solved: bool
    output_repr: str
    error: str = ""
    cost: float = 1.0


@dataclass(frozen=True)
class CapabilityDelta:
    """Capability gain signal emitted by a candidate run."""

    solved_new_tasks: int
    hidden_transfer: int
    regression_protection: int
    operator_reuse: int
    compute_cost: float
    score: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FailureResidue:
    """Structured residue extracted from a rejected candidate."""

    candidate_name: str
    failed_candidate_reason: str
    missing_operator: str
    missing_abstraction: str
    failed_evaluator: str
    overfit_signal: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationPlan:
    """Executable validation plan attached to a proposal or operator."""

    name: str
    commands: Tuple[Tuple[str, ...], ...]
    expected_signals: Tuple[str, ...]

    def executable(self) -> bool:
        return bool(self.commands) and all(command for command in self.commands)


@dataclass(frozen=True)
class OperatorSynthesisSpec:
    """Reusable operator artifact proposed by the generator."""

    name: str
    kind: str
    family: str
    target_surface: str
    rationale: str
    validation_plan: ValidationPlan

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


DEFAULT_CAPABILITY_CASES: Tuple[CapabilityCase, ...] = (
    CapabilityCase(
        name="algorithm_rle_public",
        family="algorithm_synthesis",
        operator="run_length_encode",
        inputs=((1, 1, 2, 2, 2, 3),),
        expected=((1, 2), (2, 3), (3, 1)),
        tags=("sequence", "compression"),
    ),
    CapabilityCase(
        name="algorithm_rle_hidden_transfer",
        family="algorithm_synthesis",
        operator="run_length_encode",
        inputs=(("a", "a", "b", "a"),),
        expected=(("a", 2), ("b", 1), ("a", 1)),
        split="hidden",
        tags=("sequence", "type_transfer"),
    ),
    CapabilityCase(
        name="symbolic_linear_rule_public",
        family="symbolic_reasoning",
        operator="infer_linear_rule",
        inputs=((2, 5, 8, 11),),
        expected={"start": 2, "step": 3, "next": 14},
        tags=("symbolic", "sequence_rule"),
    ),
    CapabilityCase(
        name="symbolic_linear_rule_hidden_transfer",
        family="symbolic_reasoning",
        operator="infer_linear_rule",
        inputs=((-3, -1, 1),),
        expected={"start": -3, "step": 2, "next": 3},
        split="hidden",
        tags=("symbolic", "negative_numbers"),
    ),
    CapabilityCase(
        name="grid_rotate_public",
        family="grid_transformation",
        operator="rotate_grid_clockwise",
        inputs=(((1, 2, 3), (4, 5, 6)),),
        expected=((4, 1), (5, 2), (6, 3)),
        tags=("arc_like", "geometry"),
    ),
    CapabilityCase(
        name="grid_rotate_hidden_transfer",
        family="grid_transformation",
        operator="rotate_grid_clockwise",
        inputs=((("x",), ("y",), ("z",)),),
        expected=(("z", "y", "x"),),
        split="hidden",
        tags=("arc_like", "shape_transfer"),
    ),
    CapabilityCase(
        name="bug_repair_dedupe_public",
        family="bug_repair",
        operator="dedupe_preserve_order",
        inputs=(("b", "a", "b", "c", "a"),),
        expected=("b", "a", "c"),
        tags=("repair", "ordering"),
    ),
    CapabilityCase(
        name="bug_repair_dedupe_hidden_transfer",
        family="bug_repair",
        operator="dedupe_preserve_order",
        inputs=((3, 3, 2, 3, 1, 2),),
        expected=(3, 2, 1),
        split="hidden",
        tags=("repair", "type_transfer"),
    ),
    CapabilityCase(
        name="planning_transition_public",
        family="planning_state_transition",
        operator="apply_grid_action",
        inputs=({"x": 0, "y": 0}, "east"),
        expected={"x": 1, "y": 0},
        tags=("planning", "state_update"),
    ),
    CapabilityCase(
        name="planning_transition_hidden_transfer",
        family="planning_state_transition",
        operator="apply_grid_action",
        inputs=({"x": 2, "y": -1}, "north"),
        expected={"x": 2, "y": 0},
        split="hidden",
        tags=("planning", "state_update"),
    ),
)


def normalize_output(value: object) -> object:
    """Normalize lists and tuples so evaluator comparisons are stable."""

    if isinstance(value, dict):
        return {key: normalize_output(val) for key, val in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return tuple(normalize_output(item) for item in value)
    return value


def evaluate_capability_cases(
    operators: Mapping[str, Callable[..., object]],
    cases: Sequence[CapabilityCase] = DEFAULT_CAPABILITY_CASES,
) -> Tuple[CapabilityEvaluation, ...]:
    """Execute cases against an operator bank without using external services."""

    results = []
    for case in cases:
        operator = operators.get(case.operator)
        if operator is None:
            results.append(
                CapabilityEvaluation(
                    case_name=case.name,
                    family=case.family,
                    operator=case.operator,
                    split=case.split,
                    solved=False,
                    output_repr="",
                    error=f"missing operator: {case.operator}",
                    cost=case.cost,
                )
            )
            continue
        try:
            output = operator(*case.inputs)
            solved = normalize_output(output) == normalize_output(case.expected)
            results.append(
                CapabilityEvaluation(
                    case_name=case.name,
                    family=case.family,
                    operator=case.operator,
                    split=case.split,
                    solved=solved,
                    output_repr=repr(output),
                    error="" if solved else f"expected {case.expected!r}",
                    cost=case.cost,
                )
            )
        except Exception as exc:
            results.append(
                CapabilityEvaluation(
                    case_name=case.name,
                    family=case.family,
                    operator=case.operator,
                    split=case.split,
                    solved=False,
                    output_repr="",
                    error=f"{type(exc).__name__}: {exc}",
                    cost=case.cost,
                )
            )
    return tuple(results)


def capability_delta_from_evaluations(
    evaluations: Sequence[CapabilityEvaluation],
    *,
    baseline_solved: Iterable[str] = (),
    reused_operators: Iterable[str] = (),
    regression_failures: int = 0,
    compute_cost: float = 0.0,
) -> CapabilityDelta:
    """Score new solved tasks, hidden transfer, regression safety, reuse, and cost."""

    baseline = set(baseline_solved)
    solved = [item for item in evaluations if item.solved and item.case_name not in baseline]
    solved_names = {item.case_name for item in solved}
    hidden_transfer = sum(1 for item in solved if item.split == "hidden")
    regression_protection = 1 if regression_failures == 0 else 0
    operator_reuse = len(tuple(dict.fromkeys(reused_operators)))
    cost = round(float(compute_cost), 3)
    score = (
        len(solved_names)
        + hidden_transfer * 0.5
        + regression_protection * 0.25
        + operator_reuse * 0.1
        - min(cost / 600.0, 0.5)
    )
    return CapabilityDelta(
        solved_new_tasks=len(solved_names),
        hidden_transfer=hidden_transfer,
        regression_protection=regression_protection,
        operator_reuse=operator_reuse,
        compute_cost=cost,
        score=round(score, 3),
    )


def operator_validation_plan(family: str, operator: str) -> ValidationPlan:
    """Build an executable validation plan for a synthesized operator."""

    test_path = f"tests/test_capability_{family}_operator_v1.py"
    return ValidationPlan(
        name=f"validate_{operator}",
        commands=(("python", "-m", "pytest", "-q", test_path),),
        expected_signals=(
            "public_counterexample_passes",
            "hidden_transfer_case_passes",
            "no_broad_regression_gate_failure",
        ),
    )


def synthesize_operator_specs(family: str, operator: str) -> Tuple[OperatorSynthesisSpec, ...]:
    """Generate reusable solver, search, evaluator, and counterexample specs."""

    plan = operator_validation_plan(family, operator)
    target = "shared/capability_primitives.py"
    return (
        OperatorSynthesisSpec(
            name=operator,
            kind="solver_primitive",
            family=family,
            target_surface=target,
            rationale=f"Reusable primitive for {family} benchmark tasks.",
            validation_plan=plan,
        ),
        OperatorSynthesisSpec(
            name=f"prefer_{operator}_reuse",
            kind="search_heuristic",
            family=family,
            target_surface="scripts/closed_recursive_self_improvement_loop.py",
            rationale="Rank exact capability repair operators ahead of unrelated schema repairs.",
            validation_plan=plan,
        ),
        OperatorSynthesisSpec(
            name=f"{operator}_hidden_transfer_case",
            kind="evaluator_mutation",
            family=family,
            target_surface="shared/capability_benchmarks.py",
            rationale="Add a held-out case that checks transfer beyond the public example.",
            validation_plan=plan,
        ),
        OperatorSynthesisSpec(
            name=f"test_{operator}_counterexample",
            kind="counterexample_test",
            family=family,
            target_surface=f"tests/test_capability_{family}_operator_v1.py",
            rationale="Lock the primitive with public and hidden transfer counterexamples.",
            validation_plan=plan,
        ),
    )


def first_failed_gate(gates: Sequence[Mapping[str, object]]) -> Optional[Mapping[str, object]]:
    for gate in gates:
        if int(gate.get("exit_code", 0) or 0) != 0:
            return gate
    return None


def extract_failure_residue(
    candidate_name: str,
    gates: Sequence[Mapping[str, object]],
    *,
    error: str = "",
    operator_specs: Sequence[Mapping[str, object]] = (),
) -> FailureResidue:
    """Extract reusable failure residue from validation output."""

    failed = first_failed_gate(gates)
    evaluator = str(failed.get("label", "")) if failed else ""
    text = " ".join(
        str(part)
        for part in (
            error,
            failed.get("stdout_tail", "") if failed else "",
            failed.get("stderr_tail", "") if failed else "",
        )
    )
    reason = error or (f"{evaluator} failed" if evaluator else "candidate rejected")
    missing_operator = ""
    for pattern in (
        r"cannot import name '([^']+)'",
        r"NameError: name '([^']+)'",
        r"AttributeError: .*'([^']+)'",
        r"missing operator: ([A-Za-z_][A-Za-z0-9_]*)",
    ):
        match = re.search(pattern, text)
        if match:
            missing_operator = match.group(1)
            break
    if not missing_operator and operator_specs:
        missing_operator = str(operator_specs[0].get("name", ""))
    if not missing_operator:
        missing_operator = candidate_name

    focused_passed = any(
        "focused" in str(gate.get("label", "")) and int(gate.get("exit_code", 0) or 0) == 0
        for gate in gates
    )
    broad_failed = any(
        ("root_broad" in str(gate.get("label", "")) or "thdse_core" in str(gate.get("label", "")))
        and int(gate.get("exit_code", 0) or 0) != 0
        for gate in gates
    )
    if broad_failed and focused_passed:
        missing_abstraction = "regression-aware validation abstraction"
        overfit_signal = "focused_passed_broad_failed"
    elif "AssertionError" in text:
        missing_abstraction = "behavioral invariant"
        overfit_signal = "candidate_failed_counterexample"
    elif "ImportError" in text or "NameError" in text:
        missing_abstraction = "operator surface"
        overfit_signal = "missing_operator_surface"
    else:
        missing_abstraction = "undifferentiated repair abstraction"
        overfit_signal = ""

    return FailureResidue(
        candidate_name=candidate_name,
        failed_candidate_reason=reason,
        missing_operator=missing_operator,
        missing_abstraction=missing_abstraction,
        failed_evaluator=evaluator,
        overfit_signal=overfit_signal,
    )

