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
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from shared.capability_benchmarks import (
    CAPABILITY_FAMILIES,
    CapabilityDelta,
    CapabilityEvaluation,
    capability_cases_for_seed,
    capability_delta_from_evaluations,
    detect_anti_cheat_findings,
    evaluate_capability_cases,
    extract_failure_residue,
    synthesize_operator_specs,
)


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
    extra_files: Dict[str, str] = field(default_factory=dict)
    capability_family: str = ""
    operator_specs: Tuple[Dict[str, object], ...] = field(default_factory=tuple)
    generator_improvement: Dict[str, object] = field(default_factory=dict)


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


def candidate_compute_cost(gates: Sequence[GateResult]) -> float:
    return round(sum(float(gate.elapsed_s) for gate in gates), 3)


def candidate_capability_delta(
    candidate: CandidatePatch,
    *,
    accepted: bool,
    gates: Sequence[GateResult],
    evaluations: Sequence[CapabilityEvaluation] = (),
) -> Dict[str, object]:
    """Score the capability delta represented by a candidate result."""

    if not candidate.capability_family and not candidate.operator_specs:
        return {}
    regression_failures = sum(
        1
        for gate in gates
        if gate.exit_code != 0 and ("root_broad" in gate.label or "thdse_core" in gate.label)
    )
    operator_reuse = len(
        {
            str(spec.get("name", ""))
            for spec in candidate.operator_specs
            if spec.get("kind") in {"solver_primitive", "search_heuristic"}
        }
    )
    if evaluations:
        return capability_delta_from_evaluations(
            evaluations,
            reused_operators=(
                str(spec.get("name", ""))
                for spec in candidate.operator_specs
                if spec.get("kind") in {"solver_primitive", "search_heuristic"}
            ),
            regression_failures=regression_failures,
            compute_cost=candidate_compute_cost(gates),
        ).to_dict()

    delta = CapabilityDelta(
        solved_new_tasks=0,
        hidden_transfer=0,
        regression_protection=1 if gates and regression_failures == 0 else 0,
        operator_reuse=operator_reuse,
        compute_cost=candidate_compute_cost(gates),
        score=round(
            (0.25 if gates and regression_failures == 0 else 0.0)
            + operator_reuse * 0.1
            - min(candidate_compute_cost(gates) / 600.0, 0.5),
            3,
        ),
    )
    return delta.to_dict()


def candidate_failure_residue(
    candidate: CandidatePatch,
    *,
    accepted: bool,
    gates: Sequence[GateResult],
    error: str,
) -> Dict[str, object]:
    """Return structured failure residue for rejected candidates."""

    if accepted:
        return {}
    residue = extract_failure_residue(
        candidate.name,
        [asdict(gate) for gate in gates],
        error=error,
        operator_specs=candidate.operator_specs,
    )
    return residue.to_dict()


def capability_operator_names(candidate: CandidatePatch) -> Tuple[str, ...]:
    """Return solver primitive names synthesized by a capability candidate."""

    names = [
        str(spec.get("name", ""))
        for spec in candidate.operator_specs
        if spec.get("kind") == "solver_primitive" and spec.get("name")
    ]
    if not names and candidate.capability_family in CAPABILITY_FAMILIES:
        names = [candidate.goal.name.removeprefix("repair_").removesuffix("_operator")]
    return tuple(dict.fromkeys(names))


def load_capability_operators(source_path: Path, operator_names: Sequence[str]) -> Dict[str, Callable[..., object]]:
    """Load candidate-local primitive callables for evaluator execution."""

    if not source_path.exists() or not operator_names:
        return {}
    namespace: Dict[str, object] = {
        "__builtins__": __builtins__,
        "__name__": "_closed_rsi_capability_candidate",
    }
    source = source_path.read_text(encoding="utf-8")
    exec(compile(source, str(source_path), "exec"), namespace)
    return {
        name: namespace[name]
        for name in operator_names
        if callable(namespace.get(name))
    }


def quarantine_ignore(_directory: str, names: List[str]) -> List[str]:
    """Ignore generated state and cache directories when copying quarantine repos."""

    ignored = []
    for name in names:
        if name in {
            ".git",
            ".mypy_cache",
            ".omega_rsi_runs",
            ".pytest_cache",
            "__pycache__",
            "target",
        }:
            ignored.append(name)
    return ignored


def copy_repo_to_quarantine(src: Path, dst: Path) -> None:
    """Copy a repository into a disposable quarantine workspace."""

    shutil.copytree(src, dst, ignore=quarantine_ignore)


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


def singularize_identifier(name: str) -> str:
    """Derive a conservative singular parameter name from a record field."""

    if name.endswith("_flags"):
        return name[:-6]
    if name.endswith("ies"):
        return f"{name[:-3]}y"
    if name.endswith("s") and len(name) > 1:
        return name[:-1]
    return name


def query_blueprint_for_field(field_name: str, *, style: str = "canonical") -> AutonomousQueryBlueprint:
    """Create a query candidate blueprint from a tuple-valued record field."""

    element_name = singularize_identifier(field_name)
    sample_values = {
        "definition": "function:scan_file",
        "feature": "self_improvement",
    }
    if style == "alternate":
        method_name = f"records_matching_{field_name}"
        if field_name == "imports":
            method_name = "records_with_import"
        return AutonomousQueryBlueprint(
            field_name=field_name,
            method_name=method_name,
            parameter_name=element_name if field_name != "imports" else "module_name",
            sample_value=sample_values.get(element_name, "json" if field_name == "imports" else f"sample_{element_name}"),
            candidate_name=f"emergent_local_corpus_{field_name}_membership_v1",
            goal_name=f"emergently_query_local_corpus_{field_name}",
            rationale=(
                f"The bounded emergent planner generated an alternate membership "
                f"query hypothesis for {field_name}."
            ),
            strategy="alternate_tuple_membership",
        )
    if field_name == "imports":
        return AutonomousQueryBlueprint(
            field_name=field_name,
            method_name="records_importing",
            parameter_name="module_name",
            sample_value="json",
            candidate_name="autonomous_local_corpus_imports_query_v1",
            goal_name="autonomously_query_local_corpus_imports",
            rationale="The planner found a tuple-valued imports field without a matching query API.",
        )
    return AutonomousQueryBlueprint(
        field_name=field_name,
        method_name=f"records_with_{element_name}",
        parameter_name=element_name,
        sample_value=sample_values.get(element_name, f"sample_{element_name}"),
        candidate_name=f"autonomous_local_corpus_{field_name}_query_v1",
        goal_name=f"autonomously_query_local_corpus_{field_name}",
        rationale=(
            f"The planner found a tuple-valued {field_name} field without a matching "
            "query API on LocalCorpusIndex."
        ),
    )


