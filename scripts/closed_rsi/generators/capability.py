"""Capability primitive candidate generators."""

from __future__ import annotations

from pathlib import Path
from typing import List, Mapping, Sequence, Tuple

from shared.capability_benchmarks import (
    SelfProposedCapabilityDimension,
    propose_capability_dimensions_from_residue,
    self_proposed_dynamic_cases,
)
from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.generators.operator_synthesis import (
    CAPABILITY_OPERATOR_BLUEPRINTS,
    CapabilityOperatorBlueprint,
    SynthesizedOperator,
    synthesize_capability_operator_variants,
)
from scripts.closed_rsi.records import CandidatePatch, Goal, generator_feedback


def add_capability_operator(
    text: str,
    blueprint: CapabilityOperatorBlueprint,
    synthesis: SynthesizedOperator,
) -> str:
    """Append a synthesized reusable capability primitive."""

    if f"def {blueprint.function_name}(" in text:
        return text
    return text.rstrip() + "\n\n\n" + synthesis.source.rstrip() + "\n"


def build_capability_operator_test(blueprint: CapabilityOperatorBlueprint) -> str:
    """Build public and private counterexample tests for a synthesized operator."""

    return f'''from shared.capability_primitives import {blueprint.function_name}


def test_{blueprint.function_name}_public_counterexample():
    {blueprint.public_assertion}


def test_{blueprint.function_name}_private_counterexample():
    {blueprint.hidden_assertion}
'''


def failure_residue_history_from_state(state: object) -> Tuple[Mapping[str, object], ...]:
    """Extract accumulated FailureResidue dictionaries from loop state."""

    if not isinstance(state, dict):
        return ()
    residues: List[Mapping[str, object]] = []
    for bucket in ("rejected", "quarantine_exploration"):
        for record in state.get(bucket, []):
            if not isinstance(record, dict):
                continue
            residue = record.get("failure_residue")
            if isinstance(residue, dict) and residue:
                residues.append(residue)
    return tuple(residues)


def _self_proposed_operator_source(operator_name: str) -> str:
    return f'''def {operator_name}(payload):
    """Summarize seed-varied FailureResidue pressure payloads."""

    signals = tuple(str(signal) for signal in payload.get("signals", ()) if str(signal))
    counts = {{}}
    for signal in signals:
        counts[signal] = counts.get(signal, 0) + 1
    dominant = ""
    if counts:
        dominant = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return {{
        "family": str(payload.get("family", "")),
        "dominant_signal": dominant,
        "pressure": int(payload.get("residue_count", 0) or 0) + int(payload.get("seed_pressure", 0) or 0),
        "difficulty": int(payload.get("difficulty", 1) or 1),
        "evidence_width": len(set(signals)),
    }}
'''


def add_self_proposed_operator(text: str, dimension: SelfProposedCapabilityDimension) -> str:
    """Append a generic primitive for a self-proposed residue capability family."""

    if f"def {dimension.operator}(" in text:
        return text
    return text.rstrip() + "\n\n\n" + _self_proposed_operator_source(dimension.operator).rstrip() + "\n"


def build_self_proposed_operator_test(
    dimension: SelfProposedCapabilityDimension,
    *,
    seed: str,
    residues: Sequence[Mapping[str, object]],
    mastered_capability_count: int = 0,
) -> str:
    cases = [
        case
        for case in self_proposed_dynamic_cases(
            seed,
            residues,
            mastered_capability_count=mastered_capability_count,
        )
        if case.family == dimension.family
    ]
    assertions = "\n\n".join(
        f'''def test_{dimension.operator}_private_case_{index}():
    payload = {case.inputs[0]!r}

    assert {dimension.operator}(payload) == {case.expected!r}
'''
        for index, case in enumerate(cases, start=1)
    )
    return f'''from shared.capability_primitives import {dimension.operator}


{assertions}
'''


