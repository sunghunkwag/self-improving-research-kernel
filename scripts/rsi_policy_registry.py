"""Candidate policy registry for the closed RSI loop.

The registry is intentionally declarative. It gives experiments a stable
surface for measuring what the loop is allowed to change, how candidates are
validated, how rollback works, and which safety constraints are active.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class PolicyCapability:
    """One measurable policy surface exposed by the loop."""

    name: str
    category: str
    evidence: str
    risk_control: str


def default_policy_capabilities() -> Tuple[PolicyCapability, ...]:
    """Return the generator, validator, patch, and safety policy surfaces."""

    return (
        PolicyCapability(
            name="source_tree_candidate_generation",
            category="generator",
            evidence="candidate factories inspect repository state before proposing patches",
            risk_control="candidate names are deterministic and budget bounded",
        ),
        PolicyCapability(
            name="history_aware_candidate_ranking",
            category="generator",
            evidence="candidate order is derived from persisted accepted/rejected provenance",
            risk_control="previously rejected candidate names are retried only after fresher options",
        ),
        PolicyCapability(
            name="schema_driven_candidate_synthesis",
            category="generator",
            evidence="the planner infers missing query APIs from dataclass fields and generates tests",
            risk_control="generated candidates remain deterministic and must pass validation gates",
        ),
        PolicyCapability(
            name="bounded_emergent_hypothesis_search",
            category="generator",
            evidence="the planner creates competing canonical and alternate hypotheses and scores them with rejection history",
            risk_control="hypothesis count is capped and every selected hypothesis still passes the same gates",
        ),
        PolicyCapability(
            name="open_ended_cross_domain_proposal_space",
            category="generator",
            evidence="the open exploration layer crosses broad domain seeds with generator, validator, patch, grounding, transfer, and self-limit axes",
            risk_control="the stream is open-ended but each run materializes only a bounded proposal prefix",
        ),
        PolicyCapability(
            name="meta_meta_limit_modeling",
            category="generator",
            evidence="candidate proposals include recursive self-limit layers up to configurable meta depth",
            risk_control="self-limit layers are descriptive evidence requests, not automatic patch approvals",
        ),
        PolicyCapability(
            name="compile_focused_broad_validation",
            category="validator",
            evidence="candidates must pass py_compile, focused pytest, root pytest, and THDSE core gates",
            risk_control="failed gates prevent promotion",
        ),
        PolicyCapability(
            name="atomic_patch_with_extra_files",
            category="patch_policy",
            evidence="candidate patches may change a target file plus declared supporting files",
            risk_control="rollback restores all touched files on rejection",
        ),
        PolicyCapability(
            name="speculative_unverified_self_modification_archive",
            category="patch_policy",
            evidence="unverified self-modification candidates may be archived as open-loop proposals",
            risk_control="archived proposals are never applied by the open exploration layer",
        ),
        PolicyCapability(
            name="bounded_governed_execution",
            category="safety",
            evidence="wall-clock budgets, command timeouts, kill switch, and persisted provenance",
            risk_control="no unbounded runaway loop is permitted",
        ),
        PolicyCapability(
            name="open_loop_no_auto_apply",
            category="safety",
            evidence="open-ended exploration writes reports only and leaves the closed RSI executor untouched",
            risk_control="promotion requires a separate bounded workflow with explicit gates",
        ),
    )


def candidate_policy_summary() -> Dict[str, object]:
    """Return a JSON-compatible summary for experiment reports."""

    capabilities = default_policy_capabilities()
    categories = sorted({capability.category for capability in capabilities})
    return {
        "capability_count": len(capabilities),
        "categories": categories,
        "capabilities": [asdict(capability) for capability in capabilities],
    }
