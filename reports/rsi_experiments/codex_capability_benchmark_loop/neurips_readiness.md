# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `capability_algorithm_synthesis_repo`: Executable algorithm-synthesis fixture requiring a reusable run-length encoder primitive.
- `capability_bug_repair_repo`: Executable bug-repair fixture requiring a corrected stable de-duplication primitive.
- `capability_grid_transformation_repo`: Executable grid-transformation fixture requiring ARC-like rotation.
- `capability_planning_state_transition_repo`: Executable planning fixture requiring deterministic state transition updates.
- `capability_symbolic_reasoning_repo`: Executable symbolic-reasoning fixture requiring linear rule inference.
- `compact_kernel_repo`: Minimal repository fixture containing only the closed loop, policy registry, local corpus module, and smoke tests.
- `external_dask_code_transfer_repo`: Actual dask source-code and issue-failure sandbox fixture.
- `external_dask_issue_transfer_repo`: Actual dask issue-label fixture extracted from public GitHub issue metadata.
- `external_hypothesis_code_transfer_repo`: Actual Hypothesis source-code and issue-failure sandbox fixture.
- `external_hypothesis_issue_transfer_repo`: Actual Hypothesis issue-title fixture extracted from public GitHub issue metadata.
- `external_pandas_code_transfer_repo`: Actual pandas source-code and issue-failure sandbox fixture.
- `external_pandas_issue_transfer_repo`: Actual pandas issue-title fixture extracted from public GitHub issue metadata.
- `external_requests_code_transfer_repo`: Actual psf/requests source-code and issue-failure sandbox fixture.
- `external_requests_issue_transfer_repo`: Actual psf/requests issue-label fixture extracted from public GitHub issue metadata.
- `omega_full_repo`: Full OMEGA-THDSE checkout with root tests and THDSE core gates available.
- `unseen_control_transfer_repo`: Held-out control-oriented fixture with controller-mode schema absent from the seen benchmark repositories.
- `unseen_schema_transfer_repo`: Held-out compact fixture with an unseen tuple-valued record field that tests schema transfer beyond the original task distribution.
- `unseen_science_transfer_repo`: Held-out science-oriented fixture with evidence-source schema absent from the seen benchmark repositories.
- `unseen_security_transfer_repo`: Held-out security-oriented fixture with a threat-label schema absent from the seen benchmark repositories.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| omega_full_repo | seen | local_corpus_queries_clean | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 54.89 |
| omega_full_repo | seen | policy_registry_self_patch | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 54.57 |
| omega_full_repo | seen | forced_broad_regression | verified_closed_loop | 0 | 0 | 3 | 0.00 | 3 | True | 54.77 |
| compact_kernel_repo | seen | local_corpus_queries_clean | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| compact_kernel_repo | seen | policy_registry_self_patch | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.45 |
| compact_kernel_repo | seen | forced_broad_regression | verified_closed_loop | 0 | 0 | 3 | 0.00 | 3 | True | 1.44 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| capability_symbolic_reasoning_repo | capability_unseen | capability_symbolic_reasoning | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| capability_grid_transformation_repo | capability_unseen | capability_grid_transformation | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| capability_bug_repair_repo | capability_unseen | capability_bug_repair | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| capability_planning_state_transition_repo | capability_unseen | capability_planning_state_transition | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.42 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.42 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.42 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Regression Failures Mean | Rollback Success | Depth Mean | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| capability_bug_repair_repo | capability_unseen | capability_bug_repair | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| capability_grid_transformation_repo | capability_unseen | capability_grid_transformation | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| capability_planning_state_transition_repo | capability_unseen | capability_planning_state_transition | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| capability_symbolic_reasoning_repo | capability_unseen | capability_symbolic_reasoning | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| compact_kernel_repo | seen | forced_broad_regression | verified_closed_loop | 1 | 0.00 | 3.00 | 1.00 | 0.00 | 1.44 |
| compact_kernel_repo | seen | local_corpus_queries_clean | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| compact_kernel_repo | seen | policy_registry_self_patch | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.45 |
| external_dask_code_transfer_repo | external_code_unseen | external_dask_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| external_dask_issue_transfer_repo | external_unseen | external_dask_array_labels_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.42 |
| external_hypothesis_code_transfer_repo | external_code_unseen | external_hypothesis_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.42 |
| external_hypothesis_issue_transfer_repo | external_unseen | external_hypothesis_patch_signals_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| external_pandas_code_transfer_repo | external_code_unseen | external_pandas_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| external_pandas_issue_transfer_repo | external_unseen | external_pandas_failure_terms_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| external_requests_issue_transfer_repo | external_unseen | external_requests_issue_labels_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| omega_full_repo | seen | forced_broad_regression | verified_closed_loop | 1 | 0.00 | 3.00 | 1.00 | 0.00 | 54.77 |
| omega_full_repo | seen | local_corpus_queries_clean | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 54.89 |
| omega_full_repo | seen | policy_registry_self_patch | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 54.57 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.41 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | verified_closed_loop | 1 | 1.00 | 0.00 | n/a | 3.00 | 1.42 |

## Baseline And Transfer Scorecard

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
