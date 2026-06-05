"""Immutable-boundary guards for open-ended proxy and candidate search."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence, Tuple

from scripts.closed_rsi.records import CandidatePatch


@dataclass(frozen=True)
class BoundaryFinding:
    """One immutable-boundary reference found in mutable search material."""

    source: str
    pattern: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "pattern": self.pattern,
            "reason": self.reason,
        }


IMMUTABLE_PATH_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("scripts.closed_rsi.evaluators", "immutable evaluator import"),
    ("scripts/closed_rsi/evaluators", "immutable evaluator path"),
    ("scripts.closed_rsi.gates", "immutable gate import"),
    ("scripts/closed_rsi/gates", "immutable gate path"),
    ("shared.capability_benchmarks", "ground-truth benchmark module"),
    ("capability_cases_for_seed", "evaluation case-bank access"),
    ("evaluate_capability_cases", "ground-truth evaluator access"),
    ("detect_anti_cheat_findings", "anti-cheat implementation access"),
    ("capability_fixture_metadata.json", "held-out fixture metadata access"),
    ("external_code_repair_metadata.json", "held-out external-code metadata access"),
    ("held_out_reference", "held-out reference access"),
    (".external_code_quarantine", "quarantined reference access"),
    ("expected_outputs", "expected-output access"),
    ("hidden_cases", "hidden-case access"),
    ("evaluation_seed", "evaluation seed access"),
)

MUTABLE_GENERATOR_PATHS: Tuple[str, ...] = (
    "scripts/closed_rsi/generators",
    "scripts/rsi_policy_registry.py",
    "scripts/closed_recursive_self_improvement_loop.py",
)

PROXY_ONLY_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("hidden_transfer", "ground-truth metric access"),
    ("capabilitydelta", "ground-truth delta object access"),
    ("capability_delta", "ground-truth delta access"),
    ("anti_cheat", "anti-cheat implementation access"),
    ("__import__", "dynamic import access"),
    ("importlib", "dynamic import access"),
    ("open(", "filesystem read access"),
    ("path(", "filesystem path access"),
    ("read_text", "filesystem read access"),
    ("read_bytes", "filesystem read access"),
    ("eval(", "dynamic evaluation access"),
    ("exec(", "dynamic execution access"),
)


def immutable_boundary_policy_summary() -> dict:
    """Return explicit mutable and immutable candidate surfaces."""

    return {
        "mutable_generator_surfaces": MUTABLE_GENERATOR_PATHS,
        "immutable_patterns": [
            {"pattern": pattern, "reason": reason}
            for pattern, reason in IMMUTABLE_PATH_PATTERNS
        ],
        "rationale": (
            "Generator and search-policy code may be patched by candidates; "
            "evaluator, anti-cheat, gate, metadata, and reference surfaces stay immutable "
            "so the loop cannot edit its own judge."
        ),
    }


def _normalize(text: object) -> str:
    normalized = str(text or "").replace("\\", "/")
    return normalized.lower()


def _finding_source_texts(
    named_texts: Iterable[Tuple[str, object]],
    patterns: Sequence[Tuple[str, str]],
) -> Tuple[BoundaryFinding, ...]:
    findings = []
    for source, text in named_texts:
        normalized = _normalize(text)
        for pattern, reason in patterns:
            if pattern in normalized:
                findings.append(BoundaryFinding(source=source, pattern=pattern, reason=reason))
    return tuple(findings)


def proxy_immutable_boundary_findings(*, proxy_id: str, expression: str, description: str = "") -> Tuple[BoundaryFinding, ...]:
    """Return guard findings for a mutable proxy scoring program."""

    return _finding_source_texts(
        (
            (f"{proxy_id}.expression", expression),
            (f"{proxy_id}.description", description),
        ),
        (*IMMUTABLE_PATH_PATTERNS, *PROXY_ONLY_PATTERNS),
    )


def candidate_immutable_boundary_findings(
    candidate: CandidatePatch,
    *,
    repo_root: Path | None = None,
) -> Tuple[BoundaryFinding, ...]:
    """Return guard findings for a generated candidate patch envelope.

    The guard inspects candidate-controlled metadata and generated sources. It
    does not scan the pre-existing target file content, because existing loop
    entrypoints legitimately import immutable evaluators and gates.
    """

    target_text = str(candidate.target_path)
    test_text = str(candidate.test_path)
    if repo_root is not None:
        try:
            target_text = str(candidate.target_path.resolve().relative_to(repo_root.resolve()))
        except Exception:
            target_text = str(candidate.target_path)
        try:
            test_text = str(candidate.test_path.resolve().relative_to(repo_root.resolve()))
        except Exception:
            test_text = str(candidate.test_path)

    metadata = {
        "goal": {
            "name": candidate.goal.name,
            "target": candidate.goal.target,
            "metric": candidate.goal.metric,
            "rationale": candidate.goal.rationale,
        },
        "operator_specs": candidate.operator_specs,
        "generator_improvement": candidate.generator_improvement,
        "schema_fields": candidate.schema_fields,
    }
    named_texts = [
        (f"{candidate.name}.name", candidate.name),
        (f"{candidate.name}.target_path", target_text),
        (f"{candidate.name}.test_path", test_text),
        (f"{candidate.name}.focused_tests", "\n".join(candidate.focused_tests)),
        (f"{candidate.name}.test_source", candidate.test_source),
        (f"{candidate.name}.metadata", json.dumps(metadata, sort_keys=True, default=str)),
    ]
    for relative_path, source in candidate.extra_files.items():
        named_texts.append((f"{candidate.name}.extra_path", relative_path))
        named_texts.append((f"{candidate.name}.extra_source:{relative_path}", source))

    findings = list(_finding_source_texts(named_texts, IMMUTABLE_PATH_PATTERNS))
    metric_regex = re.compile(r"(?<![A-Za-z0-9_])(?:hidden_transfer|CapabilityDelta)(?![A-Za-z0-9_])")
    for source, text in named_texts:
        if metric_regex.search(str(text or "")):
            findings.append(
                BoundaryFinding(
                    source=source,
                    pattern="hidden_transfer_or_CapabilityDelta",
                    reason="ground-truth metric access",
                )
            )
    return tuple(findings)


def findings_to_payload(findings: Sequence[BoundaryFinding]) -> dict:
    """Return a JSON-compatible immutable-boundary rejection payload."""

    return {
        "findings": [finding.to_dict() for finding in findings],
        "overfit_signal": "immutable_boundary_reference",
    }
