# Baseline Comparison Scorecard

This report separates accepted-rate wins, improvement-depth wins, safety wins, and held-out transfer successes. Rows marked as inconclusive should not be presented as evidence that the proposed loop beats all baselines.

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer | External Transfer | External Code Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | external_code_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | False | False | True |

## Interpretation Rules

- `depth_win_over_single_pass`: the proposed loop reaches deeper recursive improvement than the single-pass agent baseline without lower accepted rate.
- `safety_win_over_ablation`: rollback and broad gates prevent unsafe promotion that an ablation fails to prevent.
- `unseen_transfer_success`: the loop patches a held-out schema surface not present in the original benchmark fixtures.
- `external_transfer_success`: the loop patches a fixture schema extracted from actual external repository issue metadata.
- `external_code_transfer_success`: the loop patches a fixture schema extracted from bounded external source-code snippets and issue failure excerpts.
- `tie_or_frontier_match`: the proposed loop matches the best baseline on this metric but does not dominate it.
- `baseline_stronger_or_inconclusive`: the current evidence does not support a proposed-loop win.
