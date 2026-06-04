"""General AST-level candidate synthesis for external repair targets."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

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


_BIN_OP_REPLACEMENTS = {
    "Add": "Sub",
    "Sub": "Add",
    "Mult": "Add",
    "Div": "Mult",
    "FloorDiv": "Div",
    "Mod": "FloorDiv",
}

_COMPARE_OP_REPLACEMENTS = {
    "Eq": "NotEq",
    "NotEq": "Eq",
    "Lt": "LtE",
    "LtE": "Lt",
    "Gt": "GtE",
    "GtE": "Gt",
    "Is": "IsNot",
    "IsNot": "Is",
    "In": "NotIn",
    "NotIn": "In",
}

_BOOL_OP_REPLACEMENTS = {
    "And": "Or",
    "Or": "And",
}

_MUTATION_ORDER = (
    "insert_guarded_none_value_deletion",
    "insert_nullable_guard",
    "mutate_compare_operator",
    "mutate_bool_operator",
    "mutate_binary_operator",
    "mutate_constant",
    "negate_condition",
    "swap_adjacent_statements",
)


@dataclass(frozen=True)
class AstMutationPlan:
    """One source-derived AST mutation candidate."""

    function_name: str
    mutation_kind: str = "insert_guarded_none_value_deletion"
    target_lineno: int = 0
    target_col_offset: int = -1
    state_name: str = ""
    update_lineno: int = 0
    return_lineno: int = 0
    op_index: int = 0
    original: str = ""
    replacement: str = ""
    original_value: object = None
    replacement_value: object = None
    guard_name: str = ""
    fallback_name: str = ""
    first_lineno: int = 0
    second_lineno: int = 0


def _safe_identifier_fragment(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value)).strip("_").lower() or "target"


def _name_load(node: ast.AST | None) -> str:
    return node.id if isinstance(node, ast.Name) else ""


def _op_name(op: ast.AST) -> str:
    return type(op).__name__


def _make_operator(name: str) -> ast.AST:
    node = getattr(ast, name, None)
    if node is None:
        raise RuntimeError(f"unknown AST operator {name!r}")
    return node()


def _is_docstring_stmt(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


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


def _has_parameter_none_guard(node: ast.FunctionDef, name: str) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Compare):
            continue
        rendered = ast.unparse(child)
        if name in rendered and "None" in rendered:
            return True
    return False


def _plan_key(plan: AstMutationPlan) -> Tuple[object, ...]:
    return (
        plan.function_name,
        plan.mutation_kind,
        plan.target_lineno,
        plan.target_col_offset,
        plan.state_name,
        plan.op_index,
        plan.original,
        plan.replacement,
        repr(plan.original_value),
        repr(plan.replacement_value),
        plan.guard_name,
        plan.fallback_name,
        plan.first_lineno,
        plan.second_lineno,
    )


def _append_plan(
    plans: List[AstMutationPlan],
    plan: AstMutationPlan,
    counts: Dict[str, int],
    seen: Set[Tuple[object, ...]],
    max_per_kind: int,
) -> None:
    if counts.get(plan.mutation_kind, 0) >= max_per_kind:
        return
    key = _plan_key(plan)
    if key in seen:
        return
    seen.add(key)
    counts[plan.mutation_kind] = counts.get(plan.mutation_kind, 0) + 1
    plans.append(plan)


def _function_defs(tree: ast.AST) -> Iterable[ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            yield node


def discover_mapping_none_deletion_plans(source: str) -> Tuple[AstMutationPlan, ...]:
    """Infer mapping-repair mutations from update-then-return function structure."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()

    plans: List[AstMutationPlan] = []
    for node in _function_defs(tree):
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


def _constant_replacement(value: object) -> Optional[object]:
    if isinstance(value, bool):
        return not value
    if isinstance(value, int) and not isinstance(value, bool):
        return 1 if value == 0 else value + 1
    if isinstance(value, float):
        return 1.0 if value == 0.0 else value + 1.0
    if isinstance(value, str) and value:
        return ""
    return None


