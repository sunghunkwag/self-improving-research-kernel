# Closed RSI Growth Report

This report is generated from `.omega_rsi_runs` records produced by an actual closed-loop run. It does not claim unbounded self-improvement.

## Summary

- Active generation: 7
- Active base: `emergent_local_corpus_imports_membership_v1`
- Full test command: `python -m pytest -q`
- Full test required: True
- Final full test exit code: 0
- Plateau reason: `no_candidates_generated`
- Plateau detail: `no_candidates_generated`
- Proxy promotion events: 0

## Candidate Accounting

| Generated | Attempted | Compiled | Pre-full Gates Passed | Full-suite Passed | Solved Tasks | Hidden Transfer | Operator Reuse |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 | 1 | 0 | 0 | 2 |

## Proxy Objective Accounting

| Generation | Proxy Promotions | Proxy Hidden Transfer | Selected Proxy | Invented Proxy Descriptions |
|---:|---:|---:|---|---|
| 7 | 0 | 0 | `proxy_gen_7_0_9fa2f4e072` | Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.07, 'self_play_wins': 0.99, 'weakness_exposure': 0.59, 'archive_sparsity': 0.31, 'population_fit': 0.3, 'complexity_penalty': 0.12, 'rejection_pressure': 0.4} expression=0.07 * novelty + 0.99 * self_play_wins + 0.59 * weakness_exposure + 0.31 * archive_sparsity + 0.3 * population_fit - 0.12 * complexity_penalty - 0.4 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.84, 'self_play_wins': 0.57, 'weakness_exposure': 0.12, 'archive_sparsity': 0.28, 'population_fit': 0.41, 'complexity_penalty': 0.31, 'rejection_pressure': 0.28} expression=0.84 * novelty + 0.57 * self_play_wins + 0.12 * weakness_exposure + 0.28 * archive_sparsity + 0.41 * population_fit - 0.31 * complexity_penalty - 0.28 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.84, 'self_play_wins': 0.49, 'weakness_exposure': 0.23, 'archive_sparsity': 0.28, 'population_fit': 0.65, 'complexity_penalty': 0.18, 'rejection_pressure': 0.31} expression=0.84 * novelty + 0.49 * self_play_wins + 0.23 * weakness_exposure + 0.28 * archive_sparsity + 0.65 * population_fit - 0.18 * complexity_penalty - 0.31 * rejection_pressure |
| 8 | 0 | 0 | `proxy_gen_8_0_e5a230b92b` | Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.17, 'self_play_wins': 0.74, 'weakness_exposure': 0.42, 'archive_sparsity': 0.2, 'population_fit': 0.14, 'complexity_penalty': 0.12, 'rejection_pressure': 0.3} expression=0.17 * novelty + 0.74 * self_play_wins + 0.42 * weakness_exposure + 0.2 * archive_sparsity + 0.14 * population_fit - 0.12 * complexity_penalty - 0.3 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.44, 'self_play_wins': 0.46, 'weakness_exposure': 0.48, 'archive_sparsity': 0.11, 'population_fit': 0.46, 'complexity_penalty': 0.08, 'rejection_pressure': 0.17} expression=0.44 * novelty + 0.46 * self_play_wins + 0.48 * weakness_exposure + 0.11 * archive_sparsity + 0.46 * population_fit - 0.08 * complexity_penalty - 0.17 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.99, 'self_play_wins': 0.37, 'weakness_exposure': 0.38, 'archive_sparsity': 0.29, 'population_fit': 0.3, 'complexity_penalty': 0.2, 'rejection_pressure': 0.29} expression=0.99 * novelty + 0.37 * self_play_wins + 0.38 * weakness_exposure + 0.29 * archive_sparsity + 0.3 * population_fit - 0.2 * complexity_penalty - 0.29 * rejection_pressure |

Proxy objectives are retained only when delayed ground-truth judgment improves on two unseen seed sets. A zero count reports a plateau, not a fabricated breakthrough.

## Per Generation

| Generation | Generated | Attempted | Compiled | Pre-full Passed | Full-suite Passed | Promoted | Stop Reason | Capabilities |
|---:|---:|---:|---:|---:|---:|---|---|---|
| 7 | 1 | 1 | 1 | 1 | 1 | `emergent_local_corpus_imports_membership_v1` | `candidate_promoted` | `schema_query_repair` |
| 8 | 0 | 0 | 0 | 0 | 0 | `` | `no_candidates_generated` | `` |

## Capability Movement

Touched capability families: `schema_query_repair`

## Plateau Analysis

The run stopped at `no_candidates_generated` / `no_candidates_generated`. This is the reported ceiling for this run configuration, not evidence of unlimited growth.

