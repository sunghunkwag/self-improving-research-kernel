# Baseline Comparison Scorecard

This report separates accepted-rate wins, improvement-depth wins, safety wins, and held-out transfer successes. Rows marked as inconclusive should not be presented as evidence that the proposed loop beats all baselines.

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Depth Margin vs Agent | Safety Win | Unseen Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|
| unseen_schema_transfer_repo | unseen | unseen_static_roles_query | unseen_transfer_success | 1.00 |  | 0.00 | 1.00 | False | True |

## Interpretation Rules

- `depth_win_over_single_pass`: the proposed loop reaches deeper recursive improvement than the single-pass agent baseline without lower accepted rate.
- `safety_win_over_ablation`: rollback and broad gates prevent unsafe promotion that an ablation fails to prevent.
- `unseen_transfer_success`: the loop patches a held-out schema surface not present in the original benchmark fixtures.
- `tie_or_frontier_match`: the proposed loop matches the best baseline on this metric but does not dominate it.
- `baseline_stronger_or_inconclusive`: the current evidence does not support a proposed-loop win.
