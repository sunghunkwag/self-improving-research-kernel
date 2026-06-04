import hashlib
import json
from pathlib import Path

from scripts.closed_rsi.growth_report import build_growth_report, render_growth_markdown
from scripts.closed_recursive_self_improvement_loop import (
    BehaviorArchive,
    CandidatePatch,
    ClosedRecursiveSelfImprovementLoop,
    Goal,
    LOCAL_CORPUS_QUERY_SPECS,
    ProxyObjective,
    add_autonomous_record_query,
    add_records_importing,
    add_records_with_feature,
    apply_ast_mutation,
    ast_synthesis_candidates,
    ast_synthesis_summary,
    candidates_from_specs,
    discover_ast_mutation_plans,
    discover_local_corpus_query_blueprints,
    operator_specs_for,
    candidate_immutable_boundary_findings,
    invent_proxy_objectives,
    judge_proxy_promotion,
    proxy_immutable_boundary_findings,
    repair_external_merge_general,
    score_query_blueprints,
    score_proxy_expression,
    self_proposed_capability_candidates,
    validate_proxy_expression,
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


def test_open_ended_proxy_guard_rejects_immutable_ground_truth_access(tmp_path):
    proxy = ProxyObjective(
        proxy_id="proxy_cheats_on_ground_truth",
        generation=1,
        expression="novelty + hidden_transfer",
        description="attempts to read the ground-truth metric",
        source="score = novelty + hidden_transfer",
    )

    findings = validate_proxy_expression(proxy)

    assert findings
    assert any(finding.pattern == "hidden_transfer" for finding in findings)

    repo = tmp_path / "repo"
    target = repo / "shared" / "local_corpus.py"
    test_path = repo / "tests" / "test_forbidden_candidate.py"
    candidate = CandidatePatch(
        name="candidate_imports_evaluator",
        generation=1,
        goal=Goal(
            name="peek",
            target="shared.local_corpus",
            metric="direct evaluator import",
            rationale="This candidate should be rejected before any gate can run.",
        ),
        target_path=target,
        test_path=test_path,
        transform=lambda source: source,
        test_source="from scripts.closed_rsi.evaluators.capability import candidate_capability_delta\n",
        generator_improvement={"surface": "test", "mechanism": "test", "evidence": "test"},
    )

    candidate_findings = candidate_immutable_boundary_findings(candidate, repo_root=repo)

    assert candidate_findings
    assert any("evaluator" in finding.reason for finding in candidate_findings)


def test_open_ended_proxy_invention_uses_archive_and_self_play_without_ground_truth():
    proxy_findings = proxy_immutable_boundary_findings(
        proxy_id="clean_proxy",
        expression="novelty + self_play_wins - complexity_penalty",
        description="clean proxy over archive and self-play pressure",
    )
    archive = BehaviorArchive.from_state(
        {
            "accepted": [{"name": "prior", "generation": 1, "goal": {"name": "prior"}}],
            "rejected": [],
            "quarantine_exploration": [],
        }
    )
    proxies = invent_proxy_objectives(
        generation=2,
        state={"accepted": [], "rejected": [], "quarantine_exploration": []},
        archive=archive,
        tasks=(),
        seed="proxy-invention-test",
    )

    assert proxy_findings == ()
    assert proxies
    assert all(validate_proxy_expression(proxy) == () for proxy in proxies)
    assert "hidden_transfer" not in " ".join(proxy.expression for proxy in proxies)


def test_proxy_promotion_requires_two_unseen_seeds_both_improve():
    decision = judge_proxy_promotion(
        new_proxy={"proxy_id": "new_proxy"},
        previous_proxy={"proxy_id": "old_proxy"},
        new_seed_results={
            "proxy-unseen-alpha": 2,
            "proxy-unseen-beta": 1,
        },
        previous_seed_results={
            "proxy-unseen-alpha": 1,
            "proxy-unseen-beta": 0,
        },
    )

    assert decision["promoted"] is True
    assert decision["proxy_promotion_events"] == 1
    assert decision["reason"] == "two_unseen_seeds_improved"


def test_reward_hacking_proxy_is_rejected_by_delayed_ground_truth():
    proxy = ProxyObjective(
        proxy_id="proxy_rewards_self_report",
        generation=3,
        expression="1000 * self_reported_proxy_score + novelty",
        description="degenerate proxy that can be won on its own terms",
        source="score = 1000 * self_reported_proxy_score + novelty",
    )
    proxy_score = score_proxy_expression(
        proxy,
        {
            "self_reported_proxy_score": 1.0,
            "novelty": 1.0,
            "self_play_wins": 1.0,
            "weakness_exposure": 1.0,
            "archive_sparsity": 1.0,
            "population_fit": 1.0,
            "complexity_penalty": 0.0,
            "rejection_pressure": 0.0,
        },
    )
    decision = judge_proxy_promotion(
        new_proxy=proxy.to_dict(),
        previous_proxy={"proxy_id": "baseline_proxy"},
        new_seed_results={
            "proxy-unseen-alpha": 0,
            "proxy-unseen-beta": 0,
        },
        previous_seed_results={},
    )

    assert proxy_score > 1000
    assert decision["promoted"] is False
    assert decision["proxy_promotion_events"] == 0
    assert decision["reason"] == "ground_truth_did_not_improve_on_both_seeds"


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


CAPABILITY_PRIMITIVES_PRESENT_STUB = '''"""fixture primitives already present for static families."""


def run_length_encode(items):
    return ()


def infer_linear_rule(values):
    return {}


def rotate_grid_clockwise(grid):
    return ()


def dedupe_preserve_order(items):
    return ()


def apply_grid_action(state, action):
    return dict(state)
'''


SELF_PROPOSED_RESIDUE = {
    "candidate_name": "visible_header_repair",
    "failed_candidate_reason": "focused passed but broad gate failed",
    "missing_operator": "merge_setting_generalizer",
    "missing_abstraction": "regression-aware validation abstraction",
    "failed_evaluator": "visible_header_repair_full_pytest",
    "overfit_signal": "focused_passed_broad_failed",
    "failed_gate": "visible_header_repair_full_pytest",
    "next_hypothesis": "generalize the repair beyond focused tests",
}


def _write_self_proposed_capability_repo(repo: Path) -> None:
    shared = repo / "shared"
    tests = repo / "tests"
    shared.mkdir(parents=True)
    tests.mkdir()
    (shared / "__init__.py").write_text("", encoding="utf-8")
    (shared / "capability_primitives.py").write_text(CAPABILITY_PRIMITIVES_PRESENT_STUB, encoding="utf-8")


def test_loop_invents_self_proposed_capability_dimension_from_residue_on_two_unseen_seeds(tmp_path):
    for index, seed in enumerate(("self-proposed-residue-seed-alpha", "self-proposed-residue-seed-beta")):
        repo = tmp_path / f"repo_{index}"
        _write_self_proposed_capability_repo(repo)
        state = {
            "accepted": [],
            "rejected": [{"name": "prior_rejected_candidate", "failure_residue": SELF_PROPOSED_RESIDUE}],
            "quarantine_exploration": [],
            "active_generation": 1,
            "active_base": "prior_rejected_candidate",
        }
        loop = ClosedRecursiveSelfImprovementLoop(
            repo,
            state_dir=tmp_path / f"state_{index}",
            dry_run=False,
            timeout_s=120,
            capability_seed=seed,
        )
        loop.save_state(state)

        candidates = self_proposed_capability_candidates(repo, generation=2, state=state, seed=seed)
        assert len(candidates) == 1
        candidate = candidates[0]
        assert candidate.capability_family.startswith("residue_")
        assert candidate.capability_family not in {
            "algorithm_synthesis",
            "symbolic_reasoning",
            "grid_transformation",
            "bug_repair",
            "planning_state_transition",
        }
        assert candidate.name in {item.name for item in loop.invent_candidates(generation=2, state=state)}

        record = loop.apply_candidate(candidate)

        assert record.accepted is True
        assert record.full_test_exit_code == 0
        gate_labels = {gate["label"]: gate for gate in record.gates}
        assert gate_labels[f"{candidate.name}_focused"]["exit_code"] == 0
        assert gate_labels[f"{candidate.name}_capability_evaluator"]["exit_code"] == 0
        assert gate_labels[f"{candidate.name}_full_pytest"]["exit_code"] == 0
        assert gate_labels[f"{candidate.name}_repeat_full_pytest"]["exit_code"] == 0
        assert record.capability_delta["hidden_transfer"] >= 1
        assert record.generator_improvement["surface"] == "self-proposed capability dimension"


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


def test_growth_report_renders_generation_accounting_and_plateau():
    summary = {
        "full_test_command": "python -m pytest -q",
        "full_test_required": True,
        "full_test_exit_code": 0,
        "active_generation": 2,
        "active_base": "candidate_b",
        "plateau_reason": "candidate_budget_exhausted_without_promotion",
        "generations": [
            {
                "generation": 1,
                "generated_candidates": 4,
                "attempted_candidates": 2,
                "compiled_candidates": 2,
                "pre_full_gate_passed_candidates": 1,
                "full_suite_passed_candidates": 1,
                "accepted_candidates": ["candidate_a"],
                "rejected_candidates": ["candidate_bad"],
                "capability_families": ["algorithm_synthesis"],
                "solved_new_tasks": 1,
                "hidden_transfer": 1,
                "operator_reuse": 2,
                "invented_proxies": [
                    {
                        "proxy_id": "proxy_gen_1",
                        "expression": "novelty + self_play_wins",
                        "description": "synthetic proxy objective for report coverage",
                    }
                ],
                "selected_proxy": {"proxy_id": "proxy_gen_1"},
                "proxy_promotion_events": 1,
                "proxy_hidden_transfer": 2,
                "stop_reason": "candidate_promoted",
            },
            {
                "generation": 2,
                "generated_candidates": 3,
                "attempted_candidates": 3,
                "compiled_candidates": 2,
                "pre_full_gate_passed_candidates": 0,
                "full_suite_passed_candidates": 0,
                "accepted_candidates": [],
                "rejected_candidates": ["candidate_b", "candidate_c", "candidate_d"],
                "capability_families": ["residue_regression"],
                "solved_new_tasks": 0,
                "hidden_transfer": 0,
                "operator_reuse": 0,
                "invented_proxies": [
                    {
                        "proxy_id": "proxy_gen_2",
                        "expression": "novelty - complexity_penalty",
                        "description": "plateau proxy objective for report coverage",
                    }
                ],
                "selected_proxy": {"proxy_id": "proxy_gen_2"},
                "proxy_promotion_events": 0,
                "proxy_hidden_transfer": 0,
                "stop_reason": "candidate_budget_exhausted_without_promotion",
            },
        ],
    }
    state = {
        "accepted": [{"name": "candidate_a", "accepted": True, "capability_delta": {"score": 1.0}}],
        "rejected": [{"name": "candidate_bad", "accepted": False}],
        "quarantine_exploration": [],
    }

    report = build_growth_report(summary, state)
    markdown = render_growth_markdown(report)

    assert report["totals"]["generated_candidates"] == 7
    assert report["totals"]["compiled_candidates"] == 4
    assert report["totals"]["full_suite_passed_candidates"] == 1
    assert report["totals"]["proxy_promotion_events"] == 1
    assert report["proxy_promotion_events"] == 1
    assert report["plateau_reason"] == "candidate_budget_exhausted_without_promotion"
    assert "Proxy Objective Accounting" in markdown
    assert "proxy_gen_1" in markdown
    assert "candidate_budget_exhausted_without_promotion" in markdown
    assert "not evidence of unlimited growth" in markdown


def test_loop_summary_records_no_candidate_plateau_without_fabricated_growth(tmp_path):
    repo = tmp_path / "repo"
    (repo / "shared").mkdir(parents=True)
    (repo / "tests").mkdir()
    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state")

    summary = loop.run(max_generations=1, max_candidates=1, wall_seconds=30)

    assert summary["plateau_reason"] == "no_candidates_generated"
    assert summary["generations"][0]["generated_candidates"] == 0
    assert summary["generations"][0]["attempted_candidates"] == 0
    assert summary["generations"][0]["full_suite_passed_candidates"] == 0
    assert summary["generations"][0]["invented_proxies"]
    assert summary["generations"][0]["proxy_promotion_events"] == 0


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


HELD_OUT_AST_EXTERNAL_REPAIR_SOURCE = '''from collections import OrderedDict
from collections.abc import Mapping


def to_key_val_list(value):
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value.items()
    return value


def merge_setting(request_setting, session_setting, dict_class=OrderedDict):
    """Held-out update/return shape with variable names unlike named repairs."""

    if session_setting is None:
        return request_setting
    if request_setting is None:
        return session_setting
    if not (
        isinstance(session_setting, Mapping)
        and isinstance(request_setting, Mapping)
    ):
        return request_setting

    combined = dict_class(to_key_val_list(session_setting))
    combined.update(to_key_val_list(request_setting))
    return combined
'''


HELD_OUT_AST_EXTERNAL_REPAIR_TEST = '''from pathlib import Path

from shared.external_repair_target import merge_setting


def test_requests_header_none_removes_session_header_visible_case():
    failure_text = (Path.cwd() / "external_sandbox" / "failure_excerpt.txt").read_text(encoding="utf-8")
    session_headers = {"User-Agent": "session-agent", "Accept": "application/json"}
    request_headers = {"User-Agent": None, "Content-Type": "text/plain"}

    merged = merge_setting(request_headers, session_headers)

    assert failure_text
    assert "User-Agent" not in merged
    assert merged["Accept"] == "application/json"
    assert merged["Content-Type"] == "text/plain"
'''


def _write_held_out_ast_external_repo(repo: Path) -> None:
    shared = repo / "shared"
    tests = repo / "tests"
    sandbox = repo / "external_sandbox"
    quarantine = repo / ".external_code_quarantine"
    shared.mkdir(parents=True)
    tests.mkdir()
    sandbox.mkdir()
    quarantine.mkdir()
    (shared / "__init__.py").write_text("", encoding="utf-8")
    (shared / "external_repair_target.py").write_text(
        HELD_OUT_AST_EXTERNAL_REPAIR_SOURCE,
        encoding="utf-8",
    )
    (tests / "test_external_code_repair_task.py").write_text(
        HELD_OUT_AST_EXTERNAL_REPAIR_TEST,
        encoding="utf-8",
    )
    (sandbox / "source_snippet.txt").write_text(
        "held-out merge_setting source with non-enumerated local variable names\n",
        encoding="utf-8",
    )
    (sandbox / "failure_excerpt.txt").write_text(
        "request-level None headers should remove inherited session headers\n",
        encoding="utf-8",
    )
    forbidden_reference_span = "none_keys = [key for key, value in merged_setting.items() if value is None]"
    metadata = {
        "function_name": "merge_setting",
        "buggy_source_path": "shared/external_repair_target.py",
        "held_out_reference_sha256": hashlib.sha256(b"not the candidate").hexdigest(),
        "held_out_reference_span_sha256": [
            hashlib.sha256(forbidden_reference_span.encode("utf-8")).hexdigest(),
        ],
        "quarantine_paths": [".external_code_quarantine/reference.sha256"],
    }
    (repo / "external_code_repair_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (quarantine / "reference.sha256").write_text(
        metadata["held_out_reference_sha256"] + "\n",
        encoding="utf-8",
    )


STRUCTURAL_AST_MUTATION_SOURCE = '''
def tune_limit(items, threshold, enabled=True):
    left = 1
    right = 2
    score = len(items) + threshold
    if enabled and score > 3:
        return score
    return 0
'''


def test_ast_synthesis_discovers_structural_mutation_family_without_target_answers():
    summary = ast_synthesis_summary(STRUCTURAL_AST_MUTATION_SOURCE)
    expected_kinds = {
        "insert_nullable_guard",
        "mutate_binary_operator",
        "mutate_bool_operator",
        "mutate_compare_operator",
        "mutate_constant",
        "negate_condition",
        "swap_adjacent_statements",
    }

    assert expected_kinds <= set(summary["mutation_kinds"])
    assert summary["produced_candidates"] == summary["compiled_candidates"]
    assert summary["failed_compile_candidates"] == 0
    assert expected_kinds <= set(summary["compiled_by_kind"])

    plans = discover_ast_mutation_plans(STRUCTURAL_AST_MUTATION_SOURCE)
    assert len(plans) == summary["produced_candidates"]
    for kind in expected_kinds:
        plan = next(item for item in plans if item.mutation_kind == kind)
        rewritten = apply_ast_mutation(STRUCTURAL_AST_MUTATION_SOURCE, plan)
        assert rewritten != STRUCTURAL_AST_MUTATION_SOURCE
        compile(rewritten, f"<{kind}>", "exec")


def test_ast_synthesis_repairs_held_out_update_return_shape_on_two_unseen_seeds(tmp_path):
    failed_named_repair = False
    try:
        repair_external_merge_general(HELD_OUT_AST_EXTERNAL_REPAIR_SOURCE)
    except RuntimeError:
        failed_named_repair = True
    assert failed_named_repair, "named merge-setting repair should not match the held-out body"

    summary = ast_synthesis_summary(HELD_OUT_AST_EXTERNAL_REPAIR_SOURCE)
    assert summary["generated_by_kind"]["insert_guarded_none_value_deletion"] == 1
    assert summary["compiled_by_kind"]["insert_guarded_none_value_deletion"] == 1
    assert summary["produced_candidates"] > 1
    assert summary["compiled_candidates"] == summary["produced_candidates"]

    for index, seed in enumerate(("ast-held-out-seed-alpha", "ast-held-out-seed-beta")):
        repo = tmp_path / f"repo_{index}"
        _write_held_out_ast_external_repo(repo)
        loop = ClosedRecursiveSelfImprovementLoop(
            repo,
            state_dir=tmp_path / f"state_{index}",
            dry_run=False,
            timeout_s=120,
            capability_seed=seed,
        )
        candidates = ast_synthesis_candidates(repo, generation=1)
        ranked = loop.rank_candidates(loop.invent_candidates(generation=1), loop.load_state())
        assert {
            "insert_guarded_none_value_deletion",
            "mutate_compare_operator",
            "negate_condition",
        } <= {item.generator_improvement["evidence"].split(":")[1].split()[0] for item in candidates}
        assert len(candidates) > 1
        assert ranked[0].name == "external_code_repair_ast_merge_setting_combined_none_deletion_v1"
        candidate = ranked[0]

        record = loop.apply_candidate(candidate)

        assert record.accepted is True
        assert record.full_test_exit_code == 0
        gate_labels = {gate["label"]: gate for gate in record.gates}
        assert gate_labels[f"{candidate.name}_focused"]["exit_code"] == 0
        assert gate_labels[f"{candidate.name}_external_code_hidden_evaluator"]["exit_code"] == 0
        assert gate_labels[f"{candidate.name}_full_pytest"]["exit_code"] == 0
        assert gate_labels[f"{candidate.name}_repeat_full_pytest"]["exit_code"] == 0
        repaired = (repo / "shared" / "external_repair_target.py").read_text(encoding="utf-8")
        assert "for key in tuple(combined):" in repaired
        assert "del combined[key]" in repaired
