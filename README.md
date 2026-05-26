# Self-Improving Research Kernel

`self-improving-research-kernel` is a bounded research system for testing a
closed recursive self-improvement loop over the OMEGA-THDSE codebase.

The repository does not claim unbounded ASI behavior. Its purpose is narrower
and testable:

1. Inspect the current source tree.
2. Invent measurable improvement goals from missing project capabilities.
3. Infer candidate blueprints from source schema and persisted rejection
   history.
4. Generate real source patches and matching regression tests.
5. Apply one candidate at a time.
6. Verify candidates with compile checks, pytest, and Z3-backed gates where
   the test suite requires Z3.
7. Keep only accepted candidates in the working tree.
8. Roll back rejected candidates.
9. Persist accepted and rejected JSON records.
10. Resume the next run from the latest committed accepted state.

## Core Loop

The closed loop entrypoint is:

```bash
python scripts/closed_recursive_self_improvement_loop.py --apply --broad-gate
```

The loop writes persistent state under `.omega_rsi_runs/`:

- `closed_rsi_state.json`: accepted and rejected candidate history
- `closed_rsi_summary.json`: summary for the latest run
- `STOP_CLOSED_RSI`: optional kill-switch file

## Autonomous Generator Surface

The generator is not an unbounded code-writing agent. It is a bounded planner
that now combines:

- schema-driven candidate synthesis from `LocalPythonFileRecord` tuple fields
- bounded emergent hypothesis search over canonical and alternate query
  strategies
- generated regression tests for inferred query APIs
- history-aware candidate ranking from accepted/rejected provenance
- existing broad gates, rollback, and kill-switch controls

This makes candidate discovery less dependent on hand-coded candidate names
while keeping every patch deterministic, reviewable, and gate-verified.

## External Grounding

The repository can now ground RSI experiments in external maintenance signals
without executing untrusted code:

```bash
python scripts/external_world_grounding.py --repository psf/requests --limit-per-repo 3
```

The grounding layer reads public GitHub issue metadata, converts it into
bounded task seeds, and writes:

- `reports/external_grounding/latest/external_grounding_tasks.json`
- `reports/external_grounding/latest/external_grounding_report.md`

Safety controls:

- metadata only
- no external repository cloning
- no external code execution
- bounded issue count and body length
- source URL and retrieval provenance for every task

## GitHub Actions

The workflow `Closed RSI Loop` can be started manually from the GitHub Actions
tab through `workflow_dispatch`.

Default cloud settings:

- Python 3.11
- 90 minute wall-clock budget
- 130 minute job timeout
- broad pytest gate enabled
- candidate rollback on failure
- commit and push only when the loop leaves validated changes or JSON state

The workflow commits promoted patches and state files back to `main`, so the
next manual run resumes from the latest accepted commit.

The workflow `RSI Research Experiments` runs the review-oriented experiment
matrix in disposable repository copies. It now evaluates multiple benchmark
repository fixtures and repeated trials:

- `omega_full_repo`: the full OMEGA-THDSE checkout
- `compact_kernel_repo`: a minimal kernel fixture for faster repeated trials

- baseline and ablation metrics
- accepted/rejected candidate rates
- rollback correctness checks
- broad-gate regression counts
- wall-clock cost proxies
- improvement depth
- per-trial seeds and aggregate metrics
- failure analysis
- bounded-execution safety report

The experiment suite writes both raw and aggregate artifacts under
`reports/rsi_experiments/latest/`:

- `metrics.csv`: raw repository/task/variant/repeat outcomes
- `aggregate_metrics.csv`: grouped means and rollback success rates
- `benchmark_catalog.json`: repositories, tasks, variants, and repeat count

## Local Safety

This repository is set up so expensive validation can run in GitHub Actions
instead of a low-memory local machine. Local editing is safe, but long pytest
runs and recursive improvement experiments should be dispatched to the cloud
workflow.

## OMEGA-THDSE Base

The kernel keeps OMEGA-THDSE as the central architecture:

- `shared/`: common arenas, deterministic RNG, semantic encoding, local corpus
  indexing, and bridge utilities
- `thdse/`: topological hyperdimensional symbolic engine components
- `tests/`: root regression and integration gates
- `scripts/closed_recursive_self_improvement_loop.py`: bounded closed-loop
  patch generation, validation, rollback, and state persistence
