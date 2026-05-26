# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Experiment Matrix

| Task | Variant | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| local_corpus_queries_clean | verified_closed_loop | 2 | 0 | 1.00 | 0 | n/a | 37.08 |
| local_corpus_queries_clean | agent_coding_loop | 1 | 0 | 1.00 | 0 | n/a | 18.55 |
| local_corpus_queries_clean | evolutionary_repair_loop | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| local_corpus_queries_clean | focused_only_loop | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| local_corpus_queries_clean | no_thdse_core_gate | 2 | 0 | 1.00 | 0 | n/a | 25.39 |
| local_corpus_queries_clean | no_persistence | 2 | 0 | 1.00 | 0 | n/a | 36.52 |
| local_corpus_queries_clean | no_rollback | 2 | 0 | 1.00 | 0 | n/a | 36.42 |
| local_corpus_queries_clean | ci_only_validation | 0 | 0 | 0.00 | 0 | n/a | 12.88 |
| policy_registry_self_patch | verified_closed_loop | 1 | 0 | 1.00 | 0 | n/a | 18.81 |
| policy_registry_self_patch | agent_coding_loop | 1 | 0 | 1.00 | 0 | n/a | 18.59 |
| policy_registry_self_patch | evolutionary_repair_loop | 1 | 0 | 1.00 | 0 | n/a | 0.30 |
| policy_registry_self_patch | focused_only_loop | 1 | 0 | 1.00 | 0 | n/a | 0.30 |
| policy_registry_self_patch | no_thdse_core_gate | 1 | 0 | 1.00 | 0 | n/a | 13.13 |
| policy_registry_self_patch | no_persistence | 1 | 0 | 1.00 | 0 | n/a | 18.60 |
| policy_registry_self_patch | no_rollback | 1 | 0 | 1.00 | 0 | n/a | 18.64 |
| policy_registry_self_patch | ci_only_validation | 0 | 0 | 0.00 | 0 | n/a | 12.83 |
| forced_broad_regression | verified_closed_loop | 0 | 2 | 0.00 | 2 | True | 36.55 |
| forced_broad_regression | agent_coding_loop | 0 | 1 | 0.00 | 1 | True | 18.88 |
| forced_broad_regression | evolutionary_repair_loop | 2 | 0 | 1.00 | 0 | n/a | 0.54 |
| forced_broad_regression | focused_only_loop | 2 | 0 | 1.00 | 0 | n/a | 0.54 |
| forced_broad_regression | no_thdse_core_gate | 0 | 2 | 0.00 | 2 | True | 26.08 |
| forced_broad_regression | no_persistence | 0 | 2 | 0.00 | 2 | True | 37.36 |
| forced_broad_regression | no_rollback | 0 | 2 | 0.00 | 2 | False | 37.12 |
| forced_broad_regression | ci_only_validation | 0 | 0 | 0.00 | 0 | n/a | 13.08 |

## Review-Relevant Claims

- The proposed loop can patch real repository code and persist accepted/rejected provenance.
- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.
- Broad gates reduce regression risk relative to focused-only ablations.
- Rollback behavior is measurable on forced broad-gate rejection tasks.
- Persistence can be ablated to show that resume depth depends on durable state.
- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.
