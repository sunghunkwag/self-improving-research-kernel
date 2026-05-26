"""Closed recursive self-improvement loop for OMEGA-THDSE.

This module intentionally does not implement an unbounded runaway loop.
It implements a persistent, closed engineering loop over the real
OMEGA-THDSE source tree:

1. Inspect the current active source tree.
2. Invent a measurable improvement goal from missing project capability.
3. Generate a concrete source patch and matching regression test.
4. Apply the patch to real files.
5. Run compile, focused tests, and optional broader gates.
6. Promote only passing candidates; rollback failures.
7. Persist accepted/rejected records so the next generation starts from
   the latest accepted base.

The loop can run repeatedly in Colab, but every run has explicit budgets,
a kill-switch file, and rollback semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence


Transform = Callable[[str], str]


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


@dataclass
class CandidateRecord:
    """Persistent record for an accepted or rejected candidate."""

    name: str
    generation: int
    goal: Dict[str, str]
    target_path: str
    test_path: str
    accepted: bool
    started_at: str
    finished_at: str
    gates: List[Dict[str, object]]
    error: str = ""


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


def replace_once(text: str, old: str, new: str, candidate_name: str) -> str:
    if old not in text:
        raise RuntimeError(f"{candidate_name}: patch anchor not found")
    return text.replace(old, new, 1)


def insert_before(text: str, marker: str, insertion: str, candidate_name: str) -> str:
    if marker not in text:
        raise RuntimeError(f"{candidate_name}: insertion marker not found")
    return text.replace(marker, insertion + marker, 1)


def add_records_with_feature(text: str) -> str:
    if "def records_with_feature(" in text:
        return text
    marker = "    def write_json(self, path: Path) -> None:\n"
    insertion = '''    def records_with_feature(self, feature: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records carrying a static feature flag."""

        if not isinstance(feature, str) or not feature:
            raise ValueError("feature must be a non-empty string")
        return tuple(record for record in self.records if feature in record.feature_flags)

