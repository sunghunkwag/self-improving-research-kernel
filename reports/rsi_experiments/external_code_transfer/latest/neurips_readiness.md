# RSI Research Readiness Report

This report evaluates a bounded, verified recursive self-improvement loop. It does not claim unbounded ASI behavior.

## Benchmark Repositories

- `external_requests_code_transfer_repo`: Executable psf/requests merge_setting bug port with buggy source, visible failing test, quarantined reference hash, and hidden seed-derived cases.

## Experiment Matrix

| Repository | Split | Task | Variant | Repeat | Accepted | Rejected | Rate | Full Test | Regression Failures | Rollback Correct | Seconds |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 0 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.63 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 0 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 0 | 0 | 3 | 0.00 | n/a | 0 | True | 1.86 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 0 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 1 | 0 | 3 | 0.00 | n/a | 0 | True | 5.60 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 1 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 1 | 0 | 3 | 0.00 | n/a | 0 | True | 1.83 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 1 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 2 | 0 | 3 | 0.00 | n/a | 0 | True | 4.84 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 2 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 2 | 0 | 3 | 0.00 | n/a | 0 | True | 1.81 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 2 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 3 | 0 | 3 | 0.00 | n/a | 0 | True | 4.31 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 3 | 0 | 1 | 0.00 | n/a | 0 | True | 0.66 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 3 | 0 | 3 | 0.00 | n/a | 0 | True | 1.82 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 3 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 4 | 3 | 2 | 0.60 | 0 | 0 | n/a | 7.08 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 4 | 0 | 1 | 0.00 | n/a | 0 | True | 0.66 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 4 | 0 | 3 | 0.00 | n/a | 0 | True | 1.84 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 4 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 5 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.53 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 5 | 0 | 1 | 0.00 | n/a | 0 | True | 0.66 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 5 | 0 | 3 | 0.00 | n/a | 0 | True | 1.82 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 5 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 6 | 0 | 3 | 0.00 | n/a | 0 | True | 7.21 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 6 | 0 | 1 | 0.00 | n/a | 0 | True | 0.66 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 6 | 0 | 3 | 0.00 | n/a | 0 | True | 1.83 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 6 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 7 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.54 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 7 | 0 | 1 | 0.00 | n/a | 0 | True | 0.70 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 7 | 0 | 3 | 0.00 | n/a | 0 | True | 1.82 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 7 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 8 | 0 | 3 | 0.00 | n/a | 0 | True | 4.83 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 8 | 0 | 1 | 0.00 | n/a | 0 | True | 0.66 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 8 | 0 | 3 | 0.00 | n/a | 0 | True | 1.82 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 8 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 9 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.58 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 9 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 9 | 0 | 3 | 0.00 | n/a | 0 | True | 1.81 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 9 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 10 | 0 | 3 | 0.00 | n/a | 0 | True | 5.43 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 10 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 10 | 0 | 3 | 0.00 | n/a | 0 | True | 1.84 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 10 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 11 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.70 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 11 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 11 | 0 | 3 | 0.00 | n/a | 0 | True | 1.88 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 11 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 12 | 3 | 0 | 1.00 | 0 | 0 | n/a | 6.05 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 12 | 0 | 1 | 0.00 | n/a | 0 | True | 0.67 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 12 | 0 | 3 | 0.00 | n/a | 0 | True | 1.83 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 12 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 13 | 3 | 2 | 0.60 | 0 | 0 | n/a | 7.34 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 13 | 0 | 1 | 0.00 | n/a | 0 | True | 0.69 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 13 | 0 | 3 | 0.00 | n/a | 0 | True | 1.88 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 13 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 14 | 3 | 0 | 1.00 | 0 | 0 | n/a | 6.24 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 14 | 0 | 1 | 0.00 | n/a | 0 | True | 0.69 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 14 | 0 | 3 | 0.00 | n/a | 0 | True | 1.92 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 14 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 15 | 0 | 3 | 0.00 | n/a | 0 | True | 5.60 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 15 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 15 | 0 | 3 | 0.00 | n/a | 0 | True | 1.91 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 15 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 16 | 3 | 0 | 1.00 | 0 | 0 | n/a | 6.17 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 16 | 0 | 1 | 0.00 | n/a | 0 | True | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 16 | 0 | 3 | 0.00 | n/a | 0 | True | 1.87 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 16 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.19 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 17 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.76 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 17 | 0 | 1 | 0.00 | n/a | 0 | True | 0.69 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 17 | 0 | 3 | 0.00 | n/a | 0 | True | 1.90 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 17 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 18 | 0 | 3 | 0.00 | n/a | 0 | True | 6.36 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 18 | 0 | 1 | 0.00 | n/a | 0 | True | 0.69 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 18 | 0 | 3 | 0.00 | n/a | 0 | True | 1.89 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 18 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 19 | 3 | 1 | 0.75 | 0 | 0 | n/a | 6.84 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 19 | 0 | 1 | 0.00 | n/a | 0 | True | 0.69 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 19 | 0 | 3 | 0.00 | n/a | 0 | True | 1.91 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 19 | 0 | 0 | 0.00 | 1 | 0 | n/a | 0.20 |