def query_blueprint_hypotheses_for_field(field_name: str) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Generate bounded competing query hypotheses for one record field."""

    return (
        query_blueprint_for_field(field_name, style="canonical"),
        query_blueprint_for_field(field_name, style="alternate"),
    )


def ast_annotation_mentions_tuple_of_strings(annotation: ast.AST) -> bool:
    """Return whether an annotation looks like a tuple of strings."""

    try:
        rendered = ast.unparse(annotation)
    except Exception:
        return False
    normalized = rendered.replace("typing.", "")
    return "Tuple" in normalized and "str" in normalized


def names_from_state(state: Optional[dict], bucket: str) -> Tuple[str, ...]:
    """Return candidate names from persisted state records."""

    if not isinstance(state, dict):
        return ()
    names: List[str] = []
    for record in state.get(bucket, []):
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            names.append(str(record["name"]))
    return tuple(names)


def score_query_blueprints(
    blueprints: Sequence[AutonomousQueryBlueprint],
    *,
    state: Optional[dict] = None,
) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Score bounded planner hypotheses against accepted/rejected provenance."""

    accepted_names = set(names_from_state(state, "accepted"))
    rejected_names = set(names_from_state(state, "rejected"))
    scored: List[AutonomousQueryBlueprint] = []
    for index, blueprint in enumerate(blueprints):
        score = 10.0
        evidence = [
            f"field:{blueprint.field_name}",
            f"method:{blueprint.method_name}",
            f"strategy:{blueprint.strategy}",
        ]
        if blueprint.strategy == "tuple_membership":
            score += 2.0
            evidence.append("canonical_strategy_bonus")
        if blueprint.candidate_name in rejected_names:
            score -= 8.0
            evidence.append("rejected_history_penalty")
        if blueprint.candidate_name in accepted_names:
            score -= 4.0
            evidence.append("accepted_history_penalty")
        score -= index * 0.001
        scored.append(
            replace(
                blueprint,
                planner_score=round(score, 3),
                evidence=tuple(evidence),
            )
        )
    return tuple(
        sorted(
            scored,
            key=lambda item: (-item.planner_score, item.field_name, item.method_name),
        )
    )


def discover_local_corpus_query_blueprints(
    text: str,
    *,
    state: Optional[dict] = None,
    max_hypotheses: int = 3,
) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Infer missing LocalCorpusIndex query APIs from LocalPythonFileRecord fields."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ()
    record_fields: List[str] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if not isinstance(node, ast.ClassDef) or node.name != "LocalPythonFileRecord":
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if ast_annotation_mentions_tuple_of_strings(item.annotation):
                    record_fields.append(item.target.id)
        break
    blueprints: List[AutonomousQueryBlueprint] = []
    for field_name in record_fields:
        for blueprint in query_blueprint_hypotheses_for_field(field_name):
            if f"def {blueprint.method_name}(" not in text:
                blueprints.append(blueprint)
    return score_query_blueprints(blueprints, state=state)[:max_hypotheses]


def add_autonomous_record_query(text: str, blueprint: AutonomousQueryBlueprint) -> str:
    """Insert a planner-inferred LocalCorpusIndex query method."""

    if f"def {blueprint.method_name}(" in text:
        return text
    marker = "    def write_json(self, path: Path) -> None:\n"
    insertion = f'''    def {blueprint.method_name}(self, {blueprint.parameter_name}: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records whose ``{blueprint.field_name}`` contain ``{blueprint.parameter_name}``."""

        if not isinstance({blueprint.parameter_name}, str) or not {blueprint.parameter_name}:
            raise ValueError("{blueprint.parameter_name} must be a non-empty string")
        return tuple(record for record in self.records if {blueprint.parameter_name} in record.{blueprint.field_name})

'''
    return insert_before(text, marker, insertion, blueprint.candidate_name)


def build_autonomous_query_test(blueprint: AutonomousQueryBlueprint) -> str:
    """Build a regression test for a planner-inferred LocalCorpusIndex query."""

    return f'''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_{blueprint.method_name}_filters_{blueprint.field_name}():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            {blueprint.field_name}=("{blueprint.sample_value}",),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            {blueprint.field_name}=("other_value",),
        ),
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=2,
            syntax_ok_count=2,
            syntax_error_count=0,
            unique_sha256_count=2,
            duplicate_file_instances=0,
            feature_counts={{}},
            import_edge_count=0,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.{blueprint.method_name}("{blueprint.sample_value}")) == ("a.py",)
'''


def autonomous_local_corpus_candidates(
    repo_root: Path,
    generation: int,
    *,
    state: Optional[dict] = None,
) -> List[CandidatePatch]:
    """Plan LocalCorpusIndex candidates from source schema instead of fixed candidate names."""

    local_corpus = repo_root / "shared" / "local_corpus.py"
    if not local_corpus.exists():
        return []
    text = local_corpus.read_text(encoding="utf-8")
    candidates: List[CandidatePatch] = []
    for blueprint in discover_local_corpus_query_blueprints(text, state=state):
        candidates.append(
            CandidatePatch(
                name=blueprint.candidate_name,
                generation=generation,
                goal=Goal(
                    name=blueprint.goal_name,
                    target="shared.local_corpus.LocalCorpusIndex",
                    metric=f"planner score {blueprint.planner_score} plus generated regression test",
                    rationale=f"{blueprint.rationale} Evidence: {', '.join(blueprint.evidence)}.",
                ),
                target_path=local_corpus,
                test_path=repo_root / "tests" / f"test_{blueprint.candidate_name}.py",
                transform=lambda source, plan=blueprint: add_autonomous_record_query(source, plan),
                test_source=build_autonomous_query_test(blueprint),
                focused_tests=(f"tests/test_{blueprint.candidate_name}.py",),
                capability_family="schema_query_repair",
                operator_specs=operator_specs_for("schema_query_repair", blueprint.method_name),
                generator_improvement=generator_feedback(
                    "schema-driven query planner",
                    "adds a reusable tuple-membership operator surface inferred from dataclass fields",
                    f"{blueprint.method_name} is generated from {blueprint.field_name} and locked by a focused test",
                ),
            )
        )
    return candidates


POLICY_REGISTRY_ACTIVE_MARKER = "POLICY_REGISTRY_" + "ACTIVE = True"


