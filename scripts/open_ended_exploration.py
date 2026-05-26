"""Open-ended candidate exploration for RSI research.

This module deliberately keeps the improvement loop open. It expands the
candidate proposal space across domains, abstraction levels, and speculative
self-modification modes, but it does not apply patches or claim validation.
The output is a provenance-rich proposal archive that a later bounded workflow
can inspect, reject, or promote.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from itertools import count, product
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


DEFAULT_META_DEPTH = 3
DEFAULT_MAX_CANDIDATES = 48


@dataclass(frozen=True)
class DomainSeed:
    """One broad external or internal domain for transfer-oriented search."""

    name: str
    description: str
    signals: Tuple[str, ...]
    source: str


@dataclass(frozen=True)
class ExplorationAxis:
    """One modification axis that can be crossed with any domain seed."""

    name: str
    description: str
    target_surfaces: Tuple[str, ...]
    allows_unverified_self_modification: bool


@dataclass(frozen=True)
class MetaLimitLayer:
    """One recursive self-model layer about generator limits."""

    level: int
    label: str
    limitation: str
    transferable_question: str


@dataclass(frozen=True)
class OpenCandidate:
    """One open-loop candidate proposal that is not automatically applied."""

    candidate_id: str
    generation_index: int
    domain: str
    axis: str
    proposal_kind: str
    title: str
    hypothesis: str
    proposed_self_modification: str
    validation_status: str
    closure_state: str
    transfer_targets: Tuple[str, ...]
    meta_limit_layers: Tuple[MetaLimitLayer, ...]
    safety_controls: Tuple[str, ...]
    provenance: Dict[str, str]


@dataclass(frozen=True)
class OpenExplorationReport:
    """JSON-compatible report for open-ended proposal exploration."""

    generated_at: str
    search_space_signature: str
    open_space_claim: str
    materialized_candidate_count: int
    domains: Tuple[DomainSeed, ...]
    axes: Tuple[ExplorationAxis, ...]
    candidates: Tuple[OpenCandidate, ...]
    safety_model: Tuple[str, ...]


DEFAULT_DOMAIN_SEEDS: Tuple[DomainSeed, ...] = (
    DomainSeed(
        name="software_maintenance",
        description="Bug repair, regression triage, test design, and refactoring.",
        signals=("github_issues", "pytest_failures", "rollback_records"),
        source="local_repo_and_public_issue_metadata",
    ),
    DomainSeed(
        name="mathematical_reasoning",
        description="Symbolic constraints, theorem sketches, proof obligations, and counterexamples.",
        signals=("z3_constraints", "property_tests", "invariant_catalogs"),
        source="local_tests_and_formal_gate_artifacts",
    ),
    DomainSeed(
        name="machine_learning",
        description="Representation learning, curriculum design, data efficiency, and benchmark transfer.",
        signals=("benchmark_scores", "learning_curves", "model_card_failures"),
        source="public_project_metadata_without_remote_code_execution",
    ),
    DomainSeed(
        name="systems_engineering",
        description="Scheduling, memory budgets, isolation, build reliability, and observability.",
        signals=("ci_logs", "resource_budgets", "timeout_events"),
        source="workflow_metadata_and_local_configuration",
    ),
    DomainSeed(
        name="security_and_sandboxing",
        description="Threat models, capability boundaries, sandbox hardening, and provenance controls.",
        signals=("policy_surfaces", "sandbox_tests", "security_issue_metadata"),
        source="bounded_metadata_and_local_safety_tests",
    ),
    DomainSeed(
        name="human_computer_interaction",
        description="Operator feedback, review ergonomics, report clarity, and decision support.",
        signals=("review_notes", "report_completeness", "manual_acceptance_records"),
        source="local_reports_and_human_review_outcomes",
    ),
    DomainSeed(
        name="scientific_discovery",
        description="Hypothesis generation, experiment design, ablation structure, and failed-result mining.",
        signals=("ablation_tables", "failure_analysis", "experiment_catalogs"),
        source="local_research_artifacts",
    ),
    DomainSeed(
        name="robotics_and_control",
        description="Closed-world planning, state estimation, feedback control, and transfer under uncertainty.",
        signals=("simulated_task_specs", "controller_invariants", "safety_cases"),
        source="proposal_only_domain_seed",
    ),
    DomainSeed(
        name="biology_and_medicine",
        description="Causal mechanisms, noisy measurements, protocol design, and evidence grading.",
        signals=("evidence_hierarchy", "causal_graphs", "protocol_constraints"),
        source="proposal_only_domain_seed",
    ),
    DomainSeed(
        name="economics_and_strategy",
        description="Multi-agent incentives, decision theory, resource allocation, and robustness to gaming.",
        signals=("utility_models", "market_failures", "strategic_counterexamples"),
        source="proposal_only_domain_seed",
    ),
)


DEFAULT_EXPLORATION_AXES: Tuple[ExplorationAxis, ...] = (
    ExplorationAxis(
        name="generator_policy_rewrite",
        description="Rewrite how future candidates are invented, ranked, and diversified.",
        target_surfaces=("scripts/closed_recursive_self_improvement_loop.py", "scripts/rsi_policy_registry.py"),
        allows_unverified_self_modification=True,
    ),
    ExplorationAxis(
        name="validator_policy_rewrite",
        description="Invent new validation gates, counterexample strategies, and uncertainty labels.",
        target_surfaces=("tests", "benchmarks", "scripts/rsi_experiment_suite.py"),
        allows_unverified_self_modification=True,
    ),
    ExplorationAxis(
        name="patch_policy_rewrite",
        description="Change the granularity, rollback model, and promotion rules for candidate patches.",
        target_surfaces=(".omega_rsi_runs", "scripts/closed_recursive_self_improvement_loop.py"),
        allows_unverified_self_modification=True,
    ),
    ExplorationAxis(
        name="external_grounding_expansion",
        description="Add new external task sources while preserving source provenance and bounded fetches.",
        target_surfaces=("scripts/external_world_grounding.py", "reports/external_grounding"),
        allows_unverified_self_modification=False,
    ),
    ExplorationAxis(
        name="transfer_mechanism_synthesis",
        description="Extract cross-domain invariants and propose transfer tests between unrelated task families.",
        target_surfaces=("benchmarks", "reports/rsi_experiments", "shared"),
        allows_unverified_self_modification=True,
    ),
    ExplorationAxis(
        name="self_limit_modeling",
        description="Make the generator describe its own blind spots, missing evidence, and false-positive risks.",
        target_surfaces=("reports", "scripts/rsi_policy_registry.py"),
        allows_unverified_self_modification=False,
    ),
)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(parts: Iterable[object], *, length: int = 16) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:length]


def search_space_signature(domains: Sequence[DomainSeed], axes: Sequence[ExplorationAxis]) -> str:
    """Return a stable signature for the symbolic open search space."""

    parts: List[str] = []
    for domain in domains:
        parts.extend((domain.name, domain.description, *domain.signals))
    for axis in axes:
        parts.extend((axis.name, axis.description, *axis.target_surfaces))
    return stable_hash(parts, length=24)


def meta_label(level: int) -> str:
    if level <= 1:
        return "meta"
    return "_".join(["meta"] * level)


def build_meta_limit_layers(
    domain: DomainSeed,
    axis: ExplorationAxis,
    *,
    depth: int,
) -> Tuple[MetaLimitLayer, ...]:
    """Describe recursive generator limits up to the requested depth."""

    templates = (
        (
            "The generator may confuse a high-scoring proposal with a real capability gain.",
            "What observable evidence would distinguish search novelty from measurable improvement?",
        ),
        (
            "The generator may inherit blind spots from its current ranking and validation policy.",
            "Which rejected or unvalidated ideas should be reinterpreted under a different policy?",
        ),
        (
            "The generator may fail to transfer structure across domains because its abstractions are too local.",
            "What invariant would let this proposal transfer beyond the source domain?",
        ),
        (
            "The generator may overfit to available provenance and ignore missing external signals.",
            "Which unavailable signal would most change the proposal ranking?",
        ),
        (
            "The generator may be unable to verify the policy that decides what verification should mean.",
            "How should downstream review represent uncertainty about the validator itself?",
        ),
    )
    layers: List[MetaLimitLayer] = []
    for offset in range(max(0, depth)):
        limitation, question = templates[offset % len(templates)]
        layers.append(
            MetaLimitLayer(
                level=offset + 1,
                label=meta_label(offset + 1),
                limitation=f"{limitation} Domain={domain.name}; axis={axis.name}.",
                transferable_question=question,
            )
        )
    return tuple(layers)


def transfer_targets_for(domain: DomainSeed, domains: Sequence[DomainSeed], *, limit: int = 4) -> Tuple[str, ...]:
    targets = [candidate.name for candidate in domains if candidate.name != domain.name]
    if not targets:
        return ()
    start = int(stable_hash((domain.name, len(domains)), length=4), 16) % len(targets)
    rotated = targets[start:] + targets[:start]
    return tuple(rotated[:limit])


def candidate_stream(
    domains: Sequence[DomainSeed],
    axes: Sequence[ExplorationAxis],
    *,
    meta_depth: int,
    include_unverified: bool,
) -> Iterator[OpenCandidate]:
    """Yield a deterministic open-ended stream without applying patches."""

    if not domains:
        raise ValueError("at least one domain seed is required")
    if not axes:
        raise ValueError("at least one exploration axis is required")

    generation = count()
    combinations = tuple(product(domains, axes))
    while True:
        generation_index = next(generation)
        domain, axis = combinations[generation_index % len(combinations)]
        allows_unverified = include_unverified and axis.allows_unverified_self_modification
        proposal_kind = (
            "speculative_unverified_self_modification"
            if allows_unverified
            else "grounded_open_loop_proposal"
        )
        candidate_id = "open-" + stable_hash(
            (
                generation_index,
                domain.name,
                axis.name,
                proposal_kind,
                meta_depth,
            )
        )
        yield OpenCandidate(
            candidate_id=candidate_id,
            generation_index=generation_index,
            domain=domain.name,
            axis=axis.name,
            proposal_kind=proposal_kind,
            title=f"{domain.name} x {axis.name}",
            hypothesis=(
                f"Crossing {domain.name} with {axis.name} may reveal a transfer rule "
                "that the closed loop cannot invent from local validation alone."
            ),
            proposed_self_modification=(
                "Record the proposal as an unapplied policy mutation for later review; "
                "do not execute or promote it without a separate bounded validation plan."
            ),
            validation_status=(
                "explicitly_unverified_allowed"
                if allows_unverified
                else "not_yet_validated"
            ),
            closure_state="open_loop_not_applied",
            transfer_targets=transfer_targets_for(domain, domains),
            meta_limit_layers=build_meta_limit_layers(domain, axis, depth=meta_depth),
            safety_controls=(
                "proposal_only",
                "no_auto_patch",
                "no_remote_code_execution",
                "bounded_materialization",
                "provenance_required",
                "requires_separate_promotion_workflow",
            ),
            provenance={
                "domain_source": domain.source,
                "domain_signals": ",".join(domain.signals),
                "target_surfaces": ",".join(axis.target_surfaces),
                "generated_at": utc_now(),
            },
        )


def materialize_candidates(
    domains: Sequence[DomainSeed],
    axes: Sequence[ExplorationAxis],
    *,
    max_candidates: int,
    meta_depth: int,
    include_unverified: bool,
) -> Tuple[OpenCandidate, ...]:
    if max_candidates < 1:
        raise ValueError("max_candidates must be at least 1")
    stream = candidate_stream(
        domains,
        axes,
        meta_depth=meta_depth,
        include_unverified=include_unverified,
    )
    return tuple(next(stream) for _ in range(max_candidates))


def build_open_exploration_report(
    domains: Sequence[DomainSeed] = DEFAULT_DOMAIN_SEEDS,
    axes: Sequence[ExplorationAxis] = DEFAULT_EXPLORATION_AXES,
    *,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    meta_depth: int = DEFAULT_META_DEPTH,
    include_unverified: bool = True,
) -> OpenExplorationReport:
    candidates = materialize_candidates(
        domains,
        axes,
        max_candidates=max_candidates,
        meta_depth=meta_depth,
        include_unverified=include_unverified,
    )
    return OpenExplorationReport(
        generated_at=utc_now(),
        search_space_signature=search_space_signature(domains, axes),
        open_space_claim=(
            "The symbolic stream is open-ended by generation index, domain seed, axis, "
            "and meta-limit depth; this report materializes only a bounded prefix."
        ),
        materialized_candidate_count=len(candidates),
        domains=tuple(domains),
        axes=tuple(axes),
        candidates=candidates,
        safety_model=(
            "The open exploration layer does not apply patches.",
            "Unverified self-modification proposals may be recorded but remain unapplied.",
            "The candidate stream is conceptually open-ended, while each run materializes a bounded prefix.",
            "Every proposal records provenance, target surfaces, and transfer targets.",
            "Promotion into a closed loop requires a separate bounded workflow.",
        ),
    )


def write_report(output_dir: Path, report: OpenExplorationReport) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    (output_dir / "open_exploration_candidates.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    lines = [
        "# Open-Ended Exploration Report",
        "",
        f"- Generated at: {report.generated_at}",
        f"- Search space signature: `{report.search_space_signature}`",
        f"- Materialized candidates: {report.materialized_candidate_count}",
        f"- Domain seeds: {len(report.domains)}",
        f"- Exploration axes: {len(report.axes)}",
        "",
        "## Open Space Claim",
        "",
        report.open_space_claim,
        "",
        "## Safety Model",
        "",
        *[f"- {item}" for item in report.safety_model],
        "",
        "## Candidate Prefix",
        "",
    ]
    for candidate in report.candidates:
        meta_labels = ", ".join(layer.label for layer in candidate.meta_limit_layers)
        transfer = ", ".join(candidate.transfer_targets) if candidate.transfer_targets else "none"
        lines.extend(
            [
                f"### {candidate.candidate_id}",
                "",
                f"- Title: {candidate.title}",
                f"- Proposal kind: `{candidate.proposal_kind}`",
                f"- Validation status: `{candidate.validation_status}`",
                f"- Closure state: `{candidate.closure_state}`",
                f"- Transfer targets: {transfer}",
                f"- Meta layers: {meta_labels}",
                f"- Hypothesis: {candidate.hypothesis}",
                "",
            ]
        )
    (output_dir / "open_exploration_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--meta-depth", type=int, default=DEFAULT_META_DEPTH)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/open_exploration/latest"))
    parser.add_argument(
        "--exclude-unverified",
        action="store_true",
        help="Do not materialize proposals that explicitly allow unverified self-modification.",
    )
    args = parser.parse_args(argv)
    if args.max_candidates < 1:
        parser.error("--max-candidates must be at least 1")
    if args.meta_depth < 1:
        parser.error("--meta-depth must be at least 1")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    report = build_open_exploration_report(
        max_candidates=args.max_candidates,
        meta_depth=args.meta_depth,
        include_unverified=not args.exclude_unverified,
    )
    write_report(args.output_dir, report)
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "materialized_candidates": report.materialized_candidate_count,
                "search_space_signature": report.search_space_signature,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
