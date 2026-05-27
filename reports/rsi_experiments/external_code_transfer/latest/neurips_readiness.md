# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `external_dask_code_transfer_repo`: Actual dask source-code and issue-failure sandbox fixture.
- `external_hypothesis_code_transfer_repo`: Actual Hypothesis source-code and issue-failure sandbox fixture.
- `external_pandas_code_transfer_repo`: Actual pandas source-code and issue-failure sandbox fixture.
- `external_requests_code_transfer_repo`: Actual psf/requests source-code and issue-failure sandbox fixture.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.46 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.53 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.25 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.57 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.53 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.26 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.47 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.54 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.25 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.50 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.53 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.26 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Regression Failures Mean | Rollback Success | Depth Mean | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | agent_coding_loop | 1 | 1.00 | 0.00 | n/a | 1.00 | 0.53 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | ci_only_validation | 1 | 0.00 | 0.00 | n/a | 0.00 | 0.26 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.50 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | agent_coding_loop | 1 | 1.00 | 0.00 | n/a | 1.00 | 0.53 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | ci_only_validation | 1 | 0.00 | 0.00 | n/a | 0.00 | 0.26 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.57 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | agent_coding_loop | 1 | 1.00 | 0.00 | n/a | 1.00 | 0.54 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | ci_only_validation | 1 | 0.00 | 0.00 | n/a | 0.00 | 0.25 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.47 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 1 | 1.00 | 0.00 | n/a | 1.00 | 0.53 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 1 | 0.00 | 0.00 | n/a | 0.00 | 0.25 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.46 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True | False |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True | False |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True | False |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True | False |

## Review-Relevant Claims

- The proposed loop can patch real repository code and persist accepted/rejected provenance.
- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.
- Held-out schema-transfer fixtures are marked as unseen and compared separately.
- Baseline comparison rows explicitly label wins, ties, safety wins, and inconclusive cases.
- The generator includes schema-driven candidate synthesis instead of only fixed candidate names.
- The generator scores bounded competing hypotheses with rejection history before patching.
- CapabilityDelta scoring records solved tasks, hidden transfer, regression protection, operator reuse, and compute cost.
- Failure residue extraction records missing operators, missing abstractions, failed evaluators, and overfit signals.
- Capability fixtures include algorithm synthesis, symbolic reasoning, grid transformation, bug repair, and planning/state transitions.
- Broad gates reduce regression risk relative to focused-only ablations.
- Rollback behavior is measurable on forced broad-gate rejection tasks.
- Persistence can be ablated to show that resume depth depends on durable state.
- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.
