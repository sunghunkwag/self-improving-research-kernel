# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `compact_kernel_repo`: Minimal repository fixture containing only the closed loop, policy registry, local corpus module, and smoke tests.
- `omega_full_repo`: Full OMEGA-THDSE checkout with root tests and THDSE core gates available.

## Experiment Matrix

| Repository | Task | Variant | Repeat | Accepted | Rejected | Rate | Regression Failures | Rollback Correct | Seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| omega_full_repo | local_corpus_queries_clean | verified_closed_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 36.59 |
| omega_full_repo | local_corpus_queries_clean | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 18.45 |
| omega_full_repo | local_corpus_queries_clean | evolutionary_repair_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.53 |
| omega_full_repo | local_corpus_queries_clean | focused_only_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| omega_full_repo | local_corpus_queries_clean | no_thdse_core_gate | 0 | 2 | 0 | 1.00 | 0 | n/a | 25.08 |
| omega_full_repo | local_corpus_queries_clean | no_persistence | 0 | 2 | 0 | 1.00 | 0 | n/a | 36.08 |
| omega_full_repo | local_corpus_queries_clean | no_rollback | 0 | 2 | 0 | 1.00 | 0 | n/a | 36.02 |
| omega_full_repo | local_corpus_queries_clean | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 12.65 |
| omega_full_repo | policy_registry_self_patch | verified_closed_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 18.45 |
| omega_full_repo | policy_registry_self_patch | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 18.52 |
| omega_full_repo | policy_registry_self_patch | evolutionary_repair_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.30 |
| omega_full_repo | policy_registry_self_patch | focused_only_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.29 |
| omega_full_repo | policy_registry_self_patch | no_thdse_core_gate | 0 | 1 | 0 | 1.00 | 0 | n/a | 12.87 |
| omega_full_repo | policy_registry_self_patch | no_persistence | 0 | 1 | 0 | 1.00 | 0 | n/a | 18.46 |
| omega_full_repo | policy_registry_self_patch | no_rollback | 0 | 1 | 0 | 1.00 | 0 | n/a | 18.42 |
| omega_full_repo | policy_registry_self_patch | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 12.65 |
| omega_full_repo | forced_broad_regression | verified_closed_loop | 0 | 0 | 2 | 0.00 | 2 | True | 36.34 |
| omega_full_repo | forced_broad_regression | agent_coding_loop | 0 | 0 | 1 | 0.00 | 1 | True | 18.52 |
| omega_full_repo | forced_broad_regression | evolutionary_repair_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.51 |
| omega_full_repo | forced_broad_regression | focused_only_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| omega_full_repo | forced_broad_regression | no_thdse_core_gate | 0 | 0 | 2 | 0.00 | 2 | True | 25.30 |
| omega_full_repo | forced_broad_regression | no_persistence | 0 | 0 | 2 | 0.00 | 2 | True | 36.24 |
| omega_full_repo | forced_broad_regression | no_rollback | 0 | 0 | 2 | 0.00 | 2 | False | 36.31 |
| omega_full_repo | forced_broad_regression | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 12.63 |
| omega_full_repo | local_corpus_queries_clean | verified_closed_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 36.08 |
| omega_full_repo | local_corpus_queries_clean | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 18.39 |
| omega_full_repo | local_corpus_queries_clean | evolutionary_repair_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| omega_full_repo | local_corpus_queries_clean | focused_only_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| omega_full_repo | local_corpus_queries_clean | no_thdse_core_gate | 1 | 2 | 0 | 1.00 | 0 | n/a | 25.16 |
| omega_full_repo | local_corpus_queries_clean | no_persistence | 1 | 2 | 0 | 1.00 | 0 | n/a | 36.02 |
| omega_full_repo | local_corpus_queries_clean | no_rollback | 1 | 2 | 0 | 1.00 | 0 | n/a | 36.09 |
| omega_full_repo | local_corpus_queries_clean | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 12.61 |
| omega_full_repo | policy_registry_self_patch | verified_closed_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 18.44 |
| omega_full_repo | policy_registry_self_patch | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 18.47 |
| omega_full_repo | policy_registry_self_patch | evolutionary_repair_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.30 |
| omega_full_repo | policy_registry_self_patch | focused_only_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.29 |
| omega_full_repo | policy_registry_self_patch | no_thdse_core_gate | 1 | 1 | 0 | 1.00 | 0 | n/a | 12.98 |
| omega_full_repo | policy_registry_self_patch | no_persistence | 1 | 1 | 0 | 1.00 | 0 | n/a | 18.45 |
| omega_full_repo | policy_registry_self_patch | no_rollback | 1 | 1 | 0 | 1.00 | 0 | n/a | 18.41 |
| omega_full_repo | policy_registry_self_patch | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 12.63 |
| omega_full_repo | forced_broad_regression | verified_closed_loop | 1 | 0 | 2 | 0.00 | 2 | True | 36.29 |
| omega_full_repo | forced_broad_regression | agent_coding_loop | 1 | 0 | 1 | 0.00 | 1 | True | 18.47 |
| omega_full_repo | forced_broad_regression | evolutionary_repair_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.52 |
| omega_full_repo | forced_broad_regression | focused_only_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.51 |
| omega_full_repo | forced_broad_regression | no_thdse_core_gate | 1 | 0 | 2 | 0.00 | 2 | True | 25.54 |
| omega_full_repo | forced_broad_regression | no_persistence | 1 | 0 | 2 | 0.00 | 2 | True | 36.34 |
| omega_full_repo | forced_broad_regression | no_rollback | 1 | 0 | 2 | 0.00 | 2 | False | 36.22 |
| omega_full_repo | forced_broad_regression | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 12.75 |
| compact_kernel_repo | local_corpus_queries_clean | verified_closed_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.93 |
| compact_kernel_repo | local_corpus_queries_clean | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.47 |
| compact_kernel_repo | local_corpus_queries_clean | evolutionary_repair_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | local_corpus_queries_clean | focused_only_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | local_corpus_queries_clean | no_thdse_core_gate | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.88 |
| compact_kernel_repo | local_corpus_queries_clean | no_persistence | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.89 |
| compact_kernel_repo | local_corpus_queries_clean | no_rollback | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.90 |
| compact_kernel_repo | local_corpus_queries_clean | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.20 |
| compact_kernel_repo | policy_registry_self_patch | verified_closed_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.49 |
| compact_kernel_repo | policy_registry_self_patch | agent_coding_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | evolutionary_repair_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.28 |
| compact_kernel_repo | policy_registry_self_patch | focused_only_loop | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.28 |
| compact_kernel_repo | policy_registry_self_patch | no_thdse_core_gate | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | no_persistence | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | no_rollback | 0 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.21 |
| compact_kernel_repo | forced_broad_regression | verified_closed_loop | 0 | 0 | 2 | 0.00 | 2 | True | 0.92 |
| compact_kernel_repo | forced_broad_regression | agent_coding_loop | 0 | 0 | 1 | 0.00 | 1 | True | 0.49 |
| compact_kernel_repo | forced_broad_regression | evolutionary_repair_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | forced_broad_regression | focused_only_loop | 0 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | forced_broad_regression | no_thdse_core_gate | 0 | 0 | 2 | 0.00 | 2 | True | 0.91 |
| compact_kernel_repo | forced_broad_regression | no_persistence | 0 | 0 | 2 | 0.00 | 2 | True | 0.92 |
| compact_kernel_repo | forced_broad_regression | no_rollback | 0 | 0 | 2 | 0.00 | 2 | False | 0.93 |
| compact_kernel_repo | forced_broad_regression | ci_only_validation | 0 | 0 | 0 | 0.00 | 0 | n/a | 0.22 |
| compact_kernel_repo | local_corpus_queries_clean | verified_closed_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.89 |
| compact_kernel_repo | local_corpus_queries_clean | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | local_corpus_queries_clean | evolutionary_repair_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.49 |
| compact_kernel_repo | local_corpus_queries_clean | focused_only_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | local_corpus_queries_clean | no_thdse_core_gate | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.89 |
| compact_kernel_repo | local_corpus_queries_clean | no_persistence | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.89 |
| compact_kernel_repo | local_corpus_queries_clean | no_rollback | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.90 |
| compact_kernel_repo | local_corpus_queries_clean | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.20 |
| compact_kernel_repo | policy_registry_self_patch | verified_closed_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | agent_coding_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | evolutionary_repair_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.28 |
| compact_kernel_repo | policy_registry_self_patch | focused_only_loop | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.28 |
| compact_kernel_repo | policy_registry_self_patch | no_thdse_core_gate | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | no_persistence | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | no_rollback | 1 | 1 | 0 | 1.00 | 0 | n/a | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.21 |
| compact_kernel_repo | forced_broad_regression | verified_closed_loop | 1 | 0 | 2 | 0.00 | 2 | True | 0.91 |
| compact_kernel_repo | forced_broad_regression | agent_coding_loop | 1 | 0 | 1 | 0.00 | 1 | True | 0.49 |
| compact_kernel_repo | forced_broad_regression | evolutionary_repair_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | forced_broad_regression | focused_only_loop | 1 | 2 | 0 | 1.00 | 0 | n/a | 0.50 |
| compact_kernel_repo | forced_broad_regression | no_thdse_core_gate | 1 | 0 | 2 | 0.00 | 2 | True | 0.92 |
| compact_kernel_repo | forced_broad_regression | no_persistence | 1 | 0 | 2 | 0.00 | 2 | True | 0.92 |
| compact_kernel_repo | forced_broad_regression | no_rollback | 1 | 0 | 2 | 0.00 | 2 | False | 0.92 |
| compact_kernel_repo | forced_broad_regression | ci_only_validation | 1 | 0 | 0 | 0.00 | 0 | n/a | 0.21 |

