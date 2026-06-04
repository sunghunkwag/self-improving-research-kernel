"""General AST-level candidate synthesis for external repair targets."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.records import CandidatePatch, Goal, generator_feedback


AST_SYNTHESIS_VISIBLE_TEST = '''from shared.external_repair_target import merge_setting


def test_ast_synthesis_visible_none_removal_case():
    session_headers = {"User-Agent": "session-agent", "Accept": "application/json"}
    request_headers = {"User-Agent": None, "Content-Type": "text/plain"}

    merged = merge_setting(request_headers, session_headers)

    assert "User-Agent" not in merged
    assert merged["Accept"] == "application/json"
    assert merged["Content-Type"] == "text/plain"
'''


@dataclass(frozen=True)
class AstMutationPlan:
    """One source-derived AST mutation candidate."""

    function_name: str
    state_name: str
    update_lineno: int
    return_lineno: int
    mutation_kind: str = "insert_guarded_none_value_deletion"


def _safe_identifier_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower() or "target"


def _name_load(node: ast.AST) -> str:
    return node.id if isinstance(node, ast.Name) else ""


def _is_update_call(stmt: ast.stmt) -> str:
    if not isinstance(stmt, ast.Expr):
        return ""
    call = stmt.value
    if not isinstance(call, ast.Call):
        return ""
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "update":
        return ""
    return _name_load(func.value)


def _has_none_value_guard(node: ast.AST, state_name: str) -> bool:
    """Return whether the function already filters/deletes None-valued entries."""

    for child in ast.walk(node):
        if isinstance(child, ast.Compare):
            rendered = ast.unparse(child)
            if "None" in rendered and state_name in rendered:
                return True
        if isinstance(child, ast.comprehension):
            rendered = ast.unparse(child)
            if "None" in rendered and state_name in rendered:
                return True
    return False


def discover_mapping_none_deletion_plans(source: str) -> Tuple[AstMutationPlan, ...]:
    """Infer mapping-repair mutations from update-then-return function structure."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()

    plans: List[AstMutationPlan] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for index, stmt in enumerate(node.body):
            state_name = _is_update_call(stmt)
            if not state_name or _has_none_value_guard(node, state_name):
                continue
            for later in node.body[index + 1 :]:
                if isinstance(later, ast.Return) and _name_load(later.value) == state_name:
                    plans.append(
                        AstMutationPlan(
                            function_name=node.name,
                            state_name=state_name,
                            update_lineno=getattr(stmt, "lineno", 0),
                            return_lineno=getattr(later, "lineno", 0),
                        )
                    )
                    break
    return tuple(plans)


def _guarded_deletion_statements(state_name: str) -> List[ast.stmt]:
    snippet = f'''
for key in tuple({state_name}):
    if {state_name}[key] is None:
        del {state_name}[key]
'''
    return ast.parse(snippet).body


class _ApplyNoneDeletionPlan(ast.NodeTransformer):
    def __init__(self, plan: AstMutationPlan):
        self.plan = plan
        self.changed = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802 - ast API
        if node.name != self.plan.function_name:
            return node
        new_body: List[ast.stmt] = []
        for stmt in node.body:
            if (
                isinstance(stmt, ast.Return)
                and getattr(stmt, "lineno", 0) == self.plan.return_lineno
                and _name_load(stmt.value) == self.plan.state_name
            ):
                new_body.extend(_guarded_deletion_statements(self.plan.state_name))
                self.changed = True
            new_body.append(stmt)
        node.body = new_body
        return node


def apply_mapping_none_deletion_mutation(source: str, plan: AstMutationPlan) -> str:
    """Apply one source-derived guarded deletion mutation."""

    tree = ast.parse(source)
    transformer = _ApplyNoneDeletionPlan(plan)
    rewritten = transformer.visit(tree)
    if not transformer.changed:
        raise RuntimeError(f"{plan.function_name}: AST mutation anchor not found")
    ast.fix_missing_locations(rewritten)
    output = ast.unparse(rewritten) + "\n"
    compile(output, "<ast_synthesis_candidate>", "exec")
    return output


def _visible_test_source(repo_root: Path) -> str:
    test_path = repo_root / "tests" / "test_external_code_repair_task.py"
    if test_path.exists():
        return test_path.read_text(encoding="utf-8")
    return AST_SYNTHESIS_VISIBLE_TEST


def _candidate_for_plan(
    repo_root: Path,
    generation: int,
    plan: AstMutationPlan,
    *,
    target: Path,
    test_source: str,
) -> CandidatePatch:
    function_fragment = _safe_identifier_fragment(plan.function_name)
    state_fragment = _safe_identifier_fragment(plan.state_name)
    candidate_name = f"external_code_repair_ast_{function_fragment}_{state_fragment}_none_deletion_v1"

    def transform(source: str, selected_plan: AstMutationPlan = plan) -> str:
        return apply_mapping_none_deletion_mutation(source, selected_plan)

    return CandidatePatch(
        name=candidate_name,
        generation=generation,
        goal=Goal(
            name=f"repair_{function_fragment}_none_value_mapping_updates",
            target=f"shared.external_repair_target.{plan.function_name}",
            metric="AST-synthesized mapping repair passes visible, hidden, and full-suite gates",
            rationale=(
                "The source AST has a mapping update followed by returning the merged "
                "mapping; a guarded statement insertion removes request-level None "
                "values without relying on hard-coded header names or reference fixes."
            ),
        ),
        target_path=target,
        test_path=repo_root / "tests" / "test_external_code_repair_task.py",
        transform=transform,
        test_source=test_source,
        focused_tests=("tests/test_external_code_repair_task.py",),
        capability_family="external_code_repair",
        operator_specs=operator_specs_for("external_code_repair", f"{plan.function_name}_ast_none_deletion"),
        generator_improvement=generator_feedback(
            "AST mutation synthesis",
            "derives a guarded statement insertion from update-then-return structure in the target source",
            (
                f"{plan.function_name}:{plan.state_name} synthesized from source AST lines "
                f"{plan.update_lineno}->{plan.return_lineno}; no hidden cases or reference fixes inspected"
            ),
        ),
    )


def ast_synthesis_candidates(repo_root: Path, generation: int) -> List[CandidatePatch]:
    """Generate source-derived AST repair candidates through the normal loop API."""

    target = repo_root / "shared" / "external_repair_target.py"
    if not target.exists():
        return []
    source = target.read_text(encoding="utf-8")
    plans = discover_mapping_none_deletion_plans(source)
    if not plans:
        return []
    test_source = _visible_test_source(repo_root)
    return [
        _candidate_for_plan(
            repo_root,
            generation,
            plan,
            target=target,
            test_source=test_source,
        )
        for plan in plans
    ]


def ast_synthesis_compile_count(source: str, plans: Sequence[AstMutationPlan]) -> int:
    """Return how many discovered plans produce syntactically valid Python."""

    compiled = 0
    for plan in plans:
        try:
            compile(apply_mapping_none_deletion_mutation(source, plan), "<ast_synthesis_candidate>", "exec")
        except Exception:
            continue
        compiled += 1
    return compiled


def ast_synthesis_summary(source: str) -> dict:
    """Return generation counts for honest ablation reporting."""

    plans = discover_mapping_none_deletion_plans(source)
    return {
        "produced_candidates": len(plans),
        "compiled_candidates": ast_synthesis_compile_count(source, plans),
        "mutation_kinds": sorted({plan.mutation_kind for plan in plans}),
    }
