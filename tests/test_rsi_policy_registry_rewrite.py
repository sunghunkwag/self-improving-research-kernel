from scripts.closed_recursive_self_improvement_loop import (
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
