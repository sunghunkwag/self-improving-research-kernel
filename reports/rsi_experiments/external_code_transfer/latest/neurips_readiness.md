# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `external_requests_code_transfer_repo`: Executable psf/requests merge_setting bug port with buggy source, visible failing test, quarantined reference hash, and hidden seed-derived cases.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Full Test | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.72 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 0 | 0 | 1 | 0.00 | n/a | 0 | True | 0.49 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 0 | 0 | 3 | 0.00 | n/a | 0 | True | 1.40 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.15 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 1 | 0 | 3 | 0.00 | n/a | 0 | True | 3.97 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 1 | 0 | 1 | 0.00 | n/a | 0 | True | 0.47 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 1 | 0 | 3 | 0.00 | n/a | 0 | True | 1.38 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.15 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 2 | 0 | 3 | 0.00 | n/a | 0 | True | 3.65 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 2 | 0 | 1 | 0.00 | n/a | 0 | True | 0.47 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 2 | 0 | 3 | 0.00 | n/a | 0 | True | 1.59 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 2 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.15 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 3 | 0 | 3 | 0.00 | n/a | 0 | True | 3.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 3 | 0 | 1 | 0.00 | n/a | 0 | True | 0.48 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 3 | 0 | 3 | 0.00 | n/a | 0 | True | 1.31 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 3 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 4 | 3 | 2 | 0.60 | 0 | 0 | n/a | 5.24 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 4 | 0 | 1 | 0.00 | n/a | 0 | True | 0.47 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 4 | 0 | 3 | 0.00 | n/a | 0 | True | 1.34 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 4 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.14 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 5 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.44 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 5 | 0 | 1 | 0.00 | n/a | 0 | True | 0.46 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 5 | 0 | 3 | 0.00 | n/a | 0 | True | 1.28 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 5 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.14 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 6 | 0 | 3 | 0.00 | n/a | 0 | True | 5.16 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 6 | 0 | 1 | 0.00 | n/a | 0 | True | 0.52 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 6 | 0 | 3 | 0.00 | n/a | 0 | True | 1.43 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 6 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.16 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 7 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.91 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 7 | 0 | 1 | 0.00 | n/a | 0 | True | 0.47 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 7 | 0 | 3 | 0.00 | n/a | 0 | True | 1.29 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 7 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.14 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 8 | 0 | 3 | 0.00 | n/a | 0 | True | 3.29 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 8 | 0 | 1 | 0.00 | n/a | 0 | True | 0.44 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 8 | 0 | 3 | 0.00 | n/a | 0 | True | 1.17 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 8 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.12 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 9 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.27 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 9 | 0 | 1 | 0.00 | n/a | 0 | True | 0.42 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 9 | 0 | 3 | 0.00 | n/a | 0 | True | 1.18 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 9 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.12 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 10 | 0 | 3 | 0.00 | n/a | 0 | True | 3.49 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 10 | 0 | 1 | 0.00 | n/a | 0 | True | 0.43 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 10 | 0 | 3 | 0.00 | n/a | 0 | True | 1.18 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 10 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 11 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.45 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 11 | 0 | 1 | 0.00 | n/a | 0 | True | 0.43 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 11 | 0 | 3 | 0.00 | n/a | 0 | True | 1.29 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 11 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 12 | 3 | 0 | 1.00 | 0 | 0 | n/a | 3.89 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 12 | 0 | 1 | 0.00 | n/a | 0 | True | 0.45 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 12 | 0 | 3 | 0.00 | n/a | 0 | True | 1.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 12 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 13 | 3 | 2 | 0.60 | 0 | 0 | n/a | 4.77 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 13 | 0 | 1 | 0.00 | n/a | 0 | True | 0.47 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 13 | 0 | 3 | 0.00 | n/a | 0 | True | 1.25 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 13 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.14 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 14 | 3 | 0 | 1.00 | 0 | 0 | n/a | 4.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 14 | 0 | 1 | 0.00 | n/a | 0 | True | 0.46 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 14 | 0 | 3 | 0.00 | n/a | 0 | True | 1.25 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 14 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.12 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 15 | 0 | 3 | 0.00 | n/a | 0 | True | 3.92 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 15 | 0 | 1 | 0.00 | n/a | 0 | True | 0.45 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 15 | 0 | 3 | 0.00 | n/a | 0 | True | 1.24 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 15 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.14 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 16 | 3 | 0 | 1.00 | 0 | 0 | n/a | 3.92 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 16 | 0 | 1 | 0.00 | n/a | 0 | True | 0.44 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 16 | 0 | 3 | 0.00 | n/a | 0 | True | 1.22 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 16 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 17 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.26 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 17 | 0 | 1 | 0.00 | n/a | 0 | True | 0.44 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 17 | 0 | 3 | 0.00 | n/a | 0 | True | 1.30 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 17 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 18 | 0 | 3 | 0.00 | n/a | 0 | True | 4.00 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 18 | 0 | 1 | 0.00 | n/a | 0 | True | 0.44 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 18 | 0 | 3 | 0.00 | n/a | 0 | True | 1.25 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 18 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 19 | 3 | 1 | 0.75 | 0 | 0 | n/a | 4.49 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 19 | 0 | 1 | 0.00 | n/a | 0 | True | 0.44 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 19 | 0 | 3 | 0.00 | n/a | 0 | True | 1.25 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 19 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.13 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Accepted Rate CI | Full Test Success | Regression Failures Mean | Rollback Success | Depth Mean | Depth CI | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 0.46 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | n/a | 0.00 | [0.00, 0.00] | 0.14 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 1.29 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 20 | 0.47 | [0.29, 0.63] | 1.00 | 0.00 | 1.00 | 1.80 | [1.20, 2.40] | 4.21 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | external_code_transfer_success | 0.47 | ci_only_validation | 0.00 | [0.30, 0.64] | [1.20, 2.40] | False | False | False | True | False |

