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
            name="bounded_governed_execution",
            category="safety",
            evidence="wall-clock budgets, command timeouts, kill switch, and persisted provenance",
            risk_control="no unbounded runaway loop is permitted",
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
