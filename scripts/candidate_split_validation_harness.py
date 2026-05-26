"""Colab-safe split validation harness for OMEGA-THDSE.

This harness keeps root OMEGA tests and nested thdse tests in separate pytest
processes so identically named test packages do not collide during collection.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys


def make_env(paths: list[pathlib.Path]) -> dict[str, str]:
    env = os.environ.copy()
    env["OMEGA_THDSE_ENABLE_RUST"] = "0"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in paths) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def run(command: list[str], cwd: pathlib.Path, paths: list[pathlib.Path]) -> int:
    completed = subprocess.run(command, cwd=str(cwd), env=make_env(paths), text=True)
    return completed.returncode


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    root_tests = [
        "tests/test_local_corpus_bridge.py",
        "tests/test_arena_manager.py",
        "tests/test_agent_environment_bridge.py",
    ]
    thdse_tests = [
        "tests/test_execution_sandbox.py",
        "tests/test_adaptive_threshold.py",
    ]

    root_code = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--import-mode=importlib",
            "--maxfail=20",
            "--disable-warnings",
            *root_tests,
        ],
        root,
        [root],
    )
    if root_code != 0:
        return root_code

    return run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--import-mode=importlib",
            "--maxfail=20",
            "--disable-warnings",
            *thdse_tests,
        ],
        root / "thdse",
        [root / "thdse"],
    )


if __name__ == "__main__":
    raise SystemExit(main())
