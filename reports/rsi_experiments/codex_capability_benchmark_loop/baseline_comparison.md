# Baseline Comparison Scorecard

This report separates accepted-rate wins, improvement-depth wins, safety wins, and held-out transfer successes. Rows marked as inconclusive should not be presented as evidence that the proposed loop beats all baselines.

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | capability_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | False | True |
| capability_bug_repair_repo | capability_unseen | capability_bug_repair | capability_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | False | True |
| capability_grid_transformation_repo | capability_unseen | capability_grid_transformation | capability_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | False | True |
| capability_planning_state_transition_repo | capability_unseen | capability_planning_state_transition | capability_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | False | True |
| capability_symbolic_reasoning_repo | capability_unseen | capability_symbolic_reasoning | capability_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | False | True |
| compact_kernel_repo | seen | forced_broad_regression | tie_or_frontier_match | 0.00 |  | 0.00 | 0.00 | False | False | False | False | False |
| compact_kernel_repo | seen | local_corpus_queries_clean | depth_win_over_single_pass | 1.00 |  | 0.00 | 3.00 | False | False | False | False | False |
| compact_kernel_repo | seen | policy_registry_self_patch | depth_win_over_single_pass | 1.00 |  | 0.00 | 3.00 | False | False | False | False | False |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | external_code_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | True | False |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | external_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | True | False | False |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | external_code_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | True | False |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | external_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | True | False | False |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | external_code_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | True | False |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | external_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | True | False | False |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | external_code_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | False | True | False |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | external_transfer_success | 1.00 |  | 0.00 | 3.00 | False | False | True | False | False |
| omega_full_repo | seen | forced_broad_regression | tie_or_frontier_match | 0.00 |  | 0.00 | 0.00 | False | False | False | False | False |
| omega_full_repo | seen | local_corpus_queries_clean | depth_win_over_single_pass | 1.00 |  | 0.00 | 3.00 | False | False | False | False | False |
| omega_full_repo | seen | policy_registry_self_patch | depth_win_over_single_pass | 1.00 |  | 0.00 | 3.00 | False | False | False | False | False |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | unseen_transfer_success | 1.00 |  | 0.00 | 3.00 | False | True | False | False | False |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | unseen_transfer_success | 1.00 |  | 0.00 | 3.00 | False | True | False | False | False |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | unseen_transfer_success | 1.00 |  | 0.00 | 3.00 | False | True | False | False | False |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | unseen_transfer_success | 1.00 |  | 0.00 | 3.00 | False | True | False | False | False |

## Interpretation Rules

- `depth_win_over_single_pass`: the proposed loop reaches deeper recursive improvement than the single-pass agent baseline without lower accepted rate.
- `safety_win_over_ablation`: rollback and broad gates prevent unsafe promotion that an ablation fails to prevent.
- `unseen_transfer_success`: the loop patches a held-out schema surface not present in the original benchmark fixtures.
- `external_transfer_success`: the loop patches a fixture schema extracted from actual external repository issue metadata.
- `external_code_transfer_success`: the loop patches a fixture schema extracted from bounded external source-code snippets and issue failure excerpts.
- `capability_transfer_success`: the loop synthesizes a reusable primitive that solves executable public and hidden capability cases.
- `tie_or_frontier_match`: the proposed loop matches the best baseline on this metric but does not dominate it.
- `baseline_stronger_or_inconclusive`: the current evidence does not support a proposed-loop win.
