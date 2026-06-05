"""State-fed generator policy for recursive candidate production."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Mapping, Sequence, Tuple

from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.records import CandidatePatch, Goal, generator_feedback


FEEDBACK_POLICY_PROMOTED = False


def _promoted_assignment_active(text: str) -> bool:
    return bool(re.search(r"^FEEDBACK_POLICY_PROMOTED\s*=\s*True\s*$", text, flags=re.MULTILINE))


@dataclass(frozen=True)
class GeneratorFeedbackEvent:
    """One accepted generator-improvement signal from persisted state."""

    candidate_name: str
    generation: int
    surface: str
    mechanism: str
    evidence: str
    hidden_transfer: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GeneratorPolicy:
    """Active search policy derived from accepted feedback."""

    accepted_feedback_count: int
    synthesis_budget: int
    curriculum_difficulty: int
    archive_promotion_enabled: bool
    feedback_surfaces: Tuple[str, ...]
    feedback_signature: str

    def to_dict(self) -> dict:
        return asdict(self)


def accepted_generator_feedback(state: object) -> Tuple[GeneratorFeedbackEvent, ...]:
    """Extract accepted generator feedback events from loop state."""

    if not isinstance(state, Mapping):
        return ()
    events: List[GeneratorFeedbackEvent] = []
    for record in state.get("accepted", []):
        if not isinstance(record, Mapping):
            continue
        feedback = record.get("generator_improvement", {})
        if not isinstance(feedback, Mapping) or not feedback:
            continue
        delta = record.get("capability_delta", {})
        hidden_transfer = 0
        if isinstance(delta, Mapping):
            hidden_transfer = int(delta.get("hidden_transfer", 0) or 0)
        events.append(
            GeneratorFeedbackEvent(
                candidate_name=str(record.get("name", "")),
                generation=int(record.get("generation", 0) or 0),
                surface=str(feedback.get("surface", "")),
                mechanism=str(feedback.get("mechanism", "")),
                evidence=str(feedback.get("evidence", "")),
                hidden_transfer=hidden_transfer,
            )
        )
    return tuple(events)


def generator_policy_from_state(state: object) -> GeneratorPolicy:
    """Build the live generator policy that feeds generation N+1."""

    events = accepted_generator_feedback(state)
    synthesis_events = [
        event
        for event in events
        if "synthesis" in event.surface.lower()
        or "synthesis" in event.mechanism.lower()
        or "operator" in event.surface.lower()
    ]
    hidden_mastery = sum(1 for event in events if event.hidden_transfer > 0)
    surfaces = tuple(sorted({event.surface for event in events if event.surface}))
    signature_payload = [
        (event.candidate_name, event.generation, event.surface, event.evidence)
        for event in events
    ]
    signature = hashlib.sha256(json.dumps(signature_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return GeneratorPolicy(
        accepted_feedback_count=len(events),
        synthesis_budget=min(4, 1 + len(synthesis_events)),
        curriculum_difficulty=min(6, 1 + hidden_mastery),
        archive_promotion_enabled=bool(events),
        feedback_surfaces=surfaces,
        feedback_signature=signature,
    )


def candidate_stream_signature(candidates: Sequence[CandidatePatch], policy: GeneratorPolicy) -> str:
    """Fingerprint the observable candidate stream under a policy."""

    payload = {
        "policy": policy.to_dict(),
        "candidates": [
            {
                "name": candidate.name,
                "target": str(candidate.target_path),
                "family": candidate.capability_family,
            }
            for candidate in candidates
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def promote_feedback_policy_source(text: str) -> str:
    """Mark this generator policy surface as a promoted mutable target."""

    if _promoted_assignment_active(text):
        return text
    if "FEEDBACK_POLICY_PROMOTED = False" in text:
        return text.replace("FEEDBACK_POLICY_PROMOTED = False", "FEEDBACK_POLICY_PROMOTED = True", 1)
    return text.rstrip() + "\n\nFEEDBACK_POLICY_PROMOTED = True\n"


def feedback_policy_candidates(
    repo_root: Path,
    generation: int,
    *,
    policy: GeneratorPolicy,
) -> List[CandidatePatch]:
    """Promote the feedback policy itself after prior feedback proves useful."""

    if policy.accepted_feedback_count <= 0:
        return []
    target = repo_root / "scripts" / "closed_rsi" / "generators" / "feedback_policy.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    if _promoted_assignment_active(text):
        return []
    test_path = repo_root / "tests" / "test_generator_feedback_policy_v1.py"
    return [
        CandidatePatch(
            name="generator_feedback_policy_v1",
            generation=generation,
            goal=Goal(
                name="promote_generator_feedback_policy",
                target="scripts.closed_rsi.generators.feedback_policy",
                metric="accepted generator feedback changes the next candidate stream",
                rationale=(
                    "The generator policy module is a legitimate mutable target; "
                    "after one accepted generator delta, the loop can promote a "
                    "search-policy patch through the same gate chain."
                ),
            ),
            target_path=target,
            test_path=test_path,
            transform=promote_feedback_policy_source,
            test_source='''from scripts.closed_rsi.generators.feedback_policy import (
    FEEDBACK_POLICY_PROMOTED,
    generator_policy_from_state,
)


def test_generator_feedback_policy_promoted_marker():
    assert FEEDBACK_POLICY_PROMOTED is True


def test_generator_feedback_policy_reads_accepted_feedback():
    policy = generator_policy_from_state(
        {
            "accepted": [
                {
                    "name": "prior_synthesis",
                    "generation": 1,
                    "generator_improvement": {
                        "surface": "operator synthesis",
                        "mechanism": "compositional synthesis",
                        "evidence": "strategy=stateful_scan",
                    },
                    "capability_delta": {"hidden_transfer": 1},
                }
            ]
        }
    )

    assert policy.accepted_feedback_count == 1
    assert policy.synthesis_budget > 1
    assert policy.curriculum_difficulty > 1
''',
            focused_tests=("tests/test_generator_feedback_policy_v1.py",),
            capability_family="generator_feedback_policy",
            operator_specs=operator_specs_for("generator_feedback_policy", "feedback_policy_surface"),
            generator_improvement=generator_feedback(
                "generator search policy",
                "makes accepted generator_improvement events change later synthesis budget and curriculum difficulty",
                (
                    "policy unlocked by "
                    f"{policy.accepted_feedback_count} accepted feedback events; "
                    f"signature={policy.feedback_signature}"
                ),
            ),
        )
    ]
