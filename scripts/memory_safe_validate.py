"""Run the required full OMEGA-THDSE validation suite."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


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
    parser = argparse.ArgumentParser(description="Run the required full OMEGA-THDSE validation suite.")
    parser.add_argument("--timeout", type=int, default=240, help="Per-command timeout in seconds.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    code = run_command(["-m", "pytest", "-q"], timeout_s=args.timeout)
    if code != 0:
        print(f"Full validation failed with exit code {code}.")
        return code
    print("\nFull validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
