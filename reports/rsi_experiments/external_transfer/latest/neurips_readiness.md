# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `external_dask_issue_transfer_repo`: Actual dask issue-label fixture extracted from public GitHub issue metadata.
- `external_hypothesis_issue_transfer_repo`: Actual Hypothesis issue-title fixture extracted from public GitHub issue metadata.
- `external_pandas_issue_transfer_repo`: Actual pandas issue-title fixture extracted from public GitHub issue metadata.
- `external_requests_issue_transfer_repo`: Actual psf/requests issue-label fixture extracted from public GitHub issue metadata.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 8.69 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 2.89 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 1.33 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 8.80 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 2.98 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 1.31 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 9.00 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 2.92 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 1.41 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 8.61 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 2.91 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 1.45 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 9.38 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 3.05 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 1.31 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 8.67 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 2.98 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 1.44 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 8.69 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 2.89 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 1.55 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 8.62 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 3.00 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 1.36 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Regression Failures Mean | Rollback Success | Depth Mean | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 2.95 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 1.45 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 8.66 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 2.91 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 1.43 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 8.80 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 3.02 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 1.38 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 9.02 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 2.94 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 1.32 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 8.74 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer | External Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | external_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | True |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | external_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | True |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | external_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | True |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | external_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | True |

## Review-Relevant Claims

- The proposed loop can patch real repository code and persist accepted/rejected provenance.
- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.
- Held-out schema-transfer fixtures are marked as unseen and compared separately.
- Baseline comparison rows explicitly label wins, ties, safety wins, and inconclusive cases.
- The generator includes schema-driven candidate synthesis instead of only fixed candidate names.
- The generator scores bounded competing hypotheses with rejection history before patching.
- Broad gates reduce regression risk relative to focused-only ablations.
- Rollback behavior is measurable on forced broad-gate rejection tasks.
- Persistence can be ablated to show that resume depth depends on durable state.
- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.
