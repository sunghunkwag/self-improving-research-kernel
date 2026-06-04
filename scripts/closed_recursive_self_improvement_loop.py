"""Compatibility entrypoint for the closed recursive self-improvement loop.

The implementation lives in :mod:`scripts.closed_rsi`. This file remains as the
stable import and CLI surface because experiment fixtures, workflows, and older
candidate patches address ``scripts/closed_recursive_self_improvement_loop.py``
directly.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.closed_rsi import *  # noqa: F403 - preserve the historical public API.
from scripts.closed_rsi.generators.policy_registry import load_policy_registry as _load_policy_registry
from scripts.closed_rsi.loop import ClosedRecursiveSelfImprovementLoop as _ClosedRecursiveSelfImprovementLoop
from scripts.closed_rsi.loop import main as _main


POLICY_REGISTRY_ACTIVE = True


def load_policy_registry(repo_root: Path) -> Dict[str, object]:
    """Return metadata for the active candidate policy registry."""

    return _load_policy_registry(repo_root)


class ClosedRecursiveSelfImprovementLoop(_ClosedRecursiveSelfImprovementLoop):
    """Backward-compatible loop class exported from the historical module."""

    def policy_surface(self) -> Dict[str, object]:
        """Expose the active generator, validator, patch, and safety policy surface."""

        return load_policy_registry(self.repo_root)

    def load_state(self) -> dict:
        return super().load_state()


def main(argv: Sequence[str] | None = None) -> int:
    return _main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
