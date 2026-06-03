"""Cloud experiment suite for the verified closed RSI loop.

The suite runs only in disposable repository copies. It is designed to produce
research artifacts for review: baseline comparisons, ablations, metrics,
failure analysis, and an explicit safety model.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import random
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

FULL_TEST_COMMAND: Tuple[str, ...] = ("python", "-m", "pytest", "-q")


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
    exploration_policy: str = "conservative"
    exploration_depth: int = 0
    full_test_required: bool = True


@dataclass(frozen=True)
class ExperimentTask:
    """One repository/task state to evaluate."""

    name: str
    description: str
    repositories: Tuple[str, ...] = ()
    claim: str = ""


@dataclass(frozen=True)
class ExternalIssueFixtureSpec:
    """One fixture derived from actual external GitHub issue metadata."""

    repository_name: str
    task_name: str
    source_repository: str
    field_name: str
    value_source: str
    fallback_value: str
    description: str


@dataclass(frozen=True)
class ExternalCodeFixtureSpec:
    """One fixture derived from actual external source and failure excerpts."""

    repository_name: str
    task_name: str
    source_repository: str
    field_name: str
    fallback_value: str
    description: str


@dataclass(frozen=True)
class CapabilityFixtureSpec:
    """One executable capability benchmark fixture."""

    repository_name: str
    task_name: str
    family: str
    operator: str
    public_assertion: str
    hidden_assertion: str
    description: str


@dataclass(frozen=True)
class CompositeSchemaFixtureSpec:
    """One multi-field schema-transfer fixture requiring a general patch."""

    repository_name: str
    task_name: str
    fields: Tuple[Tuple[str, str], ...]
    split: str
    transfer_origin: str
    description: str
    claim: str


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
    capability_delta_score: float = 0.0
    solved_new_tasks: int = 0
    hidden_transfer: int = 0
    operator_reuse: int = 0
    failure_residue_count: int = 0
    quarantine_exploration_count: int = 0
    quarantine_failure_residue_count: int = 0
    full_test_command: str = " ".join(FULL_TEST_COMMAND)
    full_test_exit_code: Optional[int] = None
    full_test_required: bool = True
    paired_seed: str = ""
    provenance_hash: str = ""
    held_out_input_set: str = ""
    comparable_to_verified_config: bool = True


EXTERNAL_ISSUE_FIXTURES: Tuple[ExternalIssueFixtureSpec, ...] = (
    ExternalIssueFixtureSpec(
        repository_name="external_requests_issue_transfer_repo",
        task_name="external_requests_issue_labels_query",
        source_repository="psf/requests",
        field_name="external_issue_labels",
        value_source="labels",
        fallback_value="bug",
        description="Actual psf/requests issue-label fixture extracted from public GitHub issue metadata.",
    ),
    ExternalIssueFixtureSpec(
        repository_name="external_hypothesis_issue_transfer_repo",
        task_name="external_hypothesis_patch_signals_query",
        source_repository="hypothesisworks/hypothesis",
        field_name="external_patch_signals",
        value_source="title_terms",
        fallback_value="patch",
        description="Actual Hypothesis issue-title fixture extracted from public GitHub issue metadata.",
    ),
    ExternalIssueFixtureSpec(
        repository_name="external_pandas_issue_transfer_repo",
        task_name="external_pandas_failure_terms_query",
        source_repository="pandas-dev/pandas",
        field_name="external_failure_terms",
        value_source="title_terms",
        fallback_value="dtype",
        description="Actual pandas issue-title fixture extracted from public GitHub issue metadata.",
    ),
    ExternalIssueFixtureSpec(
        repository_name="external_dask_issue_transfer_repo",
        task_name="external_dask_array_labels_query",
        source_repository="dask/dask",
        field_name="external_array_labels",
        value_source="labels",
        fallback_value="array",
        description="Actual dask issue-label fixture extracted from public GitHub issue metadata.",
    ),
)


EXTERNAL_CODE_FIXTURES: Tuple[ExternalCodeFixtureSpec, ...] = (
    ExternalCodeFixtureSpec(
        repository_name="external_requests_code_transfer_repo",
        task_name="external_requests_code_failure_fixture_query",
        source_repository="psf/requests",
        field_name="external_requests_code_signals",
        fallback_value="response_content",
        description="Actual psf/requests source-code and issue-failure sandbox fixture.",
    ),
    ExternalCodeFixtureSpec(
        repository_name="external_hypothesis_code_transfer_repo",
        task_name="external_hypothesis_code_failure_fixture_query",
        source_repository="hypothesisworks/hypothesis",
        field_name="external_hypothesis_code_signals",
        fallback_value="pytest_patch",
        description="Actual Hypothesis source-code and issue-failure sandbox fixture.",
    ),
    ExternalCodeFixtureSpec(
        repository_name="external_pandas_code_transfer_repo",
        task_name="external_pandas_code_failure_fixture_query",
        source_repository="pandas-dev/pandas",
        field_name="external_pandas_code_signals",
        fallback_value="series_map_dtype",
        description="Actual pandas source-code and issue-failure sandbox fixture.",
    ),
    ExternalCodeFixtureSpec(
        repository_name="external_dask_code_transfer_repo",
        task_name="external_dask_code_failure_fixture_query",
        source_repository="dask/dask",
        field_name="external_dask_code_signals",
        fallback_value="array_cumsum",
        description="Actual dask source-code and issue-failure sandbox fixture.",
    ),
)


CAPABILITY_FIXTURES: Tuple[CapabilityFixtureSpec, ...] = (
    CapabilityFixtureSpec(
        repository_name="capability_algorithm_synthesis_repo",
        task_name="capability_algorithm_synthesis",
        family="algorithm_synthesis",
        operator="run_length_encode",
        public_assertion="assert run_length_encode((1, 1, 2, 2, 2, 3)) == ((1, 2), (2, 3), (3, 1))",
        hidden_assertion="assert run_length_encode(('a', 'a', 'b', 'a')) == (('a', 2), ('b', 1), ('a', 1))",
        description="Executable algorithm-synthesis fixture requiring a reusable run-length encoder primitive.",
    ),
    CapabilityFixtureSpec(
        repository_name="capability_symbolic_reasoning_repo",
        task_name="capability_symbolic_reasoning",
        family="symbolic_reasoning",
        operator="infer_linear_rule",
        public_assertion="assert infer_linear_rule((2, 5, 8, 11)) == {'start': 2, 'step': 3, 'next': 14}",
        hidden_assertion="assert infer_linear_rule((-3, -1, 1)) == {'start': -3, 'step': 2, 'next': 3}",
        description="Executable symbolic-reasoning fixture requiring linear rule inference.",
    ),
    CapabilityFixtureSpec(
        repository_name="capability_grid_transformation_repo",
        task_name="capability_grid_transformation",
        family="grid_transformation",
        operator="rotate_grid_clockwise",
        public_assertion="assert rotate_grid_clockwise(((1, 2, 3), (4, 5, 6))) == ((4, 1), (5, 2), (6, 3))",
        hidden_assertion="assert rotate_grid_clockwise((('x',), ('y',), ('z',))) == (('z', 'y', 'x'),)",
        description="Executable grid-transformation fixture requiring ARC-like rotation.",
    ),
    CapabilityFixtureSpec(
        repository_name="capability_bug_repair_repo",
        task_name="capability_bug_repair",
        family="bug_repair",
        operator="dedupe_preserve_order",
        public_assertion="assert dedupe_preserve_order(('b', 'a', 'b', 'c', 'a')) == ('b', 'a', 'c')",
        hidden_assertion="assert dedupe_preserve_order((3, 3, 2, 3, 1, 2)) == (3, 2, 1)",
        description="Executable bug-repair fixture requiring a corrected stable de-duplication primitive.",
    ),
    CapabilityFixtureSpec(
        repository_name="capability_planning_state_transition_repo",
        task_name="capability_planning_state_transition",
        family="planning_state_transition",
        operator="apply_grid_action",
        public_assertion="assert apply_grid_action({'x': 0, 'y': 0}, 'east') == {'x': 1, 'y': 0}",
        hidden_assertion="assert apply_grid_action({'x': 2, 'y': -1}, 'north') == {'x': 2, 'y': 0}",
        description="Executable planning fixture requiring deterministic state transition updates.",
    ),
)


COMPOSITE_SCHEMA_FIXTURES: Tuple[CompositeSchemaFixtureSpec, ...] = (
    CompositeSchemaFixtureSpec(
        repository_name="composite_unseen_schema_transfer_repo",
        task_name="composite_unseen_schema_transfer",
        fields=(
            ("static_roles", "moderator"),
            ("threat_labels", "sandbox_escape"),
            ("evidence_sources", "ablation_table"),
            ("controller_modes", "stabilizing_feedback"),
        ),
        split="unseen",
        transfer_origin="compact_kernel_repo",
        description=(
            "Composite held-out schema fixture with four tuple-valued record fields absent "
            "from the original benchmark repositories."
        ),
        claim=(
            "Unseen transfer succeeds only when one general schema patch repairs all held-out "
            "tuple-membership query surfaces under full pytest."
        ),
    ),
    CompositeSchemaFixtureSpec(
        repository_name="composite_external_issue_transfer_repo",
        task_name="composite_external_issue_transfer",
        fields=tuple(
            (spec.field_name, spec.fallback_value)
            for spec in EXTERNAL_ISSUE_FIXTURES
        ),
        split="external_unseen",
        transfer_origin="psf/requests,hypothesisworks/hypothesis,pandas-dev/pandas,dask/dask",
        description=(
            "Composite external issue fixture whose schema fields are derived from real "
            "GitHub issue metadata across the allowlisted repositories."
        ),
        claim=(
            "External transfer succeeds only when one general schema patch repairs all "
            "issue-metadata-derived query surfaces under full pytest."
        ),
    ),
)


DEFAULT_REPOSITORIES = (
    BenchmarkRepository(
        name="omega_full_repo",
        description="Full OMEGA-THDSE checkout with root tests and THDSE core gates available.",
    ),
    BenchmarkRepository(
        name="compact_kernel_repo",
        description="Full-test-capable disposable repository fixture used for compact task labels.",
    ),
    *(
        BenchmarkRepository(
            name=spec.repository_name,
            description=spec.description,
            split="capability_unseen",
            transfer_origin=spec.family,
        )
        for spec in CAPABILITY_FIXTURES
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
    *(
        BenchmarkRepository(
            name=spec.repository_name,
            description=spec.description,
            split="external_unseen",
            transfer_origin=spec.source_repository,
        )
        for spec in EXTERNAL_ISSUE_FIXTURES
    ),
    *(
        BenchmarkRepository(
            name=spec.repository_name,
            description=spec.description,
            split="external_code_unseen",
            transfer_origin=spec.source_repository,
        )
        for spec in EXTERNAL_CODE_FIXTURES
    ),
    *(
        BenchmarkRepository(
            name=spec.repository_name,
            description=spec.description,
            split=spec.split,
            transfer_origin=spec.transfer_origin,
        )
        for spec in COMPOSITE_SCHEMA_FIXTURES
    ),
)


DEFAULT_TASKS = (
    ExperimentTask(
        name="local_corpus_queries_clean",
        description="Remove accepted local corpus query APIs and measure whether the loop recreates them under full pytest.",
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
    *(
        ExperimentTask(
            name=spec.task_name,
            description=f"Measure executable {spec.family} repair with public and hidden counterexamples.",
            repositories=(spec.repository_name,),
            claim=(
                f"Capability transfer succeeds when the loop synthesizes the reusable "
                f"{spec.operator} primitive for {spec.family}."
            ),
        )
        for spec in CAPABILITY_FIXTURES
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
    *(
        ExperimentTask(
            name=spec.task_name,
            description=f"Measure transfer on a fixture extracted from {spec.source_repository} issue metadata.",
            repositories=(spec.repository_name,),
            claim=(
                f"External transfer succeeds when the loop patches a query API for "
                f"{spec.field_name} extracted from {spec.source_repository} issue metadata."
            ),
        )
        for spec in EXTERNAL_ISSUE_FIXTURES
    ),
    *(
        ExperimentTask(
            name=spec.task_name,
            description=(
                f"Measure transfer on a sandbox fixture extracted from actual "
                f"{spec.source_repository} source snippets and issue failure excerpts."
            ),
            repositories=(spec.repository_name,),
            claim=(
                f"External code transfer succeeds when the loop repairs a local executable "
                f"failure target derived from bounded {spec.source_repository} source and failure snippets."
            ),
        )
        for spec in EXTERNAL_CODE_FIXTURES
    ),
    *(
        ExperimentTask(
            name=spec.task_name,
            description=spec.description,
            repositories=(spec.repository_name,),
            claim=spec.claim,
        )
        for spec in COMPOSITE_SCHEMA_FIXTURES
    ),
)


DEFAULT_VARIANTS = (
    ExperimentVariant(
        name="verified_closed_loop",
        family="proposed",
        description="Full loop: candidate generation, patching, rollback, persistence, root broad gate, and THDSE core gate.",
        exploration_policy="recursive_quarantine",
        exploration_depth=2,
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
        description="Baseline: retry candidate repair loop with the same safety gates but without recursive quarantine search or persistent self-policy depth.",
        persistence=False,
        max_generations_override=3,
        max_candidates_override=3,
    ),
    ExperimentVariant(
        name="full_suite_no_broad_gate",
        family="ablation_no_broad_gate",
        description="Ablation: no extra broad gate; final full pytest remains the promotion gate.",
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


def copy_optional_file(src: Path, dst: Path, relative_path: str) -> None:
    source = src / relative_path
    if not source.exists():
        return
    target = dst / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_compact_kernel_repo(src: Path, dst: Path) -> None:
    """Build a full-test-capable disposable repository fixture."""

    copy_repo(src, dst)


def build_minimal_transfer_repo(src: Path, dst: Path) -> None:
    """Build a small full-test-capable fixture for powered transfer cells."""

    dst.mkdir(parents=True, exist_ok=True)
    copy_required_file(src, dst, "scripts/closed_recursive_self_improvement_loop.py")
    copy_required_file(src, dst, "shared/local_corpus.py")
    for relative_path in (
        "scripts/rsi_policy_registry.py",
        "shared/__init__.py",
        "shared/capability_benchmarks.py",
        "shared/capability_primitives.py",
        "conftest.py",
        "pytest.ini",
    ):
        copy_optional_file(src, dst, relative_path)


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
    fixture_test = dst / "tests" / test_name
    fixture_test.parent.mkdir(parents=True, exist_ok=True)
    fixture_test.write_text(
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


def composite_schema_fixture_for_repository(repository_name: str) -> Optional[CompositeSchemaFixtureSpec]:
    """Return a composite schema fixture spec for a benchmark repository."""

    return next(
        (spec for spec in COMPOSITE_SCHEMA_FIXTURES if spec.repository_name == repository_name),
        None,
    )


def build_composite_schema_transfer_repo(
    src: Path,
    dst: Path,
    spec: CompositeSchemaFixtureSpec,
) -> None:
    """Build a multi-field transfer fixture that requires one general schema repair."""

    build_minimal_transfer_repo(src, dst)
    local_corpus = dst / "shared" / "local_corpus.py"
    text = local_corpus.read_text(encoding="utf-8")
    marker = "    feature_flags: Tuple[str, ...] = ()\n"
    declarations = []
    for field_name, _sample_value in spec.fields:
        declaration = f"    {field_name}: Tuple[str, ...] = ()\n"
        if declaration not in text:
            declarations.append(declaration)
    if declarations:
        text = text.replace(marker, marker + "".join(declarations), 1)
    local_corpus.write_text(text, encoding="utf-8")

    record_blocks = []
    assertion_lines = []
    for index, (field_name, sample_value) in enumerate(spec.fields):
        method_name = (
            "records_with_" + field_name[:-1]
            if field_name.endswith("s") and not field_name.endswith("ies")
            else "records_with_" + field_name
        )
        if field_name.endswith("ies"):
            method_name = "records_with_" + field_name[:-3] + "y"
        record_blocks.append(
            "\n".join(
                [
                    "        LocalPythonFileRecord(",
                    f"            path='transfer_{index}.py',",
                    f"            sha256='{index}',",
                    "            size_bytes=1,",
                    "            line_count=1,",
                    "            syntax_ok=True,",
                    f"            {field_name}=('{sample_value}',),",
                    "        ),",
                ]
            )
        )
        assertion_lines.append(
            f"    assert tuple(record.path for record in index.{method_name}('{sample_value}')) == ('transfer_{index}.py',)"
        )

    test_path = dst / "tests" / f"test_{spec.repository_name}.py"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(
        "from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord\n\n\n"
        f"def test_{spec.task_name}_requires_all_transfer_queries():\n"
        "    records = (\n"
        f"{chr(10).join(record_blocks)}\n"
        "    )\n"
        "    index = LocalCorpusIndex(\n"
        "        summary=LocalCorpusSummary(\n"
        "            file_count=len(records),\n"
        "            syntax_ok_count=len(records),\n"
        "            syntax_error_count=0,\n"
        "            unique_sha256_count=len(records),\n"
        "            duplicate_file_instances=0,\n"
        "            feature_counts={},\n"
        "            import_edge_count=0,\n"
        "            definition_count=0,\n"
        "        ),\n"
        "        records=records,\n"
        "        import_edges=(),\n"
        "    )\n\n"
        f"{chr(10).join(assertion_lines)}\n",
        encoding="utf-8",
    )
    write_json(
        dst / "schema_transfer_manifest.json",
        {
            "fixture_kind": "composite_schema_transfer",
            "repository": spec.repository_name,
            "task": spec.task_name,
            "split": spec.split,
            "transfer_origin": spec.transfer_origin,
            "fields": [
                {"field_name": field_name, "sample_value": sample_value}
                for field_name, sample_value in spec.fields
            ],
            "safety_controls": [
                "held_out_schema_fields",
                "single_general_patch_required",
                "seeded_hidden_schema_evaluator",
                "full_pytest_required",
            ],
        },
    )


def strip_top_level_function(text: str, function_name: str) -> str:
    """Remove one top-level function from a source string."""

    pattern = rf"\ndef {re.escape(function_name)}\(.*?(?=\n\ndef |\n\n[A-Z_][A-Z0-9_]*\s*=|\Z)"
    prefixed = "\n" + text
    rewritten = re.sub(pattern, "\n", prefixed, count=1, flags=re.DOTALL)
    return rewritten[1:]


def top_level_function_source(text: str, function_name: str) -> str:
    """Return exact source text for one top-level function."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""
    lines = text.splitlines()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            end_lineno = getattr(node, "end_lineno", None)
            if end_lineno is None:
                return ""
            return "\n".join(lines[node.lineno - 1 : end_lineno]).rstrip() + "\n"
    return ""


