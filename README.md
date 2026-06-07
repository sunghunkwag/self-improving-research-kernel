# Self-Improving Research Kernel

[![RSI Omega Proof](https://github.com/sunghunkwag/self-improving-research-kernel/actions/workflows/rsi-omega-proof.yml/badge.svg?branch=main)](https://github.com/sunghunkwag/self-improving-research-kernel/actions/workflows/rsi-omega-proof.yml) [![RSI Bootstrap Proof](https://github.com/sunghunkwag/self-improving-research-kernel/actions/workflows/rsi-bootstrap-proof.yml/badge.svg?branch=main)](https://github.com/sunghunkwag/self-improving-research-kernel/actions/workflows/rsi-bootstrap-proof.yml)
[![Full Pytest](https://github.com/sunghunkwag/self-improving-research-kernel/actions/workflows/full-pytest.yml/badge.svg?branch=main)](https://github.com/sunghunkwag/self-improving-research-kernel/actions/workflows/full-pytest.yml)

> A program that rewrites its own code to get better at solving problems — but is only allowed to keep a change if every test still passes.

## What is this?

Most software is improved by humans. This is an experiment in software that improves **itself**. Each run, the kernel:

1. **Reads its own source code** and picks a small, measurable goal.
2. **Writes a patch** to meet that goal, plus a new test to prove it works.
3. **Applies the patch** and runs the *entire* test suite.
4. **Keeps the change only if every test passes.** Otherwise it rolls back and logs why.

Because the change is only kept when all tests pass, every accepted improvement is safe, reversible, and reviewable. The kernel saves its state, so the next run continues from the last accepted version — building on its own progress over time.

This is called **recursive self-improvement (RSI)**: the system doesn't just solve tasks, it improves the part of itself that solves tasks.

```
   +-----------------------------------------------+
   |  1. Inspect own code  ->  2. Invent a goal    |
   |                                               |
   |  4. Keep only if ALL  <-  3. Write patch +    |
   |     tests pass            matching test       |
   +-----------------------------------------------+
        keep   ->  commit & resume next run
        fail   ->  roll back & log the reason
```
## Why it's built this way

The hard part of self-improving systems isn't making changes — it's trusting them. This project's main idea is **honesty about what's actually verified**. A change counts as "real" only if it survives the full test gate; everything speculative is clearly labeled as unverified.

To keep the system from cheating, an **immutable boundary** stops the kernel from editing its own judge. The evaluators, gates, anti-cheat checks, the loop orchestrator (`scripts/closed_rsi/loop.py`), and the entrypoint are all protected by `immutable_guard`: any patch that tries to write inside that boundary is rejected. The loop can improve *what it does*, but not the code that decides whether its changes are safe.

## What is — and isn't — validated

This table is the most important thing to read.

| Layer | What it does | Touches source? | Status |
|-------|--------------|-----------------|--------|
| **Closed loop** | Generates, applies, and gate-validates patches | Yes — only if full tests pass | **Verified & promoted** |
| **Capability benchmarks** | Removes a primitive, forces the loop to re-synthesize it | Yes — same full-test gate | **Verified** |
| **External grounding** | Reads public GitHub issue *metadata* into task seeds | No code execution | Metadata only |
| **Open-ended exploration** | Proposes speculative self-modifications | **Never applied** | Proposal archive only |

The **closed loop** is the *only* path that can modify the working tree, and only behind the full-test gate. The **open-ended** layer is an archive of unvalidated proposals — proposal text alone is never promotion evidence.

## Quick Start

```bash
# 1. Fast local smoke check
python scripts/memory_safe_validate.py --quick

# 2. Run the closed self-improvement loop
python scripts/closed_recursive_self_improvement_loop.py --apply --broad-gate

# 3. The promotion gate — the only thing that can accept a candidate
python -m pytest -q
```
The smoke check is lightweight and safe to run anywhere. Full `pytest` runs and recursive experiments are heavier and are intended to run in GitHub Actions.

State is written under `.omega_rsi_runs/`: `closed_rsi_state.json` (accepted/rejected history), `closed_rsi_summary.json` (latest run), and an optional `STOP_CLOSED_RSI` kill-switch file.

---

*The sections below are reference detail for contributors.*

## How it works

The loop runs one cycle per generation: inspect the source, invent a goal, synthesize a candidate patch and matching test, apply it, then validate. **Only the full `python -m pytest -q` suite can promote a candidate** — focused tests run earlier only as diagnostics and can never accept a patch. Rejected candidates are rolled back and record structured failure residue.

The **generator** is a bounded planner, not an unbounded code-writing agent. For capability fixtures it uses a public-oracle primitive search: it builds candidate functions by searching over reusable AST primitives and executes **only the public assertion** as its oracle — no answer bodies are stored in task definitions, and private/hidden cases are never read during synthesis. Accepted `generator_improvement` records feed forward into the next generation's search budget and curriculum difficulty, so generation N can change what generation N+1 produces.

## Capability benchmarks

Executable capability fixtures cover algorithm synthesis, symbolic reasoning, grid transformation, bug repair, and planning/state-transition tasks. Each fixture removes one reusable primitive from `shared/capability_primitives.py` and adds public plus seed-derived hidden transfer counterexamples. The loop must synthesize the primitive via a bounded search over reusable AST primitives that executes only the public assertion as the synthesis oracle. Private cases, seeded evaluator cases, held-out reference hashes, anti-cheat checks, and the full repository pytest suite judge the candidate after synthesis.

## Autonomous generator surface

The generator combines: public-oracle primitive search for capability fixtures without storing answer bodies; a feedback-driven policy that lets accepted `generator_improvement` records change the next candidate stream; self-generated curriculum growth from failure residue and accepted feedback; degenerate self-authored task rejection (no private counterexample or no-op solvable); closed-loop promotion of open-ended archive entries behind the normal gates; schema-driven candidate synthesis from `LocalPythonFileRecord` fields; `CapabilityDelta` scoring across solved tasks, hidden transfer, regression protection, operator reuse, and compute cost; failure-residue extraction for rejected candidates; history-aware candidate ranking; and full-suite validation, rollback, and kill-switch controls.

## External grounding

The repository grounds RSI experiments in external maintenance signals without executing untrusted code:

```bash
python scripts/external_world_grounding.py --repository psf/requests --limit-per-repo 3
python scripts/external_code_sandbox_fixtures.py --repository psf/requests --repository pandas-dev/pandas
```
It reads public GitHub issue metadata into bounded task seeds (`reports/external_grounding/latest/`) and can transfer bounded source/failure excerpts from allowlisted repos into text-only sandbox fixtures (`reports/external_code_fixtures/latest/`). Safety controls: metadata only, no external cloning, no external code execution, bounded issue count/body length, and source-URL provenance for every task.

## Open-ended exploration

```bash
python scripts/open_ended_exploration.py --max-candidates 96 --meta-depth 3
```
This layer expands candidate search across broad domains and records speculative self-modification proposals whose validation status is explicitly unknown. These proposals are **never applied** to the source tree and do **not** close the RSI loop. Every materialized proposal carries an executable validation plan; proposal text alone is not enough for promotion.

## GitHub Actions

**Closed RSI Loop** is started manually via `workflow_dispatch`: Python 3.11, 90-minute wall-clock budget, 130-minute job timeout, full pytest promotion gate, rollback on failure, and commit/push back to `main` only when the loop leaves validated changes — so the next run resumes from the latest accepted commit. **RSI Research Experiments** runs the review matrix in disposable repo copies with baseline/ablation metrics, rollback-correctness checks, and a bounded-execution safety report. **Unseen / External / External Code Transfer Experiments** run powered held-out and issue-derived transfer cells, executing only local disposable fixtures.

## Evidence

Powered cells use at least 20 paired repeats per repository/task/variant, the same seed for proposed and baseline variants, and report mean, variance, and bootstrap confidence intervals. A win counts only when the paired margin clears the baseline with a non-degenerate interval. Current GitHub Actions evidence (vs `evolutionary_repair_loop`, full-test success rate 1.0):

- **Unseen transfer:** 20 paired repeats, proposed accepted-rate mean 0.188571, margin CI [0.172381, 0.20631].
- **External transfer:** 20 paired repeats, proposed accepted-rate mean 0.180476, margin CI [0.162381, 0.199048].
- **External code transfer:** 20 paired repeats, proposed accepted-rate mean 0.4725, margin CI [0.2975, 0.6425], improvement-depth margin CI [1.2, 2.4].

Artifacts live under `reports/rsi_experiments/latest/` (`metrics.csv`, `aggregate_metrics.csv`, `baseline_comparison.md`, `evidence_scorecard.json`); see `reports/rsi_experiments/evidence_index.md` for the full index.

## Architecture

Expensive validation runs in GitHub Actions. Use `python scripts/memory_safe_validate.py --quick` for a fast local smoke check; the `--full` mode is intended for CI.

OMEGA-THDSE base: `shared/` (arenas, deterministic RNG, semantic encoding, local corpus indexing, bridges), `thdse/` (topological hyperdimensional symbolic engine), `tests/` (root regression and integration gates), and `scripts/closed_recursive_self_improvement_loop.py` (bounded closed-loop patch generation, validation, rollback, state persistence).