def add_policy_registry_hook(text: str) -> str:
    if POLICY_REGISTRY_ACTIVE_MARKER in text:
        return text
    function_marker = "\n\nclass ClosedRecursiveSelfImprovementLoop:\n"
    function_insertion = "\n\n" + POLICY_REGISTRY_ACTIVE_MARKER + '''


def load_policy_registry(repo_root: Path) -> Dict[str, object]:
    """Return metadata for the active candidate policy registry."""

    registry_path = repo_root / "scripts" / "rsi_policy_registry.py"
    if not registry_path.exists():
        return {
            "available": False,
            "path": str(registry_path.relative_to(repo_root)),
            "capabilities": [],
        }
    return {
        "available": True,
        "path": str(registry_path.relative_to(repo_root)),
        "capabilities": [
            "generator_policy",
            "validator_policy",
            "patch_policy",
            "safety_policy",
        ],
    }
'''
    text = insert_before(
        text,
        function_marker,
        function_insertion,
        "loop_policy_registry_v1",
    )
    method_marker = "    def load_state(self) -> dict:\n"
    method_insertion = '''    def policy_surface(self) -> Dict[str, object]:
        """Expose the active generator, validator, patch, and safety policy surface."""

        return load_policy_registry(self.repo_root)

'''
    return insert_before(
        text,
        method_marker,
        method_insertion,
        "loop_policy_registry_v1",
    )


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


LOCAL_CORPUS_QUERY_SPECS: Tuple[CandidateFactorySpec, ...] = (
    CandidateFactorySpec(
        candidate_name="local_corpus_feature_query_v1",
        missing_symbol="def records_with_feature(",
        goal_name="make_local_corpus_queryable_by_feature",
        target="shared.local_corpus.LocalCorpusIndex",
        metric="new query API plus focused regression test",
        rationale="The corpus index already extracts feature flags but lacks a stable query API.",
        target_relative_path="shared/local_corpus.py",
        test_relative_path="tests/test_local_corpus_feature_query_rewrite.py",
        transform=add_records_with_feature,
        test_source=FEATURE_QUERY_TEST,
        focused_tests=("tests/test_local_corpus_feature_query_rewrite.py",),
    ),
    CandidateFactorySpec(
        candidate_name="local_corpus_import_query_v1",
        missing_symbol="def records_importing(",
        goal_name="make_local_corpus_queryable_by_import",
        target="shared.local_corpus.LocalCorpusIndex",
        metric="new import query API plus focused regression test",
        rationale="The corpus index stores static imports but lacks a direct import lookup API.",
        target_relative_path="shared/local_corpus.py",
        test_relative_path="tests/test_local_corpus_import_query_rewrite.py",
        transform=add_records_importing,
        test_source=IMPORT_QUERY_TEST,
        focused_tests=("tests/test_local_corpus_import_query_rewrite.py",),
    ),
)


def candidates_from_specs(
    repo_root: Path,
    generation: int,
    specs: Sequence[CandidateFactorySpec],
) -> List[CandidatePatch]:
    """Generate source candidates from declarative missing-capability specs."""

    candidates: List[CandidatePatch] = []
    source_cache: Dict[str, str] = {}
    for spec in specs:
        target_path = repo_root / spec.target_relative_path
        if spec.target_relative_path not in source_cache:
            source_cache[spec.target_relative_path] = target_path.read_text(encoding="utf-8")
        if spec.missing_symbol in source_cache[spec.target_relative_path]:
            continue
        candidates.append(
            CandidatePatch(
                name=spec.candidate_name,
                generation=generation,
                goal=Goal(
                    name=spec.goal_name,
                    target=spec.target,
                    metric=spec.metric,
                    rationale=spec.rationale,
                ),
                target_path=target_path,
                test_path=repo_root / spec.test_relative_path,
                transform=spec.transform,
                test_source=spec.test_source,
                focused_tests=spec.focused_tests,
                capability_family="schema_query_repair",
                operator_specs=operator_specs_for("schema_query_repair", spec.missing_symbol.strip("def (")),
                generator_improvement=generator_feedback(
                    "declarative candidate factories",
                    "keeps fixed repair recipes available as reusable generator fallbacks",
                    f"{spec.candidate_name} repairs {spec.target} with a focused regression test",
                ),
            )
        )
    return candidates


@dataclass(frozen=True)
class CapabilityOperatorBlueprint:
    """Deterministic repair plan for one capability benchmark primitive."""

    family: str
    function_name: str
    candidate_name: str
    implementation_source: str
    public_assertion: str
    hidden_assertion: str


