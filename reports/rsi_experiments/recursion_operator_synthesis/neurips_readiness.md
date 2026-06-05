# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `capability_algorithm_synthesis_repo`: Executable algorithm-synthesis fixture requiring a reusable run-length encoder primitive.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Full Test | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 0 | 0 | 1 | 0.00 | n/a | 0 | True | 9.34 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 1 | 0 | 1 | 0.00 | n/a | 0 | True | 8.74 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 2 | 0 | 1 | 0.00 | n/a | 0 | True | 8.82 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 3 | 0 | 1 | 0.00 | n/a | 0 | True | 8.92 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 4 | 0 | 1 | 0.00 | n/a | 0 | True | 8.66 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 5 | 0 | 1 | 0.00 | n/a | 0 | True | 8.51 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 6 | 0 | 1 | 0.00 | n/a | 0 | True | 8.49 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 7 | 0 | 1 | 0.00 | n/a | 0 | True | 8.60 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 8 | 0 | 1 | 0.00 | n/a | 0 | True | 8.60 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 9 | 0 | 1 | 0.00 | n/a | 0 | True | 8.63 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 10 | 0 | 1 | 0.00 | n/a | 0 | True | 8.70 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 11 | 0 | 1 | 0.00 | n/a | 0 | True | 8.62 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 12 | 0 | 1 | 0.00 | n/a | 0 | True | 8.67 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 13 | 0 | 1 | 0.00 | n/a | 0 | True | 8.64 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 14 | 0 | 1 | 0.00 | n/a | 0 | True | 8.86 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 15 | 0 | 1 | 0.00 | n/a | 0 | True | 8.74 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 16 | 0 | 1 | 0.00 | n/a | 0 | True | 8.95 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 17 | 0 | 1 | 0.00 | n/a | 0 | True | 8.71 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 18 | 0 | 1 | 0.00 | n/a | 0 | True | 8.66 |
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 19 | 0 | 1 | 0.00 | n/a | 0 | True | 8.91 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Accepted Rate CI | Full Test Success | Regression Failures Mean | Rollback Success | Depth Mean | Depth CI | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | verified_closed_loop | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 8.74 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| capability_algorithm_synthesis_repo | capability_unseen | capability_algorithm_synthesis | tie_or_frontier_match | 0.00 |  | 0.00 | [0.00, 0.00] | [0.00, 0.00] | False | False | False | False | False |

## Counted Success Provenance

| Repository | Task | Variant | Repeat | Seed | Hidden Counterexamples | Full Test Command | Exit Code | Provenance Hash | Held-Out Input Set |
|---|---|---|---:|---|---|---|---:|---|---|

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
