# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `unseen_control_transfer_repo`: Held-out control-oriented fixture with controller-mode schema absent from the seen benchmark repositories.
- `unseen_schema_transfer_repo`: Held-out compact fixture with an unseen tuple-valued record field that tests schema transfer beyond the original task distribution.
- `unseen_science_transfer_repo`: Held-out science-oriented fixture with evidence-source schema absent from the seen benchmark repositories.
- `unseen_security_transfer_repo`: Held-out security-oriented fixture with a threat-label schema absent from the seen benchmark repositories.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.45 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.51 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 1.42 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.53 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.23 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.43 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.52 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 1.43 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.52 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.43 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.52 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 1.43 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.52 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.23 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | verified_closed_loop | 0 | 3 | 0 | 1.00 | 0 | n/a | 1.41 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.51 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | verified_closed_loop | 1 | 3 | 0 | 1.00 | 0 | n/a | 1.42 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.52 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Regression Failures Mean | Rollback Success | Depth Mean | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.52 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.22 |
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 1.42 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.52 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.23 |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 1.44 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.52 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.22 |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 1.43 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.52 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.22 |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 3.00 | 1.43 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer | External Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|
| unseen_control_transfer_repo | unseen | unseen_controller_modes_query | unseen_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | True | False |
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | unseen_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | True | False |
| unseen_science_transfer_repo | unseen | unseen_evidence_sources_query | unseen_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | True | False |
| unseen_security_transfer_repo | unseen | unseen_threat_labels_query | unseen_transfer_success | 1.00 | agent_coding_loop | 1.00 | 2.00 | False | True | False |

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
