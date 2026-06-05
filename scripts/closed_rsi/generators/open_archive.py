"""Closed-loop promotion candidates derived from open-exploration archives."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Mapping, Optional

from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.generators.feedback_policy import GeneratorPolicy
from scripts.closed_rsi.records import CandidatePatch, Goal, generator_feedback


OPEN_ARCHIVE_BRIDGE_NAME = "open_archive_validation_bridge"


def _slug(value: object) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value).lower()).strip("_")[:40] or "proposal"


def _load_archive_candidate(repo_root: Path) -> Optional[Mapping[str, object]]:
    archive = repo_root / "reports" / "open_exploration" / "latest" / "open_exploration_candidates.json"
    if not archive.exists():
        return None
    try:
        payload = json.loads(archive.read_text(encoding="utf-8"))
    except Exception:
        return None
    candidates = payload.get("candidates", []) if isinstance(payload, Mapping) else []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        plan = candidate.get("validation_plan", {})
        commands = plan.get("commands", []) if isinstance(plan, Mapping) else []
        closure_state = str(candidate.get("closure_state", ""))
        axis = str(candidate.get("axis", ""))
        if commands and closure_state == "open_loop_not_applied" and axis == "generator_policy_rewrite":
            return candidate
    return None


def _policy_capability_block(proposal: Mapping[str, object]) -> str:
    candidate_id = str(proposal.get("candidate_id", "open-unknown"))
    domain = str(proposal.get("domain", "unknown_domain"))
    axis = str(proposal.get("axis", "unknown_axis"))
    return f'''        PolicyCapability(
            name="{OPEN_ARCHIVE_BRIDGE_NAME}",
            category="generator",
            evidence="open exploration proposal {candidate_id} from {domain}/{axis} enters the closed loop only as a gated patch candidate",
            risk_control="proposal text is never sufficient; promotion still requires compile, focused tests, full pytest, rollback, and boundary gates",
        ),
'''


def add_open_archive_policy_capability(text: str, proposal: Mapping[str, object]) -> str:
    """Add a registry entry documenting the archive-to-closed-loop bridge."""

    if OPEN_ARCHIVE_BRIDGE_NAME in text:
        return text
    marker = '        PolicyCapability(\n            name="capability_delta_scoring"'
    block = _policy_capability_block(proposal)
    if marker in text:
        return text.replace(marker, block + marker, 1)
    return text.rstrip() + "\n\n# Open archive bridge registered by closed-loop candidate.\n" + block + "\n"


def open_archive_candidates(
    repo_root: Path,
    generation: int,
    *,
    policy: GeneratorPolicy,
) -> List[CandidatePatch]:
    """Turn one open archive proposal into a normal gated patch candidate."""

    if not policy.archive_promotion_enabled:
        return []
    proposal = _load_archive_candidate(repo_root)
    if proposal is None:
        return []
    target = repo_root / "scripts" / "rsi_policy_registry.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    if OPEN_ARCHIVE_BRIDGE_NAME in text:
        return []
    candidate_id = str(proposal.get("candidate_id", "open-unknown"))
    name = f"open_archive_bridge_{_slug(candidate_id)}_v1"
    test_path = repo_root / "tests" / "test_open_archive_validation_bridge.py"
    return [
        CandidatePatch(
            name=name,
            generation=generation,
            goal=Goal(
                name="promote_open_archive_validation_bridge",
                target="scripts.rsi_policy_registry",
                metric="open exploration proposal enters closed-loop validation as code",
                rationale=(
                    "The open-ended archive can propose directions, but this candidate "
                    "records only a closed-loop bridge and must pass all promotion gates."
                ),
            ),
            target_path=target,
            test_path=test_path,
            transform=lambda source, selected=proposal: add_open_archive_policy_capability(source, selected),
            test_source=f'''from scripts.rsi_policy_registry import candidate_policy_summary


def test_open_archive_validation_bridge_is_registered():
    summary = candidate_policy_summary()
    names = {{item["name"] for item in summary["capabilities"]}}

    assert {OPEN_ARCHIVE_BRIDGE_NAME!r} in names
''',
            focused_tests=("tests/test_open_archive_validation_bridge.py",),
            capability_family="open_archive_validation_bridge",
            operator_specs=operator_specs_for("open_archive_validation_bridge", OPEN_ARCHIVE_BRIDGE_NAME),
            generator_improvement=generator_feedback(
                "open archive bridge",
                "converts an unapplied open-exploration proposal into an ordinary closed-loop candidate",
                f"{candidate_id} promoted only as gated policy-registry code",
            ),
        )
    ]
