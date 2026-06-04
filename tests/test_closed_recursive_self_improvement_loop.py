from pathlib import Path

from scripts.closed_recursive_self_improvement_loop import (
    CandidatePatch,
    ClosedRecursiveSelfImprovementLoop,
    Goal,
    LOCAL_CORPUS_QUERY_SPECS,
    add_autonomous_record_query,
    add_records_importing,
    add_records_with_feature,
    candidates_from_specs,
    discover_local_corpus_query_blueprints,
    operator_specs_for,
    score_query_blueprints,
)


LOCAL_CORPUS_STUB = '''
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


@dataclass(frozen=True)
class LocalPythonFileRecord:
    path: str
    feature_flags: Tuple[str, ...] = ()
    imports: Tuple[str, ...] = ()
    definitions: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalCorpusIndex:
    records: Tuple[LocalPythonFileRecord, ...]

    def to_dict(self) -> Dict[str, object]:
        return {"records": [record.path for record in self.records]}

    def write_json(self, path: Path) -> None:
        path.write_text("{}", encoding="utf-8")
'''


def test_transforms_add_query_methods_once():
    once = add_records_with_feature(LOCAL_CORPUS_STUB)
    twice = add_records_with_feature(once)

    assert "def records_with_feature(" in once
    assert once == twice

    import_query = add_records_importing(once)
    assert "def records_importing(" in import_query


def test_loop_discovers_real_source_candidates_in_temp_tree(tmp_path):
    repo = tmp_path / "OMEGA-THDSE"
    shared = repo / "shared"
    tests = repo / "tests"
    thdse = repo / "thdse"
    shared.mkdir(parents=True)
    tests.mkdir()
    thdse.mkdir()
    (shared / "local_corpus.py").write_text(LOCAL_CORPUS_STUB, encoding="utf-8")

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state")
    candidates = loop.invent_candidates(generation=1)

    assert [candidate.name for candidate in candidates] == [
        "autonomous_local_corpus_feature_flags_query_v1",
        "autonomous_local_corpus_imports_query_v1",
        "autonomous_local_corpus_definitions_query_v1",
    ]


