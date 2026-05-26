from scripts.rsi_experiment_suite import (
    DEFAULT_REPOSITORIES,
    DEFAULT_TASKS,
    ExperimentVariant,
    aggregate_results,
    build_baseline_comparisons,
    build_benchmark_repo,
    changed_files,
    remove_policy_registry_surface,
    repository_fingerprint,
    stable_trial_seed,
    strip_method,
    task_applies_to_repository,
)


def test_strip_method_removes_only_named_method():
    source = '''
class Example:
    def keep(self):
        return 1

    def remove_me(self):
        return 2

    def keep_too(self):
        return 3
'''

    rewritten = strip_method(source, "remove_me")

    assert "def remove_me" not in rewritten
    assert "def keep(self)" in rewritten
    assert "def keep_too(self)" in rewritten


def test_changed_files_detects_add_modify_delete():
    before = {"a.py": "1", "b.py": "2"}
    after = {"b.py": "3", "c.py": "4"}

    assert changed_files(before, after) == ["a.py", "b.py", "c.py"]


def test_repository_fingerprint_ignores_state_directory(tmp_path):
    (tmp_path / "a.py").write_text("print('a')\n", encoding="utf-8")
    state = tmp_path / ".omega_rsi_runs"
    state.mkdir()
    (state / "closed_rsi_state.json").write_text("{}", encoding="utf-8")
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "atom_bank.json").write_text("{}", encoding="utf-8")

    fingerprint = repository_fingerprint(tmp_path)

    assert "a.py" in fingerprint
    assert ".omega_rsi_runs/closed_rsi_state.json" not in fingerprint
    assert "shared/atom_bank.json" not in fingerprint


def test_remove_policy_registry_surface_preserves_template_string(tmp_path):
    scripts = tmp_path / "scripts"
    tests = tmp_path / "tests"
    scripts.mkdir()
    tests.mkdir()
    (scripts / "rsi_policy_registry.py").write_text("", encoding="utf-8")
    (tests / "test_rsi_policy_registry_rewrite.py").write_text("", encoding="utf-8")
    loop = scripts / "closed_recursive_self_improvement_loop.py"
    loop.write_text(
        '''POLICY_REGISTRY_ACTIVE_MARKER = "POLICY_REGISTRY_" + "ACTIVE = True"
function_insertion = "\\n\\n" + POLICY_REGISTRY_ACTIVE_MARKER + """
def load_policy_registry(repo_root):
    pass
"""
POLICY_REGISTRY_ACTIVE = True

def load_policy_registry(repo_root):
    return {}

class ClosedRecursiveSelfImprovementLoop:
    def policy_surface(self):
        return {}

    def load_state(self):
        return {}
''',
        encoding="utf-8",
    )

    remove_policy_registry_surface(tmp_path)
    text = loop.read_text(encoding="utf-8")

    assert "function_insertion =" in text
    assert '"POLICY_REGISTRY_" + "ACTIVE = True"' in text
    assert not any(line.strip() == "POLICY_REGISTRY_ACTIVE = True" for line in text.splitlines())
    assert "    def policy_surface" not in text
    assert "    def load_state" in text


def test_experiment_variant_defaults_to_safe_controls():
    variant = ExperimentVariant(
        name="verified_closed_loop",
        family="proposed",
        description="test",
    )

    assert variant.broad_gate is True
    assert variant.thdse_core_gate is True
    assert variant.rollback is True
    assert variant.persistence is True
    assert variant.max_generations_override is None
    assert variant.max_candidates_override is None


def test_stable_trial_seed_changes_by_repeat():
    first = stable_trial_seed("repo", "task", "variant", 0)
    second = stable_trial_seed("repo", "task", "variant", 1)

    assert first == stable_trial_seed("repo", "task", "variant", 0)
    assert first != second


def test_compact_benchmark_repository_builder_creates_minimal_repo(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "scripts").mkdir(parents=True)
    (source / "shared").mkdir()
    (source / "scripts" / "closed_recursive_self_improvement_loop.py").write_text("", encoding="utf-8")
    (source / "scripts" / "rsi_policy_registry.py").write_text("", encoding="utf-8")
    (source / "shared" / "__init__.py").write_text("", encoding="utf-8")
    (source / "shared" / "local_corpus.py").write_text("", encoding="utf-8")

    compact = next(repository for repository in DEFAULT_REPOSITORIES if repository.name == "compact_kernel_repo")
    build_benchmark_repo(source, target, compact)

    assert (target / "scripts" / "closed_recursive_self_improvement_loop.py").exists()
    assert (target / "shared" / "local_corpus.py").exists()
    assert (target / "tests" / "test_fixture_smoke.py").exists()


def test_unseen_schema_transfer_repository_adds_held_out_tuple_field(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "scripts").mkdir(parents=True)
    (source / "shared").mkdir()
    (source / "scripts" / "closed_recursive_self_improvement_loop.py").write_text("", encoding="utf-8")
    (source / "scripts" / "rsi_policy_registry.py").write_text("", encoding="utf-8")
    (source / "shared" / "__init__.py").write_text("", encoding="utf-8")
    (source / "shared" / "local_corpus.py").write_text(
        "from dataclasses import dataclass\n"
        "from typing import Tuple\n\n"
        "@dataclass(frozen=True)\n"
        "class LocalPythonFileRecord:\n"
        "    feature_flags: Tuple[str, ...] = ()\n",
        encoding="utf-8",
    )

    unseen = next(repository for repository in DEFAULT_REPOSITORIES if repository.name == "unseen_schema_transfer_repo")
    build_benchmark_repo(source, target, unseen)

    text = (target / "shared" / "local_corpus.py").read_text(encoding="utf-8")
    assert unseen.split == "unseen"
    assert "static_roles: Tuple[str, ...] = ()" in text
    assert (target / "tests" / "test_unseen_schema_fixture.py").exists()


