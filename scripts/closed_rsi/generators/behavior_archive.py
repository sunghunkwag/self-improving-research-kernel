"""Behavior archive used by open-ended proxy objectives."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence, Tuple

from scripts.closed_rsi.records import CandidatePatch


@dataclass(frozen=True)
class BehaviorSignature:
    """A deterministic input-output signature for one candidate on one task."""

    candidate_name: str
    generation: int
    task_id: str
    input_signature: str
    output_signature: str

    def to_dict(self) -> dict:
        return asdict(self)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _task_value(task: object, key: str, default: str = "") -> str:
    if isinstance(task, Mapping):
        return str(task.get(key, default) or default)
    return str(getattr(task, key, default) or default)


def _candidate_behavior_text(candidate: CandidatePatch) -> str:
    return "\n".join(
        (
            candidate.name,
            candidate.goal.name,
            candidate.goal.target,
            candidate.goal.metric,
            candidate.goal.rationale,
            candidate.capability_family,
            " ".join(candidate.schema_fields),
            " ".join(str(spec.get("name", "")) for spec in candidate.operator_specs),
            str(candidate.generator_improvement.get("surface", "")),
            str(candidate.generator_improvement.get("mechanism", "")),
            str(candidate.generator_improvement.get("evidence", "")),
        )
    )


def behavior_signature_for_candidate(
    candidate: CandidatePatch,
    task: object,
    *,
    generation: int | None = None,
) -> BehaviorSignature:
    """Return a candidate signature without reading evaluator or gate outputs."""

    task_id = _task_value(task, "task_id", "archive-default-task")
    input_signature = _task_value(task, "input_signature", _digest(task_id)[:16])
    behavior_text = _candidate_behavior_text(candidate)
    return BehaviorSignature(
        candidate_name=candidate.name,
        generation=int(generation if generation is not None else candidate.generation),
        task_id=task_id,
        input_signature=input_signature,
        output_signature=_digest(f"{input_signature}\n{behavior_text}")[:24],
    )


def _hex_distance(left: str, right: str) -> float:
    width = max(len(left), len(right), 1)
    padded_left = left.ljust(width, "0")
    padded_right = right.ljust(width, "0")
    return sum(1 for a, b in zip(padded_left, padded_right) if a != b) / float(width)


class BehaviorArchive:
    """Persistent behavior archive for novelty scoring."""

    def __init__(self, signatures: Iterable[BehaviorSignature] = ()):
        self.signatures: Tuple[BehaviorSignature, ...] = tuple(signatures)

    @classmethod
    def from_state(cls, state: object) -> "BehaviorArchive":
        signatures = []
        if isinstance(state, Mapping):
            for item in state.get("behavior_archive", []):
                if not isinstance(item, Mapping):
                    continue
                try:
                    signatures.append(
                        BehaviorSignature(
                            candidate_name=str(item.get("candidate_name", "")),
                            generation=int(item.get("generation", 0) or 0),
                            task_id=str(item.get("task_id", "")),
                            input_signature=str(item.get("input_signature", "")),
                            output_signature=str(item.get("output_signature", "")),
                        )
                    )
                except Exception:
                    continue
            if not signatures:
                for bucket in ("accepted", "rejected", "quarantine_exploration"):
                    for record in state.get(bucket, []):
                        if not isinstance(record, Mapping):
                            continue
                        candidate_name = str(record.get("name", "") or "")
                        if not candidate_name:
                            continue
                        goal = record.get("goal", {}) if isinstance(record.get("goal"), Mapping) else {}
                        pseudo_text = "\n".join(
                            (
                                candidate_name,
                                str(record.get("target_path", "")),
                                str(goal.get("name", "")),
                                str(goal.get("target", "")),
                                str(record.get("capability_delta", {})),
                                str(record.get("failure_residue", {})),
                            )
                        )
                        signatures.append(
                            BehaviorSignature(
                                candidate_name=candidate_name,
                                generation=int(record.get("generation", 0) or 0),
                                task_id="state-record",
                                input_signature=_digest("state-record")[:16],
                                output_signature=_digest(pseudo_text)[:24],
                            )
                        )
        return cls(signatures)

    def novelty_distance(self, candidate: CandidatePatch, tasks: Sequence[object] = ()) -> float:
        """Return distance from archived behavior signatures in the range [0, 1]."""

        active_tasks = tuple(tasks) or ({"task_id": "archive-default-task", "input_signature": _digest("default")[:16]},)
        proposed = tuple(behavior_signature_for_candidate(candidate, task) for task in active_tasks)
        if not self.signatures:
            return 1.0
        distances = []
        archived_outputs = tuple(signature.output_signature for signature in self.signatures)
        for signature in proposed:
            distances.append(min(_hex_distance(signature.output_signature, archived) for archived in archived_outputs))
        return round(sum(distances) / max(len(distances), 1), 3)

    def append_candidate(
        self,
        candidate: CandidatePatch,
        tasks: Sequence[object],
        *,
        generation: int | None = None,
    ) -> Tuple[BehaviorSignature, ...]:
        return tuple(
            behavior_signature_for_candidate(candidate, task, generation=generation)
            for task in (tuple(tasks) or ({"task_id": "archive-default-task"},))
        )


def append_behavior_signatures_to_state(
    state: dict,
    candidate: CandidatePatch,
    tasks: Sequence[object],
    *,
    generation: int | None = None,
) -> Tuple[dict, ...]:
    """Append candidate behavior signatures to persisted loop state."""

    archive = BehaviorArchive.from_state(state)
    rows = tuple(signature.to_dict() for signature in archive.append_candidate(candidate, tasks, generation=generation))
    state.setdefault("behavior_archive", []).extend(rows)
    return rows