def _loaded_names(node: ast.AST) -> Set[str]:
    names: Set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            names.add(child.id)
    return names


def _assigned_names(node: ast.AST) -> Set[str]:
    names: Set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
    return names


def _simple_reorder_candidate(stmt: ast.stmt) -> bool:
    return isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr))


def _insert_index(node: ast.FunctionDef) -> int:
    return 1 if node.body and _is_docstring_stmt(node.body[0]) else 0


def _fallback_for_guard(node: ast.FunctionDef, guarded_name: str) -> str:
    args = [arg.arg for arg in node.args.args]
    for name in args:
        if name != guarded_name:
            return name
    return "None"


def discover_ast_mutation_plans(source: str, *, max_per_kind: int = 4) -> Tuple[AstMutationPlan, ...]:
    """Discover a bounded family of source-derived structural AST mutations."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()

    plans: List[AstMutationPlan] = []
    counts: Dict[str, int] = {}
    seen: Set[Tuple[object, ...]] = set()
    for plan in discover_mapping_none_deletion_plans(source):
        _append_plan(plans, plan, counts, seen, max_per_kind)

    for function in _function_defs(tree):
        for arg in function.args.args[:2]:
            if not _has_parameter_none_guard(function, arg.arg):
                body_index = _insert_index(function)
                target_lineno = getattr(function.body[body_index], "lineno", getattr(function, "lineno", 0))
                _append_plan(
                    plans,
                    AstMutationPlan(
                        function_name=function.name,
                        mutation_kind="insert_nullable_guard",
                        target_lineno=target_lineno,
                        guard_name=arg.arg,
                        fallback_name=_fallback_for_guard(function, arg.arg),
                    ),
                    counts,
                    seen,
                    max_per_kind,
                )

        for first, second in zip(function.body, function.body[1:]):
            if _is_docstring_stmt(first) or _is_docstring_stmt(second):
                continue
            if not (_simple_reorder_candidate(first) and _simple_reorder_candidate(second)):
                continue
            if _assigned_names(first) & _loaded_names(second):
                continue
            _append_plan(
                plans,
                AstMutationPlan(
                    function_name=function.name,
                    mutation_kind="swap_adjacent_statements",
                    first_lineno=getattr(first, "lineno", 0),
                    second_lineno=getattr(second, "lineno", 0),
                ),
                counts,
                seen,
                max_per_kind,
            )

        for child in ast.walk(function):
            if isinstance(child, ast.BinOp):
                original = _op_name(child.op)
                replacement = _BIN_OP_REPLACEMENTS.get(original)
                if replacement:
                    _append_plan(
                        plans,
                        AstMutationPlan(
                            function_name=function.name,
                            mutation_kind="mutate_binary_operator",
                            target_lineno=getattr(child, "lineno", 0),
                            target_col_offset=getattr(child, "col_offset", -1),
                            original=original,
                            replacement=replacement,
                        ),
                        counts,
                        seen,
                        max_per_kind,
                    )
            elif isinstance(child, ast.BoolOp):
                original = _op_name(child.op)
                replacement = _BOOL_OP_REPLACEMENTS.get(original)
                if replacement:
                    _append_plan(
                        plans,
                        AstMutationPlan(
                            function_name=function.name,
                            mutation_kind="mutate_bool_operator",
                            target_lineno=getattr(child, "lineno", 0),
                            target_col_offset=getattr(child, "col_offset", -1),
                            original=original,
                            replacement=replacement,
                        ),
                        counts,
                        seen,
                        max_per_kind,
                    )
            elif isinstance(child, ast.Compare):
                for op_index, op in enumerate(child.ops):
                    original = _op_name(op)
                    replacement = _COMPARE_OP_REPLACEMENTS.get(original)
                    if replacement:
                        _append_plan(
                            plans,
                            AstMutationPlan(
                                function_name=function.name,
                                mutation_kind="mutate_compare_operator",
                                target_lineno=getattr(child, "lineno", 0),
                                target_col_offset=getattr(child, "col_offset", -1),
                                op_index=op_index,
                                original=original,
                                replacement=replacement,
                            ),
                            counts,
                            seen,
                            max_per_kind,
                        )
            elif isinstance(child, ast.If):
                _append_plan(
                    plans,
                    AstMutationPlan(
                        function_name=function.name,
                        mutation_kind="negate_condition",
                        target_lineno=getattr(child.test, "lineno", getattr(child, "lineno", 0)),
                        target_col_offset=getattr(child.test, "col_offset", -1),
                    ),
                    counts,
                    seen,
                    max_per_kind,
                )
            elif isinstance(child, ast.Constant):
                replacement_value = _constant_replacement(child.value)
                if replacement_value is not None:
                    _append_plan(
                        plans,
                        AstMutationPlan(
                            function_name=function.name,
                            mutation_kind="mutate_constant",
                            target_lineno=getattr(child, "lineno", 0),
                            target_col_offset=getattr(child, "col_offset", -1),
                            original_value=child.value,
                            replacement_value=replacement_value,
                        ),
                        counts,
                        seen,
                        max_per_kind,
                    )
    return tuple(plans)


def _guarded_deletion_statements(state_name: str) -> List[ast.stmt]:
    snippet = f'''
for key in tuple({state_name}):
    if {state_name}[key] is None:
        del {state_name}[key]
'''
    return ast.parse(snippet).body


def _nullable_guard_statement(guard_name: str, fallback_name: str) -> ast.stmt:
    fallback = fallback_name if fallback_name != "None" else "None"
    snippet = f'''
if {guard_name} is None:
    return {fallback}
'''
    return ast.parse(snippet).body[0]


class _ApplyAstMutationPlan(ast.NodeTransformer):
    def __init__(self, plan: AstMutationPlan):
        self.plan = plan
        self.changed = False
        self._active_function = False

    def _matches(self, node: ast.AST) -> bool:
        return (
            self._active_function
            and getattr(node, "lineno", 0) == self.plan.target_lineno
            and getattr(node, "col_offset", -1) == self.plan.target_col_offset
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802 - ast API
        if node.name != self.plan.function_name:
            return self.generic_visit(node)
        previous = self._active_function
        self._active_function = True
        try:
            if self.plan.mutation_kind == "insert_guarded_none_value_deletion":
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
            if self.plan.mutation_kind == "insert_nullable_guard":
                insertion_index = _insert_index(node)
                node.body = [
                    *node.body[:insertion_index],
                    _nullable_guard_statement(self.plan.guard_name, self.plan.fallback_name),
                    *node.body[insertion_index:],
                ]
                self.changed = True
                return node
            if self.plan.mutation_kind == "swap_adjacent_statements":
                for index, stmt in enumerate(node.body[:-1]):
                    next_stmt = node.body[index + 1]
                    if (
                        getattr(stmt, "lineno", 0) == self.plan.first_lineno
                        and getattr(next_stmt, "lineno", 0) == self.plan.second_lineno
                    ):
                        body = list(node.body)
                        body[index], body[index + 1] = body[index + 1], body[index]
                        node.body = body
                        self.changed = True
                        return node
            return self.generic_visit(node)
        finally:
            self._active_function = previous

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:  # noqa: N802 - ast API
        node = self.generic_visit(node)
        if (
            self.plan.mutation_kind == "mutate_binary_operator"
            and self._matches(node)
            and _op_name(node.op) == self.plan.original
        ):
            node.op = _make_operator(self.plan.replacement)
            self.changed = True
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:  # noqa: N802 - ast API
        node = self.generic_visit(node)
        if (
            self.plan.mutation_kind == "mutate_bool_operator"
            and self._matches(node)
            and _op_name(node.op) == self.plan.original
        ):
            node.op = _make_operator(self.plan.replacement)
            self.changed = True
        return node

    def visit_Compare(self, node: ast.Compare) -> ast.AST:  # noqa: N802 - ast API
        node = self.generic_visit(node)
        if (
            self.plan.mutation_kind == "mutate_compare_operator"
            and self._matches(node)
            and self.plan.op_index < len(node.ops)
            and _op_name(node.ops[self.plan.op_index]) == self.plan.original
        ):
            node.ops[self.plan.op_index] = _make_operator(self.plan.replacement)
            self.changed = True
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802 - ast API
        if (
            self.plan.mutation_kind == "mutate_constant"
            and self._matches(node)
            and type(node.value) is type(self.plan.original_value)
            and node.value == self.plan.original_value
        ):
            self.changed = True
            return ast.copy_location(ast.Constant(value=self.plan.replacement_value), node)
        return node

    def visit_If(self, node: ast.If) -> ast.AST:  # noqa: N802 - ast API
        node = self.generic_visit(node)
        if (
            self.plan.mutation_kind == "negate_condition"
            and self._active_function
            and getattr(node.test, "lineno", 0) == self.plan.target_lineno
            and getattr(node.test, "col_offset", -1) == self.plan.target_col_offset
        ):
            node.test = ast.copy_location(ast.UnaryOp(op=ast.Not(), operand=node.test), node.test)
            self.changed = True
        return node


def apply_ast_mutation(source: str, plan: AstMutationPlan) -> str:
    """Apply one structural AST mutation and return syntactically valid source."""

    tree = ast.parse(source)
    transformer = _ApplyAstMutationPlan(plan)
    rewritten = transformer.visit(tree)
    if not transformer.changed:
        raise RuntimeError(f"{plan.function_name}: AST mutation anchor not found for {plan.mutation_kind}")
    ast.fix_missing_locations(rewritten)
    output = ast.unparse(rewritten) + "\n"
    compile(output, "<ast_synthesis_candidate>", "exec")
    return output


def apply_mapping_none_deletion_mutation(source: str, plan: AstMutationPlan) -> str:
    """Apply one source-derived guarded deletion mutation."""

    if plan.mutation_kind != "insert_guarded_none_value_deletion":
        raise RuntimeError("mapping None deletion applicator received a non-deletion plan")
    return apply_ast_mutation(source, plan)


def _visible_test_source(repo_root: Path) -> str:
    test_path = repo_root / "tests" / "test_external_code_repair_task.py"
    if test_path.exists():
        return test_path.read_text(encoding="utf-8")
    return AST_SYNTHESIS_VISIBLE_TEST


def _candidate_name_for_plan(plan: AstMutationPlan) -> str:
    function_fragment = _safe_identifier_fragment(plan.function_name)
    if plan.mutation_kind == "insert_guarded_none_value_deletion":
        state_fragment = _safe_identifier_fragment(plan.state_name)
        return f"external_code_repair_ast_{function_fragment}_{state_fragment}_none_deletion_v1"
    fragments = [
        "external_code_repair_ast",
        function_fragment,
        _safe_identifier_fragment(plan.mutation_kind),
        str(plan.target_lineno or plan.first_lineno),
        str(max(plan.target_col_offset, 0)),
    ]
    if plan.original or plan.replacement:
        fragments.extend([_safe_identifier_fragment(plan.original), _safe_identifier_fragment(plan.replacement)])
    elif plan.guard_name:
        fragments.extend([_safe_identifier_fragment(plan.guard_name), _safe_identifier_fragment(plan.fallback_name)])
    elif plan.original_value is not None or plan.replacement_value is not None:
        fragments.extend(
            [
                _safe_identifier_fragment(repr(plan.original_value)),
                _safe_identifier_fragment(repr(plan.replacement_value)),
            ]
        )
    return "_".join(fragments) + "_v1"


def _candidate_for_plan(
    repo_root: Path,
    generation: int,
    plan: AstMutationPlan,
    *,
    target: Path,
    test_source: str,
) -> CandidatePatch:
    candidate_name = _candidate_name_for_plan(plan)
    function_fragment = _safe_identifier_fragment(plan.function_name)
    mutation_fragment = _safe_identifier_fragment(plan.mutation_kind)

    def transform(source: str, selected_plan: AstMutationPlan = plan) -> str:
        return apply_ast_mutation(source, selected_plan)

    return CandidatePatch(
        name=candidate_name,
        generation=generation,
        goal=Goal(
            name=f"repair_{function_fragment}_{mutation_fragment}",
            target=f"shared.external_repair_target.{plan.function_name}",
            metric="AST-synthesized structural candidate passes visible, hidden, and full-suite gates",
            rationale=(
                "The source AST exposes a generic structural mutation opportunity; "
                "the loop proposes it without reading hidden cases or quarantined reference fixes, "
                "and the gate chain decides whether it is a real improvement."
            ),
        ),
        target_path=target,
        test_path=repo_root / "tests" / "test_external_code_repair_task.py",
        transform=transform,
        test_source=test_source,
        focused_tests=("tests/test_external_code_repair_task.py",),
        capability_family="external_code_repair",
        operator_specs=operator_specs_for("external_code_repair", f"ast_{plan.mutation_kind}"),
        generator_improvement=generator_feedback(
            "AST mutation synthesis",
            "derives structural mutation plans from parsed source syntax rather than target-specific anchors",
            (
                f"{plan.function_name}:{plan.mutation_kind} synthesized from AST coordinates "
                f"{plan.target_lineno}:{plan.target_col_offset}; hidden cases and references not inspected"
            ),
        ),
    )


def _plan_sort_key(plan: AstMutationPlan) -> Tuple[int, str, int, int, str]:
    try:
        order = _MUTATION_ORDER.index(plan.mutation_kind)
    except ValueError:
        order = len(_MUTATION_ORDER)
    return (
        order,
        plan.function_name,
        plan.target_lineno or plan.first_lineno,
        max(plan.target_col_offset, 0),
        _candidate_name_for_plan(plan),
    )


def ast_synthesis_candidates(repo_root: Path, generation: int) -> List[CandidatePatch]:
    """Generate source-derived AST repair candidates through the normal loop API."""

    target = repo_root / "shared" / "external_repair_target.py"
    if not target.exists():
        return []
    source = target.read_text(encoding="utf-8")
    plans = discover_ast_mutation_plans(source)
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
        for plan in sorted(plans, key=_plan_sort_key)
    ]


def ast_synthesis_compile_count(source: str, plans: Sequence[AstMutationPlan]) -> int:
    """Return how many discovered plans produce syntactically valid Python."""

    compiled = 0
    for plan in plans:
        try:
            compile(apply_ast_mutation(source, plan), "<ast_synthesis_candidate>", "exec")
        except Exception:
            continue
        compiled += 1
    return compiled


def ast_synthesis_summary(source: str) -> dict:
    """Return generation counts for honest ablation reporting."""

    plans = discover_ast_mutation_plans(source)
    compiled_by_kind: Dict[str, int] = {}
    generated_by_kind: Dict[str, int] = {}
    for plan in plans:
        generated_by_kind[plan.mutation_kind] = generated_by_kind.get(plan.mutation_kind, 0) + 1
        try:
            compile(apply_ast_mutation(source, plan), "<ast_synthesis_candidate>", "exec")
        except Exception:
            continue
        compiled_by_kind[plan.mutation_kind] = compiled_by_kind.get(plan.mutation_kind, 0) + 1

    compiled_candidates = sum(compiled_by_kind.values())
    return {
        "produced_candidates": len(plans),
        "compiled_candidates": compiled_candidates,
        "failed_compile_candidates": len(plans) - compiled_candidates,
        "mutation_kinds": sorted(generated_by_kind),
        "generated_by_kind": dict(sorted(generated_by_kind.items())),
        "compiled_by_kind": dict(sorted(compiled_by_kind.items())),
    }
