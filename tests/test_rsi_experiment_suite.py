from scripts.rsi_experiment_suite import (
    ExperimentVariant,
    changed_files,
    repository_fingerprint,
    strip_method,
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

    fingerprint = repository_fingerprint(tmp_path)

    assert "a.py" in fingerprint
    assert ".omega_rsi_runs/closed_rsi_state.json" not in fingerprint


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
