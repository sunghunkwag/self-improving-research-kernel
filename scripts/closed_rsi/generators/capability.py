"""Capability primitive candidate generators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.records import CandidatePatch, Goal, generator_feedback


@dataclass(frozen=True)
class CapabilityOperatorBlueprint:
    """Deterministic repair plan for one capability benchmark primitive."""

    family: str
    function_name: str
    candidate_name: str
    implementation_source: str
    public_assertion: str
    hidden_assertion: str


CAPABILITY_OPERATOR_BLUEPRINTS: Tuple[CapabilityOperatorBlueprint, ...] = (
    CapabilityOperatorBlueprint(
        family="algorithm_synthesis",
        function_name="run_length_encode",
        candidate_name="capability_operator_algorithm_synthesis_rle_v1",
        implementation_source='''def run_length_encode(items):
    """Return adjacent value/count pairs for a sequence."""

    iterator = iter(items)
    try:
        current = next(iterator)
    except StopIteration:
        return ()
    encoded = []
    count = 1
    for item in iterator:
        if item == current:
            count += 1
            continue
        encoded.append((current, count))
        current = item
        count = 1
    if count:
        encoded.append((current, count))
    return tuple(encoded)
''',
        public_assertion="assert run_length_encode((1, 1, 2, 2, 2, 3)) == ((1, 2), (2, 3), (3, 1))",
        hidden_assertion="assert run_length_encode(('a', 'a', 'b', 'a')) == (('a', 2), ('b', 1), ('a', 1))",
    ),
    CapabilityOperatorBlueprint(
        family="symbolic_reasoning",
        function_name="infer_linear_rule",
        candidate_name="capability_operator_symbolic_reasoning_linear_rule_v1",
        implementation_source='''def infer_linear_rule(values):
    """Infer a constant-step sequence rule and its next value."""

    sequence = tuple(values)
    if len(sequence) < 2:
        raise ValueError("at least two values are required")
    deltas = tuple(right - left for left, right in zip(sequence, sequence[1:]))
    step = deltas[0]
    if any(delta != step for delta in deltas):
        raise ValueError("values do not form a linear rule")
    return {"start": sequence[0], "step": step, "next": sequence[-1] + step}
''',
        public_assertion="assert infer_linear_rule((2, 5, 8, 11)) == {'start': 2, 'step': 3, 'next': 14}",
        hidden_assertion="assert infer_linear_rule((-3, -1, 1)) == {'start': -3, 'step': 2, 'next': 3}",
    ),
    CapabilityOperatorBlueprint(
        family="grid_transformation",
        function_name="rotate_grid_clockwise",
        candidate_name="capability_operator_grid_transformation_rotate_v1",
        implementation_source='''def rotate_grid_clockwise(grid):
    """Rotate a rectangular grid clockwise."""

    rows = tuple(tuple(row) for row in grid)
    if not rows:
        return ()
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("grid must be rectangular")
    return tuple(tuple(row[column] for row in reversed(rows)) for column in range(width))
''',
        public_assertion="assert rotate_grid_clockwise(((1, 2, 3), (4, 5, 6))) == ((4, 1), (5, 2), (6, 3))",
        hidden_assertion="assert rotate_grid_clockwise((('x',), ('y',), ('z',))) == (('z', 'y', 'x'),)",
    ),
    CapabilityOperatorBlueprint(
        family="bug_repair",
        function_name="dedupe_preserve_order",
        candidate_name="capability_operator_bug_repair_dedupe_v1",
        implementation_source='''def dedupe_preserve_order(items):
    """Remove duplicate items while preserving first occurrence order."""

    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)
''',
        public_assertion="assert dedupe_preserve_order(('b', 'a', 'b', 'c', 'a')) == ('b', 'a', 'c')",
        hidden_assertion="assert dedupe_preserve_order((3, 3, 2, 3, 1, 2)) == (3, 2, 1)",
    ),
    CapabilityOperatorBlueprint(
        family="planning_state_transition",
        function_name="apply_grid_action",
        candidate_name="capability_operator_planning_state_transition_action_v1",
        implementation_source='''def apply_grid_action(state, action):
    """Apply a one-step cardinal movement action to a grid state."""

    next_state = dict(state)
    x = int(next_state.get("x", 0))
    y = int(next_state.get("y", 0))
    if action == "north":
        y += 1
    elif action == "south":
        y -= 1
    elif action == "east":
        x += 1
    elif action == "west":
        x -= 1
    elif action == "stay":
        pass
    else:
        raise ValueError(f"unknown action: {action}")
    next_state["x"] = x
    next_state["y"] = y
    return next_state
''',
        public_assertion="assert apply_grid_action({'x': 0, 'y': 0}, 'east') == {'x': 1, 'y': 0}",
        hidden_assertion="assert apply_grid_action({'x': 2, 'y': -1}, 'north') == {'x': 2, 'y': 0}",
    ),
)


def add_capability_operator(text: str, blueprint: CapabilityOperatorBlueprint) -> str:
    """Append a missing reusable capability primitive."""

    if f"def {blueprint.function_name}(" in text:
        return text
    return text.rstrip() + "\n\n\n" + blueprint.implementation_source.rstrip() + "\n"


def build_capability_operator_test(blueprint: CapabilityOperatorBlueprint) -> str:
    """Build public and hidden transfer tests for a synthesized operator."""

    return f'''from shared.capability_primitives import {blueprint.function_name}


def test_{blueprint.function_name}_public_counterexample():
    {blueprint.public_assertion}


def test_{blueprint.function_name}_hidden_transfer_counterexample():
    {blueprint.hidden_assertion}
'''


def capability_operator_candidates(repo_root: Path, generation: int) -> List[CandidatePatch]:
    """Plan repair candidates for executable capability benchmark fixtures."""

    target = repo_root / "shared" / "capability_primitives.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    candidates: List[CandidatePatch] = []
    for blueprint in CAPABILITY_OPERATOR_BLUEPRINTS:
        if f"def {blueprint.function_name}(" in text:
            continue
        candidates.append(
            CandidatePatch(
                name=blueprint.candidate_name,
                generation=generation,
                goal=Goal(
                    name=f"repair_{blueprint.family}_operator",
                    target="shared.capability_primitives",
                    metric="public and hidden transfer counterexamples pass",
                    rationale=(
                        f"The capability benchmark fixture is missing the reusable "
                        f"{blueprint.function_name} primitive for {blueprint.family}."
                    ),
                ),
                target_path=target,
                test_path=repo_root / "tests" / f"test_capability_{blueprint.family}_operator_v1.py",
                transform=lambda source, plan=blueprint: add_capability_operator(source, plan),
                test_source=build_capability_operator_test(blueprint),
                focused_tests=(f"tests/test_capability_{blueprint.family}_operator_v1.py",),
                capability_family=blueprint.family,
                operator_specs=operator_specs_for(blueprint.family, blueprint.function_name),
                generator_improvement=generator_feedback(
                    "operator synthesis",
                    "adds a reusable solver primitive and counterexample tests for future candidate generation",
                    f"{blueprint.function_name} can be reused on later {blueprint.family} fixtures",
                ),
            )
        )
    return candidates