## Counted Success Provenance

| Repository | Task | Variant | Repeat | Seed | Hidden Counterexamples | Full Test Command | Exit Code | Provenance Hash | Held-Out Input Set |
|---|---|---|---:|---|---|---|---:|---|---|
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 0 | 29ff353d7c9d | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `0a879794f1129ea14d3cf7aa81ab230102e8a53d4199dacc0be2178082f32c76` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 4 | 75eb932b5bc8 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `67f0efeb628ebb7b6e3263a7ef6deaf89a2afc086258424cbed7cd730edd4e61` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 5 | b264c9c0f054 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `f9d7c926ffdd1076a33c3fba3f1a8a5a0b448fdd0c796001da517b21de57698a` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 7 | 433ff73aab11 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `a2037983d4220f441ba92b52bbe880e53ba9f63456a96bfcf3a15730de44b7c8` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 9 | dbe4c89bed8c | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `74c06785694befd2331ed2b310d1baccefb17f0194fa91f6cba0831bb3a89665` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 11 | 20897d8188ad | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `191ac1b83fbbddfb36c7b238ea15db98df10bcae468938bedaedfa1b40c52587` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 12 | 017cc10d455c | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `ab66ff1cd4abff3a540ffb52640bfbe7eee3acbaec9974068af5b7a921444027` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 13 | 18e5cd64ae44 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `40de3213933efc024a006d72cc41cf87407545e605678347eafa4ea48c714d25` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 14 | c55e5c44e742 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `fcd77ae04ccc8821639a6e3826c8ed5fb162116d38bcf47f674f310f1b91d39e` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 16 | 8c0a1a350603 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `dbe5fe8b2a67dfaa8efd16fb39f8d1c18815ebaa815eba0c3a82a9a600467804` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 17 | 9bc27538d03a | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `5fafcd720d880b66ee6cc7b73b05475622d88dddac26e76599307dd32693a7a2` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 19 | 300df60f5f0d | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `ce827dee84ddf9dbc585e16a7c508c42a7b4f1e9ca7be248dfce08956a57cda5` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "3bd526e1c1acd6c1247d5c2bc5922ba0fe37bf52c329d978674044d6632ac2d2", "fiel` |

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
