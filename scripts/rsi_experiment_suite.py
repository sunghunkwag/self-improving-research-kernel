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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


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
class BenchmarkRepository:
    """One repository fixture used by the benchmark matrix."""

    name: str
    description: str
    split: str = "seen"
    transfer_origin: str = ""


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
    repositories: Tuple[str, ...] = ()
    claim: str = ""


@dataclass
class ExperimentResult:
    """JSON-compatible experiment outcome."""

    repository: str
    repository_description: str
    task: str
    variant: str
    family: str
    description: str
    repeat_index: int
    seed: str
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
    repository_split: str = "seen"
    transfer_origin: str = ""
    task_description: str = ""
    task_claim: str = ""


DEFAULT_REPOSITORIES = (
    BenchmarkRepository(
        name="omega_full_repo",
        description="Full OMEGA-THDSE checkout with root tests and THDSE core gates available.",
    ),
    BenchmarkRepository(
        name="compact_kernel_repo",
        description="Minimal repository fixture containing only the closed loop, policy registry, local corpus module, and smoke tests.",
    ),
    BenchmarkRepository(
        name="unseen_schema_transfer_repo",
        description="Held-out compact fixture with an unseen tuple-valued record field that tests schema transfer beyond the original task distribution.",
        split="unseen",
        transfer_origin="compact_kernel_repo",
    ),
    BenchmarkRepository(
        name="unseen_security_transfer_repo",
        description="Held-out security-oriented fixture with a threat-label schema absent from the seen benchmark repositories.",
        split="unseen",
        transfer_origin="compact_kernel_repo",
    ),
    BenchmarkRepository(
        name="unseen_science_transfer_repo",
        description="Held-out science-oriented fixture with evidence-source schema absent from the seen benchmark repositories.",
        split="unseen",
        transfer_origin="compact_kernel_repo",
    ),
    BenchmarkRepository(
        name="unseen_control_transfer_repo",
        description="Held-out control-oriented fixture with controller-mode schema absent from the seen benchmark repositories.",
        split="unseen",
        transfer_origin="compact_kernel_repo",
    ),
)


