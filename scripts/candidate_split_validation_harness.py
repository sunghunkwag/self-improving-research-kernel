"""Full validation harness for OMEGA-THDSE."""

from __future__ import annotations

import pathlib
import subprocess
import sys


def run(command: list[str], cwd: pathlib.Path) -> int:
    completed = subprocess.run(command, cwd=str(cwd), text=True)
    return completed.returncode


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    return run(
        [sys.executable, "-m", "pytest", "-q"],
        root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
