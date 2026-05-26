# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Experiment Matrix

| Task | Variant | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| local_corpus_queries_clean | verified_closed_loop | 2 | 0 | 1.00 | 0 | n/a | 36.20 |
| local_corpus_queries_clean | focused_only_loop | 2 | 0 | 1.00 | 0 | n/a | 0.54 |
| local_corpus_queries_clean | no_thdse_core_gate | 2 | 0 | 1.00 | 0 | n/a | 25.16 |
| local_corpus_queries_clean | no_persistence | 2 | 0 | 1.00 | 0 | n/a | 35.92 |
| local_corpus_queries_clean | no_rollback | 2 | 0 | 1.00 | 0 | n/a | 36.09 |
| local_corpus_queries_clean | ci_only_validation | 0 | 0 | 0.00 | 0 | n/a | 12.70 |
| policy_registry_self_patch | verified_closed_loop | 1 | 0 | 1.00 | 0 | n/a | 18.70 |
| policy_registry_self_patch | focused_only_loop | 1 | 0 | 1.00 | 0 | n/a | 0.32 |
| policy_registry_self_patch | no_thdse_core_gate | 1 | 0 | 1.00 | 0 | n/a | 13.12 |
| policy_registry_self_patch | no_persistence | 1 | 0 | 1.00 | 0 | n/a | 18.58 |
| policy_registry_self_patch | no_rollback | 1 | 0 | 1.00 | 0 | n/a | 18.73 |
| policy_registry_self_patch | ci_only_validation | 0 | 0 | 0.00 | 0 | n/a | 12.98 |
| forced_broad_regression | verified_closed_loop | 0 | 2 | 0.00 | 2 | True | 36.94 |
| forced_broad_regression | focused_only_loop | 2 | 0 | 1.00 | 0 | n/a | 0.55 |
| forced_broad_regression | no_thdse_core_gate | 0 | 2 | 0.00 | 2 | True | 25.52 |
| forced_broad_regression | no_persistence | 0 | 2 | 0.00 | 2 | True | 36.13 |
| forced_broad_regression | no_rollback | 0 | 2 | 0.00 | 2 | False | 36.40 |
| forced_broad_regression | ci_only_validation | 0 | 0 | 0.00 | 0 | n/a | 12.64 |

## Review-Relevant Claims

- The proposed loop can patch real repository code and persist accepted/rejected provenance.
- Broad gates reduce regression risk relative to focused-only ablations.
- Rollback behavior is measurable on forced broad-gate rejection tasks.
- Persistence can be ablated to show that resume depth depends on durable state.
- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.