def self_proposed_capability_candidates(
    repo_root: Path,
    generation: int,
    *,
    state: object = None,
    seed: str = "closed_rsi_capability_dynamic_v1",
    mastered_capability_count: int = 0,
) -> List[CandidatePatch]:
    """Plan candidates for capability families invented from FailureResidue history."""

    target = repo_root / "shared" / "capability_primitives.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    residues = failure_residue_history_from_state(state)
    if not residues:
        return []
    candidates: List[CandidatePatch] = []
    for dimension in propose_capability_dimensions_from_residue(
        residues,
        seed=seed,
        mastered_capability_count=mastered_capability_count,
    ):
        if f"def {dimension.operator}(" in text:
            continue
        test_path = repo_root / "tests" / f"test_capability_{dimension.family}_operator_v1.py"
        candidates.append(
            CandidatePatch(
                name=f"capability_operator_{dimension.family}_v1",
                generation=generation,
                goal=Goal(
                    name=f"repair_{dimension.family}_operator",
                    target="shared.capability_primitives",
                    metric="self-proposed residue capability hidden transfer cases pass",
                    rationale=dimension.rationale,
                ),
                target_path=target,
                test_path=test_path,
                transform=lambda source, plan=dimension: add_self_proposed_operator(source, plan),
                test_source=build_self_proposed_operator_test(
                    dimension,
                    seed=seed,
                    residues=residues,
                    mastered_capability_count=mastered_capability_count,
                ),
                focused_tests=(str(test_path.relative_to(repo_root)).replace("\\", "/"),),
                capability_family=dimension.family,
                operator_specs=operator_specs_for(dimension.family, dimension.operator),
                generator_improvement=generator_feedback(
                    "self-proposed capability dimension",
                    "derives a new family and private cases from accumulated FailureResidue state",
                    (
                        f"{dimension.family}:{dimension.operator} from residue signature "
                        f"{dimension.source_signature} using seed {seed}; "
                        f"difficulty={dimension.difficulty}"
                    ),
                ),
            )
        )
    return candidates


def _candidate_name_for_synthesis(
    blueprint: CapabilityOperatorBlueprint,
    synthesis: SynthesizedOperator,
    index: int,
) -> str:
    if index == 0:
        return blueprint.candidate_name
    return f"{blueprint.candidate_name}_{synthesis.strategy}"


def capability_operator_candidates(
    repo_root: Path,
    generation: int,
    *,
    synthesis_budget: int = 1,
) -> List[CandidatePatch]:
    """Plan synthesized repair candidates for executable capability fixtures."""

    target = repo_root / "shared" / "capability_primitives.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    candidates: List[CandidatePatch] = []
    for blueprint in CAPABILITY_OPERATOR_BLUEPRINTS:
        if f"def {blueprint.function_name}(" in text:
            continue
        for index, synthesis in enumerate(
            synthesize_capability_operator_variants(
                blueprint,
                max_variants=max(1, synthesis_budget),
            )
        ):
            candidate_name = _candidate_name_for_synthesis(blueprint, synthesis, index)
            candidates.append(
                CandidatePatch(
                    name=candidate_name,
                    generation=generation,
                    goal=Goal(
                        name=f"repair_{blueprint.family}_operator",
                        target="shared.capability_primitives",
                        metric="public, hidden, and freshly seeded transfer counterexamples pass",
                        rationale=(
                            f"The capability benchmark fixture is missing the reusable "
                            f"{blueprint.function_name} primitive for {blueprint.family}; "
                            f"the implementation is synthesized with {synthesis.strategy} "
                            "by public-oracle primitive search rather than copied from a stored body."
                        ),
                    ),
                    target_path=target,
                    test_path=repo_root / "tests" / f"test_capability_{blueprint.family}_operator_v1.py",
                    transform=lambda source, plan=blueprint, result=synthesis: add_capability_operator(
                        source,
                        plan,
                        result,
                    ),
                    test_source=build_capability_operator_test(blueprint),
                    focused_tests=(f"tests/test_capability_{blueprint.family}_operator_v1.py",),
                    capability_family=blueprint.family,
                    operator_specs=operator_specs_for(blueprint.family, blueprint.function_name),
                    generator_improvement=generator_feedback(
                        "operator synthesis",
                        (
                            "searches reusable solver primitives from public-oracle program atoms "
                            "and feeds the synthesis strategy into later search policy"
                        ),
                        (
                            f"{blueprint.function_name}:{synthesis.strategy}; "
                            f"atoms={','.join(synthesis.atoms)}; "
                            f"trace={' > '.join(synthesis.trace)}; "
                            f"source_sha256={synthesis.source_sha256[:16]}"
                        ),
                    ),
                )
            )
    return candidates