def test_declarative_candidate_specs_generate_missing_capabilities(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    shared.mkdir(parents=True)
    (shared / "local_corpus.py").write_text(LOCAL_CORPUS_STUB, encoding="utf-8")

    candidates = candidates_from_specs(repo, 7, LOCAL_CORPUS_QUERY_SPECS)

    assert [candidate.generation for candidate in candidates] == [7, 7]
    assert {candidate.name for candidate in candidates} == {
        "local_corpus_feature_query_v1",
        "local_corpus_import_query_v1",
    }


def test_autonomous_planner_infers_query_blueprints_from_schema():
    blueprints = discover_local_corpus_query_blueprints(LOCAL_CORPUS_STUB)

    assert {blueprint.method_name for blueprint in blueprints} == {
        "records_importing",
        "records_with_definition",
        "records_with_feature",
    }


def test_autonomous_planner_transform_adds_generated_method():
    blueprint = next(
        item
        for item in discover_local_corpus_query_blueprints(LOCAL_CORPUS_STUB)
        if item.method_name == "records_with_definition"
    )

    rewritten = add_autonomous_record_query(LOCAL_CORPUS_STUB, blueprint)

    assert "def records_with_definition(" in rewritten
    assert "record.definitions" in rewritten


def test_emergent_hypothesis_search_uses_rejection_history():
    blueprints = discover_local_corpus_query_blueprints(
        LOCAL_CORPUS_STUB,
        state={
            "accepted": [],
            "rejected": [{"name": "autonomous_local_corpus_feature_flags_query_v1"}],
        },
    )

    assert "emergent_local_corpus_feature_flags_membership_v1" in {
        blueprint.candidate_name for blueprint in blueprints
    }
    assert all(blueprint.planner_score > 0 for blueprint in blueprints)


def test_blueprint_scoring_penalizes_rejected_candidates():
    blueprints = discover_local_corpus_query_blueprints(LOCAL_CORPUS_STUB, max_hypotheses=6)
    scored = score_query_blueprints(
        blueprints,
        state={
            "accepted": [],
            "rejected": [{"name": "autonomous_local_corpus_feature_flags_query_v1"}],
        },
    )

    rejected = next(
        blueprint
        for blueprint in scored
        if blueprint.candidate_name == "autonomous_local_corpus_feature_flags_query_v1"
    )
    alternate = next(
        blueprint
        for blueprint in scored
        if blueprint.candidate_name == "emergent_local_corpus_feature_flags_membership_v1"
    )

    assert alternate.planner_score > rejected.planner_score


def test_history_aware_ranking_deprioritizes_rejected_candidates(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "local_corpus.py").write_text(LOCAL_CORPUS_STUB, encoding="utf-8")

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state")
    state = {"accepted": [], "rejected": [{"name": "autonomous_local_corpus_feature_flags_query_v1"}]}
    candidates = loop.invent_candidates(generation=1, state=state)
    ranked = loop.rank_candidates(
        candidates,
        state,
    )

    assert [candidate.name for candidate in ranked] == [
        "autonomous_local_corpus_definitions_query_v1",
        "autonomous_local_corpus_imports_query_v1",
        "emergent_local_corpus_feature_flags_membership_v1",
    ]


def test_recursive_schema_batch_candidate_joins_seed_varied_transfer_ranking(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "local_corpus.py").write_text(
        LOCAL_CORPUS_STUB.replace(
            "    feature_flags: Tuple[str, ...] = ()\n",
            "    feature_flags: Tuple[str, ...] = ()\n"
            "    static_roles: Tuple[str, ...] = ()\n"
            "    threat_labels: Tuple[str, ...] = ()\n",
        ),
        encoding="utf-8",
    )
    (repo / "schema_transfer_manifest.json").write_text("{}", encoding="utf-8")

    loop = ClosedRecursiveSelfImprovementLoop(
        repo,
        state_dir=tmp_path / "state",
        exploration_policy="recursive_quarantine",
        exploration_depth=2,
        capability_seed="schema-transfer-ranking",
    )
    ranked = loop.rank_candidates(loop.invent_candidates(generation=1), loop.load_state())
    ranked_again = loop.rank_candidates(loop.invent_candidates(generation=1), loop.load_state())
    batch = next(
        candidate
        for candidate in ranked
        if candidate.name == "recursive_schema_batch_query_transfer_v1"
    )
    transfer_ranked = [
        candidate.name
        for candidate in ranked
        if candidate.name.startswith(("recursive_schema_batch_", "autonomous_local_corpus_"))
    ]

    assert [candidate.name for candidate in ranked] == [candidate.name for candidate in ranked_again]
    assert batch.name in transfer_ranked
    assert {"static_roles", "threat_labels"} <= set(batch.schema_fields)


def test_schema_transfer_manifest_rejects_partial_schema_candidate_before_full_pytest(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "schema_transfer_manifest.json").write_text(
        '{"fields": [{"field_name": "static_roles"}, {"field_name": "threat_labels"}]}',
        encoding="utf-8",
    )
    candidate = CandidatePatch(
        name="partial_schema_query",
        generation=1,
        goal=Goal(
            name="partial",
            target="shared.local_corpus.LocalCorpusIndex",
            metric="manifest gate rejects partial schema repair",
            rationale="Composite fixtures require all held-out schema fields.",
        ),
        target_path=repo / "shared" / "local_corpus.py",
        test_path=repo / "tests" / "test_partial.py",
        transform=lambda source: source,
        test_source="",
        schema_fields=("static_roles",),
        generator_improvement={"surface": "test", "mechanism": "test", "evidence": "test"},
    )
    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state")

    gate = loop.schema_transfer_evaluator_gate(candidate)

    assert gate is not None, "manifest gate should reject partial schema candidates"
    assert gate.exit_code == 1
    assert gate.label == "partial_schema_query_schema_transfer_manifest"
    assert "partial_schema_candidate_failed_composite_manifest" in gate.stderr_tail


def test_schema_transfer_manifest_skips_quarantine_only_exploration(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "schema_transfer_manifest.json").write_text('{"fields": []}', encoding="utf-8")
    loop = ClosedRecursiveSelfImprovementLoop(
        repo,
        state_dir=tmp_path / "state",
        exploration_policy="recursive_quarantine",
        exploration_depth=2,
    )

    records = loop.run_quarantine_exploration(
        {"accepted": [], "rejected": [], "active_generation": 0, "active_base": "initial"},
        max_candidates=4,
        started=__import__("time").monotonic(),
        wall_seconds=60,
    )

    assert records == []


def test_capability_operator_candidates_include_delta_metadata(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "local_corpus.py").write_text(LOCAL_CORPUS_STUB, encoding="utf-8")
    (shared / "capability_primitives.py").write_text(
        '"""fixture primitives"""\n',
        encoding="utf-8",
    )

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state")
    candidates = loop.rank_candidates(loop.invent_candidates(generation=1), loop.load_state())
    first = candidates[0]

    assert first.name.startswith("capability_operator_")
    assert first.capability_family in {
        "algorithm_synthesis",
        "symbolic_reasoning",
        "grid_transformation",
        "bug_repair",
        "planning_state_transition",
    }
    assert {spec["kind"] for spec in first.operator_specs} == {
        "solver_primitive",
        "search_heuristic",
        "evaluator_mutation",
        "counterexample_test",
    }
    assert first.generator_improvement["surface"] == "operator synthesis"


def test_rejected_candidate_record_contains_failure_residue(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "local_corpus.py").write_text(LOCAL_CORPUS_STUB, encoding="utf-8")
    (shared / "capability_primitives.py").write_text(
        "def run_length_encode(items):\n"
        "    return ()\n",
        encoding="utf-8",
    )
    (tests / "test_forced_broad_failure.py").write_text(
        "def test_forced_broad_failure():\n"
        "    assert False\n",
        encoding="utf-8",
    )

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state", dry_run=False, broad_gate=True)
    candidate = loop.invent_candidates(generation=1)[0]
    record = loop.apply_candidate(candidate)

    assert record.accepted is False
    assert record.failure_residue["failed_candidate_reason"]
    assert record.operator_synthesis
    assert record.generator_improvement


def test_final_promotion_requires_full_pytest_even_when_focused_passes(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "__init__.py").write_text("", encoding="utf-8")
    target = shared / "full_gate_target.py"
    target.write_text("VALUE = 0\n", encoding="utf-8")
    (tests / "test_full_suite_guard.py").write_text(
        "def test_full_suite_guard_blocks_promotion():\n"
        "    assert False, 'full suite must run'\n",
        encoding="utf-8",
    )

    candidate = CandidatePatch(
        name="focused_pass_full_fails",
        generation=1,
        goal=Goal(
            name="prove_full_pytest_required",
            target="shared.full_gate_target",
            metric="focused diagnostic passes but full pytest fails",
            rationale="Regression coverage for full-test-only promotion.",
        ),
        target_path=target,
        test_path=tests / "test_focused_pass_full_fails.py",
        transform=lambda _source: "VALUE = 1\n",
        test_source="from shared.full_gate_target import VALUE\n\n\ndef test_value_changed():\n    assert VALUE == 1\n",
        focused_tests=("tests/test_focused_pass_full_fails.py",),
        generator_improvement={"surface": "test", "mechanism": "test", "evidence": "test"},
    )

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state", dry_run=False)
    record = loop.apply_candidate(candidate)

    focused_gate = next(gate for gate in record.gates if gate["label"] == "focused_pass_full_fails_focused")
    full_gate = next(gate for gate in record.gates if gate["label"] == "focused_pass_full_fails_full_pytest")
    assert focused_gate["exit_code"] == 0
    assert full_gate["args"][-3:] == ["-m", "pytest", "-q"]
    assert full_gate["exit_code"] != 0
    assert record.full_test_exit_code == full_gate["exit_code"]
    assert record.accepted is False
    assert target.read_text(encoding="utf-8") == "VALUE = 0\n"


def test_candidate_promotion_records_passing_full_pytest(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "__init__.py").write_text("", encoding="utf-8")
    target = shared / "full_gate_target.py"
    target.write_text("VALUE = 0\n", encoding="utf-8")

    candidate = CandidatePatch(
        name="full_pytest_acceptance",
        generation=1,
        goal=Goal(
            name="prove_full_pytest_acceptance",
            target="shared.full_gate_target",
            metric="full pytest gate passes",
            rationale="Regression coverage for full-test-only promotion.",
        ),
        target_path=target,
        test_path=tests / "test_full_pytest_acceptance.py",
        transform=lambda _source: "VALUE = 1\n",
        test_source="from shared.full_gate_target import VALUE\n\n\ndef test_value_changed():\n    assert VALUE == 1\n",
        focused_tests=("tests/test_full_pytest_acceptance.py",),
        generator_improvement={"surface": "test", "mechanism": "test", "evidence": "test"},
    )

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state", dry_run=False)
    record = loop.apply_candidate(candidate)

    full_gate = next(gate for gate in record.gates if gate["label"] == "full_pytest_acceptance_full_pytest")
    assert full_gate["args"][-3:] == ["-m", "pytest", "-q"]
    assert full_gate["exit_code"] == 0
    assert record.full_test_command == "python -m pytest -q"
    assert record.full_test_required is True
    assert record.accepted is True


def _fingerprint_files(root: Path):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
    return result


def _write_capability_quarantine_repo(repo: Path) -> None:
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "__init__.py").write_text("", encoding="utf-8")
    (shared / "capability_primitives.py").write_text('"""fixture primitives"""\n', encoding="utf-8")
    (tests / "test_forced_broad_failure.py").write_text(
        "def test_forced_broad_failure():\n"
        "    assert False, 'force quarantine-only rejection'\n",
        encoding="utf-8",
    )


