# External Grounding Report

- Generated at: 2026-05-26T13:09:11Z
- Sources: 3
- Tasks: 2

## Safety Model

- Only issue metadata is fetched.
- No external repository code is cloned or executed.
- Issue bodies are truncated before persistence.
- Repository count and issue count are bounded by CLI limits.
- Every task keeps source URL and retrieval provenance.

## Grounded Tasks

### github:psf/requests#2018

- Repository: `psf/requests`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: Breaking API Change, Bug, Planned
- URL: https://github.com/psf/requests/issues/2018
- Title: Re-order proxy precedence.

### github:psf/requests#4965

- Repository: `psf/requests`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug
- URL: https://github.com/psf/requests/issues/4965
- Title: Accessing response.content twice removes forgets read error

