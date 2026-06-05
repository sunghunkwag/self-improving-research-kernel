"""Run memory-safe local validation for OMEGA-THDSE."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]


QUICK_COMMANDS: Tuple[Tuple[str, ...], ...] = (
    (
        "-m",
        "py_compile",
        "scripts/closed_recursive_self_improvement_loop.py",
        "scripts/rsi_experiment_suite.py",
        "scripts/open_ended_exploration.py",
        "scripts/memory_safe_validate.py",
    ),
    (
        "-m",
        "pytest",
        "-q",
        "tests/test_capability_benchmarks.py",
        "tests/test_open_ended_exploration.py",
        "tests/test_rsi_policy_registry_rewrite.py",
    ),
)

NORMAL_COMMANDS: Tuple[Tuple[str, ...], ...] = (
    *QUICK_COMMANDS,
    ("-m", "pytest", "--collect-only", "-q"),
)


def run_command(args: Sequence[str], timeout_s: int) -> int:
    command = [sys.executable, *args]
    print(f"\n$ {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return int(completed.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run memory-safe local validation.")
    parser.add_argument("--quick", action="store_true", help="Run the smallest 8GB-friendly smoke check.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full pytest. Intended for CI or high-memory machines, not 8GB local use.",
    )
    parser.add_argument("--timeout", type=int, default=240, help="Per-command timeout in seconds.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.full:
        commands = (("-m", "pytest", "-q"),)
        label = "Full validation"
    elif args.quick:
        commands = QUICK_COMMANDS
        label = "Quick memory-safe validation"
    else:
        commands = NORMAL_COMMANDS
        label = "Memory-safe validation"
    for command in commands:
        code = run_command(command, timeout_s=args.timeout)
        if code != 0:
            print(f"{label} failed with exit code {code}.")
            return code
    print(f"\n{label} passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