CAPABILITY_OPERATOR_BLUEPRINTS: Tuple[CapabilityOperatorBlueprint, ...] = (
    CapabilityOperatorBlueprint(
        family="algorithm_synthesis",
        function_name="run_length_encode",
        candidate_name="capability_operator_algorithm_synthesis_rle_v1",
        implementation_source='''def run_length_encode(items):
    """Return adjacent value/count pairs for a sequence."""

    encoded = []
    marker = object()
    current = marker
    count = 0
    for item in items:
        if count == 0:
            current = item
            count = 1
            continue
        if item == current:
            count += 1
            continue
        encoded.append((current, count))
        current = item
        count = 1
    if count:
        encoded.append((current, count))
    return tuple(encoded)
''',
        public_assertion="assert run_length_encode((1, 1, 2, 2, 2, 3)) == ((1, 2), (2, 3), (3, 1))",
        hidden_assertion="assert run_length_encode(('a', 'a', 'b', 'a')) == (('a', 2), ('b', 1), ('a', 1))",
    ),
    CapabilityOperatorBlueprint(
        family="symbolic_reasoning",
        function_name="infer_linear_rule",
        candidate_name="capability_operator_symbolic_reasoning_linear_rule_v1",
        implementation_source='''def infer_linear_rule(values):
    """Infer a constant-step sequence rule and its next value."""

    if len(values) < 2:
        raise ValueError("at least two values are required")
    step = values[1] - values[0]
    for left, right in zip(values, values[1:]):
        if right - left != step:
            raise ValueError("values do not form a linear rule")
    return {"start": values[0], "step": step, "next": values[-1] + step}
''',
        public_assertion="assert infer_linear_rule((2, 5, 8, 11)) == {'start': 2, 'step': 3, 'next': 14}",
        hidden_assertion="assert infer_linear_rule((-3, -1, 1)) == {'start': -3, 'step': 2, 'next': 3}",
    ),
    CapabilityOperatorBlueprint(
        family="grid_transformation",
        function_name="rotate_grid_clockwise",
        candidate_name="capability_operator_grid_transformation_rotate_v1",
        implementation_source='''def rotate_grid_clockwise(grid):
    """Rotate a rectangular grid clockwise."""

    rows = tuple(tuple(row) for row in grid)
    if not rows:
        return ()
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("grid must be rectangular")
    return tuple(tuple(rows[row][column] for row in range(len(rows) - 1, -1, -1)) for column in range(width))
''',
        public_assertion="assert rotate_grid_clockwise(((1, 2, 3), (4, 5, 6))) == ((4, 1), (5, 2), (6, 3))",
        hidden_assertion="assert rotate_grid_clockwise((('x',), ('y',), ('z',))) == (('z', 'y', 'x'),)",
    ),
    CapabilityOperatorBlueprint(
        family="bug_repair",
        function_name="dedupe_preserve_order",
        candidate_name="capability_operator_bug_repair_dedupe_v1",
        implementation_source='''def dedupe_preserve_order(items):
    """Remove duplicate items while preserving first occurrence order."""

    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)
''',
        public_assertion="assert dedupe_preserve_order(('b', 'a', 'b', 'c', 'a')) == ('b', 'a', 'c')",
        hidden_assertion="assert dedupe_preserve_order((3, 3, 2, 3, 1, 2)) == (3, 2, 1)",
    ),
    CapabilityOperatorBlueprint(
        family="planning_state_transition",
        function_name="apply_grid_action",
        candidate_name="capability_operator_planning_state_transition_action_v1",
        implementation_source='''def apply_grid_action(state, action):
    """Apply a one-step cardinal movement action to a grid state."""

    deltas = {
        "north": (0, 1),
        "south": (0, -1),
        "east": (1, 0),
        "west": (-1, 0),
        "stay": (0, 0),
    }
    if action not in deltas:
        raise ValueError(f"unknown action: {action}")
    dx, dy = deltas[action]
    next_state = dict(state)
    next_state["x"] = int(next_state.get("x", 0)) + dx
    next_state["y"] = int(next_state.get("y", 0)) + dy
    return next_state
''',
        public_assertion="assert apply_grid_action({'x': 0, 'y': 0}, 'east') == {'x': 1, 'y': 0}",
        hidden_assertion="assert apply_grid_action({'x': 2, 'y': -1}, 'north') == {'x': 2, 'y': 0}",
    ),
)


def add_capability_operator(text: str, blueprint: CapabilityOperatorBlueprint) -> str:
    """Append a missing reusable capability primitive."""

    if f"def {blueprint.function_name}(" in text:
        return text
    return text.rstrip() + "\n\n\n" + blueprint.implementation_source.rstrip() + "\n"


def build_capability_operator_test(blueprint: CapabilityOperatorBlueprint) -> str:
    """Build public and hidden transfer tests for a synthesized operator."""

    return f'''from shared.capability_primitives import {blueprint.function_name}


def test_{blueprint.function_name}_public_counterexample():
    {blueprint.public_assertion}


def test_{blueprint.function_name}_hidden_transfer_counterexample():
    {blueprint.hidden_assertion}
'''


def capability_operator_candidates(repo_root: Path, generation: int) -> List[CandidatePatch]:
    """Plan repair candidates for executable capability benchmark fixtures."""

    target = repo_root / "shared" / "capability_primitives.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    candidates: List[CandidatePatch] = []
    for blueprint in CAPABILITY_OPERATOR_BLUEPRINTS:
        if f"def {blueprint.function_name}(" in text:
            continue
        candidates.append(
            CandidatePatch(
                name=blueprint.candidate_name,
                generation=generation,
                goal=Goal(
                    name=f"repair_{blueprint.family}_operator",
                    target="shared.capability_primitives",
                    metric="public and hidden transfer counterexamples pass",
                    rationale=(
                        f"The capability benchmark fixture is missing the reusable "
                        f"{blueprint.function_name} primitive for {blueprint.family}."
                    ),
                ),
                target_path=target,
                test_path=repo_root / "tests" / f"test_capability_{blueprint.family}_operator_v1.py",
                transform=lambda source, plan=blueprint: add_capability_operator(source, plan),
                test_source=build_capability_operator_test(blueprint),
                focused_tests=(f"tests/test_capability_{blueprint.family}_operator_v1.py",),
                capability_family=blueprint.family,
                operator_specs=operator_specs_for(blueprint.family, blueprint.function_name),
                generator_improvement=generator_feedback(
                    "operator synthesis",
                    "adds a reusable solver primitive and counterexample tests for future candidate generation",
                    f"{blueprint.function_name} can be reused on later {blueprint.family} fixtures",
                ),
            )
        )
    return candidates


EXTERNAL_REPAIR_BUGGY = '''def external_failure_signal(events):
    """Return failure signal from an event stream."""

    return ""
'''


EXTERNAL_REPAIR_FIXED = '''def external_failure_signal(events):
    """Return the first failure-like signal from an event stream."""

    for event in events:
        text = str(event)
        lowered = text.lower()
        if any(token in lowered for token in ("error", "fail", "exception", "traceback", "assert")):
            return text
    return str(events[0]) if events else ""
'''


EXTERNAL_REPAIR_TEST = '''from pathlib import Path

from shared.external_repair_target import external_failure_signal


def test_external_failure_signal_preserves_first_failure():
    events = ("metadata_loaded", "read_error", "empty_content")

    assert external_failure_signal(events) == "read_error"


def test_external_sandbox_text_fixtures_are_local_inputs():
    root = Path.cwd() / "external_sandbox"

    assert (root / "source_snippet.txt").read_text(encoding="utf-8")
    assert (root / "failure_excerpt.txt").read_text(encoding="utf-8")
'''


def repair_external_failure_target(text: str) -> str:
    """Repair the local external-code failure target."""

    if EXTERNAL_REPAIR_FIXED in text:
        return text
    return replace_once(
        text,
        EXTERNAL_REPAIR_BUGGY,
        EXTERNAL_REPAIR_FIXED,
        "external_code_repair_failure_signal_v1",
    )


