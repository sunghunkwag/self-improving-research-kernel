"""Capability-evaluation helpers for candidate records and gates."""

from __future__ import annotations

import ast
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, Sequence, Tuple

from shared.capability_benchmarks import (
    CAPABILITY_FAMILIES,
    CapabilityDelta,
    CapabilityEvaluation,
    capability_delta_from_evaluations,
    extract_failure_residue,
    synthesize_operator_specs,
)
from scripts.closed_rsi.gates.results import GateResult, candidate_compute_cost, is_full_test_gate
from scripts.closed_rsi.records import CandidatePatch, source_sha256


def operator_specs_for(family: str, operator: str) -> Tuple[Dict[str, object], ...]:
    """Return JSON-compatible operator synthesis specs for a candidate."""

    return tuple(spec.to_dict() for spec in synthesize_operator_specs(family, operator))

def candidate_capability_delta(
    candidate: CandidatePatch,
    *,
    accepted: bool,
    gates: Sequence[GateResult],
    evaluations: Sequence[CapabilityEvaluation] = (),
) -> Dict[str, object]:
    """Score the capability delta represented by a candidate result."""

    if not candidate.capability_family and not candidate.operator_specs:
        return {}
    regression_failures = sum(
        1
        for gate in gates
        if gate.exit_code != 0
        and (
            "root_broad" in gate.label
            or "thdse_full" in gate.label
            or is_full_test_gate(gate)
        )
    )
    operator_reuse = len(
        {
            str(spec.get("name", ""))
            for spec in candidate.operator_specs
            if spec.get("kind") in {"solver_primitive", "search_heuristic"}
        }
    )
    if evaluations:
        return capability_delta_from_evaluations(
            evaluations,
            reused_operators=(
                str(spec.get("name", ""))
                for spec in candidate.operator_specs
                if spec.get("kind") in {"solver_primitive", "search_heuristic"}
            ),
            regression_failures=regression_failures,
            compute_cost=candidate_compute_cost(gates),
        ).to_dict()

    delta = CapabilityDelta(
        solved_new_tasks=0,
        hidden_transfer=0,
        regression_protection=1 if gates and regression_failures == 0 else 0,
        operator_reuse=operator_reuse,
        compute_cost=candidate_compute_cost(gates),
        score=round(
            (0.25 if gates and regression_failures == 0 else 0.0)
            + operator_reuse * 0.1
            - min(candidate_compute_cost(gates) / 600.0, 0.5),
            3,
        ),
    )
    return delta.to_dict()


def candidate_failure_residue(
    candidate: CandidatePatch,
    *,
    accepted: bool,
    gates: Sequence[GateResult],
    error: str,
) -> Dict[str, object]:
    """Return structured failure residue for rejected candidates."""

    if accepted:
        return {}
    residue = extract_failure_residue(
        candidate.name,
        [asdict(gate) for gate in gates],
        error=error,
        operator_specs=candidate.operator_specs,
    )
    return residue.to_dict()


def capability_operator_names(candidate: CandidatePatch) -> Tuple[str, ...]:
    """Return solver primitive names synthesized by a capability candidate."""

    names = [
        str(spec.get("name", ""))
        for spec in candidate.operator_specs
        if spec.get("kind") == "solver_primitive" and spec.get("name")
    ]
    if not names and candidate.capability_family in CAPABILITY_FAMILIES:
        names = [candidate.goal.name.removeprefix("repair_").removesuffix("_operator")]
    return tuple(dict.fromkeys(names))


def load_capability_operators(source_path: Path, operator_names: Sequence[str]) -> Dict[str, Callable[..., object]]:
    """Load candidate-local primitive callables for evaluator execution."""

    if not source_path.exists() or not operator_names:
        return {}
    namespace: Dict[str, object] = {
        "__builtins__": __builtins__,
        "__name__": "_closed_rsi_capability_candidate",
    }
    source = source_path.read_text(encoding="utf-8")
    exec(compile(source, str(source_path), "exec"), namespace)
    return {
        name: namespace[name]
        for name in operator_names
        if callable(namespace.get(name))
    }


def top_level_function_source(text: str, function_name: str) -> str:
    """Return source for one top-level function, or an empty string."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""
    lines = text.splitlines()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            end_lineno = getattr(node, "end_lineno", None)
            if end_lineno is None:
                return ""
            return "\n".join(lines[node.lineno - 1 : end_lineno]).rstrip() + "\n"
    return ""