def capability_fixture_for_repository(repository_name: str) -> Optional[CapabilityFixtureSpec]:
    """Return the capability fixture spec for a benchmark repository."""

    return next(
        (spec for spec in CAPABILITY_FIXTURES if spec.repository_name == repository_name),
        None,
    )


def build_capability_benchmark_repo(
    src: Path,
    dst: Path,
    spec: CapabilityFixtureSpec,
) -> None:
    """Build an executable capability fixture with one missing primitive."""

    build_compact_kernel_repo(src, dst)
    primitives = dst / "shared" / "capability_primitives.py"
    if not primitives.exists():
        primitives.write_text('"""Fixture-local capability primitives."""\n', encoding="utf-8")
    original_text = primitives.read_text(encoding="utf-8")
    held_out_reference = top_level_function_source(original_text, spec.operator)
    text = strip_top_level_function(original_text, spec.operator)
    primitives.write_text(text, encoding="utf-8")
    test_path = dst / "tests" / f"test_capability_{spec.family}_fixture.py"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    dynamic_seed = f"{spec.task_name}:dynamic_hidden_v1"
    test_path.write_text(
        f"from shared.capability_benchmarks import capability_cases_for_seed, evaluate_capability_cases\n"
        f"from shared.capability_primitives import {spec.operator}\n\n\n"
        f"def test_{spec.operator}_public_case():\n"
        f"    {spec.public_assertion}\n\n\n"
        f"def test_{spec.operator}_hidden_transfer_case():\n"
        f"    {spec.hidden_assertion}\n\n\n"
        f"def test_{spec.operator}_dynamic_hidden_cases():\n"
        f"    cases = tuple(\n"
        f"        case\n"
        f"        for case in capability_cases_for_seed('{dynamic_seed}')\n"
        f"        if case.family == '{spec.family}'\n"
        f"    )\n"
        f"    evaluations = evaluate_capability_cases({{'{spec.operator}': {spec.operator}}}, cases)\n"
        f"    assert cases\n"
        f"    assert all(result.solved for result in evaluations)\n",
        encoding="utf-8",
    )
    write_json(
        dst / "capability_fixture_metadata.json",
        {
            "fixture_kind": "capability_operator_repair",
            "family": spec.family,
            "operator": spec.operator,
            "held_out_reference_sha256": hashlib.sha256(held_out_reference.encode("utf-8")).hexdigest()
            if held_out_reference
            else "",
            "task_name": spec.task_name,
            "safety_controls": [
                "local_fixture_only",
                "public_counterexample",
                "hidden_transfer_counterexample",
                "seeded_dynamic_hidden_counterexamples",
                "held_out_reference_hash_rejection",
                "no_external_code_execution",
            ],
            "dynamic_seed": dynamic_seed,
        },
    )


