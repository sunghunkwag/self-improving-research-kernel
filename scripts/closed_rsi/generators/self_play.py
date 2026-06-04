"""Self-play task proposer for open-ended candidate pressure."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from scripts.closed_rsi.generators.behavior_archive import BehaviorArchive
from scripts.closed_rsi.records import CandidatePatch


@dataclass(frozen=True)
class SelfPlayTask:
    """A task proposed to expose candidate weaknesses."""

    task_id: str
    generation: int
    proposer: str
    weakness_focus: str
    prompt: str
    input_signature: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SelfPlayResult:
    """Candidate result against self-play tasks."""

    candidate_name: str
    wins: int
    losses: int
    task_scores: Dict[str, float]
    weakness_exposure: float

    def to_dict(self) -> dict:
        return asdict(self)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _residue_focus_terms(state: object) -> Tuple[str, ...]:
    if not isinstance(state, Mapping):
        return ()
    terms = []
    for bucket in ("rejected", "quarantine_exploration"):
        for record in state.get(bucket, []):
            if not isinstance(record, Mapping):
                continue
            residue = record.get("failure_residue", {})
            if not isinstance(residue, Mapping):
                continue
            for key in ("failed_gate", "missing_operator", "overfit_signal", "next_hypothesis"):
                value = str(residue.get(key, "") or "").strip()
                if value:
                    terms.append(value)
    return tuple(dict.fromkeys(terms))


def _candidate_focus_terms(candidates: Sequence[CandidatePatch]) -> Tuple[str, ...]:
    terms = []
    for candidate in candidates:
        for value in (
            candidate.capability_family,
            candidate.goal.target,
            candidate.goal.metric,
            candidate.generator_improvement.get("surface", ""),
        ):
            value = str(value or "").strip()
            if value:
                terms.append(value)
    return tuple(dict.fromkeys(terms))


def propose_self_play_tasks(
    candidates: Sequence[CandidatePatch],
    *,
    state: object,
    archive: BehaviorArchive,
    generation: int,
    seed: str,
    max_tasks: int = 3,
) -> Tuple[SelfPlayTask, ...]:
    """Propose deterministic weakness-finding tasks from archive and residue."""

    focus_terms = [*_residue_focus_terms(state), *_candidate_focus_terms(candidates)]
    if not focus_terms:
        focus_terms = ["archive novelty gap"]
    tasks = []
    for index, focus in enumerate(focus_terms[: max(1, max_tasks)]):
        digest = _digest(f"{seed}:{generation}:{index}:{focus}:{len(archive.signatures)}")
        tasks.append(
            SelfPlayTask(
                task_id=f"self_play_{generation}_{index}_{digest[:8]}",
                generation=generation,
                proposer="weakness_task_proposer",
                weakness_focus=focus,
                prompt=(
                    "Expose candidate weakness against archive residue "
                    f"`{focus}` without consulting evaluator outputs."
                ),
                input_signature=digest[:16],
            )
        )
    return tuple(tasks)


def _candidate_text(candidate: CandidatePatch) -> str:
    return " ".join(
        (
            candidate.name,
            candidate.goal.name,
            candidate.goal.target,
            candidate.goal.metric,
            candidate.goal.rationale,
            candidate.capability_family,
            str(candidate.generator_improvement.get("surface", "")),
            str(candidate.generator_improvement.get("mechanism", "")),
            str(candidate.generator_improvement.get("evidence", "")),
        )
    ).lower()


def evaluate_candidate_self_play(
    candidate: CandidatePatch,
    tasks: Sequence[SelfPlayTask],
    *,
    state: object,
    seed: str,
) -> SelfPlayResult:
    """Score a candidate against self-play tasks without ground-truth access."""

    candidate_text = _candidate_text(candidate)
    rejected_names = set()
    if isinstance(state, Mapping):
        rejected_names = {
            str(record.get("name", ""))
            for record in state.get("rejected", [])
            if isinstance(record, Mapping)
        }
    complexity = min((len(candidate.test_source) + len(candidate.operator_specs) * 120) / 4000.0, 1.0)
    task_scores: Dict[str, float] = {}
    wins = 0
    for task in tasks:
        focus_tokens = [token for token in task.weakness_focus.lower().replace("_", " ").split() if len(token) >= 4]
        token_overlap = sum(1 for token in focus_tokens if token in candidate_text)
        overlap_score = min(token_overlap / max(len(focus_tokens), 1), 1.0)
        hash_score = int(_digest(f"{seed}:{task.task_id}:{candidate.name}")[:8], 16) / 0xFFFFFFFF
        rejection_penalty = 0.2 if candidate.name in rejected_names else 0.0
        score = round((0.45 * hash_score) + (0.45 * overlap_score) + 0.15 - (0.2 * complexity) - rejection_penalty, 3)
        task_scores[task.task_id] = score
        if score >= 0.5:
            wins += 1
    losses = max(len(tasks) - wins, 0)
    weakness_exposure = round(len(task_scores) / max(len(tasks), 1), 3) if tasks else 0.0
    return SelfPlayResult(
        candidate_name=candidate.name,
        wins=wins,
        losses=losses,
        task_scores=task_scores,
        weakness_exposure=weakness_exposure,
    )


def evaluate_population_self_play(
    candidates: Iterable[CandidatePatch],
    tasks: Sequence[SelfPlayTask],
    *,
    state: object,
    seed: str,
) -> Dict[str, SelfPlayResult]:
    """Return self-play results keyed by candidate name."""

    return {
        candidate.name: evaluate_candidate_self_play(candidate, tasks, state=state, seed=seed)
        for candidate in candidates
    }