def external_code_repair_candidates(repo_root: Path, generation: int) -> List[CandidatePatch]:
    """Plan local executable repairs derived from external-code failure fixtures."""

    target = repo_root / "shared" / "external_repair_target.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    if EXTERNAL_REPAIR_FIXED in text:
        return []
    return [
        CandidatePatch(
            name="external_code_repair_failure_signal_v1",
            generation=generation,
            goal=Goal(
                name="repair_external_code_failure_fixture",
                target="shared.external_repair_target.external_failure_signal",
                metric="local external sandbox repair test passes",
                rationale=(
                    "External source and failure excerpts have been converted into "
                    "a local executable repair target instead of a metadata-only summary."
                ),
            ),
            target_path=target,
            test_path=repo_root / "tests" / "test_external_code_repair_task.py",
            transform=repair_external_failure_target,
            test_source=EXTERNAL_REPAIR_TEST,
            focused_tests=("tests/test_external_code_repair_task.py",),
            capability_family="external_code_repair",
            operator_specs=operator_specs_for("external_code_repair", "external_failure_signal"),
            generator_improvement=generator_feedback(
                "external-code failure fixtures",
                "converts fetched source and failure excerpts into reusable local repair tasks",
                "future external fixtures can be ranked by executable repair outcome, not metadata presence",
            ),
        )
    ]


POLICY_REGISTRY_SOURCE = '''"""Candidate policy registry for the closed RSI loop.

The registry is intentionally declarative. It gives experiments a stable
surface for measuring what the loop is allowed to change, how candidates are
validated, how rollback works, and which safety constraints are active.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class PolicyCapability:
    """One measurable policy surface exposed by the loop."""

    name: str
    category: str
    evidence: str
    risk_control: str


def default_policy_capabilities() -> Tuple[PolicyCapability, ...]:
    """Return the generator, validator, patch, and safety policy surfaces."""

    return (
        PolicyCapability(
            name="source_tree_candidate_generation",
            category="generator",
            evidence="candidate factories inspect repository state before proposing patches",
            risk_control="candidate names are deterministic and budget bounded",
        ),
        PolicyCapability(
            name="history_aware_candidate_ranking",
            category="generator",
            evidence="candidate order is derived from persisted accepted/rejected provenance",
            risk_control="previously rejected candidate names are retried only after fresher options",
        ),
        PolicyCapability(
            name="schema_driven_candidate_synthesis",
            category="generator",
            evidence="the planner infers missing query APIs from dataclass fields and generates tests",
            risk_control="generated candidates remain deterministic and must pass validation gates",
        ),
        PolicyCapability(
            name="bounded_emergent_hypothesis_search",
            category="generator",
            evidence="the planner creates competing canonical and alternate hypotheses and scores them with rejection history",
            risk_control="hypothesis count is capped and every selected hypothesis still passes the same gates",
        ),
        PolicyCapability(
            name="operator_synthesis_surface",
            category="generator",
            evidence="capability repair candidates generate solver primitives, search heuristics, evaluator mutations, and counterexample tests",
            risk_control="each synthesized operator carries an executable validation plan before promotion",
        ),
        PolicyCapability(
            name="capability_delta_scoring",
            category="validator",
            evidence="accepted and rejected candidate records include solved task, hidden transfer, regression, reuse, and compute-cost signals",
            risk_control="promotion evidence separates target success from regression and transfer behavior",
        ),
        PolicyCapability(
            name="failure_residue_extraction",
            category="validator",
            evidence="rejected candidates persist failed reason, missing operator, missing abstraction, evaluator, and overfit signal",
            risk_control="future candidate ranking can use failure residue instead of retrying blind",
        ),
        PolicyCapability(
            name="compile_focused_broad_validation",
            category="validator",
            evidence="candidates must pass py_compile, focused pytest, root pytest, and THDSE core gates",
            risk_control="failed gates prevent promotion",
        ),
        PolicyCapability(
            name="atomic_patch_with_extra_files",
            category="patch_policy",
            evidence="candidate patches may change a target file plus declared supporting files",
            risk_control="rollback restores all touched files on rejection",
        ),
        PolicyCapability(
            name="bounded_governed_execution",
            category="safety",
            evidence="wall-clock budgets, command timeouts, kill switch, and persisted provenance",
            risk_control="no unbounded runaway loop is permitted",
        ),
    )


def candidate_policy_summary() -> Dict[str, object]:
    """Return a JSON-compatible summary for experiment reports."""

    capabilities = default_policy_capabilities()
    categories = sorted({capability.category for capability in capabilities})
    return {
        "capability_count": len(capabilities),
        "categories": categories,
        "capabilities": [asdict(capability) for capability in capabilities],
    }
'''


POLICY_REGISTRY_TEST = '''from scripts.closed_recursive_self_improvement_loop import (
    ClosedRecursiveSelfImprovementLoop,
    load_policy_registry,
)
from scripts.rsi_policy_registry import candidate_policy_summary


def test_policy_registry_exposes_required_policy_surfaces(tmp_path):
    summary = candidate_policy_summary()

    assert summary["capability_count"] >= 4
    assert set(summary["categories"]) == {
        "generator",
        "patch_policy",
        "safety",
        "validator",
    }


def test_closed_loop_exposes_policy_surface():
    loop = ClosedRecursiveSelfImprovementLoop(__import__("pathlib").Path.cwd())
    surface = loop.policy_surface()

    assert surface["available"] is True
    assert "generator_policy" in surface["capabilities"]
    assert load_policy_registry(__import__("pathlib").Path.cwd()) == surface
'''


POLICY_REGISTRY_ACTIVE = True


def load_policy_registry(repo_root: Path) -> Dict[str, object]:
    """Return metadata for the active candidate policy registry."""

    registry_path = repo_root / "scripts" / "rsi_policy_registry.py"
    if not registry_path.exists():
        return {
            "available": False,
            "path": str(registry_path.relative_to(repo_root)),
            "capabilities": [],
        }
    return {
        "available": True,
        "path": str(registry_path.relative_to(repo_root)),
        "capabilities": [
            "generator_policy",
            "validator_policy",
            "patch_policy",
            "safety_policy",
        ],
    }


