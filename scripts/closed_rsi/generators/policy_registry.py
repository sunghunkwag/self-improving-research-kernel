"""Policy-registry candidate generator and active registry loader."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from scripts.closed_rsi.generators.common import insert_before


POLICY_REGISTRY_ACTIVE_MARKER = "POLICY_REGISTRY_" + "ACTIVE = True"


def add_policy_registry_hook(text: str) -> str:
    if POLICY_REGISTRY_ACTIVE_MARKER in text:
        return text
    function_marker = next(
        (
            marker
            for marker in (
                "\n\nclass ClosedRecursiveSelfImprovementLoop:\n",
                "\n\nclass ClosedRecursiveSelfImprovementLoop(",
            )
            if marker in text
        ),
        "\n\nclass ClosedRecursiveSelfImprovementLoop:\n",
    )
    function_insertion = "\n\n" + POLICY_REGISTRY_ACTIVE_MARKER + '''


def load_policy_registry(repo_root: Path) -> Dict[str, object]:
    """Return metadata for the active candidate policy registry."""

    registry_path = repo_root / "scripts" / "rsi_policy_registry.py"
    if not registry_path.exists():
        return {
            "available": False,
            "path": str(registry_path.relative_to(repo_root)),
            "capabilities": [],
        }
    return {
        "available": True,
        "path": str(registry_path.relative_to(repo_root)),
        "capabilities": [
            "generator_policy",
            "validator_policy",
            "patch_policy",
            "safety_policy",
        ],
    }
'''
    text = insert_before(
        text,
        function_marker,
        function_insertion,
        "loop_policy_registry_v1",
    )
    method_marker = "    def load_state(self) -> dict:\n"
    method_insertion = '''    def policy_surface(self) -> Dict[str, object]:
        """Expose the active generator, validator, patch, and safety policy surface."""

        return load_policy_registry(self.repo_root)

'''
    return insert_before(
        text,
        method_marker,
        method_insertion,
        "loop_policy_registry_v1",
    )

POLICY_REGISTRY_SOURCE = '''"""Candidate policy registry for the closed RSI loop.

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
            name="operator_synthesis_surface",
            category="generator",
            evidence="capability repair candidates generate solver primitives, search heuristics, evaluator mutations, and counterexample tests",
            risk_control="each synthesized operator carries an executable validation plan before promotion",
        ),
        PolicyCapability(
            name="capability_delta_scoring",
            category="validator",
            evidence="accepted and rejected candidate records include solved task, hidden transfer, regression, reuse, and compute-cost signals",
            risk_control="promotion evidence separates target success from regression and transfer behavior",
        ),
        PolicyCapability(
            name="failure_residue_extraction",
            category="validator",
            evidence="rejected candidates persist failed reason, missing operator, missing abstraction, evaluator, and overfit signal",
            risk_control="future candidate ranking can use failure residue instead of retrying blind",
        ),
        PolicyCapability(
            name="compile_diagnostic_full_pytest_validation",
            category="validator",
            evidence="candidates may run focused diagnostics, but promotion requires the full python -m pytest -q suite",
            risk_control="diagnostic-only checks and selected-file subsets cannot mark a candidate successful",
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
'''


POLICY_REGISTRY_TEST = '''from scripts.closed_recursive_self_improvement_loop import (
    ClosedRecursiveSelfImprovementLoop,
    load_policy_registry,
)
from scripts.rsi_policy_registry import candidate_policy_summary


def test_policy_registry_exposes_required_policy_surfaces(tmp_path):
    summary = candidate_policy_summary()

    assert summary["capability_count"] >= 4
    assert set(summary["categories"]) == {
        "generator",
        "patch_policy",
        "safety",
        "validator",
    }


def test_closed_loop_exposes_policy_surface():
    loop = ClosedRecursiveSelfImprovementLoop(__import__("pathlib").Path.cwd())
    surface = loop.policy_surface()

    assert surface["available"] is True
    assert "generator_policy" in surface["capabilities"]
    assert load_policy_registry(__import__("pathlib").Path.cwd()) == surface
'''


POLICY_REGISTRY_ACTIVE = True


def load_policy_registry(repo_root: Path) -> Dict[str, object]:
    """Return metadata for the active candidate policy registry."""

    registry_path = repo_root / "scripts" / "rsi_policy_registry.py"
    if not registry_path.exists():
        return {
            "available": False,
            "path": str(registry_path.relative_to(repo_root)),
            "capabilities": [],
        }
    return {
        "available": True,
        "path": str(registry_path.relative_to(repo_root)),
        "capabilities": [
            "generator_policy",
            "validator_policy",
            "patch_policy",
            "safety_policy",
        ],
    }
