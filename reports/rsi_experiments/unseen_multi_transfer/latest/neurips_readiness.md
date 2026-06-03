# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `composite_unseen_schema_transfer_repo`: Composite held-out schema fixture with four tuple-valued record fields absent from the original benchmark repositories.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Full Test | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 0 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.44 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 0 | 0 | 3 | 0.00 | n/a | 0 | True | 2.08 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 1 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.41 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 1 | 0 | 3 | 0.00 | n/a | 0 | True | 2.15 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 2 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.52 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 2 | 0 | 3 | 0.00 | n/a | 0 | True | 2.10 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 3 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.44 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 3 | 0 | 3 | 0.00 | n/a | 0 | True | 2.08 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 4 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.49 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 4 | 0 | 3 | 0.00 | n/a | 0 | True | 2.18 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 5 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.56 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 5 | 0 | 3 | 0.00 | n/a | 0 | True | 2.14 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 6 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.60 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 6 | 0 | 3 | 0.00 | n/a | 0 | True | 2.09 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 7 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.42 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 7 | 0 | 3 | 0.00 | n/a | 0 | True | 2.07 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 8 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.42 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 8 | 0 | 3 | 0.00 | n/a | 0 | True | 2.06 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 9 | 1 | 3 | 0.25 | 0 | 0 | n/a | 3.42 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 9 | 0 | 3 | 0.00 | n/a | 0 | True | 2.09 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Accepted Rate CI | Full Test Success | Regression Failures Mean | Rollback Success | Depth Mean | Depth CI | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | evolutionary_repair_loop | 10 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 2.11 |
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | verified_closed_loop | 10 | 0.25 | [0.25, 0.25] | 1.00 | 0.00 | n/a | 1.00 | [1.00, 1.00] | 3.47 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | unseen_transfer_success | 0.25 | evolutionary_repair_loop | 0.00 | [0.25, 0.25] | [1.00, 1.00] | False | True | False | False | False |

## Counted Success Provenance

| Repository | Task | Variant | Repeat | Seed | Full Test Command | Exit Code | Provenance Hash | Held-Out Input Set |
|---|---|---|---:|---|---|---:|---|---|
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 0 | ce7540cddca5 | `python -m pytest -q` | 0 | `913905a810ac0caa6a71a70ec0cc58db2beb9650749ffa8ce9f8816cf06b7b49` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 1 | 1718cdfc790e | `python -m pytest -q` | 0 | `0db250f87ded819905ebaf1349a07e3fa699a6f01fb8ad9a39b6313c6ab77c6a` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 2 | 76ba1b3c1a66 | `python -m pytest -q` | 0 | `8ac9d148d48e4a49ef321009f00ec597cde01b462159ba06a163956f060ec2f2` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 3 | 56c90017f1a0 | `python -m pytest -q` | 0 | `19a9978c38d413919c129349ab049741d52b122d2321a695788b3457d26c6493` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 4 | e1278904d8e4 | `python -m pytest -q` | 0 | `36c96117358c5b84f3d5f8094e8f14c6b115580645062959e86021fc461c7e26` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 5 | 582798ab56cf | `python -m pytest -q` | 0 | `48f1f7093a4c5115e827fe6636c4d9576912145a6987a1221dc613c8075f8e44` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 6 | e043bdca4a71 | `python -m pytest -q` | 0 | `396e72fef6fca022cdbf88fc331914ab2c31c5a60cdb1e469eb3db70662cc341` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 7 | 4ea1e549549d | `python -m pytest -q` | 0 | `5eb5e9b88728112a23a0b2156156ed51afd6e40afff5b8a0fb3274aabd2d348f` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 8 | 797a1e625395 | `python -m pytest -q` | 0 | `7fc6c25772cd6cbf2a787c851031b02a7e55e9e41ea0fc96b8e7c29009e13057` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |
| composite_unseen_schema_transfer_repo | composite_unseen_schema_transfer | verified_closed_loop | 9 | db45ce36da90 | `python -m pytest -q` | 0 | `832f16fc95ba16f3b7958c5a5b2ecbbd0e3f9e14fcc30765beabce3555704331` | `{"fields": [{"field_name": "static_roles", "sample_value": "moderator"}, {"field_name": "threat_labels", "sample_value": "sandbox_escape"}, {"field_name": "evidence_sources", "sample_value": "ablation_table"}, {"field_name": "controller_modes", "sample_value": "stabilizing_feedback"}], "fixture_kind": "composite_schema_transfer", "repository": "composite_unseen_schema_transfer_repo", "safety_controls": ["held_out_schema_fields", "single_general_patch_required", "seeded_hidden_schema_evaluator", ` |

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