def external_issue_fixture_for_repository(repository_name: str) -> Optional[ExternalIssueFixtureSpec]:
    """Return the external issue fixture spec for a benchmark repository."""

    return next(
        (spec for spec in EXTERNAL_ISSUE_FIXTURES if spec.repository_name == repository_name),
        None,
    )


def external_code_fixture_for_repository(repository_name: str) -> Optional[ExternalCodeFixtureSpec]:
    """Return the external code fixture spec for a benchmark repository."""

    return next(
        (spec for spec in EXTERNAL_CODE_FIXTURES if spec.repository_name == repository_name),
        None,
    )


def normalize_fixture_token(value: object, *, fallback: str) -> str:
    """Normalize external issue text into a deterministic fixture token."""

    text = str(value or "").lower()
    compact = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not compact:
        compact = fallback
    if not compact:
        return ""
    if compact[0].isdigit():
        compact = f"x_{compact}"
    return compact[:48]


def extract_title_terms(text: str, *, fallback: str) -> Tuple[str, ...]:
    """Extract compact title/body terms from an external issue record."""

    stopwords = {
        "and",
        "are",
        "bug",
        "for",
        "from",
        "into",
        "the",
        "this",
        "when",
        "with",
    }
    terms: List[str] = []
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text.lower()):
        token = normalize_fixture_token(raw, fallback=fallback)
        if token in stopwords or token in terms:
            continue
        terms.append(token)
        if len(terms) >= 5:
            break
    return tuple(terms or (fallback,))


