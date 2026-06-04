# Self-Improving Research Kernel

> An experimental, **bounded** research kernel for recursive self-improvement.
> It proposes code patches to its own codebase, but only keeps the ones that
> pass compilation, evaluator gates, and the **full test suite**. Everything
> else is rolled back. **No unbounded ASI claims** — every change is
> deterministic, reviewable, and gate-verified.

In one paragraph: the kernel inspects its own source tree, invents a measurable
improvement goal, generates a real patch plus a matching regression test,
applies it, and then validates it. A candidate is promoted **only** if the full
`pytest` suite passes; otherwise it is reverted and its failure is logged.
State is persisted, so each run resumes from the last accepted commit.

## What is and isn't validated

| Layer | What it does | Applied to source? | Status |
|-------|--------------|--------------------|--------|
| **Closed loop** | Generates, applies, and gate-validates patches | Yes — only if full tests pass | Verified & promoted |
| **Capability benchmarks** | Removes a primitive, forces the loop to re-synthesize it | Yes — same full-test gate | Verified |
| **External grounding** | Reads public GitHub issue *metadata* into task seeds | No code execution | Metadata only |
| **Open-ended exploration** | Proposes speculative self-modifications across domains | Never applied | Proposal archive only |

The distinction is the point: the **closed loop** is the only path that can
modify the working tree, and it can do so only behind the full-test gate. The
**open-ended** layer is a research archive of unvalidated proposals.

## Quick Start

```bash
# 1. Smallest safe local smoke check (8GB-friendly)
python scripts/memory_safe_validate.py --quick

# 2. Run the closed self-improvement loop
python scripts/closed_recursive_self_improvement_loop.py --apply --broad-gate

# 3. The promotion gate — the only thing that can accept a candidate
python -m pytest -q
```