def test_unseen_domain_transfer_repositories_add_distinct_tuple_fields(tmp_path):
    expected = {
        "unseen_security_transfer_repo": "threat_labels",
        "unseen_science_transfer_repo": "evidence_sources",
        "unseen_control_transfer_repo": "controller_modes",
    }
    source = tmp_path / "source"
    (source / "scripts").mkdir(parents=True)
    (source / "shared").mkdir()
    (source / "scripts" / "closed_recursive_self_improvement_loop.py").write_text("", encoding="utf-8")
    (source / "scripts" / "rsi_policy_registry.py").write_text("", encoding="utf-8")
    (source / "shared" / "__init__.py").write_text("", encoding="utf-8")
    (source / "shared" / "local_corpus.py").write_text(
        "from dataclasses import dataclass\n"
        "from typing import Tuple\n\n"
        "@dataclass(frozen=True)\n"
        "class LocalPythonFileRecord:\n"
        "    feature_flags: Tuple[str, ...] = ()\n",
        encoding="utf-8",
    )

    for repository_name, field_name in expected.items():
        target = tmp_path / repository_name
        repository = next(item for item in DEFAULT_REPOSITORIES if item.name == repository_name)
        build_benchmark_repo(source, target, repository)
        text = (target / "shared" / "local_corpus.py").read_text(encoding="utf-8")

        assert repository.split == "unseen"
        assert f"{field_name}: Tuple[str, ...] = ()" in text


def test_unseen_transfer_task_is_limited_to_unseen_repository():
    unseen_task = next(task for task in DEFAULT_TASKS if task.name == "unseen_static_roles_query")
    compact = next(repository for repository in DEFAULT_REPOSITORIES if repository.name == "compact_kernel_repo")
    unseen = next(repository for repository in DEFAULT_REPOSITORIES if repository.name == "unseen_schema_transfer_repo")
    unseen_task_names = {
        "unseen_static_roles_query",
        "unseen_threat_labels_query",
        "unseen_evidence_sources_query",
        "unseen_controller_modes_query",
    }

    assert task_applies_to_repository(unseen_task, unseen) is True
    assert task_applies_to_repository(unseen_task, compact) is False
    assert unseen_task_names <= {task.name for task in DEFAULT_TASKS}


def test_aggregate_results_groups_repeated_trials():
    from scripts.rsi_experiment_suite import ExperimentResult

    rows = [
        ExperimentResult(
            repository="repo",
            repository_description="fixture",
            task="task",
            variant="variant",
            family="family",
            description="description",
            repeat_index=0,
            seed="a",
            exit_code=0,
            elapsed_s=1.0,
            accepted_count=1,
            rejected_count=0,
            accepted_rate=1.0,
            regression_gate_failures=0,
            rollback_correct=None,
            persistence_file_exists=True,
            improvement_depth=1,
            cost_proxy_seconds=1.0,
            changed_files_count=2,
            summary_path="summary.json",
            stdout_tail="",
            stderr_tail="",
        ),
        ExperimentResult(
            repository="repo",
            repository_description="fixture",
            task="task",
            variant="variant",
            family="family",
            description="description",
            repeat_index=1,
            seed="b",
            exit_code=0,
            elapsed_s=3.0,
            accepted_count=0,
            rejected_count=1,
            accepted_rate=0.0,
            regression_gate_failures=1,
            rollback_correct=True,
            persistence_file_exists=True,
            improvement_depth=0,
            cost_proxy_seconds=3.0,
            changed_files_count=0,
            summary_path="summary.json",
            stdout_tail="",
            stderr_tail="",
        ),
    ]

    aggregate = aggregate_results(rows)[0]

    assert aggregate["trial_count"] == 2
    assert aggregate["accepted_rate_mean"] == 0.5
    assert aggregate["rollback_success_rate"] == 1.0


def test_baseline_comparison_marks_unseen_transfer_success():
    aggregates = [
        {
            "repository": "unseen_schema_transfer_repo",
            "repository_split": "unseen",
            "transfer_origin": "compact_kernel_repo",
            "task": "unseen_static_roles_query",
            "task_claim": "held-out transfer",
            "variant": "verified_closed_loop",
            "family": "proposed",
            "accepted_rate_mean": 1.0,
            "improvement_depth_mean": 1.0,
            "cost_proxy_seconds_mean": 1.0,
            "rollback_success_rate": None,
        },
        {
            "repository": "unseen_schema_transfer_repo",
            "repository_split": "unseen",
            "transfer_origin": "compact_kernel_repo",
            "task": "unseen_static_roles_query",
            "task_claim": "held-out transfer",
            "variant": "ci_only_validation",
            "family": "baseline_ci_only",
            "accepted_rate_mean": 0.0,
            "improvement_depth_mean": 0.0,
            "cost_proxy_seconds_mean": 1.0,
            "rollback_success_rate": None,
        },
    ]

    comparison = build_baseline_comparisons(aggregates)[0]

    assert comparison["outcome"] == "unseen_transfer_success"
    assert comparison["unseen_transfer_success"] is True