def load_external_grounding_tasks(repo_root: Path) -> Tuple[Dict[str, object], ...]:
    """Load actual external grounding tasks if they are available."""

    transfer_path = (
        repo_root
        / "reports"
        / "external_grounding"
        / "external_transfer"
        / "latest"
        / "external_grounding_tasks.json"
    )
    path = (
        transfer_path
        if transfer_path.exists()
        else repo_root / "reports" / "external_grounding" / "latest" / "external_grounding_tasks.json"
    )
    payload = read_json(path, {})
    tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
    return tuple(task for task in tasks if isinstance(task, dict))


def load_external_code_sandbox_fixtures(repo_root: Path) -> Tuple[Dict[str, object], ...]:
    """Load bounded external code sandbox fixtures if they are available."""

    path = (
        repo_root
        / "reports"
        / "external_code_fixtures"
        / "latest"
        / "external_code_sandbox_fixtures.json"
    )
    payload = read_json(path, {})
    fixtures = payload.get("fixtures", []) if isinstance(payload, dict) else []
    return tuple(fixture for fixture in fixtures if isinstance(fixture, dict))


def select_external_grounding_task(
    repo_root: Path,
    spec: ExternalIssueFixtureSpec,
) -> Dict[str, object]:
    """Select the highest-scoring external issue task for a fixture spec."""

    matches = [
        task
        for task in load_external_grounding_tasks(repo_root)
        if task.get("repository") == spec.source_repository
        and task.get("task_kind") != "external_grounding_error"
    ]
    if not matches:
        return {
            "repository": spec.source_repository,
            "task_id": f"github:{spec.source_repository}:fallback",
            "title": "Fallback external issue fixture",
            "body_excerpt": "",
            "labels": (spec.fallback_value,),
            "task_kind": "external_fixture_fallback",
            "url": f"https://github.com/{spec.source_repository}/issues",
            "grounding_score": 0.0,
        }
    return max(
        matches,
        key=lambda task: (
            float(task.get("grounding_score", 0.0) or 0.0),
            str(task.get("task_id", "")),
        ),
    )


def external_issue_values(task: Dict[str, object], spec: ExternalIssueFixtureSpec) -> Tuple[str, ...]:
    """Extract fixture values from an actual external issue task."""

    fallback = normalize_fixture_token(spec.fallback_value, fallback="external")
    if spec.value_source == "labels":
        labels = task.get("labels", ())
        values = [
            normalize_fixture_token(label, fallback=fallback)
            for label in labels
            if normalize_fixture_token(label, fallback="")
        ]
        return tuple(dict.fromkeys(values)) or (fallback,)
    if spec.value_source == "title_terms":
        text = f"{task.get('title', '')} {task.get('body_excerpt', '')}"
        return extract_title_terms(text, fallback=fallback)
    if spec.value_source == "task_kind":
        return (normalize_fixture_token(task.get("task_kind", ""), fallback=fallback),)
    return (fallback,)


def select_external_code_sandbox_fixture(
    repo_root: Path,
    spec: ExternalCodeFixtureSpec,
) -> Dict[str, object]:
    """Select an external code sandbox fixture for a benchmark spec."""

    matches = [
        fixture
        for fixture in load_external_code_sandbox_fixtures(repo_root)
        if fixture.get("source_repository") == spec.source_repository
    ]
    if not matches:
        return {
            "fixture_id": f"external-code:{spec.source_repository}:fallback",
            "source_repository": spec.source_repository,
            "source_ref": "",
            "source_file_path": "",
            "source_url": f"https://github.com/{spec.source_repository}",
            "issue_task_id": f"github:{spec.source_repository}:fallback",
            "issue_url": f"https://github.com/{spec.source_repository}/issues",
            "issue_title": "Fallback external code sandbox fixture",
            "field_name": spec.field_name,
            "field_values": [spec.fallback_value],
            "source_symbols": [],
            "source_snippet_path": "",
            "failure_excerpt_path": "",
            "source_snippet_sha256": "",
            "failure_excerpt_sha256": "",
            "safety_controls": [
                "fallback_fixture",
                "no_external_code_execution",
                "bounded_fixture_values",
            ],
        }
    return max(
        matches,
        key=lambda fixture: (
            len(fixture.get("field_values", []) or []),
            str(fixture.get("source_snippet_sha256", "")),
        ),
    )


def external_code_values(
    fixture: Dict[str, object],
    spec: ExternalCodeFixtureSpec,
) -> Tuple[str, ...]:
    """Extract deterministic field values from an external code sandbox fixture."""

    fallback = normalize_fixture_token(spec.fallback_value, fallback="external_code")
    values: List[str] = []
    for bucket in (
        fixture.get("field_values", ()),
        fixture.get("source_symbols", ()),
        (fixture.get("source_file_path", ""),),
        (fixture.get("issue_title", ""),),
    ):
        if isinstance(bucket, str):
            iterable = (bucket,)
        else:
            iterable = bucket if isinstance(bucket, (list, tuple)) else ()
        for item in iterable:
            token = normalize_fixture_token(item, fallback="")
            if token and token not in values:
                values.append(token)
            if len(values) >= 8:
                return tuple(values)
    return tuple(values or (fallback,))


def build_external_issue_transfer_repo(
    src: Path,
    dst: Path,
    spec: ExternalIssueFixtureSpec,
) -> None:
    """Build a fixture whose schema is extracted from actual external issues."""

    task = select_external_grounding_task(src, spec)
    values = external_issue_values(task, spec)
    build_unseen_schema_transfer_repo(
        src,
        dst,
        field_name=spec.field_name,
        sample_value=values[0],
        test_name=f"test_{spec.repository_name}.py",
    )
    metadata = {
        "fixture_kind": "external_issue_metadata_transfer",
        "source_repository": spec.source_repository,
        "source_task_id": task.get("task_id", ""),
        "source_url": task.get("url", ""),
        "source_title": task.get("title", ""),
        "source_task_kind": task.get("task_kind", ""),
        "field_name": spec.field_name,
        "value_source": spec.value_source,
        "field_values": list(values),
        "safety_controls": [
            "metadata_only",
            "no_external_code_execution",
            "bounded_fixture_values",
            "source_url_provenance",
        ],
    }
    write_json(dst / "external_fixture_metadata.json", metadata)


