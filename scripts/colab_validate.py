"""Colab-oriented validation entry point for OMEGA-THDSE.

This script is intended for a high-memory Colab runtime, not the local 8GB PC.
It still keeps the Rust arena disabled by default unless the caller explicitly
sets ``OMEGA_THDSE_ENABLE_RUST=1``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


def run(args: Sequence[str], timeout_s: int) -> int:
    env = os.environ.copy()
    if env.get("OMEGA_THDSE_ENABLE_RUST", "").lower() not in {"1", "true", "yes"}:
        env.pop("OMEGA_THDSE_ENABLE_RUST", None)
    command = [sys.executable, *args]
    print(f"\n$ {' '.join(command)}")
    return subprocess.run(command, cwd=str(ROOT), env=env, timeout=timeout_s, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Colab validation for OMEGA-THDSE.")
    parser.add_argument("--timeout", type=int, default=900, help="Per-command timeout in seconds.")
    parser.add_argument("--full", action="store_true", help="Run all test suites. Use only on Colab or a high-memory machine.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = [
        ["-m", "pytest", "-q", "tests", "--ignore=tests/test_rust_backend.py"],
        ["-m", "pytest", "-q", "Cognitive-Core-Engine-Test/tests"],
    ]
    if args.full:
        commands.append(["-m", "pytest", "-q", "thdse/tests"])

    for command in commands:
        code = run(command, timeout_s=args.timeout)
        if code != 0:
            return code
    print("\nColab validation completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
