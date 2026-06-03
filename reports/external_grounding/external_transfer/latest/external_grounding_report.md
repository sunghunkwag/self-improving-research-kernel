# External Grounding Report

- Generated at: 2026-06-03T12:40:52Z
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
- Labels: array, bug
- URL: https://github.com/dask/dask/issues/12359
- Title: 'cumsum' results differ from 'cumsum' on a pure numpy array

### github:hypothesisworks/hypothesis#4475

- Repository: `hypothesisworks/hypothesis`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: bug
- URL: https://github.com/HypothesisWorks/hypothesis/issues/4475
- Title: Race condition error in `recursive_property`

### github:pandas-dev/pandas#20769

- Repository: `pandas-dev/pandas`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: Bug, Reshaping
- URL: https://github.com/pandas-dev/pandas/issues/20769
- Title: pd.merge: MultiIndex column label mistakenly classified as "not unique"

### github:psf/requests#4965

- Repository: `psf/requests`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug
- URL: https://github.com/psf/requests/issues/4965
- Title: Accessing response.content twice removes forgets read error