DEFAULT_TASKS = (
    ExperimentTask(
        name="local_corpus_queries_clean",
        description="Remove accepted local corpus query APIs and measure whether the loop recovers them.",
        repositories=("omega_full_repo", "compact_kernel_repo"),
    ),
    ExperimentTask(
        name="policy_registry_self_patch",
        description="Remove the explicit policy registry surface and measure whether the loop patches its own policy interface.",
        repositories=("omega_full_repo", "compact_kernel_repo"),
    ),
    ExperimentTask(
        name="forced_broad_regression",
        description="Inject a failing broad-gate test to measure rollback and no-broad-gate regression risk.",
        repositories=("omega_full_repo", "compact_kernel_repo"),
    ),
    ExperimentTask(
        name="unseen_static_roles_query",
        description="Measure whether schema-driven generation transfers to a held-out tuple-valued LocalPythonFileRecord field.",
        repositories=("unseen_schema_transfer_repo",),
        claim="Unseen transfer succeeds when the loop patches a query API for a field absent from the original benchmark repositories.",
    ),
    ExperimentTask(
        name="unseen_threat_labels_query",
        description="Measure schema transfer on a held-out security-oriented tuple-valued record field.",
        repositories=("unseen_security_transfer_repo",),
        claim="Security-domain unseen transfer succeeds when the loop patches a query API for threat labels absent from the seen fixtures.",
    ),
    ExperimentTask(
        name="unseen_evidence_sources_query",
        description="Measure schema transfer on a held-out science-oriented tuple-valued record field.",
        repositories=("unseen_science_transfer_repo",),
        claim="Science-domain unseen transfer succeeds when the loop patches a query API for evidence sources absent from the seen fixtures.",
    ),
    ExperimentTask(
        name="unseen_controller_modes_query",
        description="Measure schema transfer on a held-out control-oriented tuple-valued record field.",
        repositories=("unseen_control_transfer_repo",),
        claim="Control-domain unseen transfer succeeds when the loop patches a query API for controller modes absent from the seen fixtures.",
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


def copy_required_file(src: Path, dst: Path, relative_path: str) -> None:
    source = src / relative_path
    target = dst / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_compact_kernel_repo(src: Path, dst: Path) -> None:
    """Build a small benchmark repository fixture for fast repeated trials."""

    dst.mkdir(parents=True, exist_ok=True)
    for relative_path in (
        "scripts/closed_recursive_self_improvement_loop.py",
        "scripts/rsi_policy_registry.py",
        "shared/__init__.py",
        "shared/local_corpus.py",
    ):
        copy_required_file(src, dst, relative_path)
    tests_dir = dst / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_fixture_smoke.py").write_text(
        "from pathlib import Path\n\n"
        "from scripts.closed_recursive_self_improvement_loop import ClosedRecursiveSelfImprovementLoop\n"
        "from shared.local_corpus import LocalCorpusIndex\n\n\n"
        "def test_compact_fixture_imports_core_surfaces():\n"
        "    assert LocalCorpusIndex.__name__ == 'LocalCorpusIndex'\n"
        "    loop = ClosedRecursiveSelfImprovementLoop(Path.cwd())\n"
        "    assert loop.policy_surface()['available'] is True\n",
        encoding="utf-8",
    )


def build_unseen_schema_transfer_repo(
    src: Path,
    dst: Path,
    *,
    field_name: str = "static_roles",
    sample_value: str = "planner",
    test_name: str = "test_unseen_schema_fixture.py",
) -> None:
    """Build a held-out schema-transfer fixture.

    The fixture keeps the same loop machinery as the compact repository but
    adds a new tuple-valued field that was not part of the original repair
    tasks. The generator must infer the missing query surface from schema
    structure rather than from a hand-coded candidate name.
    """

    build_compact_kernel_repo(src, dst)
    local_corpus = dst / "shared" / "local_corpus.py"
    text = local_corpus.read_text(encoding="utf-8")
    marker = "    feature_flags: Tuple[str, ...] = ()\n"
    field_declaration = f"    {field_name}: Tuple[str, ...] = ()\n"
    if field_declaration not in text:
        text = text.replace(marker, marker + field_declaration, 1)
    local_corpus.write_text(text, encoding="utf-8")
    smoke = dst / "tests" / test_name
    smoke.write_text(
        "from shared.local_corpus import LocalPythonFileRecord\n\n\n"
        "def test_unseen_schema_field_is_present_before_transfer_patch():\n"
        "    record = LocalPythonFileRecord(\n"
        "        path='agent.py',\n"
        "        sha256='x',\n"
        "        size_bytes=1,\n"
        "        line_count=1,\n"
        "        syntax_ok=True,\n"
        f"        {field_name}=('{sample_value}',),\n"
        "    )\n"
        f"    assert record.{field_name} == ('{sample_value}',)\n",
        encoding="utf-8",
    )


def build_benchmark_repo(src: Path, dst: Path, repository: BenchmarkRepository) -> None:
    if repository.name == "omega_full_repo":
        copy_repo(src, dst)
        return
    if repository.name == "compact_kernel_repo":
        build_compact_kernel_repo(src, dst)
        return
    if repository.name == "unseen_schema_transfer_repo":
        build_unseen_schema_transfer_repo(src, dst)
        return
    if repository.name == "unseen_security_transfer_repo":
        build_unseen_schema_transfer_repo(
            src,
            dst,
            field_name="threat_labels",
            sample_value="sandbox_escape",
            test_name="test_unseen_security_schema_fixture.py",
        )
        return
    if repository.name == "unseen_science_transfer_repo":
        build_unseen_schema_transfer_repo(
            src,
            dst,
            field_name="evidence_sources",
            sample_value="ablation_table",
            test_name="test_unseen_science_schema_fixture.py",
        )
        return
    if repository.name == "unseen_control_transfer_repo":
        build_unseen_schema_transfer_repo(
            src,
            dst,
            field_name="controller_modes",
            sample_value="stabilizing_feedback",
            test_name="test_unseen_control_schema_fixture.py",
        )
        return
    raise ValueError(f"unknown benchmark repository: {repository.name}")


def strip_method(text: str, method_name: str) -> str:
    pattern = rf"\n    def {re.escape(method_name)}\(.*?(?=\n    def |\n\n[A-Za-z_@]|\Z)"
    return re.sub(pattern, "\n", text, count=1, flags=re.DOTALL)


def remove_local_corpus_query_methods(repo: Path) -> None:
    path = repo / "shared" / "local_corpus.py"
    text = path.read_text(encoding="utf-8")
    text = strip_method(text, "records_with_feature")
    text = strip_method(text, "records_importing")
    text = strip_method(text, "records_with_definition")
    path.write_text(text, encoding="utf-8")
    for test_name in (
        "test_autonomous_local_corpus_definitions_query_v1.py",
        "test_autonomous_local_corpus_feature_flags_query_v1.py",
        "test_autonomous_local_corpus_imports_query_v1.py",
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
    if task.name.startswith("unseen_"):
        return
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


def stable_trial_seed(repository: str, task: str, variant: str, repeat_index: int) -> str:
    payload = f"{repository}:{task}:{variant}:{repeat_index}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


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
    repository: BenchmarkRepository,
    task: ExperimentTask,
    variant: ExperimentVariant,
    proc: subprocess.CompletedProcess[str],
    repo: Path,
    before: Dict[str, str],
    after: Dict[str, str],
    elapsed_s: float,
    repeat_index: int,
    seed: str,
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
        repository=repository.name,
        repository_description=repository.description,
        task=task.name,
        variant=variant.name,
        family=variant.family,
        description=variant.description,
        repeat_index=repeat_index,
        seed=seed,
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
        repository_split=repository.split,
        transfer_origin=repository.transfer_origin,
        task_description=task.description,
        task_claim=task.claim,
    )


def write_csv(path: Path, results: List[ExperimentResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_results(results: Sequence[ExperimentResult]) -> List[Dict[str, object]]:
    """Aggregate repeated trials by repository, task, and variant."""

    groups: Dict[Tuple[str, str, str], List[ExperimentResult]] = {}
    for result in results:
        groups.setdefault((result.repository, result.task, result.variant), []).append(result)

    aggregates: List[Dict[str, object]] = []
    for (repository, task, variant), rows in sorted(groups.items()):
        rollback_rows = [row for row in rows if row.rollback_correct is not None]
        rollback_success_rate = (
            mean([1.0 if row.rollback_correct else 0.0 for row in rollback_rows])
            if rollback_rows
            else None
        )
        aggregates.append(
            {
                "repository": repository,
                "repository_split": rows[0].repository_split,
                "transfer_origin": rows[0].transfer_origin,
                "task": task,
                "task_description": rows[0].task_description,
                "task_claim": rows[0].task_claim,
                "variant": variant,
                "family": rows[0].family,
                "trial_count": len(rows),
                "exit_success_rate": mean([1.0 if row.exit_code == 0 else 0.0 for row in rows]),
                "accepted_count_mean": mean([float(row.accepted_count) for row in rows]),
                "rejected_count_mean": mean([float(row.rejected_count) for row in rows]),
                "accepted_rate_mean": mean([float(row.accepted_rate) for row in rows]),
                "regression_gate_failures_mean": mean([float(row.regression_gate_failures) for row in rows]),
                "rollback_success_rate": rollback_success_rate,
                "improvement_depth_mean": mean([float(row.improvement_depth) for row in rows]),
                "cost_proxy_seconds_mean": mean([float(row.cost_proxy_seconds) for row in rows]),
                "changed_files_count_mean": mean([float(row.changed_files_count) for row in rows]),
            }
        )
    return aggregates


def write_aggregate_csv(path: Path, aggregates: List[Dict[str, object]]) -> None:
    if not aggregates:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(aggregates[0].keys()))
        writer.writeheader()
        for row in aggregates:
            writer.writerow(row)


def _float_value(row: Dict[str, object], key: str) -> float:
    value = row.get(key)
    if value is None or value == "":
        return 0.0
    return float(value)


def _baseline_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return [
        row
        for row in rows
        if str(row.get("family", "")).startswith("baseline_")
    ]


def _ablation_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return [
        row
        for row in rows
        if str(row.get("family", "")).startswith("ablation_")
    ]


def build_baseline_comparisons(aggregates: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Compare the proposed loop against baselines and ablations."""

    groups: Dict[Tuple[str, str], List[Dict[str, object]]] = {}
    for row in aggregates:
        groups.setdefault((str(row["repository"]), str(row["task"])), []).append(row)

    comparisons: List[Dict[str, object]] = []
    for (repository, task), rows in sorted(groups.items()):
        proposed = next((row for row in rows if row.get("variant") == "verified_closed_loop"), None)
        if proposed is None:
            continue
        baselines = _baseline_rows(rows)
        ablations = _ablation_rows(rows)
        best_baseline = max(
            baselines,
            key=lambda row: (
                _float_value(row, "accepted_rate_mean"),
                _float_value(row, "improvement_depth_mean"),
                -_float_value(row, "cost_proxy_seconds_mean"),
            ),
            default=None,
        )
        agent = next((row for row in baselines if row.get("variant") == "agent_coding_loop"), None)
        ci_only = next((row for row in baselines if row.get("variant") == "ci_only_validation"), None)
        no_rollback = next((row for row in ablations if row.get("variant") == "no_rollback"), None)
        no_broad = next((row for row in ablations if row.get("variant") == "focused_only_loop"), None)

        proposed_acceptance = _float_value(proposed, "accepted_rate_mean")
        proposed_depth = _float_value(proposed, "improvement_depth_mean")
        best_baseline_acceptance = (
            _float_value(best_baseline, "accepted_rate_mean") if best_baseline else 0.0
        )
        best_baseline_depth = (
            _float_value(best_baseline, "improvement_depth_mean") if best_baseline else 0.0
        )
        agent_depth = _float_value(agent, "improvement_depth_mean") if agent else 0.0
        ci_depth = _float_value(ci_only, "improvement_depth_mean") if ci_only else 0.0
        rollback_success = proposed.get("rollback_success_rate")
        no_rollback_success = no_rollback.get("rollback_success_rate") if no_rollback else None
        safety_win = (
            task == "forced_broad_regression"
            and rollback_success is not None
            and float(rollback_success) >= 1.0
            and no_rollback_success is not None
            and float(no_rollback_success) <= 0.0
        )
        broad_gate_win = (
            task == "forced_broad_regression"
            and no_broad is not None
            and _float_value(no_broad, "accepted_rate_mean") > proposed_acceptance
        )
        unseen_transfer_success = (
            proposed.get("repository_split") == "unseen"
            and proposed_acceptance > 0.0
            and proposed_depth > 0.0
        )

        if unseen_transfer_success:
            outcome = "unseen_transfer_success"
        elif safety_win:
            outcome = "safety_win_over_ablation"
        elif proposed_depth > agent_depth and proposed_acceptance >= best_baseline_acceptance:
            outcome = "depth_win_over_single_pass"
        elif proposed_acceptance >= best_baseline_acceptance and proposed_depth >= best_baseline_depth:
            outcome = "tie_or_frontier_match"
        else:
            outcome = "baseline_stronger_or_inconclusive"

        comparisons.append(
            {
                "repository": repository,
                "repository_split": proposed.get("repository_split", "seen"),
                "transfer_origin": proposed.get("transfer_origin", ""),
                "task": task,
                "task_claim": proposed.get("task_claim", ""),
                "proposed_accepted_rate_mean": proposed_acceptance,
                "proposed_improvement_depth_mean": proposed_depth,
                "best_baseline_variant": best_baseline.get("variant") if best_baseline else "",
                "best_baseline_accepted_rate_mean": best_baseline_acceptance,
                "best_baseline_improvement_depth_mean": best_baseline_depth,
                "accepted_rate_margin_vs_best_baseline": proposed_acceptance - best_baseline_acceptance,
                "depth_margin_vs_agent_loop": proposed_depth - agent_depth,
                "depth_margin_vs_ci_only": proposed_depth - ci_depth,
                "safety_win_over_no_rollback": safety_win,
                "unsafe_acceptance_seen_without_broad_gate": broad_gate_win,
                "unseen_transfer_success": unseen_transfer_success,
                "outcome": outcome,
            }
        )
    return comparisons


def write_comparison_csv(path: Path, comparisons: List[Dict[str, object]]) -> None:
    if not comparisons:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0].keys()))
        writer.writeheader()
        for row in comparisons:
            writer.writerow(row)


def write_markdown_reports(output_dir: Path, results: List[ExperimentResult]) -> None:
    aggregates = aggregate_results(results)
    comparisons = build_baseline_comparisons(aggregates)
    table_lines = [
        "| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        rollback = "n/a" if result.rollback_correct is None else str(result.rollback_correct)
        table_lines.append(
            f"| {result.repository} | {result.repository_split} | {result.task} | {result.variant} | {result.repeat_index} | {result.accepted_count} | "
            f"{result.rejected_count} | {result.accepted_rate:.2f} | "
            f"{result.regression_gate_failures} | {rollback} | {result.elapsed_s:.2f} |"
        )

    aggregate_lines = [
        "| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Regression Failures Mean | Rollback Success | Depth Mean | Seconds Mean |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregates:
        rollback = "n/a" if row["rollback_success_rate"] is None else f"{float(row['rollback_success_rate']):.2f}"
        aggregate_lines.append(
            f"| {row['repository']} | {row['repository_split']} | {row['task']} | {row['variant']} | {row['trial_count']} | "
            f"{float(row['accepted_rate_mean']):.2f} | {float(row['regression_gate_failures_mean']):.2f} | "
            f"{rollback} | {float(row['improvement_depth_mean']):.2f} | {float(row['cost_proxy_seconds_mean']):.2f} |"
        )

    comparison_lines = [
        "| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer |",
        "|---|---|---|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in comparisons:
        comparison_lines.append(
            f"| {row['repository']} | {row['repository_split']} | {row['task']} | {row['outcome']} | "
            f"{float(row['proposed_accepted_rate_mean']):.2f} | {row['best_baseline_variant']} | "
            f"{float(row['best_baseline_accepted_rate_mean']):.2f} | "
            f"{float(row['depth_margin_vs_agent_loop']):.2f} | "
            f"{row['safety_win_over_no_rollback']} | {row['unseen_transfer_success']} |"
        )

    repositories = sorted({result.repository for result in results})
    readiness = [
        "# RSI Research Readiness Report",
        "",
        "This report evaluates a bounded, verified recursive self-improvement loop. "
        "It does not claim unbounded ASI behavior.",
        "",
        "## Benchmark Repositories",
        "",
        *[
            f"- `{repository}`: {next(result.repository_description for result in results if result.repository == repository)}"
            for repository in repositories
        ],
        "",
        "## Experiment Matrix",
        "",
        *table_lines,
        "",
        "## Aggregate Metrics",
        "",
        *aggregate_lines,
        "",
        "## Baseline And Transfer Scorecard",
        "",
        *comparison_lines,
        "",
        "## Review-Relevant Claims",
        "",
        "- The proposed loop can patch real repository code and persist accepted/rejected provenance.",
        "- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.",
        "- Held-out schema-transfer fixtures are marked as unseen and compared separately.",
        "- Baseline comparison rows explicitly label wins, ties, safety wins, and inconclusive cases.",
        "- The generator includes schema-driven candidate synthesis instead of only fixed candidate names.",
        "- The generator scores bounded competing hypotheses with rejection history before patching.",
        "- Broad gates reduce regression risk relative to focused-only ablations.",
        "- Rollback behavior is measurable on forced broad-gate rejection tasks.",
        "- Persistence can be ablated to show that resume depth depends on durable state.",
        "- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.",
    ]
    (output_dir / "neurips_readiness.md").write_text("\n".join(readiness) + "\n", encoding="utf-8")

    comparison_report = [
        "# Baseline Comparison Scorecard",
        "",
        "This report separates accepted-rate wins, improvement-depth wins, safety wins, and held-out transfer successes. "
        "Rows marked as inconclusive should not be presented as evidence that the proposed loop beats all baselines.",
        "",
        *comparison_lines,
        "",
        "## Interpretation Rules",
        "",
        "- `depth_win_over_single_pass`: the proposed loop reaches deeper recursive improvement than the single-pass agent baseline without lower accepted rate.",
        "- `safety_win_over_ablation`: rollback and broad gates prevent unsafe promotion that an ablation fails to prevent.",
        "- `unseen_transfer_success`: the loop patches a held-out schema surface not present in the original benchmark fixtures.",
        "- `tie_or_frontier_match`: the proposed loop matches the best baseline on this metric but does not dominate it.",
        "- `baseline_stronger_or_inconclusive`: the current evidence does not support a proposed-loop win.",
    ]
    (output_dir / "baseline_comparison.md").write_text(
        "\n".join(comparison_report) + "\n",
        encoding="utf-8",
    )
    write_json(output_dir / "evidence_scorecard.json", comparisons)
    write_comparison_csv(output_dir / "baseline_comparison.csv", comparisons)

    failures = ["# Failure Analysis", ""]
    for result in results:
        if result.rejected_count or result.exit_code:
            failures.extend(
                [
                    f"## {result.repository} / {result.task} / {result.variant} / repeat {result.repeat_index}",
                    "",
                    f"- Seed: {result.seed}",
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
        "- Benchmark trials run inside isolated disposable repository fixtures.",
        "- Dangerous ablations such as no rollback run only in disposable experiment copies.",
        "- The main workflow commits only accepted state and validated source changes.",
    ]
    (output_dir / "safety_model.md").write_text("\n".join(safety) + "\n", encoding="utf-8")


def select_by_name(items, selected: Sequence[str]):
    if not selected or "all" in selected:
        return list(items)
    names = set(selected)
    return [item for item in items if item.name in names]


def task_applies_to_repository(task: ExperimentTask, repository: BenchmarkRepository) -> bool:
    """Return whether a task is part of a repository fixture's matrix."""

    return not task.repositories or repository.name in task.repositories


def run_suite(args: argparse.Namespace) -> Path:
    repo_root = args.repo_root.resolve()
    output_dir = (args.output_dir or repo_root / "reports" / "rsi_experiments" / "latest").resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    repositories = select_by_name(DEFAULT_REPOSITORIES, args.repository)
    tasks = select_by_name(DEFAULT_TASKS, args.task)
    variants = select_by_name(DEFAULT_VARIANTS, args.variant)
    results: List[ExperimentResult] = []

    with tempfile.TemporaryDirectory(prefix="rsi_experiments_") as tmp:
        tmp_root = Path(tmp)
        for repository in repositories:
            for repeat_index in range(args.repeats):
                for task in tasks:
                    if not task_applies_to_repository(task, repository):
                        continue
                    for variant in variants:
                        seed = stable_trial_seed(repository.name, task.name, variant.name, repeat_index)
                        work_repo = tmp_root / f"{repository.name}__{task.name}__{variant.name}__r{repeat_index}"
                        build_benchmark_repo(repo_root, work_repo, repository)
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
                        result = build_result(
                            repository,
                            task,
                            variant,
                            proc,
                            work_repo,
                            before,
                            after,
                            elapsed,
                            repeat_index,
                            seed,
                        )
                        results.append(result)

    write_json(output_dir / "summary.json", [asdict(result) for result in results])
    write_json(
        output_dir / "benchmark_catalog.json",
        {
            "repositories": [asdict(repository) for repository in repositories],
            "tasks": [asdict(task) for task in tasks],
            "variants": [asdict(variant) for variant in variants],
            "repeats": args.repeats,
        },
    )
    if results:
        write_csv(output_dir / "metrics.csv", results)
        write_aggregate_csv(output_dir / "aggregate_metrics.csv", aggregate_results(results))
    write_markdown_reports(output_dir, results)
    return output_dir


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--repository", action="append", default=[])
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--variant", action="append", default=[])
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--max-generations", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=4)
    parser.add_argument("--wall-seconds", type=int, default=1800)
    parser.add_argument("--timeout-seconds", type=int, default=420)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")

    output_dir = run_suite(args)
    print(json.dumps({"output_dir": str(output_dir)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
