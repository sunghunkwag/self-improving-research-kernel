"""Active generation base harness for OMEGA-THDSE Colab validation.

This file represents the latest accepted candidate base from the Colab
accepted-only loop. New candidate generations should extend this passing base
instead of starting from the original minimal validation set.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_DIR = pathlib.Path("/content/omega_thdse_candidate_runs")

ROOT_TESTS = [
    "tests/test_local_corpus_bridge.py",
    "tests/test_arena_manager.py",
    "tests/test_agent_environment_bridge.py",
    "tests/test_semantic_encoder.py",
    "tests/test_deterministic_rng.py",
    "tests/test_reasoning_bridge.py",
]

THDSE_TESTS = [
    "tests/test_execution_sandbox.py",
    "tests/test_adaptive_threshold.py",
    "tests/test_direct_io_scoring.py",
    "tests/test_structural_diff.py",
    "tests/test_batch_correlation.py",
]


def make_env(paths: list[pathlib.Path]) -> dict[str, str]:
    env = os.environ.copy()
    env["OMEGA_THDSE_ENABLE_RUST"] = "0"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in paths) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def existing(paths: list[str], base: pathlib.Path) -> list[str]:
    return [path for path in paths if (base / path).exists()]


def run(command: list[str], cwd: pathlib.Path, paths: list[pathlib.Path]) -> int:
    completed = subprocess.run(command, cwd=str(cwd), env=make_env(paths), text=True)
    return completed.returncode


def main() -> int:
    root_tests = existing(ROOT_TESTS, ROOT)
    thdse_tests = existing(THDSE_TESTS, ROOT / "thdse")

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
        ROOT,
        [ROOT],
    )
    if root_code != 0:
        return root_code

    thdse_code = run(
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
        ROOT / "thdse",
        [ROOT / "thdse"],
    )
    if thdse_code != 0:
        return thdse_code

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "candidate_id": "gen4_from_base_test_batch_correlation_v1",
        "parent_id": "gen4_from_base_test_reasoning_bridge_v1",
        "root_tests": root_tests,
        "thdse_tests": thdse_tests,
        "fitness": len(root_tests) * 10 + len(thdse_tests) * 12,
    }
    (RUN_DIR / "active_generation_base_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