def copy_external_sandbox_text_fixture(
    src: Path,
    dst: Path,
    fixture: Dict[str, object],
    fixture_key: str,
    target_name: str,
) -> str:
    """Copy a text-only external sandbox artifact into a disposable repo."""

    relative = str(fixture.get(fixture_key, "") or "")
    target = dst / "external_sandbox" / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    source = src / "reports" / "external_code_fixtures" / "latest" / relative
    if relative and source.exists():
        shutil.copy2(source, target)
    else:
        target.write_text("No external sandbox text fixture was available.\n", encoding="utf-8")
    return str(target.relative_to(dst))


EXTERNAL_REPAIR_TARGET_SOURCE = '''"""Local executable repair target derived from external code failure excerpts."""

EXTERNAL_REPAIR_TASK = "preserve_first_failure_signal"


def external_failure_signal(events):
    """Return failure signal from an event stream."""

    return ""
'''


EXTERNAL_REPAIR_FIXTURE_TEST = '''from pathlib import Path

from shared.external_repair_target import external_failure_signal


def test_external_failure_signal_is_a_real_local_repair_task():
    failure_text = (Path.cwd() / "external_sandbox" / "failure_excerpt.txt").read_text(encoding="utf-8")
    events = ("metadata_loaded", "read_error", "empty_content")

    assert failure_text
    assert external_failure_signal(events) == "read_error"
'''


def build_external_code_transfer_repo(
    src: Path,
    dst: Path,
    spec: ExternalCodeFixtureSpec,
) -> None:
    """Build a fixture whose schema is extracted from source/failure snippets."""

    fixture = select_external_code_sandbox_fixture(src, spec)
    values = external_code_values(fixture, spec)
    build_unseen_schema_transfer_repo(
        src,
        dst,
        field_name=spec.field_name,
        sample_value=values[0],
        test_name=f"test_{spec.repository_name}.py",
    )
    copied_source = copy_external_sandbox_text_fixture(
        src,
        dst,
        fixture,
        "source_snippet_path",
        "source_snippet.txt",
    )
    copied_failure = copy_external_sandbox_text_fixture(
        src,
        dst,
        fixture,
        "failure_excerpt_path",
        "failure_excerpt.txt",
    )
    repair_target = dst / "shared" / "external_repair_target.py"
    repair_target.parent.mkdir(parents=True, exist_ok=True)
    repair_target.write_text(EXTERNAL_REPAIR_TARGET_SOURCE, encoding="utf-8")
    repair_test = dst / "tests" / "test_external_code_repair_task.py"
    repair_test.parent.mkdir(parents=True, exist_ok=True)
    repair_test.write_text(EXTERNAL_REPAIR_FIXTURE_TEST, encoding="utf-8")
    metadata = {
        "fixture_kind": "external_code_sandbox_transfer",
        "source_repository": spec.source_repository,
        "fixture_id": fixture.get("fixture_id", ""),
        "source_ref": fixture.get("source_ref", ""),
        "source_file_path": fixture.get("source_file_path", ""),
        "source_url": fixture.get("source_url", ""),
        "issue_task_id": fixture.get("issue_task_id", ""),
        "issue_url": fixture.get("issue_url", ""),
        "issue_title": fixture.get("issue_title", ""),
        "field_name": spec.field_name,
        "field_values": list(values),
        "source_symbols": list(fixture.get("source_symbols", []) or []),
        "source_snippet_sha256": fixture.get("source_snippet_sha256", ""),
        "failure_excerpt_sha256": fixture.get("failure_excerpt_sha256", ""),
        "copied_source_fixture": copied_source,
        "copied_failure_fixture": copied_failure,
        "repair_target": "shared/external_repair_target.py",
        "repair_test": "tests/test_external_code_repair_task.py",
        "safety_controls": [
            "text_fixture_only",
            "no_external_code_execution",
            "bounded_source_excerpt",
            "bounded_failure_excerpt",
            "source_url_provenance",
            "disposable_repo_execution_only",
            "local_executable_repair_task",
        ],
    }
    write_json(dst / "external_code_sandbox_fixture.json", metadata)


def build_benchmark_repo(src: Path, dst: Path, repository: BenchmarkRepository) -> None:
    if repository.name == "omega_full_repo":
        copy_repo(src, dst)
        return
    if repository.name == "compact_kernel_repo":
        build_compact_kernel_repo(src, dst)
        return
    capability_spec = capability_fixture_for_repository(repository.name)
    if capability_spec is not None:
        build_capability_benchmark_repo(src, dst, capability_spec)
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
    external_spec = external_issue_fixture_for_repository(repository.name)
    if external_spec is not None:
        build_external_issue_transfer_repo(src, dst, external_spec)
        return
    external_code_spec = external_code_fixture_for_repository(repository.name)
    if external_code_spec is not None:
        build_external_code_transfer_repo(src, dst, external_code_spec)
        return
    composite_spec = composite_schema_fixture_for_repository(repository.name)
    if composite_spec is not None:
        build_composite_schema_transfer_repo(src, dst, composite_spec)
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
        failing_test.parent.mkdir(parents=True, exist_ok=True)
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


def stable_paired_seed(repository: str, task: str, repeat_index: int) -> str:
    """Return the shared seed used by all variants in one paired trial."""

    payload = f"{repository}:{task}:paired:{repeat_index}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def run_command(args: Sequence[str], cwd: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    paths = [str(cwd), str(cwd / "thdse"), str(cwd / "thdse" / "src")]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return subprocess.run(
        list(args),
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )


def run_ci_only(repo: Path, timeout_s: int) -> subprocess.CompletedProcess[str]:
    py = sys.executable
    return run_command(
        [py, "-m", "pytest", "-q"],
        repo,
        timeout_s,
    )


def run_loop_variant(
    repo: Path,
    variant: ExperimentVariant,
    *,
    seed: str,
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
        "--capability-seed",
        seed,
    ]
    if variant.exploration_policy != "conservative":
        args.extend(
            [
                "--exploration-policy",
                variant.exploration_policy,
                "--exploration-depth",
                str(variant.exploration_depth),
                "--exploration-seed",
                seed,
            ]
        )
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
                "root_broad" in label or "thdse_full" in label or "full_pytest" in label
            ):
                failures += 1
    return failures


def record_full_test_exit_code(record: dict) -> Optional[int]:
    """Return the full pytest exit code from a candidate record."""

    direct = record.get("full_test_exit_code")
    if direct is not None:
        return int(direct)
    for gate in reversed(record.get("gates", [])):
        label = str(gate.get("label", ""))
        args = list(gate.get("args", []))
        if label.endswith("_full_pytest") and len(args) >= 4 and args[-3:] == ["-m", "pytest", "-q"]:
            return int(gate.get("exit_code", 1))
    return None


def record_has_passing_full_test(record: dict) -> bool:
    return record_full_test_exit_code(record) == 0


def variant_comparable_to_verified_config(variant: ExperimentVariant) -> bool:
    """Return whether a variant keeps the safety gates needed for direct comparison."""

    return (
        variant.broad_gate is True
        and variant.thdse_core_gate is True
        and variant.rollback is True
        and variant.full_test_required is True
    )


def load_held_out_input_set(repo: Path) -> Dict[str, object]:
    """Return held-out or external fixture inputs used by a disposable repo."""

    for name in (
        "schema_transfer_manifest.json",
        "external_fixture_metadata.json",
        "external_code_sandbox_fixture.json",
        "capability_fixture_metadata.json",
    ):
        path = repo / name
        if path.exists():
            payload = read_json(path, {})
            if isinstance(payload, dict):
                return payload
    return {}


