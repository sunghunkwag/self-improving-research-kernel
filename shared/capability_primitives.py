"""Reusable solver primitives for capability benchmark fixtures."""

from __future__ import annotations


def run_length_encode(items):
    """Return adjacent value/count pairs for a sequence."""

    encoded = []
    marker = object()
    current = marker
    count = 0
    for item in items:
        if count == 0:
            current = item
            count = 1
            continue
        if item == current:
            count += 1
            continue
        encoded.append((current, count))
        current = item
        count = 1
    if count:
        encoded.append((current, count))
    return tuple(encoded)


def infer_linear_rule(values):
    """Infer a constant-step sequence rule and its next value."""

    if len(values) < 2:
        raise ValueError("at least two values are required")
    step = values[1] - values[0]
    for left, right in zip(values, values[1:]):
        if right - left != step:
            raise ValueError("values do not form a linear rule")
    return {"start": values[0], "step": step, "next": values[-1] + step}


def rotate_grid_clockwise(grid):
    """Rotate a rectangular grid clockwise."""

    rows = tuple(tuple(row) for row in grid)
    if not rows:
        return ()
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("grid must be rectangular")
    return tuple(tuple(rows[row][column] for row in range(len(rows) - 1, -1, -1)) for column in range(width))


def dedupe_preserve_order(items):
    """Remove duplicate items while preserving first occurrence order."""

    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)


def apply_grid_action(state, action):
    """Apply a one-step cardinal movement action to a grid state."""

    deltas = {
        "north": (0, 1),
        "south": (0, -1),
        "east": (1, 0),
        "west": (-1, 0),
        "stay": (0, 0),
    }
    if action not in deltas:
        raise ValueError(f"unknown action: {action}")
    dx, dy = deltas[action]
    next_state = dict(state)
    next_state["x"] = int(next_state.get("x", 0)) + dx
    next_state["y"] = int(next_state.get("y", 0)) + dy
    return next_state


def classify_residue_feedback_policy_surface_generator_feedback_polic_runtimeerror_pressure(payload):
    """Summarize seed-varied FailureResidue pressure payloads."""

    signals = tuple(str(signal) for signal in payload.get("signals", ()) if str(signal))
    counts = {}
    for signal in signals:
        counts[signal] = counts.get(signal, 0) + 1
    dominant = ""
    if counts:
        dominant = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return {
        "family": str(payload.get("family", "")),
        "dominant_signal": dominant,
        "pressure": int(payload.get("residue_count", 0) or 0) + int(payload.get("seed_pressure", 0) or 0),
        "difficulty": int(payload.get("difficulty", 1) or 1),
        "evidence_width": len(set(signals)),
    }
