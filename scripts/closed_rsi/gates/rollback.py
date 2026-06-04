"""Rollback and quarantine filesystem helpers for the closed RSI loop."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List


def quarantine_ignore(_directory: str, names: List[str]) -> List[str]:
    """Ignore generated state and cache directories when copying quarantine repos."""

    ignored = []
    for name in names:
        if name in {
            ".git",
            ".mypy_cache",
            ".omega_rsi_runs",
            ".pytest_cache",
            "__pycache__",
            "target",
        }:
            ignored.append(name)
    return ignored


def copy_repo_to_quarantine(src: Path, dst: Path) -> None:
    """Copy a repository into a disposable quarantine workspace."""

    shutil.copytree(src, dst, ignore=quarantine_ignore)