> **Local safety:** heavy `pytest` runs and full recursive experiments should
> be dispatched to GitHub Actions, not run on a low-memory local machine.
> See [Local Safety](#local-safety).

State is written under `.omega_rsi_runs/`: `closed_rsi_state.json`
(accepted/rejected history), `closed_rsi_summary.json` (latest run), and an
optional `STOP_CLOSED_RSI` kill-switch file.

---

## Table of Contents

- [Core Loop](#core-loop)
- [Full-Test-Only Validation](#full-test-only-validation)
- [Autonomous Generator Surface](#autonomous-generator-surface)
- [Capability Benchmarks](#capability-benchmarks)
- [External Grounding](#external-grounding)
- [Open-Ended Exploration](#open-ended-exploration)
- [GitHub Actions](#github-actions)
- [Evidence](#evidence)
- [Local Safety](#local-safety)
- [OMEGA-THDSE Base](#omega-thdse-base)

---

## Core Loop

The closed loop entrypoint is:

```bash
python scripts/closed_recursive_self_improvement_loop.py --apply --broad-gate
```

The loop writes persistent state under `.omega_rsi_runs/`:

- `closed_rsi_state.json`: accepted and rejected candidate history
- `closed_rsi_summary.json`: summary for the latest run
- `STOP_CLOSED_RSI`: optional kill-switch file

## Full-Test-Only Validation

Closed-loop success requires the full repository test command:

```bash
python -m pytest -q
```

Focused tests may run earlier as diagnostics, but they cannot accept a
candidate, promote a patch, or count as experiment success. Broad validation
also runs the same full pytest command. Rejected candidates are rolled back and
record structured failure residue; only candidates with executable behavior and
a passing full suite can remain in the working tree.

## Autonomous Generator Surface

The generator is not an unbounded code-writing agent. It is a bounded planner
that combines:

- schema-driven candidate synthesis from LocalPythonFileRecord tuple fields
- bounded emergent hypothesis search over canonical and alternate query strategies
- reusable operator synthesis for executable capability fixtures
- CapabilityDelta scoring across solved tasks, hidden transfer, regression protection, operator reuse, and compute cost
- failure-residue extraction for rejected candidates, including failed reason, missing operator, missing abstraction, failed evaluator, and overfit signal
- generated regression tests for inferred query APIs
- history-aware candidate ranking from accepted/rejected provenance
- full-suite validation, rollback, and kill-switch controls

This makes candidate discovery less dependent on hand-coded candidate names
while keeping every patch deterministic, reviewable, and gate-verified.

## Capability Benchmarks

The experiment suite includes executable capability fixtures beyond
schema-query repair:

- algorithm synthesis
- symbolic reasoning
- grid transformation
- bug repair
- planning/state transition tasks

Each capability fixture removes one reusable primitive from
`shared/capability_primitives.py` and adds public plus seed-derived hidden
transfer counterexamples. The loop must synthesize the primitive, generate
diagnostic counterexample tests where useful, and pass the full repository
pytest suite before promotion.

## External Grounding

The repository can ground RSI experiments in external maintenance signals
without executing untrusted code:

```bash
python scripts/external_world_grounding.py --repository psf/requests --limit-per-repo 3
python scripts/external_world_grounding.py --domain all --limit-per-repo 1
```

The grounding layer reads public GitHub issue metadata, converts it into
bounded task seeds, and writes:

- `reports/external_grounding/latest/external_grounding_tasks.json`
- `reports/external_grounding/latest/external_grounding_report.md`

The repository can also transfer bounded source excerpts and issue failure
excerpts from allowlisted external repositories into text-only sandbox
fixtures:

```bash
python scripts/external_code_sandbox_fixtures.py \
  --repository psf/requests \
  --repository hypothesisworks/hypothesis \
  --repository pandas-dev/pandas \
  --repository dask/dask
```

The external code sandbox builder writes:

- `reports/external_code_fixtures/latest/external_code_sandbox_fixtures.json`
- `reports/external_code_fixtures/latest/external_code_sandbox_report.md`
- bounded `.txt` source and failure excerpts under `reports/external_code_fixtures/latest/snippets/` and `reports/external_code_fixtures/latest/failures/`

Safety controls:

- metadata only
- no external repository cloning
- no external code execution
- bounded issue count and body length
- source URL and retrieval provenance for every task

## Open-Ended Exploration

The repository also includes an open-loop exploration layer:

```bash
python scripts/open_ended_exploration.py --max-candidates 96 --meta-depth 3
```

This layer expands candidate search across broad domains and policy surfaces:
software maintenance, mathematical reasoning, machine learning, systems
engineering, security and sandboxing, human-computer interaction, scientific
discovery, robotics and control, biology and medicine, and economics and
strategy.

It may record speculative self-modification proposals whose validation status
is explicitly unknown. Those proposals are archived as open-loop research
objects; they are **not** applied to the source tree and do **not** close the
RSI loop. Every materialized proposal carries an executable validation plan;
proposal text alone is not enough for promotion into the closed loop.

Each materialized proposal records its target domain and policy axis, transfer
targets into other domains, provenance and target surfaces, recursive meta /
meta_meta / meta_meta_meta self-limit layers, and proposal-only safety
controls.

The workflow Open-Ended Exploration can materialize a bounded prefix of this
open candidate stream in GitHub Actions and commit the resulting report under
`reports/open_exploration/latest/`.

## GitHub Actions

The workflow **Closed RSI Loop** can be started manually from the GitHub
Actions tab through `workflow_dispatch`.

Default cloud settings:

- Python 3.11
- 90 minute wall-clock budget
- 130 minute job timeout
- full pytest promotion gate enabled
- candidate rollback on failure
- commit and push only when the loop leaves validated changes or JSON state

The workflow commits promoted patches and state files back to `main`, so the
next manual run resumes from the latest accepted commit.

The workflow **RSI Research Experiments** runs the review-oriented experiment
matrix in disposable repository copies, evaluating multiple benchmark
repository fixtures and repeated trials:

- `omega_full_repo`: the full OMEGA-THDSE checkout
- `compact_kernel_repo`: a minimal kernel fixture for faster repeated trials
- baseline and ablation metrics, accepted/rejected candidate rates
- rollback correctness checks, full-suite regression counts
- wall-clock cost proxies, improvement depth
- per-trial seeds and aggregate metrics, failure analysis
- bounded-execution safety report

Additional workflows:

- **Unseen Transfer Experiments** runs a powered composite held-out schema cell without the heavier full repository matrix. Local smoke checks can use `--allow-low-repeats`, but reported transfer wins should come from the Actions path with at least twenty repeats and full-pytest evidence.
- **External Transfer Experiments** refreshes bounded external GitHub issue metadata, builds an issue-derived composite fixture over the allowlisted repositories, and runs the external transfer cell without executing external repository code.
- **External Code Sandbox Experiments** refreshes the issue metadata, fetches bounded external source excerpts as text fixtures, pairs them with issue failure excerpts, and runs the transfer matrix against those sandbox fixtures. It still executes only the local disposable fixture repositories.

## Evidence

The experiment suite writes both raw and aggregate artifacts under
`reports/rsi_experiments/latest/`:

- `metrics.csv`: raw repository/task/variant/repeat outcomes
- `aggregate_metrics.csv`: grouped means and rollback success rates
- `benchmark_catalog.json`: repositories, tasks, variants, and repeat count
- `baseline_comparison.md`: proposed-loop vs baseline scorecard
- `evidence_scorecard.json`: machine-readable win/tie/inconclusive labels

Powered experiment cells use at least twenty paired repeats per
repository/task/variant. The same seed is recorded for proposed and baseline
variants in each repeat, and aggregate rows report mean, variance, and
bootstrap confidence intervals for accepted rate and improvement depth. A win
is counted only when the paired margin or confidence-bound comparison clears
the baseline with a non-degenerate interval; otherwise the scorecard keeps
`deterministic_not_powered`, `tie_or_frontier_match`, or
`baseline_stronger_or_inconclusive`.

Current GitHub Actions evidence:

- `unseen_transfer_success=true` on `reports/rsi_experiments/unseen_multi_transfer/latest/`: 20 paired repeats, proposed accepted-rate mean 0.188571, accepted-rate margin CI [0.172381, 0.20631] vs evolutionary_repair_loop, full-test success rate 1.0.
- `external_transfer_success=true` on `reports/rsi_experiments/external_transfer/latest/`: 20 paired repeats, proposed accepted-rate mean 0.180476, accepted-rate margin CI [0.162381, 0.199048] vs evolutionary_repair_loop, full-test success rate 1.0.
- `external_code_transfer_success=true` on `reports/rsi_experiments/external_code_transfer/latest/`: 20 paired repeats, proposed accepted-rate mean 0.4725, accepted-rate margin CI [0.2975, 0.6425], improvement-depth margin CI [1.2, 2.4], full-test success rate 1.0.

Additional evidence artifacts:

- `reports/rsi_experiments/evidence_index.md`: index of repeated, transfer, baseline, ablation, and failure-analysis evidence
- `reports/rsi_experiments/unseen_multi_transfer/latest/`: four held-out schema-transfer fixtures across generic, security, science, and control domains, plus a composite held-out fixture
- `reports/rsi_experiments/external_transfer/latest/`: fixtures extracted from actual external GitHub issue metadata for psf/requests, hypothesisworks/hypothesis, pandas-dev/pandas, and dask/dask
- `reports/external_code_fixtures/latest/`: bounded psf/requests source-code and issue-excerpt sandbox fixture
- `reports/rsi_experiments/external_code_transfer/latest/`: transfer matrix over the executable external code sandbox repair fixture

The external code sandbox fixture ports the `requests.sessions.merge_setting`
None-removal behavior into local buggy source, uses a visible failing test,
generates seed-derived hidden counterexamples after the candidate patch, and
stores the held-out reference fix only as quarantine hashes. The external source
and failure excerpts remain text-only, but the downstream benchmark is a real
local repair task rather than only a metadata summary.

The held-out transfer fixture `unseen_schema_transfer_repo` adds a
tuple-valued record field absent from the original benchmark repositories. The
proposed loop must infer and patch the missing query surface from schema
structure, then record the result as an unseen transfer cell rather than as
another seen-repo repair.

## Local Safety

This repository is set up so expensive validation can run in GitHub Actions
instead of a low-memory local machine. Local editing is safe, but long pytest
runs and recursive improvement experiments should be dispatched to the cloud
workflow.

## OMEGA-THDSE Base

The kernel keeps OMEGA-THDSE as the central architecture:

- `shared/`: common arenas, deterministic RNG, semantic encoding, local corpus indexing, and bridge utilities
- `thdse/`: topological hyperdimensional symbolic engine components
- `tests/`: root regression and integration gates
- `scripts/closed_recursive_self_improvement_loop.py`: bounded closed-loop patch generation, validation, rollback, and state persistence