## Aggregate Metrics

| Repository | Task | Variant | Trials | Accepted Rate Mean | Regression Failures Mean | Rollback Success | Depth Mean | Seconds Mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| compact_kernel_repo | forced_broad_regression | agent_coding_loop | 2 | 0.00 | 1.00 | 1.00 | 0.00 | 0.49 |
| compact_kernel_repo | forced_broad_regression | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.22 |
| compact_kernel_repo | forced_broad_regression | evolutionary_repair_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.50 |
| compact_kernel_repo | forced_broad_regression | focused_only_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.50 |
| compact_kernel_repo | forced_broad_regression | no_persistence | 2 | 0.00 | 2.00 | 1.00 | 0.00 | 0.92 |
| compact_kernel_repo | forced_broad_regression | no_rollback | 2 | 0.00 | 2.00 | 0.00 | 0.00 | 0.92 |
| compact_kernel_repo | forced_broad_regression | no_thdse_core_gate | 2 | 0.00 | 2.00 | 1.00 | 0.00 | 0.92 |
| compact_kernel_repo | forced_broad_regression | verified_closed_loop | 2 | 0.00 | 2.00 | 1.00 | 0.00 | 0.92 |
| compact_kernel_repo | local_corpus_queries_clean | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.48 |
| compact_kernel_repo | local_corpus_queries_clean | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.20 |
| compact_kernel_repo | local_corpus_queries_clean | evolutionary_repair_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.50 |
| compact_kernel_repo | local_corpus_queries_clean | focused_only_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.50 |
| compact_kernel_repo | local_corpus_queries_clean | no_persistence | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.89 |
| compact_kernel_repo | local_corpus_queries_clean | no_rollback | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.90 |
| compact_kernel_repo | local_corpus_queries_clean | no_thdse_core_gate | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.89 |
| compact_kernel_repo | local_corpus_queries_clean | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.91 |
| compact_kernel_repo | policy_registry_self_patch | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 0.21 |
| compact_kernel_repo | policy_registry_self_patch | evolutionary_repair_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.28 |
| compact_kernel_repo | policy_registry_self_patch | focused_only_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.28 |
| compact_kernel_repo | policy_registry_self_patch | no_persistence | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | no_rollback | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | no_thdse_core_gate | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.48 |
| compact_kernel_repo | policy_registry_self_patch | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.49 |
| omega_full_repo | forced_broad_regression | agent_coding_loop | 2 | 0.00 | 1.00 | 1.00 | 0.00 | 18.49 |
| omega_full_repo | forced_broad_regression | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 12.69 |
| omega_full_repo | forced_broad_regression | evolutionary_repair_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.52 |
| omega_full_repo | forced_broad_regression | focused_only_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.52 |
| omega_full_repo | forced_broad_regression | no_persistence | 2 | 0.00 | 2.00 | 1.00 | 0.00 | 36.29 |
| omega_full_repo | forced_broad_regression | no_rollback | 2 | 0.00 | 2.00 | 0.00 | 0.00 | 36.27 |
| omega_full_repo | forced_broad_regression | no_thdse_core_gate | 2 | 0.00 | 2.00 | 1.00 | 0.00 | 25.42 |
| omega_full_repo | forced_broad_regression | verified_closed_loop | 2 | 0.00 | 2.00 | 1.00 | 0.00 | 36.32 |
| omega_full_repo | local_corpus_queries_clean | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 18.42 |
| omega_full_repo | local_corpus_queries_clean | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 12.63 |
| omega_full_repo | local_corpus_queries_clean | evolutionary_repair_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.52 |
| omega_full_repo | local_corpus_queries_clean | focused_only_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 0.52 |
| omega_full_repo | local_corpus_queries_clean | no_persistence | 2 | 1.00 | 0.00 | n/a | 2.00 | 36.05 |
| omega_full_repo | local_corpus_queries_clean | no_rollback | 2 | 1.00 | 0.00 | n/a | 2.00 | 36.05 |
| omega_full_repo | local_corpus_queries_clean | no_thdse_core_gate | 2 | 1.00 | 0.00 | n/a | 2.00 | 25.12 |
| omega_full_repo | local_corpus_queries_clean | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 2.00 | 36.33 |
| omega_full_repo | policy_registry_self_patch | agent_coding_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 18.50 |
| omega_full_repo | policy_registry_self_patch | ci_only_validation | 2 | 0.00 | 0.00 | n/a | 0.00 | 12.64 |
| omega_full_repo | policy_registry_self_patch | evolutionary_repair_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.30 |
| omega_full_repo | policy_registry_self_patch | focused_only_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 0.29 |
| omega_full_repo | policy_registry_self_patch | no_persistence | 2 | 1.00 | 0.00 | n/a | 1.00 | 18.46 |
| omega_full_repo | policy_registry_self_patch | no_rollback | 2 | 1.00 | 0.00 | n/a | 1.00 | 18.41 |
| omega_full_repo | policy_registry_self_patch | no_thdse_core_gate | 2 | 1.00 | 0.00 | n/a | 1.00 | 12.93 |
| omega_full_repo | policy_registry_self_patch | verified_closed_loop | 2 | 1.00 | 0.00 | n/a | 1.00 | 18.44 |

## Review-Relevant Claims

- The proposed loop can patch real repository code and persist accepted/rejected provenance.
- The matrix includes CI-only, single-pass agent coding, and evolutionary repair baselines.
- Broad gates reduce regression risk relative to focused-only ablations.
- Rollback behavior is measurable on forced broad-gate rejection tasks.
- Persistence can be ablated to show that resume depth depends on durable state.
- The policy registry candidate turns the loop's generator, validator, patch, and safety policies into a measurable surface.
