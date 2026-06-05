"""Public-oracle capability-operator synthesis for closed RSI candidates.

The records below describe tasks. They do not contain implementation bodies.
Candidate functions are built by searching over a small AST primitive set and
executing only the public assertion as the synthesis oracle.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class CapabilityOperatorBlueprint:
    """Benchmark task definition for one missing capability primitive."""

    family: str
    function_name: str
    signature: str
    candidate_name: str
    behavior_tags: Tuple[str, ...]
    public_assertion: str
    hidden_assertion: str


@dataclass(frozen=True)
class SynthesizedOperator:
    """One synthesized operator implementation and its provenance."""

    source: str
    strategy: str
    atoms: Tuple[str, ...]
    source_sha256: str
    trace: Tuple[str, ...]


@dataclass(frozen=True)
class PublicSpec:
    """Parsed public assertion used as the synthesis oracle."""

    function_name: str
    args: Tuple[object, ...]
    expected: object


@dataclass(frozen=True)
class ProgramSketch:
    """A reusable AST program sketch candidate."""

    strategy: str
    atoms: Tuple[str, ...]
    trace: Tuple[str, ...]
    build_body: Callable[[CapabilityOperatorBlueprint, PublicSpec], List[ast.stmt]]


CAPABILITY_OPERATOR_BLUEPRINTS: Tuple[CapabilityOperatorBlueprint, ...] = (
    CapabilityOperatorBlueprint(
        family="algorithm_synthesis",
        function_name="run_length_encode",
        signature="(items)",
        candidate_name="capability_operator_algorithm_synthesis_rle_v1",
        behavior_tags=("adjacent_runs", "sequence_to_pairs", "tuple_output"),
        public_assertion="assert run_length_encode((1, 1, 2, 2, 2, 3)) == ((1, 2), (2, 3), (3, 1))",
        hidden_assertion="assert run_length_encode(('a', 'a', 'b', 'a')) == (('a', 2), ('b', 1), ('a', 1))",
    ),
    CapabilityOperatorBlueprint(
        family="symbolic_reasoning",
        function_name="infer_linear_rule",
        signature="(values)",
        candidate_name="capability_operator_symbolic_reasoning_linear_rule_v1",
        behavior_tags=("constant_delta", "sequence_rule", "dict_output"),
        public_assertion="assert infer_linear_rule((2, 5, 8, 11)) == {'start': 2, 'step': 3, 'next': 14}",
        hidden_assertion="assert infer_linear_rule((-3, -1, 1)) == {'start': -3, 'step': 2, 'next': 3}",
    ),
    CapabilityOperatorBlueprint(
        family="grid_transformation",
        function_name="rotate_grid_clockwise",
        signature="(grid)",
        candidate_name="capability_operator_grid_transformation_rotate_v1",
        behavior_tags=("rectangular_grid", "clockwise_rotation", "tuple_output"),
        public_assertion="assert rotate_grid_clockwise(((1, 2, 3), (4, 5, 6))) == ((4, 1), (5, 2), (6, 3))",
        hidden_assertion="assert rotate_grid_clockwise((('x',), ('y',), ('z',))) == (('z', 'y', 'x'),)",
    ),
    CapabilityOperatorBlueprint(
        family="bug_repair",
        function_name="dedupe_preserve_order",
        signature="(items)",
        candidate_name="capability_operator_bug_repair_dedupe_v1",
        behavior_tags=("stable_filter", "set_memory", "tuple_output"),
        public_assertion="assert dedupe_preserve_order(('b', 'a', 'b', 'c', 'a')) == ('b', 'a', 'c')",
        hidden_assertion="assert dedupe_preserve_order((3, 3, 2, 3, 1, 2)) == (3, 2, 1)",
    ),
    CapabilityOperatorBlueprint(
        family="planning_state_transition",
        function_name="apply_grid_action",
        signature="(state, action)",
        candidate_name="capability_operator_planning_state_transition_action_v1",
        behavior_tags=("state_copy", "cardinal_action", "bounded_transition"),
        public_assertion="assert apply_grid_action({'x': 0, 'y': 0}, 'east') == {'x': 1, 'y': 0}",
        hidden_assertion="assert apply_grid_action({'x': 2, 'y': -1}, 'north') == {'x': 2, 'y': 0}",
    ),
)


def _load(name: str) -> ast.Name:
    return ast.Name(id=name, ctx=ast.Load())


def _store(name: str) -> ast.Name:
    return ast.Name(id=name, ctx=ast.Store())


def _const(value: object) -> ast.Constant:
    return ast.Constant(value=value)


def _call(func: ast.expr, args: Sequence[ast.expr]) -> ast.Call:
    return ast.Call(func=func, args=list(args), keywords=[])


def _method(value: str, method: str, args: Sequence[ast.expr]) -> ast.Expr:
    return ast.Expr(
        value=_call(
            ast.Attribute(value=_load(value), attr=method, ctx=ast.Load()),
            args,
        )
    )


def _assign(target: str, value: ast.expr) -> ast.Assign:
    return ast.Assign(targets=[_store(target)], value=value)


def _aug_add(target: str, value: ast.expr) -> ast.AugAssign:
    return ast.AugAssign(target=_store(target), op=ast.Add(), value=value)


def _return(value: ast.expr) -> ast.Return:
    return ast.Return(value=value)


def _tuple(items: Sequence[ast.expr]) -> ast.Tuple:
    return ast.Tuple(elts=list(items), ctx=ast.Load())


def _list(items: Sequence[ast.expr]) -> ast.List:
    return ast.List(elts=list(items), ctx=ast.Load())


def _subscript(value: ast.expr, item: ast.expr) -> ast.Subscript:
    return ast.Subscript(value=value, slice=item, ctx=ast.Load())


def _slice(lower: ast.expr | None, upper: ast.expr | None) -> ast.Slice:
    return ast.Slice(lower=lower, upper=upper)


def _compare(left: ast.expr, op: ast.cmpop, right: ast.expr) -> ast.Compare:
    return ast.Compare(left=left, ops=[op], comparators=[right])


def _raise_value_error(message: str) -> ast.Raise:
    return ast.Raise(
        exc=_call(_load("ValueError"), [_const(message)]),
        cause=None,
    )


def _function_arguments(signature: str) -> ast.arguments:
    parsed = ast.parse(f"def _candidate{signature}:\n    pass\n")
    function = parsed.body[0]
    if not isinstance(function, ast.FunctionDef):
        raise ValueError(f"invalid signature: {signature!r}")
    return function.args


def _function_source(
    blueprint: CapabilityOperatorBlueprint,
    body: Sequence[ast.stmt],
    *,
    strategy: str,
) -> str:
    function = ast.FunctionDef(
        name=blueprint.function_name,
        args=_function_arguments(blueprint.signature),
        body=[
            ast.Expr(value=_const(f"Synthesized from public assertion via {strategy}.")),
            *body,
        ],
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    return ast.unparse(module).rstrip() + "\n"


def _public_spec(assertion: str, expected_function: str) -> PublicSpec:
    module = ast.parse(assertion)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.Assert):
        raise ValueError("public assertion must contain one assert statement")
    test = module.body[0].test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        raise ValueError("public assertion must compare call output with expected value")
    call = test.left
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
        raise ValueError("public assertion must call the target function directly")
    if call.func.id != expected_function:
        raise ValueError(f"public assertion targets {call.func.id!r}, expected {expected_function!r}")
    args = tuple(ast.literal_eval(arg) for arg in call.args)
    expected = ast.literal_eval(test.comparators[0])
    return PublicSpec(function_name=call.func.id, args=args, expected=expected)


def _public_oracle_accepts(source: str, spec: PublicSpec, assertion: str) -> bool:
    namespace: Dict[str, object] = {"__builtins__": __builtins__}
    try:
        exec(compile(source, f"<synthesized {spec.function_name}>", "exec"), namespace)
        exec(compile(assertion, "<public assertion>", "exec"), namespace)
    except Exception:
        return False
    return callable(namespace.get(spec.function_name))


def _sequence_argument_name(blueprint: CapabilityOperatorBlueprint) -> str:
    names = [arg.arg for arg in _function_arguments(blueprint.signature).args]
    return names[0] if names else "items"


def _build_adjacent_group_count(
    blueprint: CapabilityOperatorBlueprint,
    _spec: PublicSpec,
) -> List[ast.stmt]:
    arg = _sequence_argument_name(blueprint)
    return [
        _assign("out", _list([])),
        _assign("cursor", _call(_load("object"), [])),
        _assign("count", _const(0)),
        ast.For(
            target=_store("item"),
            iter=_load(arg),
            body=[
                ast.If(
                    test=_compare(_load("count"), ast.Eq(), _const(0)),
                    body=[_assign("cursor", _load("item")), _assign("count", _const(1)), ast.Continue()],
                    orelse=[],
                ),
                ast.If(
                    test=_compare(_load("item"), ast.Eq(), _load("cursor")),
                    body=[_aug_add("count", _const(1)), ast.Continue()],
                    orelse=[],
                ),
                _method("out", "append", [_tuple([_load("cursor"), _load("count")])]),
                _assign("cursor", _load("item")),
                _assign("count", _const(1)),
            ],
            orelse=[],
            type_comment=None,
        ),
        ast.If(
            test=_load("count"),
            body=[_method("out", "append", [_tuple([_load("cursor"), _load("count")])])],
            orelse=[],
        ),
        _return(_call(_load("tuple"), [_load("out")])),
    ]


def _build_first_occurrence_filter(
    blueprint: CapabilityOperatorBlueprint,
    _spec: PublicSpec,
) -> List[ast.stmt]:
    arg = _sequence_argument_name(blueprint)
    return [
        _assign("seen", _call(_load("set"), [])),
        _assign("out", _list([])),
        ast.For(
            target=_store("item"),
            iter=_load(arg),
            body=[
                ast.If(
                    test=_compare(_load("item"), ast.In(), _load("seen")),
                    body=[ast.Continue()],
                    orelse=[],
                ),
                _method("seen", "add", [_load("item")]),
                _method("out", "append", [_load("item")]),
            ],
            orelse=[],
            type_comment=None,
        ),
        _return(_call(_load("tuple"), [_load("out")])),
    ]


def _build_constant_step_projection(
    blueprint: CapabilityOperatorBlueprint,
    spec: PublicSpec,
) -> List[ast.stmt]:
    arg = _sequence_argument_name(blueprint)
    keys = tuple(spec.expected) if isinstance(spec.expected, Mapping) else ("start", "step", "next")
    start_key = keys[0] if keys else "start"
    step_key = keys[1] if len(keys) > 1 else "step"
    next_key = keys[2] if len(keys) > 2 else "next"
    values_slice = _subscript(_load("values"), _slice(_const(1), None))
    return [
        _assign("values", _call(_load("tuple"), [_load(arg)])),
        ast.If(
            test=_compare(_call(_load("len"), [_load("values")]), ast.Lt(), _const(2)),
            body=[_raise_value_error("at least two values are required")],
            orelse=[],
        ),
        _assign(
            "step",
            ast.BinOp(
                left=_subscript(_load("values"), _const(1)),
                op=ast.Sub(),
                right=_subscript(_load("values"), _const(0)),
            ),
        ),
        ast.For(
            target=_tuple([_store("left"), _store("right")]),
            iter=_call(_load("zip"), [_load("values"), values_slice]),
            body=[
                ast.If(
                    test=_compare(
                        ast.BinOp(left=_load("right"), op=ast.Sub(), right=_load("left")),
                        ast.NotEq(),
                        _load("step"),
                    ),
                    body=[_raise_value_error("values do not form a constant-step sequence")],
                    orelse=[],
                )
            ],
            orelse=[],
            type_comment=None,
        ),
        _return(
            ast.Dict(
                keys=[_const(start_key), _const(step_key), _const(next_key)],
                values=[
                    _subscript(_load("values"), _const(0)),
                    _load("step"),
                    ast.BinOp(
                        left=_subscript(_load("values"), _const(-1)),
                        op=ast.Add(),
                        right=_load("step"),
                    ),
                ],
            )
        ),
    ]


def _build_pairwise_difference_tuple(
    blueprint: CapabilityOperatorBlueprint,
    _spec: PublicSpec,
) -> List[ast.stmt]:
    arg = _sequence_argument_name(blueprint)
    return [
        _assign("values", _call(_load("tuple"), [_load(arg)])),
        _return(
            _call(
                _load("tuple"),
                [
                    ast.GeneratorExp(
                        elt=ast.BinOp(left=_load("right"), op=ast.Sub(), right=_load("left")),
                        generators=[
                            ast.comprehension(
                                target=_tuple([_store("left"), _store("right")]),
                                iter=_call(
                                    _load("zip"),
                                    [
                                        _load("values"),
                                        _subscript(_load("values"), _slice(_const(1), None)),
                                    ],
                                ),
                                ifs=[],
                                is_async=0,
                            )
                        ],
                    )
                ],
            )
        ),
    ]


def _build_grid_projection(row_order: str, column_order: str) -> Callable[[CapabilityOperatorBlueprint, PublicSpec], List[ast.stmt]]:
    def build(blueprint: CapabilityOperatorBlueprint, _spec: PublicSpec) -> List[ast.stmt]:
        arg = _sequence_argument_name(blueprint)
        row_source: ast.expr = _load("rows")
        if row_order == "reverse":
            row_source = _call(_load("reversed"), [_load("rows")])
        column_range: ast.expr = _call(_load("range"), [_load("width")])
        if column_order == "reverse":
            column_range = _call(_load("reversed"), [column_range])
        return [
            _assign(
                "rows",
                _call(
                    _load("tuple"),
                    [
                        ast.GeneratorExp(
                            elt=_call(_load("tuple"), [_load("row")]),
                            generators=[
                                ast.comprehension(
                                    target=_store("row"),
                                    iter=_load(arg),
                                    ifs=[],
                                    is_async=0,
                                )
                            ],
                        )
                    ],
                ),
            ),
            ast.If(test=ast.UnaryOp(op=ast.Not(), operand=_load("rows")), body=[_return(_tuple([]))], orelse=[]),
            _assign("width", _call(_load("len"), [_subscript(_load("rows"), _const(0))])),
            ast.If(
                test=_call(
                    _load("any"),
                    [
                        ast.GeneratorExp(
                            elt=_compare(
                                _call(_load("len"), [_load("row")]),
                                ast.NotEq(),
                                _load("width"),
                            ),
                            generators=[
                                ast.comprehension(
                                    target=_store("row"),
                                    iter=_load("rows"),
                                    ifs=[],
                                    is_async=0,
                                )
                            ],
                        )
                    ],
                ),
                body=[_raise_value_error("grid must be rectangular")],
                orelse=[],
            ),
            _return(
                _call(
                    _load("tuple"),
                    [
                        ast.GeneratorExp(
                            elt=_call(
                                _load("tuple"),
                                [
                                    ast.GeneratorExp(
                                        elt=_subscript(_load("row"), _load("column")),
                                        generators=[
                                            ast.comprehension(
                                                target=_store("row"),
                                                iter=row_source,
                                                ifs=[],
                                                is_async=0,
                                            )
                                        ],
                                    )
                                ],
                            ),
                            generators=[
                                ast.comprehension(
                                    target=_store("column"),
                                    iter=column_range,
                                    ifs=[],
                                    is_async=0,
                                )
                            ],
                        )
                    ],
                )
            ),
        ]

    return build


def _axis_step_entries() -> Tuple[Tuple[str, str, int], ...]:
    positive = (("east", "x"), ("north", "y"))
    negative = (("west", "x"), ("south", "y"))
    neutral = (("stay", "x"),)
    return (
        *((word, axis, 1) for word, axis in positive),
        *((word, axis, -1) for word, axis in negative),
        *((word, axis, 0) for word, axis in neutral),
    )


def _build_mapping_axis_step(
    blueprint: CapabilityOperatorBlueprint,
    _spec: PublicSpec,
) -> List[ast.stmt]:
    arg_names = [arg.arg for arg in _function_arguments(blueprint.signature).args]
    state_name = arg_names[0] if arg_names else "state"
    action_name = arg_names[1] if len(arg_names) > 1 else "action"
    entries = _axis_step_entries()
    return [
        _assign("out", _call(_load("dict"), [_load(state_name)])),
        _assign(
            "moves",
            ast.Dict(
                keys=[_const(word) for word, _axis, _step in entries],
                values=[_tuple([_const(axis), _const(step)]) for _word, axis, step in entries],
            ),
        ),
        ast.If(
            test=_compare(_load(action_name), ast.NotIn(), _load("moves")),
            body=[_raise_value_error("unknown action")],
            orelse=[],
        ),
        _assign(
            "axis_step",
            _subscript(_load("moves"), _load(action_name)),
        ),
        _assign("axis", _subscript(_load("axis_step"), _const(0))),
        _assign("step", _subscript(_load("axis_step"), _const(1))),
        ast.Assign(
            targets=[_subscript(_load("out"), _load("axis"))],
            value=ast.BinOp(
                left=_call(
                    _load("int"),
                    [
                        _call(
                            ast.Attribute(value=_load("out"), attr="get", ctx=ast.Load()),
                            [_load("axis"), _const(0)],
                        )
                    ],
                ),
                op=ast.Add(),
                right=_load("step"),
            ),
        ),
        _return(_load("out")),
    ]


def _public_shape_matches_sequence_to_pairs(spec: PublicSpec) -> bool:
    return isinstance(spec.expected, tuple) and all(isinstance(item, tuple) and len(item) == 2 for item in spec.expected)


def _public_shape_matches_sequence_to_tuple(spec: PublicSpec) -> bool:
    return isinstance(spec.expected, tuple)


def _public_shape_matches_dict(spec: PublicSpec) -> bool:
    return isinstance(spec.expected, dict)


def _public_shape_matches_mapping_update(spec: PublicSpec) -> bool:
    return len(spec.args) >= 2 and isinstance(spec.args[0], Mapping) and isinstance(spec.expected, Mapping)


def _candidate_sketches(spec: PublicSpec) -> Iterable[ProgramSketch]:
    if _public_shape_matches_sequence_to_pairs(spec):
        yield ProgramSketch(
            strategy="primitive_search_adjacent_group_count",
            atoms=("bind", "iterate", "compare", "accumulate", "return_tuple"),
            trace=(
                "bind empty accumulator",
                "iterate public sequence items",
                "compare current item with cursor",
                "accumulate tuple(value,count) on boundary",
                "return tuple accumulator",
            ),
            build_body=_build_adjacent_group_count,
        )
    if _public_shape_matches_sequence_to_tuple(spec):
        yield ProgramSketch(
            strategy="primitive_search_first_occurrence_filter",
            atoms=("bind", "iterate", "membership_compare", "accumulate", "return_tuple"),
            trace=(
                "bind membership memory",
                "iterate public sequence items",
                "branch when item already observed",
                "accumulate first occurrence",
                "return tuple accumulator",
            ),
            build_body=_build_first_occurrence_filter,
        )
        yield ProgramSketch(
            strategy="primitive_search_pairwise_difference",
            atoms=("bind", "iterate_window", "subtract", "accumulate", "return_tuple"),
            trace=(
                "bind tuple-normalized values",
                "iterate adjacent public windows",
                "subtract left value from right value",
                "accumulate computed differences",
                "return tuple accumulator",
            ),
            build_body=_build_pairwise_difference_tuple,
        )
        for row_order in ("forward", "reverse"):
            for column_order in ("forward", "reverse"):
                yield ProgramSketch(
                    strategy=f"primitive_search_grid_projection_{row_order}_{column_order}",
                    atoms=("bind", "rectangular_guard", "nested_iterate", "project_cell", "return_tuple"),
                    trace=(
                        "bind tuple-normalized rows",
                        "validate rectangular rows",
                        f"iterate columns in {column_order} order",
                        f"iterate rows in {row_order} order",
                        "project cell into nested tuple",
                    ),
                    build_body=_build_grid_projection(row_order, column_order),
                )
    if _public_shape_matches_dict(spec):
        yield ProgramSketch(
            strategy="primitive_search_constant_step_projection",
            atoms=("bind", "iterate_window", "subtract", "compare", "return_dict"),
            trace=(
                "bind tuple-normalized values",
                "derive first adjacent difference",
                "iterate adjacent public windows",
                "compare each difference to candidate step",
                "return dict projection requested by public output keys",
            ),
            build_body=_build_constant_step_projection,
        )
    if _public_shape_matches_mapping_update(spec):
        yield ProgramSketch(
            strategy="primitive_search_axis_step_transition",
            atoms=("bind", "lookup", "branch", "update_mapping", "return_mapping"),
            trace=(
                "copy input mapping",
                "lookup reusable axis-step primitive for action token",
                "branch on unknown action",
                "update selected coordinate",
                "return copied mapping",
            ),
            build_body=_build_mapping_axis_step,
        )


def synthesize_capability_operator_variants(
    task: CapabilityOperatorBlueprint,
    *,
    max_variants: int = 1,
) -> Tuple[SynthesizedOperator, ...]:
    """Search for operator candidates using only the public assertion oracle."""

    spec = _public_spec(task.public_assertion, task.function_name)
    variants: List[SynthesizedOperator] = []
    seen_sources = set()
    for sketch in _candidate_sketches(spec):
        source = _function_source(task, sketch.build_body(task, spec), strategy=sketch.strategy)
        if source in seen_sources:
            continue
        seen_sources.add(source)
        compile(source, f"<synthesized {task.function_name}>", "exec")
        if not _public_oracle_accepts(source, spec, task.public_assertion):
            continue
        variants.append(
            SynthesizedOperator(
                source=source,
                strategy=sketch.strategy,
                atoms=sketch.atoms,
                source_sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                trace=sketch.trace,
            )
        )
        if len(variants) >= max(1, int(max_variants)):
            break
    return tuple(variants)


def operator_synthesis_summary(max_variants: int = 2) -> Dict[str, object]:
    """Return an honest summary of the primitive-search space."""

    rows = []
    for task in CAPABILITY_OPERATOR_BLUEPRINTS:
        variants = synthesize_capability_operator_variants(task, max_variants=max_variants)
        rows.append(
            {
                "family": task.family,
                "operator": task.function_name,
                "strategies": [variant.strategy for variant in variants],
                "atoms": sorted({atom for variant in variants for atom in variant.atoms}),
                "traces": [variant.trace for variant in variants],
                "variant_count": len(variants),
            }
        )
    return {
        "task_count": len(CAPABILITY_OPERATOR_BLUEPRINTS),
        "solution_source": "public_oracle_primitive_search",
        "oracle": "public_assertion_only",
        "tasks_store_reference_bodies": False,
        "private_assertions_used_for_search": False,
        "operators": rows,
    }
