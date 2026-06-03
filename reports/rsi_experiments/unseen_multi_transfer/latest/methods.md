# Methods Note

## Stochasticity

- Trials use paired same-seed runs across proposed and baseline variants.
- External-code candidate ordering is seed-derived, so visible-only, wrong, and general repairs appear in different orders across trials.
- Composite schema tasks also use seeded candidate ordering and hidden counterexamples rather than metric noise.

## Reference Quarantine

- External-code fixtures ship buggy source and failing tests into the disposable repo.
- The held-out reference fix is represented only by SHA-256 hashes and forbidden span hashes.
- Candidate validation rejects writes to quarantine paths and rejects verbatim reference function/span hashes.

## Hidden Counterexamples

- Hidden external-code inputs are generated after the candidate patch from the paired trial seed.
- A visible-pass hidden-fail candidate records `overfit_signal=visible_passed_hidden_external_code_failed`.

## Proof-Carrying Discipline

- Candidate examples and probes may propose a repair, but executable guards dispose of it.
- Promotion evidence must include the proof object carried by the accepted record: exact full-test command, exit code, seed, held-out inputs, provenance hash, and hidden-counterexample family.
- A candidate with only visible examples and no independent guard evidence remains a rejected hypothesis, not a discovered capability.

## Paired Comparison

- Proposed and baseline rows share the same `paired_seed` for each repeat index.
- Margins use percentile bootstrap over same-seed proposed-baseline differences.
- Degenerate intervals are labeled `deterministic_not_powered` and are not counted as transfer wins.

## Guard Coverage

- Reference leakage: `external_code_reference_hash`, `external_code_reference_span_hash`, and quarantine-touch gates.
- Test narrowing: pre/post `pytest --collect-only -q` superset gate.
- Hardcoding or overfit: visible focused tests plus independent seed-derived hidden evaluator.
- Evaluator/report mutation: protected-path anti-cheat guard.
- Fake variance: metric writer paths remain read-only to candidates; stochasticity is from seed-driven candidate/input order.
- Gate weakening: broad/full pytest checks and comparability labels remain explicit.
