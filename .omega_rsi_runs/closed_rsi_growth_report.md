# Closed RSI Growth Report

This report is generated from `.omega_rsi_runs` records produced by an actual closed-loop run. It does not claim unbounded self-improvement.

## Summary

- Active generation: 8
- Active base: `capability_operator_residue_feedback_policy_surface_generator_feedback_polic_runtimeerror_v1`
- Full test command: `python -m pytest -q`
- Full test required: True
- Final full test exit code: 0
- Plateau reason: `max_generations_reached`
- Plateau detail: `candidate_promoted`
- Proxy promotion events: 1

## Candidate Accounting

| Generated | Attempted | Compiled | Pre-full Gates Passed | Full-suite Passed | Solved Tasks | Hidden Transfer | Operator Reuse |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 1 | 1 | 1 | 1 | 1 | 2 |

## Proxy Objective Accounting

| Generation | Proxy Promotions | Proxy Hidden Transfer | Selected Proxy | Invented Proxy Descriptions |
|---:|---:|---:|---|---|
| 8 | 1 | 2 | `proxy_gen_8_0_491195b064` | Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.91, 'self_play_wins': 0.46, 'weakness_exposure': 0.3, 'archive_sparsity': 0.08, 'population_fit': 0.48, 'complexity_penalty': 0.17, 'rejection_pressure': 0.13} expression=0.91 * novelty + 0.46 * self_play_wins + 0.3 * weakness_exposure + 0.08 * archive_sparsity + 0.48 * population_fit - 0.17 * complexity_penalty - 0.13 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.5, 'self_play_wins': 0.34, 'weakness_exposure': 0.43, 'archive_sparsity': 0.32, 'population_fit': 0.61, 'complexity_penalty': 0.18, 'rejection_pressure': 0.15} expression=0.5 * novelty + 0.34 * self_play_wins + 0.43 * weakness_exposure + 0.32 * archive_sparsity + 0.61 * population_fit - 0.18 * complexity_penalty - 0.15 * rejection_pressure<br>Invented structural proxy over novelty, self-play wins, weakness exposure, archive sparsity, population fit, complexity, and rejection pressure. weights={'novelty': 0.53, 'self_play_wins': 0.07, 'weakness_exposure': 0.34, 'archive_sparsity': 0.24, 'population_fit': 0.12, 'complexity_penalty': 0.35, 'rejection_pressure': 0.2} expression=0.53 * novelty + 0.07 * self_play_wins + 0.34 * weakness_exposure + 0.24 * archive_sparsity + 0.12 * population_fit - 0.35 * complexity_penalty - 0.2 * rejection_pressure |

Proxy objectives are retained only when delayed ground-truth judgment improves on two unseen seed sets. A zero count reports a plateau, not a fabricated breakthrough.

## Per Generation

| Generation | Generated | Attempted | Compiled | Pre-full Passed | Full-suite Passed | Promoted | Stop Reason | Capabilities |
|---:|---:|---:|---:|---:|---:|---|---|---|
| 8 | 2 | 1 | 1 | 1 | 1 | `capability_operator_residue_feedback_policy_surface_generator_feedback_polic_runtimeerror_v1` | `candidate_promoted` | `residue_feedback_policy_surface_generator_feedback_polic_runtimeerror` |

## Capability Movement

Touched capability families: `residue_feedback_policy_surface_generator_feedback_polic_runtimeerror`

## Plateau Analysis

The run stopped at `max_generations_reached` / `candidate_promoted`. This is the reported ceiling for this run configuration, not evidence of unlimited growth.

