# Self-Improving Research Kernel

`self-improving-research-kernel` is a bounded research system for testing a
closed recursive self-improvement loop over the OMEGA-THDSE codebase.

The repository does not claim unbounded ASI behavior. Its purpose is narrower
and testable:

1. Inspect the current source tree.
2. Invent measurable improvement goals from missing project capabilities.
3. Generate real source patches and matching regression tests.
4. Apply one candidate at a time.
5. Verify candidates with compile checks, pytest, and Z3-backed gates where
   the test suite requires Z3.
6. Keep only accepted candidates in the working tree.
7. Roll back rejected candidates.
8. Persist accepted and rejected JSON records.
9. Resume the next run from the latest committed accepted state.

## Core Loop

The closed loop entrypoint is:

```bash
python scripts/closed_recursive_self_improvement_loop.py --apply --broad-gate
```

The loop writes persistent state under `.omega_rsi_runs/`:

- `closed_rsi_state.json`: accepted and rejected candidate history
- `closed_rsi_summary.json`: summary for the latest run
- `STOP_CLOSED_RSI`: optional kill-switch file

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
