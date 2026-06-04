"""Self-invented proxy objectives for open-ended candidate selection."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from scripts.closed_rsi.generators.behavior_archive import BehaviorArchive
from scripts.closed_rsi.generators.immutable_guard import (
    BoundaryFinding,
    candidate_immutable_boundary_findings,
    proxy_immutable_boundary_findings,
)
from scripts.closed_rsi.generators.self_play import SelfPlayResult, SelfPlayTask
from scripts.closed_rsi.records import CandidatePatch


ALLOWED_PROXY_FEATURES = frozenset(
    {
        "novelty",
        "self_play_wins",
        "weakness_exposure",
        "archive_sparsity",
        "population_fit",
        "complexity_penalty",
        "rejection_pressure",
        "self_reported_proxy_score",
    }
)

ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.UAdd,
    ast.USub,
)


@dataclass(frozen=True)
class ProxyObjective:
    """A guarded mutable scoring expression invented by the loop."""

    proxy_id: str
    generation: int
    expression: str
    description: str
    source: str

    def to_dict(self) -> dict:
        return asdict(self)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _weight(seed: str, generation: int, salt: str, *, low: float = 0.05, high: float = 1.0) -> float:
    span = high - low
    raw = int(_digest(f"{seed}:{generation}:{salt}")[:8], 16) / 0xFFFFFFFF
    return round(low + span * raw, 2)


def validate_proxy_expression(proxy: ProxyObjective) -> Tuple[BoundaryFinding, ...]:
    """Validate a proxy expression without executing it."""

    findings = list(
        proxy_immutable_boundary_findings(
            proxy_id=proxy.proxy_id,
            expression=proxy.expression,
            description=proxy.description,
        )
    )
    try:
        tree = ast.parse(proxy.expression, mode="eval")
    except SyntaxError as exc:
        findings.append(
            BoundaryFinding(
                source=f"{proxy.proxy_id}.expression",
                pattern="syntax_error",
                reason=f"invalid proxy expression: {exc.msg}",
            )
        )
        return tuple(findings)

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            findings.append(
                BoundaryFinding(
                    source=f"{proxy.proxy_id}.expression",
                    pattern=type(node).__name__,
                    reason="disallowed proxy expression syntax",
                )
            )
            continue
        if isinstance(node, ast.Name) and node.id not in ALLOWED_PROXY_FEATURES:
            findings.append(
                BoundaryFinding(
                    source=f"{proxy.proxy_id}.expression",
                    pattern=node.id,
                    reason="disallowed proxy feature",
                )
            )
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            findings.append(
                BoundaryFinding(
                    source=f"{proxy.proxy_id}.expression",
                    pattern=repr(node.value),
                    reason="non-numeric proxy constant",
                )
            )
    return tuple(findings)


def invent_proxy_objectives(
    *,
    generation: int,
    state: object,
    archive: BehaviorArchive,
    tasks: Sequence[SelfPlayTask],
    seed: str,
    max_proxies: int = 3,
) -> Tuple[ProxyObjective, ...]:
    """Invent guarded proxy objectives from archive and self-play structure."""

    state_size = 0
    if isinstance(state, Mapping):
        state_size = sum(
            len(state.get(bucket, []))
            for bucket in ("accepted", "rejected", "quarantine_exploration")
            if isinstance(state.get(bucket, []), list)
        )
    proxies = []
    for index in range(max(1, max_proxies)):
        proxy_seed = f"{seed}:{generation}:{index}:{len(archive.signatures)}:{len(tasks)}:{state_size}"
        weights = {
            "novelty": _weight(proxy_seed, generation, "novelty"),
            "self_play_wins": _weight(proxy_seed, generation, "self_play_wins"),
            "weakness_exposure": _weight(proxy_seed, generation, "weakness_exposure", low=0.1, high=0.6),
            "archive_sparsity": _weight(proxy_seed, generation, "archive_sparsity", low=0.05, high=0.4),
            "population_fit": _weight(proxy_seed, generation, "population_fit", low=0.05, high=0.7),
            "complexity_penalty": _weight(proxy_seed, generation, "complexity_penalty", low=0.05, high=0.35),
            "rejection_pressure": _weight(proxy_seed, generation, "rejection_pressure", low=0.05, high=0.45),
        }
        expression = (
            f"{weights['novelty']} * novelty + "
            f"{weights['self_play_wins']} * self_play_wins + "
            f"{weights['weakness_exposure']} * weakness_exposure + "
            f"{weights['archive_sparsity']} * archive_sparsity + "
            f"{weights['population_fit']} * population_fit - "
            f"{weights['complexity_penalty']} * complexity_penalty - "
            f"{weights['rejection_pressure']} * rejection_pressure"
        )
        proxy_id = f"proxy_gen_{generation}_{index}_{_digest(proxy_seed)[:10]}"
        proxy = ProxyObjective(
            proxy_id=proxy_id,
            generation=generation,
            expression=expression,
            description=(
                "Invented structural proxy over novelty, self-play wins, weakness exposure, "
                "archive sparsity, population fit, complexity, and rejection pressure. "
                f"weights={weights}"
            ),
            source=f"score = {expression}",
        )
        if not validate_proxy_expression(proxy):
            proxies.append(proxy)
    return tuple(proxies)


def proxy_candidate_features(
    candidate: CandidatePatch,
    *,
    archive: BehaviorArchive,
    tasks: Sequence[SelfPlayTask],
    self_play_result: SelfPlayResult | None,
    state: object,
    population_size: int,
) -> Dict[str, float]:
    """Build proxy features without evaluator or gate access."""

    rejected_names = set()
    family_counts: Dict[str, int] = {}
    if isinstance(state, Mapping):
        for record in state.get("rejected", []):
            if isinstance(record, Mapping):
                rejected_names.add(str(record.get("name", "")))
        for bucket in ("accepted", "rejected"):
            for record in state.get(bucket, []):
                if not isinstance(record, Mapping):
                    continue
                delta = record.get("capability_delta", {})
                family = str(delta.get("family", "")) if isinstance(delta, Mapping) else ""
                if family:
                    family_counts[family] = family_counts.get(family, 0) + 1
    self_play_wins = 0.0
    weakness_exposure = 0.0
    if self_play_result is not None:
        self_play_wins = self_play_result.wins / max(self_play_result.wins + self_play_result.losses, 1)
        weakness_exposure = self_play_result.weakness_exposure
    complexity_penalty = min((len(candidate.test_source) + len(candidate.operator_specs) * 100) / 5000.0, 1.0)
    population_fit = 0.0
    if candidate.capability_family and family_counts:
        population_fit = family_counts.get(candidate.capability_family, 0) / max(sum(family_counts.values()), 1)
    elif population_size:
        population_fit = 1.0 / population_size
    self_reported_proxy_score = 0.0
    try:
        self_reported_proxy_score = float(candidate.generator_improvement.get("proxy_score", 0.0) or 0.0)
    except Exception:
        self_reported_proxy_score = 0.0
    return {
        "novelty": archive.novelty_distance(candidate, tasks),
        "self_play_wins": round(self_play_wins, 3),
        "weakness_exposure": round(weakness_exposure, 3),
        "archive_sparsity": round(1.0 / (1.0 + len(archive.signatures)), 3),
        "population_fit": round(population_fit, 3),
        "complexity_penalty": round(complexity_penalty, 3),
        "rejection_pressure": 1.0 if candidate.name in rejected_names else 0.0,
        "self_reported_proxy_score": round(self_reported_proxy_score, 3),
    }


def score_proxy_expression(proxy: ProxyObjective, features: Mapping[str, float]) -> float:
    """Evaluate a previously guarded proxy expression."""

    findings = validate_proxy_expression(proxy)
    if findings:
        raise ValueError(f"proxy failed immutable guard: {[finding.to_dict() for finding in findings]}")
    tree = ast.parse(proxy.expression, mode="eval")
    values = {name: float(features.get(name, 0.0) or 0.0) for name in ALLOWED_PROXY_FEATURES}
    score = eval(compile(tree, f"<{proxy.proxy_id}>", "eval"), {"__builtins__": {}}, values)
    return round(float(score), 6)


def rank_candidates_under_proxy(
    candidates: Sequence[CandidatePatch],
    *,
    proxy: ProxyObjective,
    archive: BehaviorArchive,
    tasks: Sequence[SelfPlayTask],
    self_play_results: Mapping[str, SelfPlayResult],
    state: object,
    repo_root,
) -> Tuple[Tuple[CandidatePatch, ...], Tuple[dict, ...]]:
    """Rank candidates by invented proxy score while surfacing guard rejections."""

    base_order = {candidate.name: index for index, candidate in enumerate(candidates)}
    score_rows = []
    for candidate in candidates:
        guard_findings = candidate_immutable_boundary_findings(candidate, repo_root=repo_root)
        features = proxy_candidate_features(
            candidate,
            archive=archive,
            tasks=tasks,
            self_play_result=self_play_results.get(candidate.name),
            state=state,
            population_size=len(candidates),
        )
        score = -1_000_000.0
        if not guard_findings:
            score = score_proxy_expression(proxy, features)
        score_rows.append(
            {
                "candidate": candidate.name,
                "proxy_id": proxy.proxy_id,
                "proxy_score": score,
                "features": features,
                "immutable_boundary_findings": [finding.to_dict() for finding in guard_findings],
            }
        )
    score_by_name = {row["candidate"]: float(row["proxy_score"]) for row in score_rows}
    guarded = {
        row["candidate"]
        for row in score_rows
        if row.get("immutable_boundary_findings")
    }
    ranked = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.name in guarded,
                -score_by_name.get(candidate.name, -1_000_000.0),
                base_order.get(candidate.name, 999999),
                candidate.name,
            ),
        )
    )
    return ranked, tuple(score_rows)


def proxy_unseen_seed_labels(proxy: ProxyObjective, candidate_name: str) -> Tuple[str, str]:
    """Return two deterministic held-out seed labels unused by proxy scoring."""

    digest = _digest(f"{proxy.proxy_id}:{candidate_name}:delayed-ground-truth")
    return (
        f"proxy-unseen-{digest[:16]}",
        f"proxy-unseen-{digest[16:32]}",
    )


def judge_proxy_promotion(
    *,
    new_proxy: Mapping[str, object],
    previous_proxy: Mapping[str, object] | None,
    new_seed_results: Mapping[str, int],
    previous_seed_results: Mapping[str, int] | None = None,
    required_seed_count: int = 2,
) -> dict:
    """Decide whether a proxy is retained by delayed two-seed ground truth."""

    clean_new = {str(seed): int(value or 0) for seed, value in new_seed_results.items()}
    selected_seeds = tuple(sorted(clean_new)[:required_seed_count])
    previous = previous_proxy or {}
    clean_previous = {
        str(seed): int(value or 0)
        for seed, value in (previous_seed_results or {}).items()
    }
    no_previous_best = not previous or str(previous.get("proxy_id", "") or "") in {"", "baseline_proxy"}
    if len(selected_seeds) < required_seed_count:
        return {
            "promoted": False,
            "proxy_promotion_events": 0,
            "reason": "fewer_than_two_unseen_seed_results",
            "seeds": selected_seeds,
            "new_hidden_transfer": sum(clean_new.get(seed, 0) for seed in selected_seeds),
            "previous_hidden_transfer": 0,
        }
    if not no_previous_best and not set(selected_seeds).issubset(set(clean_previous)):
        return {
            "promoted": False,
            "proxy_promotion_events": 0,
            "reason": "previous_proxy_missing_matching_seed_results",
            "seeds": selected_seeds,
            "new_hidden_transfer": sum(clean_new.get(seed, 0) for seed in selected_seeds),
            "previous_hidden_transfer": sum(clean_previous.get(seed, 0) for seed in selected_seeds),
        }
    seed_decisions = []
    for seed in selected_seeds:
        previous_value = 0 if no_previous_best else clean_previous.get(seed, 0)
        new_value = clean_new.get(seed, 0)
        seed_decisions.append(
            {
                "seed": seed,
                "new_hidden_transfer": new_value,
                "previous_hidden_transfer": previous_value,
                "improved": new_value > previous_value,
            }
        )
    promoted = all(item["improved"] for item in seed_decisions)
    return {
        "promoted": promoted,
        "proxy_promotion_events": 1 if promoted else 0,
        "reason": "two_unseen_seeds_improved" if promoted else "ground_truth_did_not_improve_on_both_seeds",
        "seeds": selected_seeds,
        "seed_decisions": seed_decisions,
        "new_proxy": dict(new_proxy),
        "previous_proxy": dict(previous),
        "new_hidden_transfer": sum(item["new_hidden_transfer"] for item in seed_decisions),
        "previous_hidden_transfer": sum(item["previous_hidden_transfer"] for item in seed_decisions),
    }