'''
    return insert_before(text, marker, insertion, "local_corpus_feature_query_v1")


def add_records_importing(text: str) -> str:
    if "def records_importing(" in text:
        return text
    marker = "    def write_json(self, path: Path) -> None:\n"
    insertion = '''    def records_importing(self, module_name: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records that statically import ``module_name``."""

        if not isinstance(module_name, str) or not module_name:
            raise ValueError("module_name must be a non-empty string")
        return tuple(record for record in self.records if module_name in record.imports)

'''
    return insert_before(text, marker, insertion, "local_corpus_import_query_v1")


FEATURE_QUERY_TEST = '''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_records_with_feature_filters_static_flags():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            feature_flags=("validation", "self_improvement"),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            feature_flags=("validation",),
        ),
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=2,
            syntax_ok_count=2,
            syntax_error_count=0,
            unique_sha256_count=2,
            duplicate_file_instances=0,
            feature_counts={"validation": 2, "self_improvement": 1},
            import_edge_count=0,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.records_with_feature("self_improvement")) == ("a.py",)
'''


IMPORT_QUERY_TEST = '''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_records_importing_filters_static_imports():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            imports=("json", "pathlib"),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            imports=("math",),
        ),
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=2,
            syntax_ok_count=2,
            syntax_error_count=0,
            unique_sha256_count=2,
            duplicate_file_instances=0,
            feature_counts={},
            import_edge_count=3,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.records_importing("json")) == ("a.py",)
'''


class ClosedRecursiveSelfImprovementLoop:
    """Persistent patch-test-promote loop over the real source tree."""

    def __init__(
        self,
        repo_root: Path,
        *,
        state_dir: Optional[Path] = None,
        broad_gate: bool = False,
        timeout_s: int = 300,
        dry_run: bool = True,
    ):
        self.repo_root = repo_root.resolve()
        self.thdse_root = self.repo_root / "thdse"
        self.state_dir = (
            state_dir
            or Path(os.environ.get("OMEGA_RSI_STATE_DIR", ""))
            or self.repo_root / ".omega_rsi_runs"
        )
        if str(self.state_dir) == ".":
            self.state_dir = self.repo_root / ".omega_rsi_runs"
        self.state_dir = self.state_dir.resolve()
        self.state_path = self.state_dir / "closed_rsi_state.json"
        self.summary_path = self.state_dir / "closed_rsi_summary.json"
        self.kill_switch_path = self.state_dir / "STOP_CLOSED_RSI"
        self.broad_gate = broad_gate
        self.timeout_s = int(timeout_s)
        self.dry_run = bool(dry_run)
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(self.repo_root)

    def load_state(self) -> dict:
        state = read_json(self.state_path, {})
        if not isinstance(state, dict):
            state = {}
        state.setdefault("accepted", [])
        state.setdefault("rejected", [])
        state.setdefault("active_generation", 0)
        state.setdefault("active_base", "initial")
        return state

    def save_state(self, state: dict) -> None:
        write_json(self.state_path, state)

    def invent_candidates(self, generation: int) -> List[CandidatePatch]:
        """Invent candidates from missing source capabilities."""

        local_corpus = self.repo_root / "shared" / "local_corpus.py"
        text = local_corpus.read_text(encoding="utf-8")
        candidates: List[CandidatePatch] = []

        if "def records_with_feature(" not in text:
            goal = Goal(
                name="make_local_corpus_queryable_by_feature",
                target="shared.local_corpus.LocalCorpusIndex",
                metric="new query API plus focused regression test",
                rationale="The corpus index already extracts feature flags but lacks a stable query API.",
            )
            candidates.append(
                CandidatePatch(
                    name="local_corpus_feature_query_v1",
                    generation=generation,
                    goal=goal,
                    target_path=local_corpus,
                    test_path=self.repo_root / "tests" / "test_local_corpus_feature_query_rewrite.py",
                    transform=add_records_with_feature,
                    test_source=FEATURE_QUERY_TEST,
                    focused_tests=("tests/test_local_corpus_feature_query_rewrite.py",),
                )
            )

        if "def records_importing(" not in text:
            goal = Goal(
                name="make_local_corpus_queryable_by_import",
                target="shared.local_corpus.LocalCorpusIndex",
                metric="new import query API plus focused regression test",
                rationale="The corpus index stores static imports but lacks a direct import lookup API.",
            )
            candidates.append(
                CandidatePatch(
                    name="local_corpus_import_query_v1",
                    generation=generation,
                    goal=goal,
                    target_path=local_corpus,
                    test_path=self.repo_root / "tests" / "test_local_corpus_import_query_rewrite.py",
                    transform=add_records_importing,
                    test_source=IMPORT_QUERY_TEST,
                    focused_tests=("tests/test_local_corpus_import_query_rewrite.py",),
                )
            )

        return candidates

    def run_command(self, label: str, args: Sequence[str], cwd: Path) -> GateResult:
        start = time.monotonic()
        try:
            proc = subprocess.run(
                list(args),
                cwd=str(cwd),
                env=self.env,
                text=True,
                capture_output=True,
                timeout=self.timeout_s,
            )
            elapsed = round(time.monotonic() - start, 3)
            return GateResult(
                label=label,
                args=list(args),
                cwd=str(cwd),
                exit_code=proc.returncode,
                elapsed_s=elapsed,
                stdout_tail=proc.stdout[-4000:],
                stderr_tail=proc.stderr[-2000:],
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = round(time.monotonic() - start, 3)
            return GateResult(
                label=label,
                args=list(args),
                cwd=str(cwd),
                exit_code=124,
                elapsed_s=elapsed,
                stdout_tail=(exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                stderr_tail=(exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
                timed_out=True,
            )

    def validate(self, candidate: CandidatePatch) -> List[GateResult]:
        py = sys.executable
        gates = [
            self.run_command(
                f"{candidate.name}_compile",
                [
                    py,
                    "-m",
                    "py_compile",
                    str(candidate.target_path.relative_to(self.repo_root)),
                    str(candidate.test_path.relative_to(self.repo_root)),
                ],
                self.repo_root,
            )
        ]
        gates.append(
            self.run_command(
                f"{candidate.name}_focused",
                [
                    py,
                    "-m",
                    "pytest",
                    "-q",
                    "--import-mode=importlib",
                    "--maxfail=5",
                    "--disable-warnings",
                    *candidate.focused_tests,
                ],
                self.repo_root,
            )
        )
        if self.broad_gate:
            gates.append(
                self.run_command(
                    f"{candidate.name}_root_broad",
                    [py, "-m", "pytest", "-q", "--import-mode=importlib", "--maxfail=20", "--disable-warnings", "tests"],
                    self.repo_root,
                )
            )
            if self.thdse_root.exists():
                gates.append(
                    self.run_command(
                        f"{candidate.name}_thdse_core",
                        [
                            py,
                            "-m",
                            "pytest",
                            "-q",
                            "--import-mode=importlib",
                            "--maxfail=20",
                            "--disable-warnings",
                            "tests/test_execution_sandbox.py",
                            "tests/test_adaptive_threshold.py",
                            "tests/test_direct_io_scoring.py",
                            "tests/test_structural_diff.py",
                            "tests/test_batch_correlation.py",
                        ],
                        self.thdse_root,
                    )
                )
        return gates

    def apply_candidate(self, candidate: CandidatePatch) -> CandidateRecord:
        started = utc_now()
        original_target = candidate.target_path.read_text(encoding="utf-8")
        original_test = candidate.test_path.read_text(encoding="utf-8") if candidate.test_path.exists() else None
        gates: List[GateResult] = []
        error = ""
        accepted = False

        try:
            rewritten = candidate.transform(original_target)
            if rewritten == original_target:
                raise RuntimeError("candidate made no source change")
            if self.dry_run:
                accepted = True
            else:
                candidate.target_path.write_text(rewritten, encoding="utf-8")
                candidate.test_path.parent.mkdir(parents=True, exist_ok=True)
                candidate.test_path.write_text(candidate.test_source, encoding="utf-8")
                gates = self.validate(candidate)
                accepted = all(gate.exit_code == 0 for gate in gates)
                if not accepted:
                    raise RuntimeError("one or more validation gates failed")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            accepted = False
            if not self.dry_run:
                candidate.target_path.write_text(original_target, encoding="utf-8")
                if original_test is None:
                    try:
                        candidate.test_path.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    candidate.test_path.write_text(original_test, encoding="utf-8")

        return CandidateRecord(
            name=candidate.name,
            generation=candidate.generation,
            goal=asdict(candidate.goal),
            target_path=str(candidate.target_path.relative_to(self.repo_root)),
            test_path=str(candidate.test_path.relative_to(self.repo_root)),
            accepted=accepted,
            started_at=started,
            finished_at=utc_now(),
            gates=[asdict(gate) for gate in gates],
            error=error,
        )

    def run(self, *, max_generations: int = 10, max_candidates: int = 10, wall_seconds: int = 1800) -> dict:
        """Run the closed loop until budget, kill switch, or no candidates."""

        state = self.load_state()
        started = time.monotonic()
        accepted_this_run: List[dict] = []
        rejected_this_run: List[dict] = []

        for _ in range(max_generations):
            if self.kill_switch_path.exists():
                break
            if time.monotonic() - started > wall_seconds:
                break
            generation = int(state.get("active_generation", 0)) + 1
            candidates = self.invent_candidates(generation)
            if not candidates:
                break

            promoted = False
            for candidate in candidates[:max_candidates]:
                record = self.apply_candidate(candidate)
                if record.accepted:
                    state["active_generation"] = generation
                    state["active_base"] = candidate.name
                    state["accepted"].append(asdict(record))
                    accepted_this_run.append(asdict(record))
                    promoted = True
                    self.save_state(state)
                    break
                state["rejected"].append(asdict(record))
                rejected_this_run.append(asdict(record))
                self.save_state(state)

            if not promoted:
                break

        summary = {
            "dry_run": self.dry_run,
            "broad_gate": self.broad_gate,
            "state_path": str(self.state_path),
            "accepted_this_run": accepted_this_run,
            "rejected_this_run": rejected_this_run,
            "active_generation": state.get("active_generation", 0),
            "active_base": state.get("active_base", "initial"),
            "total_accepted": len(state.get("accepted", [])),
            "total_rejected": len(state.get("rejected", [])),
        }
        write_json(self.summary_path, summary)
        return summary


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / "shared").exists() and (path / "tests").exists():
            return path
    raise RuntimeError("OMEGA-THDSE repository root not found")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--apply", action="store_true", help="Apply passing candidates to the real source tree.")
    parser.add_argument("--broad-gate", action="store_true", help="Run broader pytest gates after focused tests.")
    parser.add_argument("--max-generations", type=int, default=10)
    parser.add_argument("--max-candidates", type=int, default=10)
    parser.add_argument("--wall-seconds", type=int, default=1800)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or find_repo_root(Path.cwd())
    loop = ClosedRecursiveSelfImprovementLoop(
        repo_root,
        state_dir=args.state_dir,
        broad_gate=args.broad_gate,
        timeout_s=args.timeout_seconds,
        dry_run=not args.apply,
    )
    summary = loop.run(
        max_generations=args.max_generations,
        max_candidates=args.max_candidates,
        wall_seconds=args.wall_seconds,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
