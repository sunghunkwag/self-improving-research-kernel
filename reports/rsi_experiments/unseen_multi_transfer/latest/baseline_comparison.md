# Baseline Comparison Scorecard

This report separates accepted-rate wins, improvement-depth wins, safety wins, and held-out transfer successes. Rows marked as inconclusive should not be presented as evidence that the proposed loop beats all baselines.

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| composite_unseen_schema_transfer_repo | unseen | composite_unseen_schema_transfer | unseen_transfer_success | 0.19 | evolutionary_repair_loop | 0.00 | [0.17, 0.21] | [1.00, 1.00] | False | True | False | False | False |

## Interpretation Rules

- `depth_win_over_single_pass`: the proposed loop reaches deeper recursive improvement than the single-pass agent baseline without lower accepted rate.
- `safety_win_over_ablation`: rollback and broad gates prevent unsafe promotion that an ablation fails to prevent.
- `unseen_transfer_success`: the loop patches a held-out schema surface not present in the original benchmark fixtures.
- `external_transfer_success`: the loop patches a fixture schema extracted from actual external repository issue metadata.
- `external_code_transfer_success`: the loop patches an executable bug fixture ported from external source plus a failing test, with hidden seed-derived counterexamples and passing full pytest.
- `deterministic_not_powered`: the proposed loop has a positive-looking CI signal but every relevant interval is degenerate, so it is not counted as a powered win.
- `capability_transfer_success`: the loop synthesizes a reusable primitive that solves executable public and hidden capability cases.
- All success outcomes require a recorded passing full `python -m pytest -q` result.
- `tie_or_frontier_match`: the proposed loop matches the best baseline on this metric but does not dominate it.
- `baseline_stronger_or_inconclusive`: the current evidence does not support a proposed-loop win.
