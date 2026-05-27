# External Grounding Report

- Generated at: 2026-05-27T04:00:33Z
- Sources: 4
- Tasks: 4

## Safety Model

- Only issue metadata is fetched.
- No external repository code is cloned or executed.
- Issue bodies are truncated before persistence.
- Repository count and issue count are bounded by CLI limits.
- Every task keeps source URL and retrieval provenance.

## Grounded Tasks

### github:dask/dask#12359

- Repository: `dask/dask`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: array, bug, needs triage
- URL: https://github.com/dask/dask/issues/12359
- Title: 'cumsum' results differ from 'cumsum' on a pure numpy array

### github:hypothesisworks/hypothesis#4729

- Repository: `hypothesisworks/hypothesis`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: bug, performance
- URL: https://github.com/HypothesisWorks/hypothesis/issues/4729
- Title: Time blowup for `from_type` with certain abstract classes

### github:pandas-dev/pandas#65735

- Repository: `pandas-dev/pandas`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug, Needs Triage
- URL: https://github.com/pandas-dev/pandas/issues/65735
- Title: BUG: Incoherent dynamic dtype changes in `.map()`

### github:psf/requests#4965

- Repository: `psf/requests`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug
- URL: https://github.com/psf/requests/issues/4965
- Title: Accessing response.content twice removes forgets read error

