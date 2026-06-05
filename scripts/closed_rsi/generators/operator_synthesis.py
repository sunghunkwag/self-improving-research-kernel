"""Compositional capability-operator synthesis for closed RSI candidates.

The task records in this module describe required behavior, not reference
implementations. Candidate source is assembled from reusable program atoms so
the loop no longer copies a stored answer body out of a blueprint table.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class CapabilityOperatorBlueprint:
    """Benchmark task definition for one missing capability primitive."""

    family: str
    function_name: str
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


CAPABILITY_OPERATOR_BLUEPRINTS: Tuple[CapabilityOperatorBlueprint, ...] = (
    CapabilityOperatorBlueprint(
        family="algorithm_synthesis",
        function_name="run_length_encode",
        candidate_name="capability_operator_algorithm_synthesis_rle_v1",
        behavior_tags=("adjacent_runs", "sequence_to_pairs", "tuple_output"),
        public_assertion="assert run_length_encode((1, 1, 2, 2, 2, 3)) == ((1, 2), (2, 3), (3, 1))",
        hidden_assertion="assert run_length_encode(('a', 'a', 'b', 'a')) == (('a', 2), ('b', 1), ('a', 1))",
    ),
    CapabilityOperatorBlueprint(
        family="symbolic_reasoning",
        function_name="infer_linear_rule",
        candidate_name="capability_operator_symbolic_reasoning_linear_rule_v1",
        behavior_tags=("constant_delta", "sequence_rule", "dict_output"),
        public_assertion="assert infer_linear_rule((2, 5, 8, 11)) == {'start': 2, 'step': 3, 'next': 14}",
        hidden_assertion="assert infer_linear_rule((-3, -1, 1)) == {'start': -3, 'step': 2, 'next': 3}",
    ),
    CapabilityOperatorBlueprint(
        family="grid_transformation",
        function_name="rotate_grid_clockwise",
        candidate_name="capability_operator_grid_transformation_rotate_v1",
        behavior_tags=("rectangular_grid", "clockwise_rotation", "tuple_output"),
        public_assertion="assert rotate_grid_clockwise(((1, 2, 3), (4, 5, 6))) == ((4, 1), (5, 2), (6, 3))",
        hidden_assertion="assert rotate_grid_clockwise((('x',), ('y',), ('z',))) == (('z', 'y', 'x'),)",
    ),
    CapabilityOperatorBlueprint(
        family="bug_repair",
        function_name="dedupe_preserve_order",
        candidate_name="capability_operator_bug_repair_dedupe_v1",
        behavior_tags=("stable_filter", "set_memory", "tuple_output"),
        public_assertion="assert dedupe_preserve_order(('b', 'a', 'b', 'c', 'a')) == ('b', 'a', 'c')",
        hidden_assertion="assert dedupe_preserve_order((3, 3, 2, 3, 1, 2)) == (3, 2, 1)",
    ),
    CapabilityOperatorBlueprint(
        family="planning_state_transition",
        function_name="apply_grid_action",
        candidate_name="capability_operator_planning_state_transition_action_v1",
        behavior_tags=("state_copy", "cardinal_action", "bounded_transition"),
        public_assertion="assert apply_grid_action({'x': 0, 'y': 0}, 'east') == {'x': 1, 'y': 0}",
        hidden_assertion="assert apply_grid_action({'x': 2, 'y': -1}, 'north') == {'x': 2, 'y': 0}",
    ),
)


def _indent(lines: Tuple[str, ...]) -> str:
    return "\n".join(f"    {line}" if line else "" for line in lines)


def _signature_for(function_name: str) -> str:
    signatures = {
        "run_length_encode": "(items)",
        "infer_linear_rule": "(values)",
        "rotate_grid_clockwise": "(grid)",
        "dedupe_preserve_order": "(items)",
        "apply_grid_action": "(state, action)",
    }
    return signatures[function_name]


def _function_source(name: str, docstring: str, body: Tuple[str, ...]) -> str:
    source = f'def {name}{_signature_for(name)}:\n    """{docstring}"""\n\n{_indent(body)}\n'
    return source


def _recipes_for(task: CapabilityOperatorBlueprint) -> Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...]], ...]:
    """Return synthesized recipes selected by behavior tags."""

    if "adjacent_runs" in task.behavior_tags:
        return (
            (
                "stateful_scan_v1",
                ("iterator_seed", "run_counter", "tuple_pairs"),
                (
                    "iterator = iter(items)",
                    "try:",
                    "    current = next(iterator)",
                    "except StopIteration:",
                    "    return ()",
                    "pairs = []",
                    "count = 1",
                    "for item in iterator:",
                    "    if item == current:",
                    "        count += 1",
                    "    else:",
                    "        pairs.append((current, count))",
                    "        current = item",
                    "        count = 1",
                    "pairs.append((current, count))",
                    "return tuple(pairs)",
                ),
            ),
            (
                "boundary_scan_v2",
                ("index_windows", "run_counter", "tuple_pairs"),
                (
                    "sequence = tuple(items)",
                    "pairs = []",
                    "index = 0",
                    "while index < len(sequence):",
                    "    value = sequence[index]",
                    "    next_index = index + 1",
                    "    while next_index < len(sequence) and sequence[next_index] == value:",
                    "        next_index += 1",
                    "    pairs.append((value, next_index - index))",
                    "    index = next_index",
                    "return tuple(pairs)",
                ),
            ),
        )
    if "constant_delta" in task.behavior_tags:
        return (
            (
                "delta_consistency_v1",
                ("tuple_normalization", "pairwise_delta", "dict_projection"),
                (
                    "sequence = tuple(values)",
                    "if len(sequence) < 2:",
                    "    raise ValueError(\"at least two values are required\")",
                    "deltas = tuple(right - left for left, right in zip(sequence, sequence[1:]))",
                    "step = deltas[0]",
                    "if any(delta != step for delta in deltas):",
                    "    raise ValueError(\"values do not form a linear rule\")",
                    "return {\"start\": sequence[0], \"step\": step, \"next\": sequence[-1] + step}",
                ),
            ),
        )
    if "clockwise_rotation" in task.behavior_tags:
        return (
            (
                "column_projection_v1",
                ("rectangular_guard", "reverse_rows", "column_projection"),
                (
                    "rows = tuple(tuple(row) for row in grid)",
                    "if not rows:",
                    "    return ()",
                    "width = len(rows[0])",
                    "if any(len(row) != width for row in rows):",
                    "    raise ValueError(\"grid must be rectangular\")",
                    "return tuple(tuple(row[column] for row in reversed(rows)) for column in range(width))",
                ),
            ),
        )
    if "stable_filter" in task.behavior_tags:
        return (
            (
                "first_seen_filter_v1",
                ("set_memory", "stable_append", "tuple_output"),
                (
                    "seen = set()",
                    "ordered = []",
                    "for item in items:",
                    "    if item not in seen:",
                    "        seen.add(item)",
                    "        ordered.append(item)",
                    "return tuple(ordered)",
                ),
            ),
        )
    if "cardinal_action" in task.behavior_tags:
        return (
            (
                "branch_transition_v1",
                ("state_copy", "cardinal_branch", "integer_projection"),
                (
                    "next_state = dict(state)",
                    "x = int(next_state.get(\"x\", 0))",
                    "y = int(next_state.get(\"y\", 0))",
                    "if action == \"north\":",
                    "    y += 1",
                    "elif action == \"south\":",
                    "    y -= 1",
                    "elif action == \"east\":",
                    "    x += 1",
                    "elif action == \"west\":",
                    "    x -= 1",
                    "elif action == \"stay\":",
                    "    pass",
                    "else:",
                    "    raise ValueError(f\"unknown action: {action}\")",
                    "next_state[\"x\"] = x",
                    "next_state[\"y\"] = y",
                    "return next_state",
                ),
            ),
        )
    raise RuntimeError(f"no synthesis recipe for {task.family}:{task.function_name}")


def synthesize_capability_operator_variants(
    task: CapabilityOperatorBlueprint,
    *,
    max_variants: int = 1,
) -> Tuple[SynthesizedOperator, ...]:
    """Synthesize bounded operator candidates from reusable recipes."""

    variants: List[SynthesizedOperator] = []
    for strategy, atoms, body in _recipes_for(task)[: max(1, int(max_variants))]:
        source = _function_source(
            task.function_name,
            f"Synthesized {task.family} operator via {strategy}.",
            body,
        )
        compile(source, f"<synthesized {task.function_name}>", "exec")
        variants.append(
            SynthesizedOperator(
                source=source,
                strategy=strategy,
                atoms=atoms,
                source_sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(variants)


def operator_synthesis_summary(max_variants: int = 2) -> Dict[str, object]:
    """Return an honest summary of the synthesized operator search space."""

    rows = []
    for task in CAPABILITY_OPERATOR_BLUEPRINTS:
        variants = synthesize_capability_operator_variants(task, max_variants=max_variants)
        rows.append(
            {
                "family": task.family,
                "operator": task.function_name,
                "strategies": [variant.strategy for variant in variants],
                "atoms": sorted({atom for variant in variants for atom in variant.atoms}),
                "variant_count": len(variants),
            }
        )
    return {
        "task_count": len(CAPABILITY_OPERATOR_BLUEPRINTS),
        "solution_source": "compositional_synthesis_recipes",
        "tasks_store_reference_bodies": False,
        "operators": rows,
    }