def result_provenance_hash(
    *,
    repository: BenchmarkRepository,
    task: ExperimentTask,
    variant: ExperimentVariant,
    seed: str,
    full_test_command: str,
    full_test_exit_code: Optional[int],
    held_out_input_set: str,
    accepted_count: int,
    improvement_depth: int,
) -> str:
    payload = {
        "repository": repository.name,
        "task": task.name,
        "variant": variant.name,
        "seed": seed,
        "full_test_command": full_test_command,
        "full_test_exit_code": full_test_exit_code,
        "held_out_input_set": held_out_input_set,
        "accepted_count": accepted_count,
        "improvement_depth": improvement_depth,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


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
    raw_accepted = list(summary.get("accepted_this_run", []))
    accepted = [record for record in raw_accepted if record_has_passing_full_test(record)]
    rejected = list(summary.get("rejected_this_run", []))
    quarantine = list(summary.get("quarantine_exploration", []))
    records = [*accepted, *rejected]
    total_candidates = len(raw_accepted) + len(rejected)
    full_test_required = bool(summary.get("full_test_required", variant.full_test_required))
    full_test_exit_codes = [
        code
        for code in (record_full_test_exit_code(record) for record in [*raw_accepted, *rejected])
        if code is not None
    ]
    if not full_test_exit_codes and variant.run_loop is False:
        full_test_exit_codes = [int(proc.returncode)]
    changed = changed_files(before, after)
    rollback_correct: Optional[bool] = None
    if variant.rollback and rejected and not accepted:
        rollback_correct = changed == []
    elif not variant.rollback and rejected:
        rollback_correct = False
    full_test_command = str(summary.get("full_test_command") or " ".join(FULL_TEST_COMMAND))
    final_full_test_exit_code = full_test_exit_codes[-1] if full_test_exit_codes else None
    held_out_payload = load_held_out_input_set(repo)
    held_out_input_set = json.dumps(held_out_payload, sort_keys=True)
    accepted_count = len(accepted)
    improvement_depth = int(summary.get("active_generation", 0))
    provenance_hash = result_provenance_hash(
        repository=repository,
        task=task,
        variant=variant,
        seed=seed,
        full_test_command=full_test_command,
        full_test_exit_code=final_full_test_exit_code,
        held_out_input_set=held_out_input_set,
        accepted_count=accepted_count,
        improvement_depth=improvement_depth,
    )
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
        accepted_count=accepted_count,
        rejected_count=len(rejected),
        accepted_rate=(accepted_count / total_candidates) if total_candidates else 0.0,
        regression_gate_failures=summarize_gates([*accepted, *rejected]),
        rollback_correct=rollback_correct,
        persistence_file_exists=(repo / ".omega_rsi_runs" / "closed_rsi_state.json").exists(),
        improvement_depth=improvement_depth,
        cost_proxy_seconds=round(elapsed_s, 3),
        changed_files_count=len(changed),
        summary_path=str(summary_path),
        stdout_tail=proc.stdout[-4000:],
        stderr_tail=proc.stderr[-2000:],
        repository_split=repository.split,
        transfer_origin=repository.transfer_origin,
        task_description=task.description,
        task_claim=task.claim,
        capability_delta_score=round(
            sum(float(record.get("capability_delta", {}).get("score", 0.0) or 0.0) for record in records),
            3,
        ),
        solved_new_tasks=sum(
            int(record.get("capability_delta", {}).get("solved_new_tasks", 0) or 0) for record in records
        ),
        hidden_transfer=sum(
            int(record.get("capability_delta", {}).get("hidden_transfer", 0) or 0) for record in records
        ),
        operator_reuse=sum(
            int(record.get("capability_delta", {}).get("operator_reuse", 0) or 0) for record in records
        ),
        failure_residue_count=sum(1 for record in records if record.get("failure_residue")),
        quarantine_exploration_count=len(quarantine),
        quarantine_failure_residue_count=sum(1 for record in quarantine if record.get("failure_residue")),
        full_test_command=full_test_command,
        full_test_exit_code=final_full_test_exit_code,
        full_test_required=full_test_required,
        paired_seed=seed,
        provenance_hash=provenance_hash,
        held_out_input_set=held_out_input_set,
        comparable_to_verified_config=variant_comparable_to_verified_config(variant),
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


def variance(values: Sequence[float]) -> float:
    """Return sample variance for repeated-trial values."""

    if len(values) < 2:
        return 0.0
    center = mean(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def bootstrap_ci(
    values: Sequence[float],
    *,
    seed: str,
    iterations: int = 1000,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """Return a deterministic percentile bootstrap confidence interval."""

    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (float(values[0]), float(values[0]))
    rng = random.Random(int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16))
    samples = []
    for _ in range(iterations):
        draw = [values[rng.randrange(len(values))] for _ in values]
        samples.append(mean(draw))
    samples.sort()
    lower_index = max(0, int((alpha / 2.0) * iterations) - 1)
    upper_index = min(iterations - 1, int((1.0 - alpha / 2.0) * iterations) - 1)
    return (round(samples[lower_index], 6), round(samples[upper_index], 6))


def paired_margin_ci(
    proposed: Sequence[ExperimentResult],
    baseline: Sequence[ExperimentResult],
    metric: str,
    *,
    seed: str,
) -> Tuple[float, float, float]:
    """Return mean and bootstrap CI for same-seed proposed-baseline margins."""

    baseline_by_seed = {row.paired_seed or row.seed: row for row in baseline}
    margins = []
    for row in proposed:
        match = baseline_by_seed.get(row.paired_seed or row.seed)
        if match is None:
            continue
        margins.append(float(getattr(row, metric)) - float(getattr(match, metric)))
    if not margins:
        return (0.0, 0.0, 0.0)
    lower, upper = bootstrap_ci(margins, seed=seed)
    return (round(mean(margins), 6), lower, upper)


def aggregate_results(results: Sequence[ExperimentResult]) -> List[Dict[str, object]]:
    """Aggregate repeated trials by repository, task, and variant."""

    groups: Dict[Tuple[str, str, str], List[ExperimentResult]] = {}
    for result in results:
        groups.setdefault((result.repository, result.task, result.variant), []).append(result)

    aggregates: List[Dict[str, object]] = []
    for (repository, task, variant), rows in sorted(groups.items()):
        rollback_rows = [row for row in rows if row.rollback_correct is not None]
        accepted_rate_values = [float(row.accepted_rate) for row in rows]
        improvement_depth_values = [float(row.improvement_depth) for row in rows]
        accepted_rate_ci = bootstrap_ci(
            accepted_rate_values,
            seed=f"{repository}:{task}:{variant}:accepted_rate",
        )
        improvement_depth_ci = bootstrap_ci(
            improvement_depth_values,
            seed=f"{repository}:{task}:{variant}:improvement_depth",
        )
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
                "accepted_rate_mean": mean(accepted_rate_values),
                "accepted_rate_variance": variance(accepted_rate_values),
                "accepted_rate_ci_lower": accepted_rate_ci[0],
                "accepted_rate_ci_upper": accepted_rate_ci[1],
                "regression_gate_failures_mean": mean([float(row.regression_gate_failures) for row in rows]),
                "rollback_success_rate": rollback_success_rate,
                "improvement_depth_mean": mean(improvement_depth_values),
                "improvement_depth_variance": variance(improvement_depth_values),
                "improvement_depth_ci_lower": improvement_depth_ci[0],
                "improvement_depth_ci_upper": improvement_depth_ci[1],
                "cost_proxy_seconds_mean": mean([float(row.cost_proxy_seconds) for row in rows]),
                "changed_files_count_mean": mean([float(row.changed_files_count) for row in rows]),
                "capability_delta_score_mean": mean([float(row.capability_delta_score) for row in rows]),
                "solved_new_tasks_mean": mean([float(row.solved_new_tasks) for row in rows]),
                "hidden_transfer_mean": mean([float(row.hidden_transfer) for row in rows]),
                "operator_reuse_mean": mean([float(row.operator_reuse) for row in rows]),
                "failure_residue_count_mean": mean([float(row.failure_residue_count) for row in rows]),
                "quarantine_exploration_count_mean": mean(
                    [float(row.quarantine_exploration_count) for row in rows]
                ),
                "quarantine_failure_residue_count_mean": mean(
                    [float(row.quarantine_failure_residue_count) for row in rows]
                ),
                "full_test_required": all(row.full_test_required for row in rows),
                "comparable_to_verified_config": all(row.comparable_to_verified_config for row in rows),
                "seed_registry": ",".join(row.seed for row in rows),
                "full_test_success_rate": mean(
                    [
                        1.0 if row.full_test_exit_code == 0 else 0.0
                        for row in rows
                        if row.full_test_exit_code is not None
                    ]
                ),
                "full_test_command": rows[0].full_test_command,
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


def _ci_lower(row: Dict[str, object], key: str) -> float:
    ci_key = f"{key}_ci_lower"
    if ci_key in row:
        return _float_value(row, ci_key)
    return _float_value(row, f"{key}_mean")


def _ci_upper(row: Dict[str, object], key: str) -> float:
    ci_key = f"{key}_ci_upper"
    if ci_key in row:
        return _float_value(row, ci_key)
    return _float_value(row, f"{key}_mean")


def build_baseline_comparisons(
    aggregates: Sequence[Dict[str, object]],
    *,
    results: Sequence[ExperimentResult] = (),
) -> List[Dict[str, object]]:
    """Compare the proposed loop against baselines and ablations."""

    groups: Dict[Tuple[str, str], List[Dict[str, object]]] = {}
    for row in aggregates:
        groups.setdefault((str(row["repository"]), str(row["task"])), []).append(row)
    result_groups: Dict[Tuple[str, str, str], List[ExperimentResult]] = {}
    for result in results:
        result_groups.setdefault((result.repository, result.task, result.variant), []).append(result)

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
        no_broad = next((row for row in ablations if row.get("variant") == "full_suite_no_broad_gate"), None)

        proposed_acceptance = _float_value(proposed, "accepted_rate_mean")
        proposed_depth = _float_value(proposed, "improvement_depth_mean")
        proposed_full_test_success = _float_value(proposed, "full_test_success_rate")
        proposed_acceptance_ci_lower = _ci_lower(proposed, "accepted_rate")
        proposed_acceptance_ci_upper = _ci_upper(proposed, "accepted_rate")
        proposed_depth_ci_lower = _ci_lower(proposed, "improvement_depth")
        proposed_depth_ci_upper = _ci_upper(proposed, "improvement_depth")
        best_baseline_acceptance = (
            _float_value(best_baseline, "accepted_rate_mean") if best_baseline else 0.0
        )
        best_baseline_depth = (
            _float_value(best_baseline, "improvement_depth_mean") if best_baseline else 0.0
        )
        best_baseline_acceptance_ci_upper = (
            _ci_upper(best_baseline, "accepted_rate") if best_baseline else 0.0
        )
        best_baseline_depth_ci_upper = (
            _ci_upper(best_baseline, "improvement_depth") if best_baseline else 0.0
        )
        best_baseline_comparable = bool(
            best_baseline.get("comparable_to_verified_config", True)
        ) if best_baseline else False
        paired_acceptance_margin_mean = proposed_acceptance - best_baseline_acceptance
        paired_acceptance_margin_ci_lower = paired_acceptance_margin_mean
        paired_acceptance_margin_ci_upper = paired_acceptance_margin_mean
        paired_depth_margin_mean = proposed_depth - best_baseline_depth
        paired_depth_margin_ci_lower = paired_depth_margin_mean
        paired_depth_margin_ci_upper = paired_depth_margin_mean
        if best_baseline and results:
            proposed_rows = result_groups.get((repository, task, "verified_closed_loop"), [])
            baseline_rows = result_groups.get((repository, task, str(best_baseline.get("variant"))), [])
            (
                paired_acceptance_margin_mean,
                paired_acceptance_margin_ci_lower,
                paired_acceptance_margin_ci_upper,
            ) = paired_margin_ci(
                proposed_rows,
                baseline_rows,
                "accepted_rate",
                seed=f"{repository}:{task}:accepted_rate_margin",
            )
            (
                paired_depth_margin_mean,
                paired_depth_margin_ci_lower,
                paired_depth_margin_ci_upper,
            ) = paired_margin_ci(
                proposed_rows,
                baseline_rows,
                "improvement_depth",
                seed=f"{repository}:{task}:improvement_depth_margin",
            )
        accepted_rate_ci_win = (
            best_baseline is not None
            and best_baseline_comparable
            and (
                paired_acceptance_margin_ci_lower > 0.0
                or proposed_acceptance_ci_lower > best_baseline_acceptance_ci_upper
            )
        )
        improvement_depth_ci_win = (
            best_baseline is not None
            and best_baseline_comparable
            and (
                paired_depth_margin_ci_lower > 0.0
                or proposed_depth_ci_lower > best_baseline_depth_ci_upper
            )
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
            and proposed_full_test_success > 0.0
            and (accepted_rate_ci_win or improvement_depth_ci_win or best_baseline is None)
        )
        external_transfer_success = (
            proposed.get("repository_split") == "external_unseen"
            and proposed_acceptance > 0.0
            and proposed_full_test_success > 0.0
            and (accepted_rate_ci_win or improvement_depth_ci_win)
        )
        external_code_transfer_success = (
            proposed.get("repository_split") == "external_code_unseen"
            and proposed_acceptance > 0.0
            and proposed_full_test_success > 0.0
            and (
                _float_value(proposed, "solved_new_tasks_mean") > 0.0
                or accepted_rate_ci_win
                or improvement_depth_ci_win
            )
        )
        capability_transfer_success = (
            proposed.get("repository_split") == "capability_unseen"
            and proposed_acceptance > 0.0
            and proposed_full_test_success > 0.0
            and _float_value(proposed, "solved_new_tasks_mean") > 0.0
            and (accepted_rate_ci_win or improvement_depth_ci_win or best_baseline is None)
        )

        if capability_transfer_success:
            outcome = "capability_transfer_success"
        elif external_code_transfer_success:
            outcome = "external_code_transfer_success"
        elif external_transfer_success:
            outcome = "external_transfer_success"
        elif unseen_transfer_success:
            outcome = "unseen_transfer_success"
        elif safety_win:
            outcome = "safety_win_over_ablation"
        elif improvement_depth_ci_win and proposed_acceptance >= best_baseline_acceptance:
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
                "best_baseline_comparable_to_verified_config": best_baseline_comparable,
                "best_baseline_accepted_rate_mean": best_baseline_acceptance,
                "best_baseline_improvement_depth_mean": best_baseline_depth,
                "accepted_rate_margin_vs_best_baseline": proposed_acceptance - best_baseline_acceptance,
                "accepted_rate_margin_ci_lower": paired_acceptance_margin_ci_lower,
                "accepted_rate_margin_ci_upper": paired_acceptance_margin_ci_upper,
                "paired_accepted_rate_margin_mean": paired_acceptance_margin_mean,
                "improvement_depth_margin": proposed_depth - best_baseline_depth,
                "improvement_depth_margin_ci_lower": paired_depth_margin_ci_lower,
                "improvement_depth_margin_ci_upper": paired_depth_margin_ci_upper,
                "paired_improvement_depth_margin_mean": paired_depth_margin_mean,
                "accepted_rate_ci_win": accepted_rate_ci_win,
                "improvement_depth_ci_win": improvement_depth_ci_win,
                "proposed_accepted_rate_ci_lower": proposed_acceptance_ci_lower,
                "proposed_accepted_rate_ci_upper": proposed_acceptance_ci_upper,
                "proposed_improvement_depth_ci_lower": proposed_depth_ci_lower,
                "proposed_improvement_depth_ci_upper": proposed_depth_ci_upper,
                "depth_margin_vs_agent_loop": proposed_depth - agent_depth,
                "depth_margin_vs_ci_only": proposed_depth - ci_depth,
                "safety_win_over_no_rollback": safety_win,
                "unsafe_acceptance_seen_without_broad_gate": broad_gate_win,
                "unseen_transfer_success": unseen_transfer_success,
                "external_transfer_success": external_transfer_success,
                "external_code_transfer_success": external_code_transfer_success,
                "capability_transfer_success": capability_transfer_success,
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
    comparisons = build_baseline_comparisons(aggregates, results=results)
    table_lines = [
        "| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Full Test | Regression Failures | Rollback Correct | Seconds |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        rollback = "n/a" if result.rollback_correct is None else str(result.rollback_correct)
        full_test = "n/a" if result.full_test_exit_code is None else str(result.full_test_exit_code)
        table_lines.append(
            f"| {result.repository} | {result.repository_split} | {result.task} | {result.variant} | {result.repeat_index} | {result.accepted_count} | "
            f"{result.rejected_count} | {result.accepted_rate:.2f} | "
            f"{full_test} | {result.regression_gate_failures} | {rollback} | {result.elapsed_s:.2f} |"
        )

    aggregate_lines = [
        "| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Accepted Rate CI | Full Test Success | Regression Failures Mean | Rollback Success | Depth Mean | Depth CI | Seconds Mean |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregates:
        rollback = "n/a" if row["rollback_success_rate"] is None else f"{float(row['rollback_success_rate']):.2f}"
        aggregate_lines.append(
            f"| {row['repository']} | {row['repository_split']} | {row['task']} | {row['variant']} | {row['trial_count']} | "
            f"{float(row['accepted_rate_mean']):.2f} | "
            f"[{float(row['accepted_rate_ci_lower']):.2f}, {float(row['accepted_rate_ci_upper']):.2f}] | "
            f"{float(row['full_test_success_rate']):.2f} | "
            f"{float(row['regression_gate_failures_mean']):.2f} | "
            f"{rollback} | {float(row['improvement_depth_mean']):.2f} | "
            f"[{float(row['improvement_depth_ci_lower']):.2f}, {float(row['improvement_depth_ci_upper']):.2f}] | "
            f"{float(row['cost_proxy_seconds_mean']):.2f} |"
        )

    comparison_lines = [
        "| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |",
        "|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparisons:
        comparison_lines.append(
            f"| {row['repository']} | {row['repository_split']} | {row['task']} | {row['outcome']} | "
            f"{float(row['proposed_accepted_rate_mean']):.2f} | {row['best_baseline_variant']} | "
            f"{float(row['best_baseline_accepted_rate_mean']):.2f} | "
            f"[{float(row['accepted_rate_margin_ci_lower']):.2f}, {float(row['accepted_rate_margin_ci_upper']):.2f}] | "
            f"[{float(row['improvement_depth_margin_ci_lower']):.2f}, {float(row['improvement_depth_margin_ci_upper']):.2f}] | "
            f"{row['safety_win_over_no_rollback']} | {row['unseen_transfer_success']} | "
            f"{row['external_transfer_success']} | {row['external_code_transfer_success']} | "
            f"{row['capability_transfer_success']} |"
        )

    success_provenance_lines = [
        "| Repository | Task | Variant | Repeat | Seed | Full Test Command | Exit Code | Provenance Hash | Held-Out Input Set |",
        "|---|---|---|---:|---|---|---:|---|---|",
    ]
    for result in results:
        if result.accepted_count <= 0 or result.full_test_exit_code != 0:
            continue
        success_provenance_lines.append(
            f"| {result.repository} | {result.task} | {result.variant} | {result.repeat_index} | "
            f"{result.seed} | `{result.full_test_command}` | {result.full_test_exit_code} | "
            f"`{result.provenance_hash}` | `{result.held_out_input_set[:500]}` |"
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
        "## Counted Success Provenance",
        "",
        *success_provenance_lines,
        "",
        "## Review-Relevant Claims",
        "",
        "- The proposed loop can patch real repository code and persist accepted/rejected provenance.",
        "- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.",
        "- Held-out schema-transfer fixtures are marked as unseen and compared separately.",
        "- Baseline comparison rows explicitly label wins, ties, safety wins, and inconclusive cases.",
        "- The generator includes schema-driven candidate synthesis instead of only fixed candidate names.",
        "- The generator scores bounded competing hypotheses with rejection history before patching.",
        "- CapabilityDelta scoring records solved tasks, hidden transfer, regression protection, operator reuse, and compute cost.",
        "- Failure residue extraction records missing operators, missing abstractions, failed evaluators, and overfit signals.",
        "- Capability fixtures include algorithm synthesis, symbolic reasoning, grid transformation, bug repair, and planning/state transitions.",
        "- Candidate promotion and success accounting require the full `python -m pytest -q` suite.",
        "- Focused diagnostics and extra broad gates cannot mark a candidate successful without full pytest.",
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
        "- `external_transfer_success`: the loop patches a fixture schema extracted from actual external repository issue metadata.",
        "- `external_code_transfer_success`: the loop patches a fixture schema extracted from bounded external source-code snippets and issue failure excerpts.",
        "- `capability_transfer_success`: the loop synthesizes a reusable primitive that solves executable public and hidden capability cases.",
        "- All success outcomes require a recorded passing full `python -m pytest -q` result.",
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
        "- The main workflow commits only accepted state and source changes validated by full pytest.",
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
                        seed = stable_paired_seed(repository.name, task.name, repeat_index)
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
                                    seed=seed,
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
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument(
        "--allow-low-repeats",
        action="store_true",
        help="Allow fewer than 10 repeats for local smoke checks; reported wins remain underpowered.",
    )
    parser.add_argument("--max-generations", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=4)
    parser.add_argument("--wall-seconds", type=int, default=1800)
    parser.add_argument("--timeout-seconds", type=int, default=420)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if args.repeats < 10 and not args.allow_low_repeats:
        parser.error("--repeats must be at least 10 unless --allow-low-repeats is set")

    output_dir = run_suite(args)
    print(json.dumps({"output_dir": str(output_dir)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
