from pathlib import Path

from scripts.closed_recursive_self_improvement_loop import (
    ClosedRecursiveSelfImprovementLoop,
    LOCAL_CORPUS_QUERY_SPECS,
    add_autonomous_record_query,
    add_records_importing,
    add_records_with_feature,
    candidates_from_specs,
    discover_local_corpus_query_blueprints,
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
