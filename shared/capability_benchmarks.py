"""Executable capability benchmark primitives for RSI experiments.

The benchmark layer is intentionally small and deterministic. It gives the
closed loop concrete task families beyond schema-query repair, plus structured
evidence objects for scoring, failure residue, and synthesized operators.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


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
    failed_gate: str = ""
    next_hypothesis: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SelfProposedCapabilityDimension:
    """Capability family inferred from accumulated rejected-candidate residue."""

    family: str
    operator: str
    source_signature: str
    residue_count: int
    trigger_terms: Tuple[str, ...]
    rationale: str
    difficulty: int = 1
    hidden_case_count: int = 1

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AntiCheatFinding:
    """One deterministic anti-gaming finding for a candidate patch."""

    kind: str
    path: str
    detail: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SelfAuthoredTaskFinding:
    """One reason a self-authored curriculum task is degenerate."""

    kind: str
    detail: str

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


CAPABILITY_FAMILIES: Tuple[str, ...] = (
    "algorithm_synthesis",
    "symbolic_reasoning",
    "grid_transformation",
    "bug_repair",
    "planning_state_transition",
)


def _seed_digest(seed: str, label: str) -> bytes:
    payload = f"{seed}:{label}".encode("utf-8")
    return hashlib.sha256(payload).digest()


def _seed_int(seed: str, label: str, modulo: int, *, offset: int = 0) -> int:
    if modulo <= 0:
        raise ValueError("modulo must be positive")
    value = int.from_bytes(_seed_digest(seed, label)[:8], "big")
    return offset + (value % modulo)


def _run_length_expected(items: Sequence[object]) -> Tuple[Tuple[object, int], ...]:
    result: List[Tuple[object, int]] = []
    marker = object()
    current: object = marker
    count = 0
    for item in items:
        if count == 0:
            current = item
            count = 1
        elif item == current:
            count += 1
        else:
            result.append((current, count))
            current = item
            count = 1
    if count:
        result.append((current, count))
    return tuple(result)


def _rotate_clockwise_expected(grid: Sequence[Sequence[object]]) -> Tuple[Tuple[object, ...], ...]:
    rows = tuple(tuple(row) for row in grid)
    if not rows:
        return ()
    return tuple(
        tuple(rows[row][column] for row in range(len(rows) - 1, -1, -1))
        for column in range(len(rows[0]))
    )


def _dedupe_expected(items: Sequence[object]) -> Tuple[object, ...]:
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)


_RESIDUE_STOP_WORDS = {
    "and",
    "before",
    "candidate",
    "failed",
    "failure",
    "gate",
    "implement",
    "missing",
    "one",
    "operator",
    "or",
    "repair",
    "rerunning",
    "the",
    "with",
}


def _residue_mapping(residue: object) -> Dict[str, object]:
    if isinstance(residue, FailureResidue):
        return residue.to_dict()
    if isinstance(residue, Mapping):
        return dict(residue)
    return {}


def _residue_text(residue: Mapping[str, object]) -> str:
    fields = (
        "failed_candidate_reason",
        "missing_operator",
        "missing_abstraction",
        "failed_evaluator",
        "overfit_signal",
        "failed_gate",
        "next_hypothesis",
    )
    return " ".join(str(residue.get(field, "") or "") for field in fields)


def _residue_terms(residues: Sequence[Mapping[str, object]]) -> Tuple[str, ...]:
    counts: Counter[str] = Counter()
    for residue in residues:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]+", _residue_text(residue).lower()):
            token = token.strip("_")
            if len(token) < 4 or token in _RESIDUE_STOP_WORDS:
                continue
            counts[token] += 1
    return tuple(token for token, _count in counts.most_common(5))


def _slug_terms(terms: Sequence[str], fallback: str) -> Tuple[str, ...]:
    selected = [
        re.sub(r"[^a-z0-9_]+", "_", term.lower()).strip("_")[:24]
        for term in terms
        if term
    ]
    selected = [term for term in selected if term]
    if not selected:
        selected = [fallback]
    return tuple(dict.fromkeys(selected))[:3]


def _dimension_group_key(residue: Mapping[str, object]) -> str:
    return str(
        residue.get("missing_abstraction")
        or residue.get("overfit_signal")
        or residue.get("failed_gate")
        or residue.get("failed_candidate_reason")
        or "undifferentiated residue"
    )


def propose_capability_dimensions_from_residue(
    failure_residue_history: Sequence[object],
    *,
    seed: str = "self_proposed_capability_dimension_v1",
    max_dimensions: int = 3,
    mastered_capability_count: int = 0,
) -> Tuple[SelfProposedCapabilityDimension, ...]:
    """Infer new capability dimensions from accumulated failure residue.

    The family names and operators are derived from residue text and a seed. The
    function does not inspect benchmark expected outputs or quarantined fixes.
    """

    groups: Dict[str, List[Dict[str, object]]] = {}
    for item in failure_residue_history:
        residue = _residue_mapping(item)
        if not residue:
            continue
        if not _residue_text(residue).strip():
            continue
        groups.setdefault(_dimension_group_key(residue), []).append(residue)

    dimensions: List[SelfProposedCapabilityDimension] = []
    for group_key, residues in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        terms = _residue_terms(residues)
        fallback = hashlib.sha256(f"{seed}:{group_key}".encode("utf-8")).hexdigest()[:8]
        slug = "_".join(_slug_terms(terms, fallback))
        family = f"residue_{slug}"
        if family in CAPABILITY_FAMILIES:
            family = f"residue_invented_{slug}"
        operator = f"classify_{family}_pressure"
        signature = hashlib.sha256(
            f"{seed}:{group_key}:{tuple(sorted(_residue_text(item) for item in residues))}".encode("utf-8")
        ).hexdigest()[:16]
        difficulty = max(1, min(6, 1 + int(mastered_capability_count) + min(2, len(residues) // 2)))
        dimensions.append(
            SelfProposedCapabilityDimension(
                family=family,
                operator=operator,
                source_signature=signature,
                residue_count=len(residues),
                trigger_terms=terms[:5] or (fallback,),
                rationale=(
                    "Derived from repeated FailureResidue signals rather than a fixed "
                    "benchmark family list."
                ),
                difficulty=difficulty,
                hidden_case_count=max(1, difficulty),
            )
        )
        if len(dimensions) >= max_dimensions:
            break
    return tuple(dimensions)


def _self_proposed_expected(payload: Mapping[str, object]) -> Dict[str, object]:
    signals = tuple(str(signal) for signal in payload.get("signals", ()) if str(signal))
    counts = Counter(signals)
    dominant = ""
    if counts:
        dominant = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    difficulty = int(payload.get("difficulty", 1) or 1)
    return {
        "family": str(payload.get("family", "")),
        "dominant_signal": dominant,
        "pressure": int(payload.get("residue_count", 0) or 0) + int(payload.get("seed_pressure", 0) or 0),
        "difficulty": difficulty,
        "evidence_width": len(set(signals)),
    }


def self_proposed_dynamic_cases(
    seed: str,
    failure_residue_history: Sequence[object],
    *,
    mastered_capability_count: int = 0,
) -> Tuple[CapabilityCase, ...]:
    """Emit seed-derived hidden cases for residue-proposed capability families."""

    cases: List[CapabilityCase] = []
    for dimension in propose_capability_dimensions_from_residue(
        failure_residue_history,
        seed=seed,
        mastered_capability_count=mastered_capability_count,
    ):
        digest_prefix = hashlib.sha256(f"{seed}:{dimension.source_signature}".encode("utf-8")).hexdigest()[:10]
        for case_index in range(dimension.hidden_case_count):
            seed_pressure = _seed_int(seed, f"{dimension.family}:pressure:{case_index}", 5, offset=1)
            seed_term = f"seed_{_seed_int(seed, f'{dimension.family}:{case_index}', 997, offset=1)}"
            trigger = dimension.trigger_terms[case_index % len(dimension.trigger_terms)]
            signals = (*dimension.trigger_terms, seed_term, trigger)
            payload = {
                "family": dimension.family,
                "signals": signals,
                "residue_count": dimension.residue_count,
                "seed_pressure": seed_pressure,
                "hidden": True,
                "difficulty": dimension.difficulty,
                "case_index": case_index,
            }
            cases.append(
                CapabilityCase(
                    name=f"{dimension.family}_dynamic_hidden_{digest_prefix}_{case_index + 1}",
                    family=dimension.family,
                    operator=dimension.operator,
                    inputs=(payload,),
                    expected=_self_proposed_expected(payload),
                    split="hidden",
                    tags=("dynamic", "seeded", "failure_residue", "self_proposed", f"difficulty_{dimension.difficulty}"),
                    cost=1.5 + (0.1 * max(0, dimension.difficulty - 1)),
                )
            )
    return tuple(cases)


self_proposed_dynamic_hidden_cases = self_proposed_dynamic_cases


def dynamic_hidden_cases(
    seed: str,
    families: Sequence[str] = CAPABILITY_FAMILIES,
) -> Tuple[CapabilityCase, ...]:
    """Return deterministic seed-derived hidden cases for each capability family."""

    family_set = set(families)
    digest_prefix = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:10]
    cases: List[CapabilityCase] = []

    if "algorithm_synthesis" in family_set:
        base = _seed_int(seed, "algorithm_base", 13, offset=3)
        items = (
            f"tok_{base}",
            f"tok_{base}",
            f"tok_{base + 1}",
            f"tok_{base + 1}",
            f"tok_{base + 1}",
            f"tok_{base + 2}",
            f"tok_{base}",
        )
        cases.append(
            CapabilityCase(
                name=f"algorithm_rle_dynamic_hidden_{digest_prefix}",
                family="algorithm_synthesis",
                operator="run_length_encode",
                inputs=(items,),
                expected=_run_length_expected(items),
                split="hidden",
                tags=("dynamic", "seeded", "sequence"),
                cost=1.25,
            )
        )

    if "symbolic_reasoning" in family_set:
        start = _seed_int(seed, "symbolic_start", 41, offset=-20)
        step = _seed_int(seed, "symbolic_step", 9, offset=1)
        if _seed_int(seed, "symbolic_sign", 2) == 1:
            step *= -1
        length = _seed_int(seed, "symbolic_length", 3, offset=4)
        values = tuple(start + step * index for index in range(length))
        cases.append(
            CapabilityCase(
                name=f"symbolic_linear_rule_dynamic_hidden_{digest_prefix}",
                family="symbolic_reasoning",
                operator="infer_linear_rule",
                inputs=(values,),
                expected={"start": start, "step": step, "next": values[-1] + step},
                split="hidden",
                tags=("dynamic", "seeded", "sequence_rule"),
                cost=1.25,
            )
        )

    if "grid_transformation" in family_set:
        height = _seed_int(seed, "grid_height", 3, offset=2)
        width = _seed_int(seed, "grid_width", 3, offset=2)
        base = _seed_int(seed, "grid_base", 50, offset=10)
        grid = tuple(
            tuple(base + row * width + column for column in range(width))
            for row in range(height)
        )
        cases.append(
            CapabilityCase(
                name=f"grid_rotate_dynamic_hidden_{digest_prefix}",
                family="grid_transformation",
                operator="rotate_grid_clockwise",
                inputs=(grid,),
                expected=_rotate_clockwise_expected(grid),
                split="hidden",
                tags=("dynamic", "seeded", "arc_like"),
                cost=1.25,
            )
        )

    if "bug_repair" in family_set:
        base = _seed_int(seed, "dedupe_base", 17, offset=5)
        items = (
            base,
            base + 1,
            base,
            base + 2,
            base + 1,
            base + 3,
            base + 2,
        )
        cases.append(
            CapabilityCase(
                name=f"bug_repair_dedupe_dynamic_hidden_{digest_prefix}",
                family="bug_repair",
                operator="dedupe_preserve_order",
                inputs=(items,),
                expected=_dedupe_expected(items),
                split="hidden",
                tags=("dynamic", "seeded", "ordering"),
                cost=1.25,
            )
        )

    if "planning_state_transition" in family_set:
        actions = ("north", "south", "east", "west", "stay")
        action = actions[_seed_int(seed, "planning_action", len(actions))]
        x = _seed_int(seed, "planning_x", 21, offset=-10)
        y = _seed_int(seed, "planning_y", 21, offset=-10)
        deltas = {
            "north": (0, 1),
            "south": (0, -1),
            "east": (1, 0),
            "west": (-1, 0),
            "stay": (0, 0),
        }
        dx, dy = deltas[action]
        cases.append(
            CapabilityCase(
                name=f"planning_transition_dynamic_hidden_{digest_prefix}",
                family="planning_state_transition",
                operator="apply_grid_action",
                inputs=({"x": x, "y": y}, action),
                expected={"x": x + dx, "y": y + dy},
                split="hidden",
                tags=("dynamic", "seeded", "state_update"),
                cost=1.25,
            )
        )

    return tuple(cases)


def capability_cases_for_seed(
    seed: str,
    *,
    include_static: bool = True,
    failure_residue_history: Sequence[object] = (),
    mastered_capability_count: int = 0,
) -> Tuple[CapabilityCase, ...]:
    """Return static benchmark cases plus deterministic dynamic hidden cases."""

    dynamic = dynamic_hidden_cases(seed)
    self_proposed = self_proposed_dynamic_cases(
        seed,
        failure_residue_history,
        mastered_capability_count=mastered_capability_count,
    )
    if include_static:
        return (*DEFAULT_CAPABILITY_CASES, *dynamic, *self_proposed)
    return (*dynamic, *self_proposed)


def normalize_output(value: object) -> object:
    """Normalize lists and tuples so evaluator comparisons are stable."""

    if isinstance(value, dict):
        return {key: normalize_output(val) for key, val in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return tuple(normalize_output(item) for item in value)
    return value


def detect_degenerate_self_authored_task(
    cases: Sequence[CapabilityCase],
) -> Tuple[SelfAuthoredTaskFinding, ...]:
    """Reject self-authored tasks that lack hidden transfer or need only no-op behavior."""

    findings: List[SelfAuthoredTaskFinding] = []
    if not cases:
        findings.append(
            SelfAuthoredTaskFinding(
                kind="no_cases",
                detail="self-authored task generated no executable cases",
            )
        )
        return tuple(findings)
    hidden = [case for case in cases if case.split == "hidden"]
    if not hidden:
        findings.append(
            SelfAuthoredTaskFinding(
                kind="no_hidden_transfer",
                detail="self-authored task has no hidden transfer cases",
            )
        )
    no_op_cases = [
        case.name
        for case in cases
        if case.inputs and normalize_output(case.inputs[0]) == normalize_output(case.expected)
    ]
    if no_op_cases and len(no_op_cases) == len(cases):
        findings.append(
            SelfAuthoredTaskFinding(
                kind="noop_solvable",
                detail="every self-authored case is solvable by returning the first input unchanged",
            )
        )
    return tuple(findings)


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


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return normalized.startswith("tests/") or "/tests/" in normalized


def _is_doc_report_or_metadata_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    name = normalized.rsplit("/", 1)[-1]
    return (
        normalized.startswith("reports/")
        or normalized.startswith("docs/")
        or name.startswith("readme")
        or normalized.endswith(".md")
        or normalized.endswith("_metadata.json")
        or normalized.endswith("metadata.json")
        or normalized.endswith("summary.json")
    )


def _introduced_text(before: Optional[str], after: str) -> str:
    if before is None:
        return after
    before_lines = set(before.splitlines())
    return "\n".join(line for line in after.splitlines() if line not in before_lines)


def _normalized_repr(value: object) -> str:
    return repr(normalize_output(value))


def _case_literal_sets(cases: Sequence[CapabilityCase]) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    input_literals = []
    output_literals = []
    for case in cases:
        input_literals.append(_normalized_repr(case.inputs))
        input_literals.extend(_normalized_repr(item) for item in case.inputs)
        output_literals.append(_normalized_repr(case.expected))
    return tuple(dict.fromkeys(input_literals)), tuple(dict.fromkeys(output_literals))


def _literal_branch_findings(
    path: str,
    text: str,
    cases: Sequence[CapabilityCase],
) -> Tuple[AntiCheatFinding, ...]:
    case_literals = {
        _normalized_repr(case.inputs)
        for case in cases
    } | {
        _normalized_repr(item)
        for case in cases
        for item in case.inputs
    }
    findings: List[AntiCheatFinding] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ()

    class ExactBranchVisitor(ast.NodeVisitor):
        def visit_Compare(self, node: ast.Compare) -> None:  # noqa: N802 - ast API name
            values = [node.left, *node.comparators]
            for value_node in values:
                try:
                    literal = ast.literal_eval(value_node)
                except Exception:
                    continue
                if _normalized_repr(literal) in case_literals:
                    findings.append(
                        AntiCheatFinding(
                            kind="exact_input_branching",
                            path=path,
                            detail="candidate branches on an exact public or hidden benchmark input",
                        )
                    )
                    break
            self.generic_visit(node)

    ExactBranchVisitor().visit(tree)
    return tuple(findings[:1])


def detect_anti_cheat_findings(
    changed_files: Mapping[str, Tuple[Optional[str], Optional[str]]],
    *,
    cases: Sequence[CapabilityCase] = (),
) -> Tuple[AntiCheatFinding, ...]:
    """Detect deterministic benchmark and validation bypass attempts."""

    active_cases = tuple(cases) if cases else capability_cases_for_seed("anti_cheat_default")
    input_literals, output_literals = _case_literal_sets(active_cases)
    material_paths = [
        path
        for path, (before, after) in changed_files.items()
        if before != after
    ]
    protected_paths = []
    findings: List[AntiCheatFinding] = []

    for path in material_paths:
        normalized_path = path.replace("\\", "/").lower()
        normalized_name = normalized_path.rsplit("/", 1)[-1]
        if (
            normalized_path.startswith("reports/")
            or normalized_name in {
                "aggregate_metrics.csv",
                "baseline_comparison.csv",
                "evidence_scorecard.json",
                "metrics.csv",
                "seed_registry.json",
            }
            or "seed_registry" in normalized_name
            or normalized_path in {
                "scripts/rsi_experiment_suite.py",
                "scripts/external_world_grounding.py",
                "scripts/external_code_sandbox_fixtures.py",
                "shared/capability_benchmarks.py",
            }
        ):
            protected_paths.append(path)
    if protected_paths:
        findings.append(
            AntiCheatFinding(
                kind="protected_evaluator_or_report_mutation",
                path=",".join(sorted(protected_paths)),
                detail="candidate patches may not mutate reports, metric writers, seed registries, evaluator code, or fixture builders",
            )
        )

    if material_paths and all(_is_doc_report_or_metadata_path(path) for path in material_paths):
        findings.append(
            AntiCheatFinding(
                kind="readme_report_or_metadata_only",
                path=",".join(sorted(material_paths)),
                detail="candidate changes only documentation, reports, or metadata",
            )
        )

    executable_paths = [
        path
        for path in material_paths
        if path.endswith(".py") and not _is_test_path(path)
    ]
    if not executable_paths and material_paths:
        fake_success_paths = [
            path
            for path, (_before, after) in changed_files.items()
            if after and re.search(r'"?(accepted|success|capability_delta)"?\s*[:=]\s*(true|True|\{)', after)
        ]
        if fake_success_paths:
            findings.append(
                AntiCheatFinding(
                    kind="fake_success_metadata_without_behavior",
                    path=",".join(sorted(fake_success_paths)),
                    detail="success metadata changed without executable Python behavior",
                )
            )

    for path, (before, after) in changed_files.items():
        if after is None:
            if _is_test_path(path):
                findings.append(
                    AntiCheatFinding(
                        kind="test_deletion",
                        path=path,
                        detail="candidate deletes a test file",
                    )
                )
            continue

        introduced = _introduced_text(before, after)
        normalized_path = path.replace("\\", "/").lower()

        if _is_test_path(path):
            if re.search(r"pytest\.(skip|xfail)|@pytest\.mark\.(skip|xfail)", after):
                findings.append(
                    AntiCheatFinding(
                        kind="pytest_skip_xfail_bypass",
                        path=path,
                        detail="candidate bypasses tests with pytest skip or xfail",
                    )
                )
            if re.search(r"assert\s+True\b", after):
                findings.append(
                    AntiCheatFinding(
                        kind="test_weakening",
                        path=path,
                        detail="candidate weakens a test to assert True",
                    )
                )
            if before is not None and before.count("assert") > after.count("assert"):
                findings.append(
                    AntiCheatFinding(
                        kind="test_weakening",
                        path=path,
                        detail="candidate removes assertions from an existing test",
                    )
                )

        if normalized_path == "shared/capability_benchmarks.py" and before is not None:
            weakening_signals = (
                ("evaluate_capability_cases" in before and "evaluate_capability_cases" not in after),
                ("capability_delta_from_evaluations" in before and "capability_delta_from_evaluations" not in after),
                ("dynamic_hidden_cases" in before and "dynamic_hidden_cases" not in after),
                (before.count("case.expected") > after.count("case.expected")),
                bool(re.search(r"solved\s*=\s*True|solved=True", introduced)),
            )
            if any(weakening_signals):
                findings.append(
                    AntiCheatFinding(
                        kind="evaluator_weakening",
                        path=path,
                        detail="candidate weakens capability evaluator behavior",
                    )
                )

        if normalized_path in {
            "scripts/closed_recursive_self_improvement_loop.py",
            "scripts/rsi_experiment_suite.py",
        } and before is not None:
            broad_removed = (
                "root_broad" in before and "root_broad" not in after
            ) or (
                "if self.broad_gate" in before and "if self.broad_gate" not in after
            ) or (
                "--broad-gate" in before and "--broad-gate" not in after
            ) or (
                "full_pytest" in before and "full_pytest" not in after
            ) or (
                "full_test_required" in before and "full_test_required" not in after
            )
            if broad_removed or re.search(r"BYPASS|SKIP|DISABLE", introduced, flags=re.IGNORECASE) and "gate" in introduced.lower():
                findings.append(
                    AntiCheatFinding(
                        kind="broad_gate_bypass",
                        path=path,
                        detail="candidate removes or bypasses broad validation gates",
                    )
                )

        if re.search(r"os\.(environ|getenv)", introduced) and re.search(
            r"BYPASS|SKIP|DISABLE|ALLOW|ACCEPT|SUCCESS",
            introduced,
            flags=re.IGNORECASE,
        ):
            findings.append(
                AntiCheatFinding(
                    kind="environment_variable_bypass",
                    path=path,
                    detail="candidate introduces an environment-variable validation bypass",
                )
            )

        if path.endswith(".py") and not _is_test_path(path):
            scan_text = introduced if before is not None else after
            has_input_literal = any(literal and literal in scan_text for literal in input_literals)
            has_output_literal = any(literal and literal in scan_text for literal in output_literals)
            if has_input_literal and has_output_literal:
                findings.append(
                    AntiCheatFinding(
                        kind="hardcoded_benchmark_literals",
                        path=path,
                        detail="candidate embeds exact benchmark input-output literals in executable code",
                    )
                )
            findings.extend(_literal_branch_findings(path, scan_text, active_cases))

    deduped: List[AntiCheatFinding] = []
    seen = set()
    for finding in findings:
        key = (finding.kind, finding.path, finding.detail)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return tuple(deduped)


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
    failed_gate = evaluator
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
        (
            "root_broad" in str(gate.get("label", ""))
            or "thdse_full" in str(gate.get("label", ""))
            or "full_pytest" in str(gate.get("label", ""))
        )
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

    if "anti-cheat" in evaluator or "anti-cheat" in text.lower():
        next_hypothesis = "replace shortcut metadata or literals with executable evaluator-passing behavior"
    elif broad_failed and focused_passed:
        next_hypothesis = "generalize the repair beyond focused tests and rerun broad validation"
    elif missing_operator:
        next_hypothesis = f"implement or expose {missing_operator} before rerunning the failed evaluator"
    elif "AssertionError" in text:
        next_hypothesis = "derive a more general invariant from the counterexample"
    else:
        next_hypothesis = "collect a specific failing gate and synthesize a targeted follow-up candidate"

    return FailureResidue(
        candidate_name=candidate_name,
        failed_candidate_reason=reason,
        missing_operator=missing_operator,
        missing_abstraction=missing_abstraction,
        failed_evaluator=evaluator,
        overfit_signal=overfit_signal,
        failed_gate=failed_gate,
        next_hypothesis=next_hypothesis,
    )

