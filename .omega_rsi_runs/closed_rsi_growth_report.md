# Closed RSI Growth Report

This report is generated from `.omega_rsi_runs` records produced by an actual closed-loop run. It does not claim unbounded self-improvement.

## Summary

- Active generation: 7
- Active base: `emergent_local_corpus_imports_membership_v1`
- Full test command: `python -m pytest -q`
- Full test required: True
- Final full test exit code: None
- Plateau reason: `candidate_budget_exhausted_without_promotion`
- Plateau detail: `candidate_budget_exhausted_without_promotion`
- Proxy promotion events: 0

## Candidate Accounting

| Generated | Attempted | Compiled | Pre-full Gates Passed | Full-suite Passed | Solved Tasks | Hidden Transfer | Operator Reuse |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 |

## Proxy Objective Accounting

| Generation | Proxy Promotions | Proxy Hidden Transfer | Selected Proxy | Invented Proxy Descriptions |
|---:|---:|---:|---|---|
| 8 | 0 | 0 | `proxy_gen_8_0_1b3bf24927` | Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.69, 'self_play_wins': 0.89, 'weakness_exposure': 0.19, 'archive_sparsity': 0.25, 'population_fit': 0.59, 'complexity_penalty': 0.26, 'rejection_pressure': 0.41} expression=0.69 * novelty + 0.89 * self_play_wins + 0.19 * weakness_exposure + 0.25 * archive_sparsity + 0.59 * population_fit - 0.26 * complexity_penalty - 0.41 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.2, 'self_play_wins': 1.0, 'weakness_exposure': 0.17, 'archive_sparsity': 0.36, 'population_fit': 0.47, 'complexity_penalty': 0.27, 'rejection_pressure': 0.12} expression=0.2 * novelty + 1.0 * self_play_wins + 0.17 * weakness_exposure + 0.36 * archive_sparsity + 0.47 * population_fit - 0.27 * complexity_penalty - 0.12 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.83, 'self_play_wins': 0.63, 'weakness_exposure': 0.32, 'archive_sparsity': 0.39, 'population_fit': 0.68, 'complexity_penalty': 0.34, 'rejection_pressure': 0.09} expression=0.83 * novelty + 0.63 * self_play_wins + 0.32 * weakness_exposure + 0.39 * archive_sparsity + 0.68 * population_fit - 0.34 * complexity_penalty - 0.09 * rejection_pressure |

Proxy objectives are retained only when delayed ground-truth judgment improves on two unseen seed sets. A zero count reports a plateau, not a fabricated breakthrough.

## Per Generation

| Generation | Generated | Attempted | Compiled | Pre-full Passed | Full-suite Passed | Promoted | Stop Reason | Capabilities |
|---:|---:|---:|---:|---:|---:|---|---|---|
| 8 | 1 | 1 | 0 | 0 | 0 | `` | `candidate_budget_exhausted_without_promotion` | `generator_feedback_policy` |

## Capability Movement

Touched capability families: `generator_feedback_policy`

## Plateau Analysis

The run stopped at `candidate_budget_exhausted_without_promotion` / `candidate_budget_exhausted_without_promotion`. This is the reported ceiling for this run configuration, not evidence of unlimited growth.

