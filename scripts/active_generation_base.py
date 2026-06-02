"""Active generation base harness for OMEGA-THDSE Colab validation.

This file represents the latest accepted candidate base from the Colab
accepted-only loop. New candidate generations should extend this passing base
instead of starting from selected validation subsets.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_DIR = pathlib.Path("/content/omega_thdse_candidate_runs")


def run(command: list[str], cwd: pathlib.Path) -> int:
    completed = subprocess.run(command, cwd=str(cwd), text=True)
    return completed.returncode


def main() -> int:
    full_test_command = [sys.executable, "-m", "pytest", "-q"]
    full_test_code = run(full_test_command, ROOT)
    if full_test_code != 0:
        return full_test_code

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "candidate_id": "gen4_from_base_test_batch_correlation_v1",
        "parent_id": "gen4_from_base_test_reasoning_bridge_v1",
        "full_test_command": "python -m pytest -q",
        "full_test_exit_code": full_test_code,
        "fitness": 1,
    }
    (RUN_DIR / "active_generation_base_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
