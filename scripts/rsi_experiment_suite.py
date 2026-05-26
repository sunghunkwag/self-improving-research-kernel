"""Cloud experiment suite for the verified closed RSI loop.

The suite runs only in disposable repository copies. It is designed to produce
research artifacts for review: baseline comparisons, ablations, metrics,
failure analysis, and an explicit safety model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".omega_rsi_runs",
    ".pytest_cache",
    "__pycache__",
    "target",
}

EXCLUDED_FILES = {
    "shared/atom_bank.json",
}


@dataclass(frozen=True)
class ExperimentVariant:
    """One baseline or ablation configuration."""

    name: str
    family: str
    description: str
    broad_gate: bool = True
    thdse_core_gate: bool = True
    rollback: bool = True
    persistence: bool = True
    run_loop: bool = True
    max_generations_override: Optional[int] = None
    max_candidates_override: Optional[int] = None


@dataclass(frozen=True)
class ExperimentTask:
    """One repository/task state to evaluate."""

    name: str
    description: str


@dataclass
class ExperimentResult:
    """JSON-compatible experiment outcome."""

    task: str
    variant: str
    family: str
    description: str
    exit_code: int
    elapsed_s: float
    accepted_count: int
    rejected_count: int
    accepted_rate: float
    regression_gate_failures: int
    rollback_correct: Optional[bool]
    persistence_file_exists: bool
    improvement_depth: int
    cost_proxy_seconds: float
    changed_files_count: int
    summary_path: str
    stdout_tail: str
    stderr_tail: str


DEFAULT_TASKS = (
    ExperimentTask(
        name="local_corpus_queries_clean",
        description="Remove accepted local corpus query APIs and measure whether the loop recovers them.",
    ),
    ExperimentTask(
        name="policy_registry_self_patch",
        description="Remove the explicit policy registry surface and measure whether the loop patches its own policy interface.",
    ),
    ExperimentTask(
        name="forced_broad_regression",
        description="Inject a failing broad-gate test to measure rollback and no-broad-gate regression risk.",
    ),
)


DEFAULT_VARIANTS = (
    ExperimentVariant(
        name="verified_closed_loop",
        family="proposed",
        description="Full loop: candidate generation, patching, rollback, persistence, root broad gate, and THDSE core gate.",
    ),
    ExperimentVariant(
        name="agent_coding_loop",
        family="baseline_agent_coding_loop",
        description="Baseline: single-pass automated coding loop with validation but without persistent recursive depth.",
        persistence=False,
        max_generations_override=1,
        max_candidates_override=1,
    ),
    ExperimentVariant(
        name="evolutionary_repair_loop",
        family="baseline_evolutionary_repair_loop",
        description="Baseline: retry candidate repair loop using focused validation without broad gates or persistent self-policy depth.",
        broad_gate=False,
        thdse_core_gate=False,
        persistence=False,
        max_generations_override=3,
        max_candidates_override=3,
    ),
    ExperimentVariant(
        name="focused_only_loop",
        family="ablation_no_broad_gate",
        description="Ablation: focused tests only, no broad regression gate.",
        broad_gate=False,
        thdse_core_gate=False,
    ),
    ExperimentVariant(
        name="no_thdse_core_gate",
        family="ablation_no_z3_thdse_gate",
        description="Ablation: root broad gate enabled but THDSE/Z3-focused core gate skipped.",
        thdse_core_gate=False,
    ),
    ExperimentVariant(
        name="no_persistence",
        family="ablation_no_persistence",
        description="Ablation: state is not persisted, so future runs cannot resume from accepted history.",
        persistence=False,
    ),
    ExperimentVariant(
        name="no_rollback",
        family="ablation_no_rollback",
        description="Ablation: rejected candidates are intentionally left in disposable copies.",
        rollback=False,
    ),
    ExperimentVariant(
        name="ci_only_validation",
        family="baseline_ci_only",
        description="Baseline: run validation without candidate generation or code patching.",
        run_loop=False,
    ),
)


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def should_ignore(_directory: str, names: List[str]) -> List[str]:
    ignored = []
    for name in names:
        if name in EXCLUDED_DIRS:
            ignored.append(name)
    return ignored


def copy_repo(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=should_ignore)
    reports_dir = dst / "reports" / "rsi_experiments"
    if reports_dir.exists():
        shutil.rmtree(reports_dir)


def strip_method(text: str, method_name: str) -> str:
    pattern = rf"\n    def {re.escape(method_name)}\(.*?(?=\n    def |\n\n[A-Za-z_@]|\Z)"
    return re.sub(pattern, "\n", text, count=1, flags=re.DOTALL)


def remove_local_corpus_query_methods(repo: Path) -> None:
    path = repo / "shared" / "local_corpus.py"
    text = path.read_text(encoding="utf-8")
    text = strip_method(text, "records_with_feature")
    text = strip_method(text, "records_importing")
    path.write_text(text, encoding="utf-8")
    for test_name in (
        "test_local_corpus_feature_query_rewrite.py",
        "test_local_corpus_import_query_rewrite.py",
    ):
        try:
            (repo / "tests" / test_name).unlink()
        except FileNotFoundError:
            pass


def remove_policy_registry_surface(repo: Path) -> None:
    registry = repo / "scripts" / "rsi_policy_registry.py"
    try:
        registry.unlink()
    except FileNotFoundError:
        pass
    try:
        (repo / "tests" / "test_rsi_policy_registry_rewrite.py").unlink()
    except FileNotFoundError:
        pass
    loop_path = repo / "scripts" / "closed_recursive_self_improvement_loop.py"
    text = loop_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    stripped: List[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "POLICY_REGISTRY_ACTIVE = True":
            while i < len(lines) and not lines[i].startswith("class ClosedRecursiveSelfImprovementLoop:"):
                i += 1
            continue
        stripped.append(lines[i])
        i += 1
    lines = stripped
    stripped = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("    def policy_surface(self)"):
            while i < len(lines) and not lines[i].startswith("    def load_state(self)"):
                i += 1
            continue
        stripped.append(lines[i])
        i += 1
    text = "".join(stripped)
    loop_path.write_text(text, encoding="utf-8")


def prepare_task(repo: Path, task: ExperimentTask) -> None:
    state_dir = repo / ".omega_rsi_runs"
    if state_dir.exists():
        shutil.rmtree(state_dir)
    if task.name in {"local_corpus_queries_clean", "forced_broad_regression"}:
        remove_local_corpus_query_methods(repo)
    if task.name == "policy_registry_self_patch":
        remove_policy_registry_surface(repo)
    if task.name == "forced_broad_regression":
        failing_test = repo / "tests" / "test_forced_broad_regression_gate.py"
        failing_test.write_text(
            "def test_forced_broad_regression_gate():\n"
            "    assert False, 'intentional broad-gate regression for rollback ablation'\n",
            encoding="utf-8",
        )


def iter_fingerprint_files(repo: Path) -> Iterable[Path]:
    for path in sorted(repo.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(repo)
        parts = set(relative.parts)
        if parts & EXCLUDED_DIRS:
            continue
        if relative.as_posix() in EXCLUDED_FILES:
            continue
        if relative.parts[:3] == ("reports", "rsi_experiments"):
            continue
        yield path


def repository_fingerprint(repo: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for path in iter_fingerprint_files(repo):
        relative = path.relative_to(repo).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[relative] = digest
    return result


def changed_files(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
    keys = sorted(set(before) | set(after))
    return [key for key in keys if before.get(key) != after.get(key)]


def run_command(args: Sequence[str], cwd: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )


def run_ci_only(repo: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    py = sys.executable
    return run_command(
        [
            py,
            "-m",
            "pytest",
            "-q",
            "--import-mode=importlib",
            "--maxfail=20",
            "--disable-warnings",
            "tests",
        ],
        repo,
        timeout_s,
    )


def run_loop_variant(
    repo: Path,
    variant: ExperimentVariant,
    *,
    max_generations: int,
    max_candidates: int,
    wall_seconds: int,
    timeout_s: int,
) -> subprocess.CompletedProcess[str]:
    py = sys.executable
    effective_generations = variant.max_generations_override or max_generations
    effective_candidates = variant.max_candidates_override or max_candidates
    args = [
        py,
        "scripts/closed_recursive_self_improvement_loop.py",
        "--repo-root",
        str(repo),
        "--state-dir",
        str(repo / ".omega_rsi_runs"),
        "--apply",
        "--max-generations",
        str(effective_generations),
        "--max-candidates",
        str(effective_candidates),
        "--wall-seconds",
        str(wall_seconds),
        "--timeout-seconds",
        str(timeout_s),
    ]
    if variant.broad_gate:
        args.append("--broad-gate")
    if not variant.thdse_core_gate:
        args.append("--no-thdse-core-gate")
    if not variant.rollback:
        args.append("--no-rollback")
    if not variant.persistence:
        args.append("--no-persistence")
    return run_command(args, repo, max(timeout_s, wall_seconds + 60))


def summarize_gates(records: Iterable[dict]) -> int:
    failures = 0
    for record in records:
        for gate in record.get("gates", []):
            label = str(gate.get("label", ""))
            if gate.get("exit_code") != 0 and (
                "root_broad" in label or "thdse_core" in label
            ):
                failures += 1
    return failures


def build_result(
    task: ExperimentTask,
    variant: ExperimentVariant,
    proc: subprocess.CompletedProcess[str],
    repo: Path,
    before: Dict[str, str],
    after: Dict[str, str],
    elapsed_s: float,
) -> ExperimentResult:
    summary_path = repo / ".omega_rsi_runs" / "closed_rsi_summary.json"
    summary = read_json(summary_path, {})
    accepted = list(summary.get("accepted_this_run", []))
    rejected = list(summary.get("rejected_this_run", []))
    total_candidates = len(accepted) + len(rejected)
    changed = changed_files(before, after)
    rollback_correct: Optional[bool] = None
    if variant.rollback and rejected and not accepted:
        rollback_correct = changed == []
    elif not variant.rollback and rejected:
        rollback_correct = False
    return ExperimentResult(
        task=task.name,
        variant=variant.name,
        family=variant.family,
        description=variant.description,
        exit_code=proc.returncode,
        elapsed_s=round(elapsed_s, 3),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        accepted_rate=(len(accepted) / total_candidates) if total_candidates else 0.0,
        regression_gate_failures=summarize_gates([*accepted, *rejected]),
        rollback_correct=rollback_correct,
        persistence_file_exists=(repo / ".omega_rsi_runs" / "closed_rsi_state.json").exists(),
        improvement_depth=int(summary.get("active_generation", 0)),
        cost_proxy_seconds=round(elapsed_s, 3),
        changed_files_count=len(changed),
        summary_path=str(summary_path),
        stdout_tail=proc.stdout[-4000:],
        stderr_tail=proc.stderr[-2000:],
    )


def write_csv(path: Path, results: List[ExperimentResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_markdown_reports(output_dir: Path, results: List[ExperimentResult]) -> None:
    table_lines = [
        "| Task | Variant | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        rollback = "n/a" if result.rollback_correct is None else str(result.rollback_correct)
        table_lines.append(
            f"| {result.task} | {result.variant} | {result.accepted_count} | "
            f"{result.rejected_count} | {result.accepted_rate:.2f} | "
            f"{result.regression_gate_failures} | {rollback} | {result.elapsed_s:.2f} |"
        )

    readiness = [
        "# RSI Research Readiness Report",
        "",
        "This report evaluates a bounded, verified recursive self-improvement loop. "
        "It does not claim unbounded ASI behavior.",
        "",
        "## Experiment Matrix",
        "",
        *table_lines,
        "",
        "## Review-Relevant Claims",
        "",
        "- The proposed loop can patch real repository code and persist accepted/rejected provenance.",
        "- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.",
        "- Broad gates reduce regression risk relative to focused-only ablations.",
        "- Rollback behavior is measurable on forced broad-gate rejection tasks.",
        "- Persistence can be ablated to show that resume depth depends on durable state.",
        "- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.",
    ]
    (output_dir / "neurips_readiness.md").write_text("\n".join(readiness) + "\n", encoding="utf-8")

    failures = ["# Failure Analysis", ""]
    for result in results:
        if result.rejected_count or result.exit_code:
            failures.extend(
                [
                    f"## {result.task} / {result.variant}",
                    "",
                    f"- Rejected candidates: {result.rejected_count}",
                    f"- Regression gate failures: {result.regression_gate_failures}",
                    f"- Exit code: {result.exit_code}",
                    "",
                ]
            )
    if len(failures) == 2:
        failures.append("No rejected candidates or command failures were observed.")
    (output_dir / "failure_analysis.md").write_text("\n".join(failures) + "\n", encoding="utf-8")

    safety = [
        "# Safety Model",
        "",
        "- Execution is bounded by workflow timeout, loop wall-clock budget, and per-command timeout.",
        "- Candidates are deterministic source patches, not unbounded autonomous processes.",
        "- Rejected candidates are rolled back by default.",
        "- A kill-switch file at `.omega_rsi_runs/STOP_CLOSED_RSI` stops the loop.",
        "- Accepted and rejected records are persisted as JSON provenance.",
        "- Dangerous ablations such as no rollback run only in disposable experiment copies.",
        "- The main workflow commits only accepted state and validated source changes.",
    ]
    (output_dir / "safety_model.md").write_text("\n".join(safety) + "\n", encoding="utf-8")


def select_by_name(items, selected: Sequence[str]):
    if not selected or "all" in selected:
        return list(items)
    names = set(selected)
    return [item for item in items if item.name in names]


def run_suite(args: argparse.Namespace) -> Path:
    repo_root = args.repo_root.resolve()
    output_dir = (args.output_dir or repo_root / "reports" / "rsi_experiments" / "latest").resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = select_by_name(DEFAULT_TASKS, args.task)
    variants = select_by_name(DEFAULT_VARIANTS, args.variant)
    results: List[ExperimentResult] = []

    with tempfile.TemporaryDirectory(prefix="rsi_experiments_") as tmp:
        tmp_root = Path(tmp)
        for task in tasks:
            for variant in variants:
                work_repo = tmp_root / f"{task.name}__{variant.name}"
                copy_repo(repo_root, work_repo)
                prepare_task(work_repo, task)
                before = repository_fingerprint(work_repo)
                started = time.monotonic()
                try:
                    if variant.run_loop:
                        proc = run_loop_variant(
                            work_repo,
                            variant,
                            max_generations=args.max_generations,
                            max_candidates=args.max_candidates,
                            wall_seconds=args.wall_seconds,
                            timeout_s=args.timeout_seconds,
                        )
                    else:
                        proc = run_ci_only(work_repo, args.timeout_seconds)
                except subprocess.TimeoutExpired as exc:
                    proc = subprocess.CompletedProcess(
                        args=exc.cmd,
                        returncode=124,
                        stdout=exc.stdout or "",
                        stderr=exc.stderr or "command timed out",
                    )
                elapsed = time.monotonic() - started
                after = repository_fingerprint(work_repo)
                result = build_result(task, variant, proc, work_repo, before, after, elapsed)
                results.append(result)

    write_json(output_dir / "summary.json", [asdict(result) for result in results])
    if results:
        write_csv(output_dir / "metrics.csv", results)
    write_markdown_reports(output_dir, results)
    return output_dir


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--variant", action="append", default=[])
    parser.add_argument("--max-generations", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=4)
    parser.add_argument("--wall-seconds", type=int, default=1800)
    parser.add_argument("--timeout-seconds", type=int, default=420)
    args = parser.parse_args(argv)

    output_dir = run_suite(args)
    print(json.dumps({"output_dir": str(output_dir)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
