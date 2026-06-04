"""Common text-rewrite and provenance helpers for candidate generators."""

from __future__ import annotations

from typing import List, Optional, Tuple


def replace_once(text: str, old: str, new: str, candidate_name: str) -> str:
    if old not in text:
        raise RuntimeError(f"{candidate_name}: patch anchor not found")
    return text.replace(old, new, 1)


def insert_before(text: str, marker: str, insertion: str, candidate_name: str) -> str:
    if marker not in text:
        raise RuntimeError(f"{candidate_name}: insertion marker not found")
    return text.replace(marker, insertion + marker, 1)

def names_from_state(state: Optional[dict], bucket: str) -> Tuple[str, ...]:
    """Return candidate names from persisted state records."""

    if not isinstance(state, dict):
        return ()
    names: List[str] = []
    for record in state.get(bucket, []):
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            names.append(str(record["name"]))
    return tuple(names)
