"""Shared records and state helpers for the closed RSI loop."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from scripts.closed_rsi.gates.results import FULL_TEST_COMMAND


Transform = Callable[[str], str]


@dataclass(frozen=True)
class Goal:
    """A measurable codebase improvement goal invented by the loop."""

    name: str
    target: str
    metric: str
    rationale: str


@dataclass(frozen=True)
class CandidatePatch:
    """Concrete source rewrite candidate."""

    name: str
    generation: int
    goal: Goal
    target_path: Path
    test_path: Path
    transform: Transform
    test_source: str
    focused_tests: Sequence[str] = field(default_factory=tuple)
    extra_files: Dict[str, str] = field(default_factory=dict)
    capability_family: str = ""
    operator_specs: Tuple[Dict[str, object], ...] = field(default_factory=tuple)
    generator_improvement: Dict[str, object] = field(default_factory=dict)
    schema_fields: Tuple[str, ...] = field(default_factory=tuple)


@dataclass
class CandidateRecord:
    """Persistent record for an accepted or rejected candidate."""

    name: str
    generation: int
    goal: Dict[str, str]
    target_path: str
    test_path: str
    extra_paths: List[str]
    accepted: bool
    started_at: str
    finished_at: str
    gates: List[Dict[str, object]]
    error: str = ""
    capability_delta: Dict[str, object] = field(default_factory=dict)
    failure_residue: Dict[str, object] = field(default_factory=dict)
    operator_synthesis: List[Dict[str, object]] = field(default_factory=list)
    generator_improvement: Dict[str, object] = field(default_factory=dict)
    quarantine: bool = False
    promoted: bool = False
    chain_depth: int = 0
    full_test_command: str = " ".join(FULL_TEST_COMMAND)
    full_test_exit_code: Optional[int] = None
    full_test_required: bool = True


@dataclass(frozen=True)
class CandidateFactorySpec:
    """Declarative recipe for one source-inspection candidate factory."""

    candidate_name: str
    missing_symbol: str
    goal_name: str
    target: str
    metric: str
    rationale: str
    target_relative_path: str
    test_relative_path: str
    transform: Transform
    test_source: str
    focused_tests: Tuple[str, ...]


@dataclass(frozen=True)
class AutonomousQueryBlueprint:
    """Planner-inferred query API candidate for a record tuple field."""

    field_name: str
    method_name: str
    parameter_name: str
    sample_value: str
    candidate_name: str
    goal_name: str
    rationale: str
    strategy: str = "tuple_membership"
    planner_score: float = 0.0
    evidence: Tuple[str, ...] = ()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def generator_feedback(surface: str, mechanism: str, evidence: str) -> Dict[str, object]:
    """Describe how a candidate improves future candidate generation."""

    return {
        "surface": surface,
        "mechanism": mechanism,
        "evidence": evidence,
    }


def operator_specs_for(family: str, operator: str) -> Tuple[Dict[str, object], ...]:
    """Return JSON-compatible operator synthesis specs for a candidate."""

    return tuple(spec.to_dict() for spec in synthesize_operator_specs(family, operator))

def source_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
