# Closed RSI Growth Report

This report is generated from `.omega_rsi_runs` records produced by an actual closed-loop run. It does not claim unbounded self-improvement.

## Summary

- Active generation: 6
- Active base: `emergent_local_corpus_feature_flags_membership_v1`
- Full test command: `python -m pytest -q`
- Full test required: True
- Final full test exit code: 0
- Plateau reason: `max_generations_reached`
- Plateau detail: `candidate_promoted`

## Candidate Accounting

| Generated | Attempted | Compiled | Pre-full Gates Passed | Full-suite Passed | Solved Tasks | Hidden Transfer | Operator Reuse |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 3 | 3 | 3 | 3 | 0 | 0 | 6 |

## Per Generation

| Generation | Generated | Attempted | Compiled | Pre-full Passed | Full-suite Passed | Promoted | Stop Reason | Capabilities |
|---:|---:|---:|---:|---:|---:|---|---|---|
| 4 | 3 | 1 | 1 | 1 | 1 | `autonomous_local_corpus_definitions_query_v1` | `candidate_promoted` | `schema_query_repair` |
| 5 | 3 | 1 | 1 | 1 | 1 | `emergent_local_corpus_definitions_membership_v1` | `candidate_promoted` | `schema_query_repair` |
| 6 | 2 | 1 | 1 | 1 | 1 | `emergent_local_corpus_feature_flags_membership_v1` | `candidate_promoted` | `schema_query_repair` |

## Capability Movement

Touched capability families: `schema_query_repair`

## Plateau Analysis

The run stopped at `max_generations_reached` / `candidate_promoted`. This is the reported ceiling for this run configuration, not evidence of unlimited growth.

