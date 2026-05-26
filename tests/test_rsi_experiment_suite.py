from scripts.rsi_experiment_suite import (
    ExperimentVariant,
    changed_files,
    remove_policy_registry_surface,
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
