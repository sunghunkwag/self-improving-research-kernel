# Recursion Notes

The closed loop is still bounded and gate-driven. It does not get to keep a
patch because a proposal sounds plausible. A candidate must compile, pass its
focused diagnostics, pass evaluator gates, preserve the collected test set, and
pass the full `python -m pytest -q` promotion gate in GitHub Actions before it
can be treated as accepted evidence.

Genuine recursion now occurs in the generator state. Accepted candidate records
with `generator_improvement` are read by the next generation's live
`GeneratorPolicy`. That policy changes the later candidate stream by raising
the compositional operator-synthesis budget, enabling closed-loop promotion of
open-exploration archive entries, and raising self-authored curriculum
difficulty after hidden-transfer wins. Generation summaries record the active
policy, feedback events, candidate names, and a candidate-stream signature so a
run can show that generation N changed generation N+1.

Capability primitives are no longer copied from stored answer bodies in
`CAPABILITY_OPERATOR_BLUEPRINTS`. Those records now define benchmark tasks and
assertions only. Candidate source is assembled by a bounded compositional
synthesizer from reusable program atoms and strategies, then validated on public
cases, seeded hidden cases, held-out reference hashes, anti-cheat checks, and
the full promotion gate.

The open-ended exploration layer remains proposal-only. The closed loop can now
read the archive and convert one eligible proposal into a normal code candidate,
but proposal text alone is never promotion evidence. The bridge patch still
passes through the same rollback, anti-cheat, immutable-boundary, focused, and
full-pytest gates.

The curriculum can now grow from failure residue plus mastered hidden-transfer
signals. Self-authored residue tasks carry a difficulty metric and generate a
larger hidden transfer suite as difficulty rises. A self-authored task gate
rejects degenerate tasks with no hidden transfer or cases solvable by returning
the first input unchanged.

The mutable generator surface is limited to `scripts/closed_rsi/generators/`,
`scripts/rsi_policy_registry.py`, and the loop search-policy surface. The
evaluator, anti-cheat, gate, reference, metadata, and report-writing surfaces
remain immutable to generated candidates because editing the judge would make
the evidence meaningless.

This is still not unbounded RSI. The search space is deterministic and
budgeted, every candidate is reviewable source code, rollback remains active,
and the strongest validation claims must come from GitHub Actions rather than
local full-suite or local multi-generation runs.
