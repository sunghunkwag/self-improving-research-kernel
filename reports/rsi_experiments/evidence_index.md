# RSI Evidence Index

This index points to the current reproducible evidence artifacts for the
bounded recursive self-improvement kernel. The artifacts do not claim unbounded
ASI behavior.

## Repeated Experiment Matrix

- Path: `reports/rsi_experiments/latest/`
- Trial count: 96
- Repositories: `omega_full_repo`, `compact_kernel_repo`
- Repeats: 2 per repository/task/variant cell
- Coverage: proposed loop, CI-only baseline, single-pass agent loop baseline,
  evolutionary repair loop baseline, broad-gate ablation, THDSE/Z3-gate
  ablation, persistence ablation, rollback ablation
- Primary files:
  - `metrics.csv`
  - `aggregate_metrics.csv`
  - `neurips_readiness.md`
  - `failure_analysis.md`
  - `safety_model.md`

## Unseen Transfer Evidence

- Path: `reports/rsi_experiments/unseen_transfer/latest/`
- Trial count: 9
- Repository split: `unseen`
- Held-out fixture: `unseen_schema_transfer_repo`
- Transfer origin: `compact_kernel_repo`
- Task: `unseen_static_roles_query`
- Repeats: 3 per variant
- Variants: proposed loop, single-pass agent loop baseline, CI-only baseline

Observed aggregate result:

- Proposed loop accepted rate mean: 1.00
- Proposed loop improvement depth mean: 3.00
- Single-pass agent accepted rate mean: 1.00
- Single-pass agent improvement depth mean: 1.00
- CI-only accepted rate mean: 0.00
- Scorecard outcome: `unseen_transfer_success`

## Workflow Recovery Evidence

- Path: `reports/rsi_experiments/recovery/latest/`
- Purpose: fast Actions health check after stale queue recovery
- Run type: narrowed `workflow_dispatch`
- Repository: `unseen_schema_transfer_repo`
- Task: `unseen_static_roles_query`
- Variant: `verified_closed_loop`
- Repeats: 1

Recovery runs should use `output_subdir=recovery/latest` so they do not
overwrite the broader repeated experiment matrix under
`reports/rsi_experiments/latest/`.

## Baseline Comparison Evidence

- Path: `reports/rsi_experiments/unseen_transfer/latest/baseline_comparison.md`
- Machine-readable scorecard:
  `reports/rsi_experiments/unseen_transfer/latest/evidence_scorecard.json`

The current scorecard distinguishes:

- accepted-rate wins
- recursive-depth wins
- safety wins over ablations
- held-out transfer successes
- ties or inconclusive cells

## Failure Analysis Evidence

- Path: `reports/rsi_experiments/latest/failure_analysis.md`
- The forced broad-gate regression task records rejected candidates, regression
  gate failures, rollback outcomes, and CI-only failures.
- The unseen transfer smoke matrix had no rejected candidates or command
  failures.

## Current Research Interpretation

The strongest current evidence is not that the proposed loop dominates every
baseline. The strongest evidence is narrower:

- It repeatedly patches and validates code in disposable repositories.
- It reaches deeper accepted improvement chains than a single-pass agent loop on
  the held-out schema-transfer fixture.
- It preserves rollback behavior on forced broad-gate rejection tasks.
- It records enough per-trial provenance for baseline, ablation, transfer, and
  failure-analysis tables.

The main remaining research gap is broader external validity: more unseen
repositories, more task families, and stronger baselines are still required
before making a NeurIPS main-track strength claim.
