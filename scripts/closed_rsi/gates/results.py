"""Validation gate result records for the closed RSI loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


FULL_TEST_COMMAND: Tuple[str, ...] = ("python", "-m", "pytest", "-q")


@dataclass(frozen=True)
class GateResult:
    """One validation command result."""

    label: str
    args: List[str]
    cwd: str
    exit_code: int
    elapsed_s: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    timed_out: bool = False

def candidate_compute_cost(gates: Sequence[GateResult]) -> float:
    return round(sum(float(gate.elapsed_s) for gate in gates), 3)


def is_full_test_gate(gate: GateResult | Dict[str, object]) -> bool:
    """Return whether a gate ran the required full repository pytest command."""

    label = str(gate.label if isinstance(gate, GateResult) else gate.get("label", ""))
    args = list(gate.args if isinstance(gate, GateResult) else gate.get("args", []))
    return label.endswith("_full_pytest") and len(args) >= 4 and args[-3:] == ["-m", "pytest", "-q"]


def full_test_exit_code(gates: Sequence[GateResult]) -> Optional[int]:
    """Return the final full pytest exit code from a candidate gate list."""

    for gate in reversed(gates):
        if is_full_test_gate(gate):
            return int(gate.exit_code)
    return None


def full_test_passed(gates: Sequence[GateResult]) -> bool:
    exit_code = full_test_exit_code(gates)
    return exit_code == 0