def test_recursive_quarantine_explores_deeper_failed_candidate_chain(tmp_path):
    repo = tmp_path / "repo"
    _write_capability_quarantine_repo(repo)
    before = _fingerprint_files(repo)

    loop = ClosedRecursiveSelfImprovementLoop(
        repo,
        state_dir=tmp_path / "state",
        dry_run=False,
        broad_gate=True,
        thdse_core_gate=False,
        exploration_policy="recursive_quarantine",
        exploration_depth=3,
        exploration_seed="quarantine-depth-test",
    )
    summary = loop.run(max_generations=0, max_candidates=1, wall_seconds=120)
    quarantine_records = summary["quarantine_exploration"]

    assert summary["quarantine_max_depth"] == 3
    assert len(quarantine_records) == 3
    assert all(record["accepted"] is False for record in quarantine_records)
    assert all(record["quarantine"] is True for record in quarantine_records)
    assert all(record["promoted"] is False for record in quarantine_records)
    assert all(record["failure_residue"]["failed_gate"] for record in quarantine_records)
    assert all(record["failure_residue"]["next_hypothesis"] for record in quarantine_records)
    assert _fingerprint_files(repo) == before


def test_anti_cheat_rejects_hardcoded_candidate_without_main_tree_change(tmp_path):
    repo = tmp_path / "repo"
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "__init__.py").write_text("", encoding="utf-8")
    target = shared / "capability_primitives.py"
    target.write_text('"""fixture primitives"""\n', encoding="utf-8")
    before = target.read_text(encoding="utf-8")

    def hardcode_public_case(_source: str) -> str:
        return (
            "def run_length_encode(items):\n"
            "    if items == (1, 1, 2, 2, 2, 3):\n"
            "        return ((1, 2), (2, 3), (3, 1))\n"
            "    return ()\n"
        )

    candidate = CandidatePatch(
        name="hardcoded_rle_cheat",
        generation=1,
        goal=Goal(
            name="hardcode_public_case",
            target="shared.capability_primitives.run_length_encode",
            metric="anti-cheat rejects literal branch",
            rationale="Fixture candidate intentionally cheats for anti-cheat coverage.",
        ),
        target_path=target,
        test_path=tests / "test_hardcoded_rle_cheat.py",
        transform=hardcode_public_case,
        test_source="from shared.capability_primitives import run_length_encode\n",
        focused_tests=("tests/test_hardcoded_rle_cheat.py",),
        capability_family="algorithm_synthesis",
        operator_specs=operator_specs_for("algorithm_synthesis", "run_length_encode"),
        generator_improvement={"surface": "test", "mechanism": "test", "evidence": "test"},
    )
    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state", dry_run=False)
    record = loop.apply_candidate(candidate)

    assert record.accepted is False
    assert record.gates[0]["label"] == "hardcoded_rle_cheat_anti_cheat"
    assert record.failure_residue["failed_gate"] == "hardcoded_rle_cheat_anti_cheat"
    assert target.read_text(encoding="utf-8") == before
