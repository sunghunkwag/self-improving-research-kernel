"""Run an 8GB-RAM-safe OMEGA-THDSE validation subset.

This intentionally avoids the full test suite and keeps the Rust arena backend
disabled unless the caller explicitly opts in outside this script.  The goal is
to validate core wiring, the local corpus connector, arena basics, and a small
THDSE synthesis/sandbox slice without multi-GB allocations.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence


ROOT = Path(__file__).resolve().parents[1]


QUICK_COMMANDS: List[List[str]] = [
    [
        "-m",
        "py_compile",
        "shared/local_corpus.py",
        "bridges/local_corpus_bridge.py",
        "scripts/connect_local_python_corpus.py",
        "shared/arena_manager.py",
        "Cognitive-Core-Engine-Test/cognitive_core_engine/core/hdc.py",
    ],
    [
        "-m",
        "pytest",
        "-q",
        "tests/test_local_corpus_bridge.py",
        "thdse/tests/test_execution_sandbox.py",
    ],
]


BASE_COMMANDS: List[List[str]] = [
    [
        "-m",
        "py_compile",
        "shared/local_corpus.py",
        "bridges/local_corpus_bridge.py",
        "scripts/connect_local_python_corpus.py",
        "shared/arena_manager.py",
        "Cognitive-Core-Engine-Test/cognitive_core_engine/core/hdc.py",
    ],
    [
        "-m",
        "pytest",
        "-q",
        "tests/test_local_corpus_bridge.py",
        "tests/test_arena_manager.py",
        "tests/test_agent_environment_bridge.py",
    ],
    [
        "-m",
        "pytest",
        "-q",
        "thdse/tests/test_execution_sandbox.py",
        "thdse/tests/test_adaptive_threshold.py",
    ],
]


EXTENDED_COMMANDS: List[List[str]] = [
    ["-m", "pytest", "-q", "Cognitive-Core-Engine-Test/tests/test_solvers.py"],
    ["-m", "pytest", "-q", "Cognitive-Core-Engine-Test/tests/test_selftest.py"],
]


def run_command(args: Sequence[str], timeout_s: int) -> int:
    env = os.environ.copy()
    env.pop("OMEGA_THDSE_ENABLE_RUST", None)
    command = [sys.executable, *args]
    print(f"\n$ {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return int(completed.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an 8GB-safe OMEGA-THDSE validation subset.")
    parser.add_argument("--quick", action="store_true", help="Run the smallest smoke set only.")
    parser.add_argument("--extended", action="store_true", help="Also run small CCE validation slices.")
    parser.add_argument("--timeout", type=int, default=240, help="Per-command timeout in seconds.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = list(QUICK_COMMANDS if args.quick else BASE_COMMANDS)
    if args.extended and not args.quick:
        commands.extend(EXTENDED_COMMANDS)

    for command in commands:
        code = run_command(command, timeout_s=args.timeout)
        if code != 0:
            print(f"Command failed with exit code {code}.")
            return code

    print("\nMemory-safe validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