class ClosedRecursiveSelfImprovementLoop:
    """Persistent patch-test-promote loop over the real source tree."""

    def __init__(
        self,
        repo_root: Path,
        *,
        state_dir: Optional[Path] = None,
        broad_gate: bool = False,
        thdse_core_gate: bool = True,
        timeout_s: int = 300,
        dry_run: bool = True,
        rollback: bool = True,
        persistence: bool = True,
        exploration_policy: str = "conservative",
        exploration_depth: int = 0,
        exploration_seed: str = "closed_rsi_quarantine_v1",
        capability_seed: str = "closed_rsi_capability_dynamic_v1",
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
        self.thdse_core_gate = bool(thdse_core_gate)
        self.timeout_s = int(timeout_s)
        self.dry_run = bool(dry_run)
        self.rollback = bool(rollback)
        self.persistence = bool(persistence)
        self.exploration_policy = str(exploration_policy)
        self.exploration_depth = max(0, int(exploration_depth))
        self.exploration_seed = str(exploration_seed)
        self.capability_seed = str(capability_seed)
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(self.repo_root)

    def policy_surface(self) -> Dict[str, object]:
        """Expose the active generator, validator, patch, and safety policy surface."""

        return load_policy_registry(self.repo_root)

    def load_state(self) -> dict:
        state = read_json(self.state_path, {})
        if not isinstance(state, dict):
            state = {}
        state.setdefault("accepted", [])
        state.setdefault("rejected", [])
        state.setdefault("quarantine_exploration", [])
        state.setdefault("active_generation", 0)
        state.setdefault("active_base", "initial")
        return state

    def save_state(self, state: dict) -> None:
        if not self.persistence:
            return
        write_json(self.state_path, state)

    def invent_candidates(self, generation: int, state: Optional[dict] = None) -> List[CandidatePatch]:
        """Invent candidates from missing source capabilities."""

        loop_script = self.repo_root / "scripts" / "closed_recursive_self_improvement_loop.py"
        loop_text = loop_script.read_text(encoding="utf-8") if loop_script.exists() else ""
        candidates = []
        candidates.extend(external_code_repair_candidates(self.repo_root, generation))
        candidates.extend(capability_operator_candidates(self.repo_root, generation))
        candidates.extend(autonomous_local_corpus_candidates(self.repo_root, generation, state=state))

        if loop_script.exists() and POLICY_REGISTRY_ACTIVE_MARKER not in loop_text:
            goal = Goal(
                name="make_generator_policy_surface_explicit",
                target="scripts.closed_recursive_self_improvement_loop",
                metric="self-patchable policy registry plus focused regression test",
                rationale=(
                    "The loop can promote source candidates, but it needs a measurable "
                    "policy surface for generator, validator, patch, and safety ablations."
                ),
            )
            candidates.append(
                CandidatePatch(
                    name="loop_policy_registry_v1",
                    generation=generation,
                    goal=goal,
                    target_path=loop_script,
                    test_path=self.repo_root / "tests" / "test_rsi_policy_registry_rewrite.py",
                    transform=add_policy_registry_hook,
                    test_source=POLICY_REGISTRY_TEST,
                    focused_tests=("tests/test_rsi_policy_registry_rewrite.py",),
                    extra_files={
                        "scripts/rsi_policy_registry.py": POLICY_REGISTRY_SOURCE,
                    },
                    capability_family="generator_policy_repair",
                    operator_specs=operator_specs_for("generator_policy_repair", "policy_surface"),
                    generator_improvement=generator_feedback(
                        "candidate policy registry",
                        "turns generator, validator, patch, and safety policies into measurable search inputs",
                        "future experiments can ablate and rank candidates by explicit policy capabilities",
                    ),
                )
            )

        return candidates

    def rank_candidates(self, candidates: Sequence[CandidatePatch], state: dict) -> List[CandidatePatch]:
        """Rank candidates with persisted acceptance and rejection provenance."""

        accepted_names = {
            str(record.get("name"))
            for record in state.get("accepted", [])
            if isinstance(record, dict)
        }
        rejected_names = {
            str(record.get("name"))
            for record in state.get("rejected", [])
            if isinstance(record, dict)
        }

        def candidate_key(candidate: CandidatePatch) -> Tuple[int, int, int, int, str]:
            rejected_penalty = 1 if candidate.name in rejected_names else 0
            novelty_bonus = 0 if candidate.name not in accepted_names else 1
            executable_repair_bonus = 0 if candidate.name.startswith(("external_code_repair_", "capability_operator_")) else 1
            policy_bonus = 0 if candidate.name.startswith("loop_policy") else 1
            return (rejected_penalty, novelty_bonus, executable_repair_bonus, policy_bonus, candidate.name)

        return sorted(candidates, key=candidate_key)

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

    def candidate_changed_sources(
        self,
        candidate: CandidatePatch,
        *,
        rewritten_target: str,
        original_target: str,
        original_test: Optional[str],
        original_extra: Dict[Path, Optional[str]],
        extra_paths: Dict[Path, str],
    ) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        """Return candidate file changes for anti-cheat inspection."""

        changed: Dict[str, Tuple[Optional[str], Optional[str]]] = {
            str(candidate.target_path.relative_to(self.repo_root)): (original_target, rewritten_target),
            str(candidate.test_path.relative_to(self.repo_root)): (original_test, candidate.test_source),
        }
        for path, source in extra_paths.items():
            changed[str(path.relative_to(self.repo_root))] = (original_extra.get(path), source)
        return changed

    def anti_cheat_gate(
        self,
        candidate: CandidatePatch,
        changed_sources: Dict[str, Tuple[Optional[str], Optional[str]]],
    ) -> Optional[GateResult]:
        """Return a failing anti-cheat gate when a candidate bypasses evaluation."""

        start = time.monotonic()
        findings = detect_anti_cheat_findings(
            changed_sources,
            cases=capability_cases_for_seed(self.capability_seed),
        )
        if not findings:
            return None
        elapsed = round(time.monotonic() - start, 3)
        payload = {
            "findings": [finding.to_dict() for finding in findings],
        }
        return GateResult(
            label=f"{candidate.name}_anti_cheat",
            args=["internal", "anti_cheat"],
            cwd=str(self.repo_root),
            exit_code=1,
            elapsed_s=elapsed,
            stdout_tail="",
            stderr_tail=json.dumps(payload, sort_keys=True),
        )

    def capability_evaluations(self, candidate: CandidatePatch) -> Tuple[CapabilityEvaluation, ...]:
        """Run dynamic capability evaluator cases for a candidate primitive."""

        if candidate.capability_family not in CAPABILITY_FAMILIES:
            return ()
        cases = tuple(
            case
            for case in capability_cases_for_seed(self.capability_seed)
            if case.family == candidate.capability_family
        )
        if not cases:
            return ()
        operators = load_capability_operators(candidate.target_path, capability_operator_names(candidate))
        return evaluate_capability_cases(operators, cases)

    def capability_evaluator_gate(self, candidate: CandidatePatch) -> Optional[GateResult]:
        """Return an executable capability evaluator gate for capability candidates."""

        if candidate.capability_family not in CAPABILITY_FAMILIES:
            return None
        start = time.monotonic()
        try:
            evaluations = self.capability_evaluations(candidate)
            exit_code = 0 if evaluations and all(item.solved for item in evaluations) else 1
            payload = {
                "seed": self.capability_seed,
                "evaluations": [asdict(item) for item in evaluations],
            }
            elapsed = round(time.monotonic() - start, 3)
            return GateResult(
                label=f"{candidate.name}_capability_evaluator",
                args=["internal", "capability_evaluator", self.capability_seed],
                cwd=str(self.repo_root),
                exit_code=exit_code,
                elapsed_s=elapsed,
                stdout_tail=json.dumps(payload, sort_keys=True)[-4000:],
                stderr_tail="" if exit_code == 0 else "one or more capability evaluator cases failed",
            )
        except Exception as exc:
            elapsed = round(time.monotonic() - start, 3)
            return GateResult(
                label=f"{candidate.name}_capability_evaluator",
                args=["internal", "capability_evaluator", self.capability_seed],
                cwd=str(self.repo_root),
                exit_code=1,
                elapsed_s=elapsed,
                stdout_tail="",
                stderr_tail=f"{type(exc).__name__}: {exc}",
            )

    def validate(self, candidate: CandidatePatch) -> List[GateResult]:
        py = sys.executable
        compile_targets = [
            str(candidate.target_path.relative_to(self.repo_root)),
            str(candidate.test_path.relative_to(self.repo_root)),
        ]
        compile_targets.extend(
            path
            for path in sorted(candidate.extra_files)
            if path.endswith(".py")
        )
        gates = [
            self.run_command(
                f"{candidate.name}_compile",
                [py, "-m", "py_compile", *compile_targets],
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
        capability_gate = self.capability_evaluator_gate(candidate)
        if capability_gate is not None:
            gates.append(capability_gate)
        if self.broad_gate:
            gates.append(
                self.run_command(
                    f"{candidate.name}_root_broad",
                    [py, "-m", "pytest", "-q", "--import-mode=importlib", "--maxfail=20", "--disable-warnings", "tests"],
                    self.repo_root,
                )
            )
            if self.thdse_core_gate and self.thdse_root.exists():
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
        extra_paths = {
            (self.repo_root / relative_path): source
            for relative_path, source in candidate.extra_files.items()
        }
        original_extra = {
            path: path.read_text(encoding="utf-8") if path.exists() else None
            for path in extra_paths
        }
        gates: List[GateResult] = []
        error = ""
        accepted = False
        capability_delta: Dict[str, object] = {}

        try:
            rewritten = candidate.transform(original_target)
            missing_extra = [path for path in extra_paths if not path.exists()]
            if rewritten == original_target and not missing_extra:
                raise RuntimeError("candidate made no source change")
            changed_sources = self.candidate_changed_sources(
                candidate,
                rewritten_target=rewritten,
                original_target=original_target,
                original_test=original_test,
                original_extra=original_extra,
                extra_paths=extra_paths,
            )
            anti_cheat = self.anti_cheat_gate(candidate, changed_sources)
            if anti_cheat is not None:
                gates.append(anti_cheat)
                raise RuntimeError("anti-cheat validation failed")
            if self.dry_run:
                accepted = True
            else:
                candidate.target_path.write_text(rewritten, encoding="utf-8")
                candidate.test_path.parent.mkdir(parents=True, exist_ok=True)
                candidate.test_path.write_text(candidate.test_source, encoding="utf-8")
                for path, source in extra_paths.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(source, encoding="utf-8")
                gates = self.validate(candidate)
                capability_delta = candidate_capability_delta(
                    candidate,
                    accepted=all(gate.exit_code == 0 for gate in gates),
                    gates=gates,
                    evaluations=self.capability_evaluations(candidate),
                )
                accepted = all(gate.exit_code == 0 for gate in gates)
                if not accepted:
                    raise RuntimeError("one or more validation gates failed")
            if accepted and not candidate.generator_improvement:
                raise RuntimeError("accepted candidate lacks generator improvement evidence")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            accepted = False
            if not self.dry_run and self.rollback:
                candidate.target_path.write_text(original_target, encoding="utf-8")
                if original_test is None:
                    try:
                        candidate.test_path.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    candidate.test_path.write_text(original_test, encoding="utf-8")
                for path, original in original_extra.items():
                    if original is None:
                        try:
                            path.unlink()
                        except FileNotFoundError:
                            pass
                    else:
                        path.write_text(original, encoding="utf-8")
        if not capability_delta:
            capability_delta = candidate_capability_delta(candidate, accepted=accepted, gates=gates)

        return CandidateRecord(
            name=candidate.name,
            generation=candidate.generation,
            goal=asdict(candidate.goal),
            target_path=str(candidate.target_path.relative_to(self.repo_root)),
            test_path=str(candidate.test_path.relative_to(self.repo_root)),
            extra_paths=sorted(candidate.extra_files),
            accepted=accepted,
            started_at=started,
            finished_at=utc_now(),
            gates=[asdict(gate) for gate in gates],
            error=error,
            capability_delta=capability_delta,
            failure_residue=candidate_failure_residue(candidate, accepted=accepted, gates=gates, error=error),
            operator_synthesis=[dict(spec) for spec in candidate.operator_specs],
            generator_improvement=dict(candidate.generator_improvement),
            promoted=accepted,
        )

    def exploration_enabled(self) -> bool:
        return self.exploration_policy in {"recursive_quarantine", "high_entropy_quarantine"} and self.exploration_depth > 0

    def rank_quarantine_candidates(
        self,
        candidates: Sequence[CandidatePatch],
        state: dict,
        depth: int,
    ) -> List[CandidatePatch]:
        """Rank quarantine candidates by deterministic high-entropy seed order."""

        accepted_names = set(names_from_state(state, "accepted"))
        rejected_names = set(names_from_state(state, "rejected"))

        def candidate_key(candidate: CandidatePatch) -> Tuple[int, str, str]:
            seen_penalty = 1 if candidate.name in accepted_names or candidate.name in rejected_names else 0
            digest = hashlib.sha256(
                f"{self.exploration_seed}:{depth}:{candidate.name}:{candidate.goal.name}".encode("utf-8")
            ).hexdigest()
            return (seen_penalty, digest, candidate.name)

        return sorted(candidates, key=candidate_key)

    def run_quarantine_exploration(
        self,
        state: dict,
        *,
        max_candidates: int,
        started: float,
        wall_seconds: int,
    ) -> List[dict]:
        """Explore deeper candidate chains in a disposable quarantine copy."""

        if not self.exploration_enabled():
            return []
        records: List[dict] = []
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="closed_rsi_quarantine_", dir=str(self.state_dir)) as tmp:
            quarantine_root = Path(tmp) / "repo"
            copy_repo_to_quarantine(self.repo_root, quarantine_root)
            quarantine_loop = ClosedRecursiveSelfImprovementLoop(
                quarantine_root,
                state_dir=Path(tmp) / "state",
                broad_gate=self.broad_gate,
                thdse_core_gate=self.thdse_core_gate,
                timeout_s=self.timeout_s,
                dry_run=False,
                rollback=False,
                persistence=False,
                exploration_policy="conservative",
                exploration_depth=0,
                exploration_seed=self.exploration_seed,
                capability_seed=self.capability_seed,
            )
            quarantine_state = {
                "accepted": [],
                "rejected": [],
                "quarantine_exploration": [],
                "active_generation": int(state.get("active_generation", 0)),
                "active_base": state.get("active_base", "initial"),
            }
            attempted = set()
            for depth in range(1, self.exploration_depth + 1):
                if self.kill_switch_path.exists() or time.monotonic() - started > wall_seconds:
                    break
                generation = int(quarantine_state.get("active_generation", 0)) + 1
                candidates = quarantine_loop.invent_candidates(generation, quarantine_state)
                ranked = self.rank_quarantine_candidates(candidates, quarantine_state, depth)
                if not ranked:
                    break
                tried_at_depth = 0
                for candidate in ranked:
                    if tried_at_depth >= max_candidates:
                        break
                    if candidate.name in attempted:
                        continue
                    record = quarantine_loop.apply_candidate(candidate)
                    record.quarantine = True
                    record.promoted = False
                    record.chain_depth = depth
                    payload = asdict(record)
                    records.append(payload)
                    attempted.add(candidate.name)
                    tried_at_depth += 1
                    if record.accepted:
                        quarantine_state["accepted"].append(payload)
                        quarantine_state["active_generation"] = generation
                        quarantine_state["active_base"] = candidate.name
                    else:
                        quarantine_state["rejected"].append(payload)
                    quarantine_state["quarantine_exploration"].append(payload)
                if tried_at_depth == 0:
                    break
        return records

    def run(self, *, max_generations: int = 10, max_candidates: int = 10, wall_seconds: int = 1800) -> dict:
        """Run the closed loop until budget, kill switch, or no candidates."""

        state = self.load_state()
        started = time.monotonic()
        accepted_this_run: List[dict] = []
        rejected_this_run: List[dict] = []
        quarantine_exploration: List[dict] = []

        for _ in range(max_generations):
            if self.kill_switch_path.exists():
                break
            if time.monotonic() - started > wall_seconds:
                break
            generation = int(state.get("active_generation", 0)) + 1
            candidates = self.rank_candidates(self.invent_candidates(generation, state), state)
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

        if not self.kill_switch_path.exists() and time.monotonic() - started <= wall_seconds:
            quarantine_exploration = self.run_quarantine_exploration(
                state,
                max_candidates=max_candidates,
                started=started,
                wall_seconds=wall_seconds,
            )
            if quarantine_exploration:
                state.setdefault("quarantine_exploration", []).extend(quarantine_exploration)
                self.save_state(state)

        run_records = [*accepted_this_run, *rejected_this_run]
        summary = {
            "dry_run": self.dry_run,
            "broad_gate": self.broad_gate,
            "thdse_core_gate": self.thdse_core_gate,
            "rollback": self.rollback,
            "persistence": self.persistence,
            "exploration_policy": self.exploration_policy,
            "exploration_depth": self.exploration_depth,
            "state_path": str(self.state_path),
            "accepted_this_run": accepted_this_run,
            "rejected_this_run": rejected_this_run,
            "quarantine_exploration": quarantine_exploration,
            "active_generation": state.get("active_generation", 0),
            "active_base": state.get("active_base", "initial"),
            "total_accepted": len(state.get("accepted", [])),
            "total_rejected": len(state.get("rejected", [])),
            "total_quarantine_exploration": len(state.get("quarantine_exploration", [])),
            "quarantine_max_depth": max(
                (int(record.get("chain_depth", 0) or 0) for record in quarantine_exploration),
                default=0,
            ),
            "capability_delta_score": round(
                sum(float(record.get("capability_delta", {}).get("score", 0.0) or 0.0) for record in run_records),
                3,
            ),
            "solved_new_tasks": sum(
                int(record.get("capability_delta", {}).get("solved_new_tasks", 0) or 0) for record in run_records
            ),
            "hidden_transfer": sum(
                int(record.get("capability_delta", {}).get("hidden_transfer", 0) or 0) for record in run_records
            ),
            "operator_reuse": sum(
                int(record.get("capability_delta", {}).get("operator_reuse", 0) or 0) for record in run_records
            ),
            "failure_residue_count": sum(1 for record in run_records if record.get("failure_residue")),
            "quarantine_failure_residue_count": sum(
                1 for record in quarantine_exploration if record.get("failure_residue")
            ),
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
    parser.add_argument("--no-thdse-core-gate", action="store_true", help="Skip the THDSE core gate inside broad validation.")
    parser.add_argument("--no-rollback", action="store_true", help="Leave rejected candidate changes in place. Use only in disposable experiment copies.")
    parser.add_argument("--no-persistence", action="store_true", help="Do not persist accepted/rejected state between runs.")
    parser.add_argument("--max-generations", type=int, default=10)
    parser.add_argument("--max-candidates", type=int, default=10)
    parser.add_argument("--wall-seconds", type=int, default=1800)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--exploration-policy",
        choices=("conservative", "recursive_quarantine", "high_entropy_quarantine"),
        default="conservative",
        help="Run deeper recursive exploration in a disposable quarantine copy.",
    )
    parser.add_argument("--exploration-depth", type=int, default=0)
    parser.add_argument("--exploration-seed", default="closed_rsi_quarantine_v1")
    parser.add_argument("--capability-seed", default="closed_rsi_capability_dynamic_v1")
    args = parser.parse_args(argv)

    repo_root = args.repo_root or find_repo_root(Path.cwd())
    loop = ClosedRecursiveSelfImprovementLoop(
        repo_root,
        state_dir=args.state_dir,
        broad_gate=args.broad_gate,
        thdse_core_gate=not args.no_thdse_core_gate,
        timeout_s=args.timeout_seconds,
        dry_run=not args.apply,
        rollback=not args.no_rollback,
        persistence=not args.no_persistence,
        exploration_policy=args.exploration_policy,
        exploration_depth=args.exploration_depth,
        exploration_seed=args.exploration_seed,
        capability_seed=args.capability_seed,
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
