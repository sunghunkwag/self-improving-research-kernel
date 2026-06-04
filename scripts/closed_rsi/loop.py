"""Closed recursive self-improvement loop for OMEGA-THDSE.

This module intentionally does not implement an unbounded runaway loop.
It implements a persistent, closed engineering loop over the real
OMEGA-THDSE source tree:

1. Inspect the current active source tree.
2. Invent a measurable improvement goal from missing project capability.
3. Generate a concrete source patch and matching regression test.
4. Apply the patch to real files.
5. Run compile, focused diagnostics, and the full pytest suite.
6. Promote only passing candidates; rollback failures.
7. Persist accepted/rejected records so the next generation starts from
   the latest accepted base.

The loop can run repeatedly in Colab, but every run has explicit budgets,
a kill-switch file, and rollback semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from shared.capability_benchmarks import (
    CAPABILITY_FAMILIES,
    CapabilityEvaluation,
    capability_cases_for_seed,
    detect_anti_cheat_findings,
    evaluate_capability_cases,
)
from scripts.closed_rsi.evaluators.capability import (
    candidate_capability_delta,
    candidate_failure_residue,
    capability_operator_names,
    load_capability_operators,
    operator_specs_for,
    top_level_function_source,
)
from scripts.closed_rsi.gates.results import FULL_TEST_COMMAND, GateResult, full_test_exit_code
from scripts.closed_rsi.gates.rollback import copy_repo_to_quarantine
from scripts.closed_rsi.generators.ast_synthesis import ast_synthesis_candidates
from scripts.closed_rsi.generators.capability import capability_operator_candidates
from scripts.closed_rsi.generators.common import names_from_state
from scripts.closed_rsi.generators.external_code import external_code_repair_candidates
from scripts.closed_rsi.generators.local_corpus import (
    autonomous_local_corpus_candidates,
    query_blueprint_for_field,
    schema_batch_query_candidates,
)
from scripts.closed_rsi.generators.policy_registry import (
    POLICY_REGISTRY_ACTIVE_MARKER,
    POLICY_REGISTRY_SOURCE,
    POLICY_REGISTRY_TEST,
    add_policy_registry_hook,
    load_policy_registry,
)
from scripts.closed_rsi.records import (
    CandidatePatch,
    CandidateRecord,
    Goal,
    generator_feedback,
    read_json,
    source_sha256,
    utc_now,
    write_json,
)


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
        candidates.extend(
            external_code_repair_candidates(
                self.repo_root,
                generation,
                include_recursive_general=self.exploration_policy == "recursive_quarantine",
            )
        )
        candidates.extend(ast_synthesis_candidates(self.repo_root, generation))
        candidates.extend(capability_operator_candidates(self.repo_root, generation))
        if self.exploration_policy == "recursive_quarantine":
            candidates.extend(schema_batch_query_candidates(self.repo_root, generation, state=state))
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

        schema_transfer_active = (self.repo_root / "schema_transfer_manifest.json").exists()

        def candidate_key(candidate: CandidatePatch) -> Tuple[int, int, int, int, int, str, str]:
            rejected_penalty = 1 if candidate.name in rejected_names else 0
            novelty_bonus = 0 if candidate.name not in accepted_names else 1
            schema_transfer_candidate = schema_transfer_active and candidate.name.startswith(
                (
                    "recursive_schema_batch_",
                    "autonomous_local_corpus_",
                )
            )
            executable_repair_bonus = (
                0
                if schema_transfer_candidate
                or candidate.name.startswith(
                    (
                        "external_code_repair_",
                        "capability_operator_",
                    )
                )
                else 1
            )
            policy_bonus = 0 if candidate.name.startswith("loop_policy") else 1
            ast_synthesis_bonus = 0 if candidate.name.startswith("external_code_repair_ast_") else 1
            if candidate.name.startswith("external_code_repair_") or schema_transfer_candidate:
                seed_tiebreak = hashlib.sha256(
                    f"{self.capability_seed}:{candidate.name}:{candidate.goal.name}".encode("utf-8")
                ).hexdigest()
            else:
                seed_tiebreak = candidate.name
            return (
                rejected_penalty,
                novelty_bonus,
                executable_repair_bonus,
                ast_synthesis_bonus,
                policy_bonus,
                seed_tiebreak,
                candidate.name,
            )

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

    def collect_test_nodeids(self, label: str) -> Tuple[GateResult, Tuple[str, ...]]:
        """Collect pytest node ids so candidates cannot narrow the suite."""

        py = sys.executable
        args = [py, "-m", "pytest", "--collect-only", "-q"]
        start = time.monotonic()
        stdout = ""
        stderr = ""
        exit_code = 1
        timed_out = False
        try:
            proc = subprocess.run(
                args,
                cwd=str(self.repo_root),
                env=self.env,
                text=True,
                capture_output=True,
                timeout=self.timeout_s,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else "collection timed out"
            exit_code = 124
            timed_out = True
        if exit_code == 5 and "no tests collected" in f"{stdout}\n{stderr}".lower():
            exit_code = 0
        elapsed = round(time.monotonic() - start, 3)
        gate = GateResult(
            label=label,
            args=args,
            cwd=str(self.repo_root),
            exit_code=exit_code,
            elapsed_s=elapsed,
            stdout_tail=stdout[-4000:],
            stderr_tail=stderr[-2000:],
            timed_out=timed_out,
        )
        nodeids: List[str] = []
        if gate.exit_code == 0:
            for raw_line in stdout.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("=") or "collected" in line:
                    continue
                if "::" in line:
                    nodeids.append(line)
        return gate, tuple(dict.fromkeys(nodeids))

    def test_collection_superset_gate(
        self,
        before: Sequence[str],
        after: Sequence[str],
    ) -> Optional[GateResult]:
        """Return a failing gate if a candidate removes collected tests."""

        missing = sorted(set(before) - set(after))
        if not missing:
            return None
        payload = {
            "before_count": len(before),
            "after_count": len(after),
            "missing_nodeids": missing[:25],
        }
        return GateResult(
            label="candidate_test_collection_superset",
            args=["internal", "pytest_collect_superset"],
            cwd=str(self.repo_root),
            exit_code=1,
            elapsed_s=0.0,
            stdout_tail="",
            stderr_tail=json.dumps(payload, sort_keys=True),
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

    def held_out_reference_gate(
        self,
        candidate: CandidatePatch,
        changed_sources: Dict[str, Tuple[Optional[str], Optional[str]]],
    ) -> Optional[GateResult]:
        """Reject a candidate that pastes the held-out primitive reference."""

        metadata = read_json(self.repo_root / "capability_fixture_metadata.json", {})
        reference_hash = str(metadata.get("held_out_reference_sha256", "") or "")
        operator = str(metadata.get("operator", "") or "")
        if not reference_hash or not operator:
            return None
        relative_target = str(candidate.target_path.relative_to(self.repo_root)).replace("\\", "/")
        if relative_target != "shared/capability_primitives.py":
            return None
        _before, after = changed_sources.get(relative_target, (None, None))
        if not after:
            return None
        candidate_source = top_level_function_source(after, operator)
        if not candidate_source or source_sha256(candidate_source) != reference_hash:
            return None
        payload = {
            "operator": operator,
            "held_out_reference_sha256": reference_hash,
        }
        return GateResult(
            label=f"{candidate.name}_held_out_reference",
            args=["internal", "held_out_reference_hash"],
            cwd=str(self.repo_root),
            exit_code=1,
            elapsed_s=0.0,
            stdout_tail="",
            stderr_tail=json.dumps(payload, sort_keys=True),
        )

    def external_code_reference_gate(
        self,
        candidate: CandidatePatch,
        changed_sources: Dict[str, Tuple[Optional[str], Optional[str]]],
    ) -> Optional[GateResult]:
        """Reject external-code candidates that paste or touch quarantined reference material."""

        metadata = read_json(self.repo_root / "external_code_repair_metadata.json", {})
        if not isinstance(metadata, dict):
            return None
        relative_target = str(candidate.target_path.relative_to(self.repo_root)).replace("\\", "/")
        buggy_source_path = str(metadata.get("buggy_source_path", "") or "")
        quarantine_paths = {
            str(path).replace("\\", "/")
            for path in metadata.get("quarantine_paths", [])
            if path
        }
        material_paths = {
            path.replace("\\", "/")
            for path, (before, after) in changed_sources.items()
            if before != after
        }
        touched_quarantine = sorted(material_paths & quarantine_paths)
        if touched_quarantine:
            payload = {
                "quarantine_paths": touched_quarantine,
                "overfit_signal": "candidate_touched_quarantined_reference_path",
            }
            return GateResult(
                label=f"{candidate.name}_external_code_quarantine_touch",
                args=["internal", "external_code_quarantine_touch"],
                cwd=str(self.repo_root),
                exit_code=1,
                elapsed_s=0.0,
                stdout_tail="",
                stderr_tail=json.dumps(payload, sort_keys=True),
            )
        if relative_target != buggy_source_path:
            return None
        _before, after = changed_sources.get(relative_target, (None, None))
        if not after:
            return None
        function_name = str(metadata.get("function_name", "merge_setting") or "merge_setting")
        candidate_source = top_level_function_source(after, function_name)
        reference_hash = str(metadata.get("held_out_reference_sha256", "") or "")
        if reference_hash and candidate_source and source_sha256(candidate_source) == reference_hash:
            payload = {
                "function_name": function_name,
                "held_out_reference_sha256": reference_hash,
                "overfit_signal": "verbatim_external_code_reference_function",
            }
            return GateResult(
                label=f"{candidate.name}_external_code_reference",
                args=["internal", "external_code_reference_hash"],
                cwd=str(self.repo_root),
                exit_code=1,
                elapsed_s=0.0,
                stdout_tail="",
                stderr_tail=json.dumps(payload, sort_keys=True),
            )
        forbidden_spans = {
            str(item)
            for item in metadata.get("held_out_reference_span_sha256", [])
            if item
        }
        if forbidden_spans and candidate_source:
            candidate_span_hashes = {
                source_sha256(line.strip())
                for line in candidate_source.splitlines()
                if len(line.strip()) >= 24
            }
            overlap = sorted(candidate_span_hashes & forbidden_spans)
            if overlap:
                payload = {
                    "function_name": function_name,
                    "span_hashes": overlap,
                    "overfit_signal": "verbatim_external_code_reference_span",
                }
                return GateResult(
                    label=f"{candidate.name}_external_code_reference_span",
                    args=["internal", "external_code_reference_span_hash"],
                    cwd=str(self.repo_root),
                    exit_code=1,
                    elapsed_s=0.0,
                    stdout_tail="",
                    stderr_tail=json.dumps(payload, sort_keys=True),
                )
        return None

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

    def schema_transfer_evaluator_gate(self, candidate: CandidatePatch) -> Optional[GateResult]:
        """Run freshly seeded hidden schema-query probes after candidate patching."""

        if not candidate.schema_fields:
            return None
        fields = tuple(dict.fromkeys(candidate.schema_fields))
        manifest = read_json(self.repo_root / "schema_transfer_manifest.json", {})
        required_fields = tuple(
            str(item.get("field_name", ""))
            for item in manifest.get("fields", [])
            if isinstance(item, dict) and item.get("field_name")
        ) if isinstance(manifest, dict) else ()
        if required_fields and not set(required_fields).issubset(set(fields)):
            payload = {
                "required_fields": required_fields,
                "candidate_fields": fields,
                "overfit_signal": "partial_schema_candidate_failed_composite_manifest",
            }
            return GateResult(
                label=f"{candidate.name}_schema_transfer_manifest",
                args=["internal", "schema_transfer_manifest"],
                cwd=str(self.repo_root),
                exit_code=1,
                elapsed_s=0.0,
                stdout_tail="",
                stderr_tail=json.dumps(payload, sort_keys=True),
            )
        hidden_inputs = {
            field: (
                f"hidden_{field}_"
                f"{hashlib.sha256(f'{self.capability_seed}:{field}'.encode('utf-8')).hexdigest()[:10]}"
            )
            for field in fields
        }
        methods = {field: query_blueprint_for_field(field).method_name for field in fields}
        probe = f'''
from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord

hidden_inputs = {hidden_inputs!r}
methods = {methods!r}
records = []
for offset, (field, value) in enumerate(hidden_inputs.items()):
    kwargs = dict(
        path=f"hidden_{{offset}}.py",
        sha256=str(offset),
        size_bytes=1,
        line_count=1,
        syntax_ok=True,
    )
    kwargs[field] = (value,)
    records.append(LocalPythonFileRecord(**kwargs))

index = LocalCorpusIndex(
    summary=LocalCorpusSummary(
        file_count=len(records),
        syntax_ok_count=len(records),
        syntax_error_count=0,
        unique_sha256_count=len(records),
        duplicate_file_instances=0,
        feature_counts={{}},
        import_edge_count=0,
        definition_count=0,
    ),
    records=tuple(records),
    import_edges=(),
)

for offset, (field, value) in enumerate(hidden_inputs.items()):
    method = getattr(index, methods[field])
    assert tuple(record.path for record in method(value)) == (f"hidden_{{offset}}.py",)
print({{"seed": {self.capability_seed!r}, "hidden_inputs": hidden_inputs, "methods": methods}})
'''
        py = sys.executable
        return self.run_command(
            f"{candidate.name}_schema_transfer_evaluator",
            [py, "-c", probe],
            self.repo_root,
        )

    def external_code_repair_evaluator_gate(self, candidate: CandidatePatch) -> Optional[GateResult]:
        """Run seed-derived hidden cases for executable external-code repairs."""

        if candidate.capability_family != "external_code_repair":
            return None
        metadata = read_json(self.repo_root / "external_code_repair_metadata.json", {})
        if not isinstance(metadata, dict) or metadata.get("function_name") != "merge_setting":
            return None
        digest = hashlib.sha256(f"{self.capability_seed}:external_code:merge_setting".encode("utf-8")).hexdigest()
        hidden_remove = f"X-Remove-{digest[:8]}"
        hidden_keep = f"X-Keep-{digest[8:16]}"
        hidden_new = f"X-New-{digest[16:24]}"
        probe = f'''
import json
import sys
from shared.external_repair_target import merge_setting

seed = {self.capability_seed!r}
hidden_remove = {hidden_remove!r}
hidden_keep = {hidden_keep!r}
hidden_new = {hidden_new!r}
session_headers = {{
    "User-Agent": "session-agent",
    hidden_remove: "remove-me",
    hidden_keep: "keep-me",
}}
request_headers = {{
    hidden_remove: None,
    hidden_new: "new-value",
}}
merged = merge_setting(request_headers, session_headers)
expected = {{
    "User-Agent": "session-agent",
    hidden_keep: "keep-me",
    hidden_new: "new-value",
}}
payload = {{
    "seed": seed,
    "hidden_counterexample_family": "requests_merge_setting_none_removal",
    "hidden_inputs": {{
        "remove_header": hidden_remove,
        "keep_header": hidden_keep,
        "new_header": hidden_new,
    }},
    "observed": dict(merged),
    "expected": expected,
}}
if dict(merged) != expected:
    payload["overfit_signal"] = "visible_passed_hidden_external_code_failed"
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    raise SystemExit(1)
print(json.dumps(payload, sort_keys=True))
'''
        py = sys.executable
        return self.run_command(
            f"{candidate.name}_external_code_hidden_evaluator",
            [py, "-c", probe],
            self.repo_root,
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
        if candidate.focused_tests:
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
        schema_gate = self.schema_transfer_evaluator_gate(candidate)
        if schema_gate is not None:
            gates.append(schema_gate)
        external_code_gate = self.external_code_repair_evaluator_gate(candidate)
        if external_code_gate is not None:
            gates.append(external_code_gate)
        if any(gate.exit_code != 0 for gate in gates):
            return gates
        gates.append(
            self.run_command(
                f"{candidate.name}_full_pytest",
                [py, "-m", "pytest", "-q"],
                self.repo_root,
            )
        )
        gates.append(
            self.run_command(
                f"{candidate.name}_repeat_full_pytest",
                [py, "-m", "pytest", "-q"],
                self.repo_root,
            )
        )
        if self.broad_gate:
            gates.append(
                self.run_command(
                    f"{candidate.name}_root_broad",
                    [py, "-m", "pytest", "-q"],
                    self.repo_root,
                )
            )
            if self.thdse_core_gate and self.thdse_root.exists():
                gates.append(
                    self.run_command(
                        f"{candidate.name}_thdse_full",
                        [py, "-m", "pytest", "-q"],
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
            reference_gate = self.held_out_reference_gate(candidate, changed_sources)
            if reference_gate is not None:
                gates.append(reference_gate)
                raise RuntimeError("held-out reference validation failed")
            external_reference_gate = self.external_code_reference_gate(candidate, changed_sources)
            if external_reference_gate is not None:
                gates.append(external_reference_gate)
                raise RuntimeError("external-code reference validation failed")
            pre_collect_gate, pre_nodeids = self.collect_test_nodeids(f"{candidate.name}_pre_collect")
            gates.append(pre_collect_gate)
            if pre_collect_gate.exit_code != 0:
                raise RuntimeError("pre-candidate pytest collection failed")
            if self.dry_run:
                raise RuntimeError("dry run cannot promote without full pytest")
            else:
                candidate.target_path.write_text(rewritten, encoding="utf-8")
                candidate.test_path.parent.mkdir(parents=True, exist_ok=True)
                candidate.test_path.write_text(candidate.test_source, encoding="utf-8")
                for path, source in extra_paths.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(source, encoding="utf-8")
                post_collect_gate, post_nodeids = self.collect_test_nodeids(f"{candidate.name}_post_collect")
                gates.append(post_collect_gate)
                if post_collect_gate.exit_code != 0:
                    raise RuntimeError("post-candidate pytest collection failed")
                superset_gate = self.test_collection_superset_gate(pre_nodeids, post_nodeids)
                if superset_gate is not None:
                    gates.append(superset_gate)
                    raise RuntimeError("candidate reduced collected test set")
                gates.extend(self.validate(candidate))
                full_exit = full_test_exit_code(gates)
                capability_delta = candidate_capability_delta(
                    candidate,
                    accepted=full_exit == 0 and all(gate.exit_code == 0 for gate in gates),
                    gates=gates,
                    evaluations=self.capability_evaluations(candidate),
                )
                accepted = full_exit == 0 and all(gate.exit_code == 0 for gate in gates)
                if not accepted:
                    if full_exit is None:
                        raise RuntimeError("full pytest gate did not run")
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
            full_test_exit_code=full_test_exit_code(gates),
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
        if (self.repo_root / "schema_transfer_manifest.json").exists():
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
        full_test_exit_codes = [
            int(record["full_test_exit_code"])
            for record in run_records
            if record.get("full_test_exit_code") is not None
        ]
        summary = {
            "dry_run": self.dry_run,
            "broad_gate": self.broad_gate,
            "thdse_core_gate": self.thdse_core_gate,
            "rollback": self.rollback,
            "persistence": self.persistence,
            "exploration_policy": self.exploration_policy,
            "exploration_depth": self.exploration_depth,
            "full_test_command": " ".join(FULL_TEST_COMMAND),
            "full_test_required": True,
            "full_test_exit_code": full_test_exit_codes[-1] if full_test_exit_codes else None,
            "full_test_ran": bool(full_test_exit_codes),
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
