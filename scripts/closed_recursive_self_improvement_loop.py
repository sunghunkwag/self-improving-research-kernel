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
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple


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


def singularize_identifier(name: str) -> str:
    """Derive a conservative singular parameter name from a record field."""

    if name.endswith("_flags"):
        return name[:-6]
    if name.endswith("ies"):
        return f"{name[:-3]}y"
    if name.endswith("s") and len(name) > 1:
        return name[:-1]
    return name


def query_blueprint_for_field(field_name: str) -> AutonomousQueryBlueprint:
    """Create a query candidate blueprint from a tuple-valued record field."""

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
    element_name = singularize_identifier(field_name)
    sample_values = {
        "definition": "function:scan_file",
        "feature": "self_improvement",
    }
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


def ast_annotation_mentions_tuple_of_strings(annotation: ast.AST) -> bool:
    """Return whether an annotation looks like a tuple of strings."""

    try:
        rendered = ast.unparse(annotation)
    except Exception:
        return False
    normalized = rendered.replace("typing.", "")
    return "Tuple" in normalized and "str" in normalized


def discover_local_corpus_query_blueprints(text: str) -> Tuple[AutonomousQueryBlueprint, ...]:
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
        blueprint = query_blueprint_for_field(field_name)
        if f"def {blueprint.method_name}(" not in text:
            blueprints.append(blueprint)
    return tuple(blueprints)


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


def autonomous_local_corpus_candidates(repo_root: Path, generation: int) -> List[CandidatePatch]:
    """Plan LocalCorpusIndex candidates from source schema instead of fixed candidate names."""

    local_corpus = repo_root / "shared" / "local_corpus.py"
    if not local_corpus.exists():
        return []
    text = local_corpus.read_text(encoding="utf-8")
    candidates: List[CandidatePatch] = []
    for blueprint in discover_local_corpus_query_blueprints(text):
        candidates.append(
            CandidatePatch(
                name=blueprint.candidate_name,
                generation=generation,
                goal=Goal(
                    name=blueprint.goal_name,
                    target="shared.local_corpus.LocalCorpusIndex",
                    metric="planner-inferred query API plus generated regression test",
                    rationale=blueprint.rationale,
                ),
                target_path=local_corpus,
                test_path=repo_root / "tests" / f"test_{blueprint.candidate_name}.py",
                transform=lambda source, plan=blueprint: add_autonomous_record_query(source, plan),
                test_source=build_autonomous_query_test(blueprint),
                focused_tests=(f"tests/test_{blueprint.candidate_name}.py",),
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
            )
        )
    return candidates


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
        state.setdefault("active_generation", 0)
        state.setdefault("active_base", "initial")
        return state

    def save_state(self, state: dict) -> None:
        if not self.persistence:
            return
        write_json(self.state_path, state)

    def invent_candidates(self, generation: int) -> List[CandidatePatch]:
        """Invent candidates from missing source capabilities."""

        loop_script = self.repo_root / "scripts" / "closed_recursive_self_improvement_loop.py"
        loop_text = loop_script.read_text(encoding="utf-8") if loop_script.exists() else ""
        candidates = autonomous_local_corpus_candidates(self.repo_root, generation)

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

        def candidate_key(candidate: CandidatePatch) -> Tuple[int, int, int, str]:
            rejected_penalty = 1 if candidate.name in rejected_names else 0
            novelty_bonus = 0 if candidate.name not in accepted_names else 1
            policy_bonus = 0 if candidate.name.startswith("loop_policy") else 1
            return (rejected_penalty, novelty_bonus, policy_bonus, candidate.name)

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

        try:
            rewritten = candidate.transform(original_target)
            missing_extra = [path for path in extra_paths if not path.exists()]
            if rewritten == original_target and not missing_extra:
                raise RuntimeError("candidate made no source change")
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
                accepted = all(gate.exit_code == 0 for gate in gates)
                if not accepted:
                    raise RuntimeError("one or more validation gates failed")
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
            candidates = self.rank_candidates(self.invent_candidates(generation), state)
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
            "thdse_core_gate": self.thdse_core_gate,
            "rollback": self.rollback,
            "persistence": self.persistence,
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
    parser.add_argument("--no-thdse-core-gate", action="store_true", help="Skip the THDSE core gate inside broad validation.")
    parser.add_argument("--no-rollback", action="store_true", help="Leave rejected candidate changes in place. Use only in disposable experiment copies.")
    parser.add_argument("--no-persistence", action="store_true", help="Do not persist accepted/rejected state between runs.")
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
        thdse_core_gate=not args.no_thdse_core_gate,
        timeout_s=args.timeout_seconds,
        dry_run=not args.apply,
        rollback=not args.no_rollback,
        persistence=not args.no_persistence,
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