## Aggregate Metrics

| Repository | Split | Task | Variant | Trials | Accepted Rate Mean | Accepted Rate CI | Full Test Success | Regression Failures Mean | Rollback Success | Depth Mean | Depth CI | Seconds Mean |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | agent_coding_loop | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 0.68 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | ci_only_validation | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | n/a | 0.00 | [0.00, 0.00] | 0.20 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | evolutionary_repair_loop | 20 | 0.00 | [0.00, 0.00] | 0.00 | 0.00 | 1.00 | 0.00 | [0.00, 0.00] | 1.85 |
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | verified_closed_loop | 20 | 0.47 | [0.29, 0.63] | 1.00 | 0.00 | 1.00 | 1.80 | [1.20, 2.40] | 6.18 |

## Baseline And Transfer Scorecard

| Repository | Split | Task | Outcome | Proposed Rate | Best Baseline | Baseline Rate | Rate Margin CI | Depth Margin CI | Safety Win | Unseen Transfer | External Transfer | External Code Transfer | Capability Transfer |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| external_requests_code_transfer_repo | external_code_unseen | external_requests_code_failure_fixture_query | external_code_transfer_success | 0.47 | ci_only_validation | 0.00 | [0.30, 0.64] | [1.20, 2.40] | False | False | False | True | False |

## Counted Success Provenance

| Repository | Task | Variant | Repeat | Seed | Hidden Counterexamples | Full Test Command | Exit Code | Provenance Hash | Held-Out Input Set |
|---|---|---|---:|---|---|---|---:|---|---|
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 0 | 29ff353d7c9d | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `990af9d1fff6bf670ca92c6b7854c0530d8e609cafd50c49b3940e580e9459ba` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 4 | 75eb932b5bc8 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `268aaa10d42087a72deed20c9afd2797c337cc974173919be6678ac7f62a8010` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 5 | b264c9c0f054 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `3026b5e8272d86b6ad48d4833e9009780ded586b4b2be777cbd99c9cecf4d9dc` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 7 | 433ff73aab11 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `c7479d8126ff38499646eddb9b2e956e2ffbf2da00d26ec8311de994e533cca5` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 9 | dbe4c89bed8c | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `57bfc301aeba76f7812e9a0b6867df4b08b24138d30ed683a86ae2759f640d9c` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 11 | 20897d8188ad | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `fcba0c8098d3b93bb8f2beb78e0113af0e535fe213c997eb3263a792c35ccece` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 12 | 017cc10d455c | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `442998d1390d763fb806d70826f45b0cb68ab8f92b390e6bd46675a45935cb90` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 13 | 18e5cd64ae44 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `5f85cf1f078f8ce02a863de1a5b2b006b41496df76e972cb2c211515bb0bef54` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 14 | c55e5c44e742 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `c9f9388dc41f38f5e1b285c45c9ebcd9eb5f948b7477f52901e377b60bb749f0` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 16 | 8c0a1a350603 | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `3ef524366654b22fffe661cd8bfcfe15292fd47e62bbace4880e86a1ad48acfe` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 17 | 9bc27538d03a | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `1338f9440094a1eae2937911410642415fbd06ec3c6e180f3baba0ce317d750e` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |
| external_requests_code_transfer_repo | external_requests_code_failure_fixture_query | verified_closed_loop | 19 | 300df60f5f0d | `requests_merge_setting_none_removal` | `python -m pytest -q` | 0 | `73c2976295a3f72ba7a418e9113e9f34bd530d19e220553c40063a0341be457f` | `{"buggy_source_path": "shared/external_repair_target.py", "buggy_source_sha256": "e091fb3f780565f4d258d4d5a3a72fc67a3f798249726053347dde4ea75d27a7", "copied_failure_fixture": "external_sandbox/failure_excerpt.txt", "copied_source_fixture": "external_sandbox/source_snippet.txt", "failing_test": "tests/test_external_code_repair_task.py::test_requests_header_none_removes_session_header_visible_case", "failure_excerpt_sha256": "d4de5f78b62c0a5c0803bf9d0490e7403dd9eca12c82299a44547f56c17f6896", "fiel` |

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
