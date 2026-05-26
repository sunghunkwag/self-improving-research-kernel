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

## Multi-Domain Unseen Transfer Evidence

- Path: `reports/rsi_experiments/unseen_multi_transfer/latest/`
- Trial count: 24
- Repository split: `unseen`
- Held-out fixtures:
  - `unseen_schema_transfer_repo`
  - `unseen_security_transfer_repo`
  - `unseen_science_transfer_repo`
  - `unseen_control_transfer_repo`
- Tasks:
  - `unseen_static_roles_query`
  - `unseen_threat_labels_query`
  - `unseen_evidence_sources_query`
  - `unseen_controller_modes_query`
- Repeats: 2 per repository/task/variant cell
- Variants: proposed loop, single-pass agent loop baseline, CI-only baseline

Observed aggregate result:

- Proposed loop accepted rate mean: 1.00 on all four unseen tasks
- Proposed loop improvement depth mean: 3.00 on all four unseen tasks
- Single-pass agent accepted rate mean: 1.00 on all four unseen tasks
- Single-pass agent improvement depth mean: 1.00 on all four unseen tasks
- CI-only accepted rate mean: 0.00 on all four unseen tasks
- Scorecard outcome: `unseen_transfer_success` on all four unseen tasks
- Rejected candidates or command failures: none observed

## Actual External Issue Transfer Evidence

- Path: `reports/rsi_experiments/external_transfer/latest/`
- External grounding path:
  `reports/external_grounding/external_transfer/latest/`
- Trial count: 24
- Repository split: `external_unseen`
- Actual source repositories:
  - `psf/requests`
  - `hypothesisworks/hypothesis`
  - `pandas-dev/pandas`
  - `dask/dask`
- Extracted signals:
  - issue labels
  - issue title terms
  - source URLs
  - task kinds
- Repeats: 2 per repository/task/variant cell
- Variants: proposed loop, single-pass agent loop baseline, CI-only baseline

Observed aggregate result:

- Proposed loop accepted rate mean: 1.00 on all four external issue fixtures
- Proposed loop improvement depth mean: 3.00 on all four external issue fixtures
- Single-pass agent accepted rate mean: 1.00 on all four external issue fixtures
- Single-pass agent improvement depth mean: 1.00 on all four external issue fixtures
- CI-only accepted rate mean: 0.00 on all four external issue fixtures
- Scorecard outcome: `external_transfer_success` on all four external issue fixtures
- Rejected candidates or command failures: none observed

## Actual External Code Sandbox Fixture Evidence

- Fixture path: `reports/external_code_fixtures/latest/`
- Transfer workflow output path:
  `reports/rsi_experiments/external_code_transfer/latest/`
- Repository split: `external_code_unseen`
- Actual source repositories:
  - `psf/requests`
  - `hypothesisworks/hypothesis`
  - `pandas-dev/pandas`
  - `dask/dask`
- Extracted signals:
  - bounded external source-code excerpts stored as `.txt`
  - bounded issue failure excerpts stored as `.txt`
  - source file paths, branch refs, source URLs, and SHA-256 hashes
  - schema field values derived from source and failure signals
- Safety controls:
  - no external repository cloning
  - no external package installation
  - no external code import or execution
  - downstream trials execute only disposable local sandbox fixtures

The workflow `External Code Sandbox Experiments` refreshes issue metadata,
rebuilds these code/failure fixtures, and runs the external-code transfer
matrix against `external_*_code_transfer_repo` fixtures.

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
  four held-out schema-transfer fixtures.
- It now reaches deeper accepted improvement chains on four fixtures extracted
  from actual external GitHub issue metadata.
- It preserves rollback behavior on forced broad-gate rejection tasks.
- It records enough per-trial provenance for baseline, ablation, transfer, and
  failure-analysis tables.

The main remaining research gap is external validity beyond issue-metadata
fixtures: more real repository code surfaces, more task families, and stronger
baselines are still required before making a NeurIPS main-track strength claim.
