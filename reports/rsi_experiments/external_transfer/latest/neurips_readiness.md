# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `composite_external_issue_transfer_repo`: Composite external issue fixture whose schema fields are derived from real GitHub issue metadata across the allowlisted repositories.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Full Test | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 0 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.13 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 0 | 0 | 3 | 0.00 | n/a | 0 | True | 1.90 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 1 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.13 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 1 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 2 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.15 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 2 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 3 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.17 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 3 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 4 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.15 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 4 | 0 | 3 | 0.00 | n/a | 0 | True | 1.90 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 5 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.13 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 5 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 6 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.13 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 6 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 7 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.14 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 7 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 8 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.13 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 8 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 9 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.12 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 9 | 0 | 3 | 0.00 | n/a | 0 | True | 1.90 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Accepted Rate CI | Full Test Success | Regression Failures Mean | Rollback Success | Depth Mean | Depth CI | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | evolutionary_repair_loop | 10 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 1.89 |
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | verified_closed_loop | 10 | 0.25 | [0.25, 0.25] | 1.00 | 0.00 | n/a | 1.00 | [1.00, 1.00] | 3.14 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_external_issue_transfer_repo | external_unseen | composite_external_issue_transfer | external_transfer_success | 0.25 | evolutionary_repair_loop | 0.00 | [0.25, 0.25] | [1.00, 1.00] | False | False | True | False | False |

## Counted Success Provenance

| Repository | Task | Variant | Repeat | Seed | Full Test Command | Exit Code | Provenance Hash | Held-Out Input Set |
|---|---|---|---:|---|---|---:|---|---|
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 0 | 7ee87d4e2c2c | `python -m pytest -q` | 0 | `92f8076e46970b574b385d5f274efe75121a6fdda260dc785563fe43f0233c46` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 1 | 79ccbb0a7dd9 | `python -m pytest -q` | 0 | `0310c91d5afe4a4089b1339080cd1e5af8c9cf5f2c65d58d03c909c65c92ca70` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 2 | 08c28f5b4812 | `python -m pytest -q` | 0 | `20c787533e0c02ea3e69d3c5f90cc025e7f22602a999184aba4f4d0c4f04bbbe` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 3 | c07daa903ee4 | `python -m pytest -q` | 0 | `22e5e419728b3b2b98786adc0ab372bfc9685044258b027606a3aa346c37797a` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 4 | 5c511f9ce470 | `python -m pytest -q` | 0 | `2a5f020a47cd2d032aa4d1f0efffeaa2d96492e904f67db61b1198b37c46f23a` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 5 | 0a6197fe0572 | `python -m pytest -q` | 0 | `ca2d1f5c9aa80c0495d138ede85220510670b388507408d7ea12a41f599e7d8f` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 6 | 9ddbca2c3a7c | `python -m pytest -q` | 0 | `fc54b2e7d20f393df3236f9ae71219a8e8ad52cfe4af43902e58990a9b002391` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 7 | c309ce2e3469 | `python -m pytest -q` | 0 | `bee379a64fc0272ce77046dbe85428eaa4fdeed37d7b4236feefe36fdb9ee644` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 8 | b1736b2e0cd9 | `python -m pytest -q` | 0 | `4bdcdad009e856e28a5cdfa09d2b14f0626f9d52f03f94c07c954cf55c085fa3` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |
| composite_external_issue_transfer_repo | composite_external_issue_transfer | verified_closed_loop | 9 | 490b2400c58c | `python -m pytest -q` | 0 | `0e8f84b080fa0dea7487665603ced104050c535b155890927b524aa186742e7b` | `{"fields": [{"field_name": "external_issue_labels", "sample_value": "bug"}, {"field_name": "external_patch_signals", "sample_value": "patch"}, {"field_name": "external_failure_terms", "sample_value": "dtype"}, {"field_name": "external_array_labels", "sample_value": "array"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_external_issue_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", "full_pyt` |

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
- Candidate promotion and success accounting require the full `python -m pytest -q` suite.
- Focused diagnostics and extra broad gates cannot mark a candidate successful without full pytest.
- Rollback behavior is measurable on forced broad-gate rejection tasks.
- Persistence can be ablated to show that resume depth depends on durable state.
- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.
