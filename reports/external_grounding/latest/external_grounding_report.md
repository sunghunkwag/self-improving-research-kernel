# External Grounding Report

- Generated at: 2026-05-26T21:43:40Z
- Sources: 22
- Tasks: 11

## Safety Model

- Only issue metadata is fetched.
- No external repository code is cloned or executed.
- Issue bodies are truncated before persistence.
- Repository count and issue count are bounded by CLI limits.
- Every task keeps source URL and retrieval provenance.

## Grounded Tasks

### github:certbot/certbot#5201

- Repository: `certbot/certbot`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: area: code health, area: ui / ux, bug, priority: unplanned
- URL: https://github.com/certbot/certbot/issues/5201
- Title: Certbot always checks default cli.ini locations when the --config option is set

### github:dask/dask#12359

- Repository: `dask/dask`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: array, bug, needs triage
- URL: https://github.com/dask/dask/issues/12359
- Title: 'cumsum' results differ from 'cumsum' on a pure numpy array

### github:hypothesisworks/hypothesis#4744

- Repository: `hypothesisworks/hypothesis`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: bug
- URL: https://github.com/HypothesisWorks/hypothesis/issues/4744
- Title: Pytest plugin produces corrupt patch if source file doesn't end in a newline

### github:mkdocs/mkdocs#3991

- Repository: `mkdocs/mkdocs`
- Kind: `external_documentation_repair`
- Score: 3.000
- Labels: Bug
- URL: https://github.com/mkdocs/mkdocs/issues/3991
- Title: Verbose flag overrides --strict flag.

### github:pandas-dev/pandas#65735

- Repository: `pandas-dev/pandas`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug, Needs Triage
- URL: https://github.com/pandas-dev/pandas/issues/65735
- Title: BUG: Incoherent dynamic dtype changes in `.map()`

### github:pre-commit/pre-commit#2530

- Repository: `pre-commit/pre-commit`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: bug, windows
- URL: https://github.com/pre-commit/pre-commit/issues/2530
- Title: ValueError on Windows when config is on a different drive than the git repo

### github:psf/requests#4965

- Repository: `psf/requests`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug
- URL: https://github.com/psf/requests/issues/4965
- Title: Accessing response.content twice removes forgets read error

### github:ray-project/ray#54428

- Repository: `ray-project/ray`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: P2, bug, data, stability
- URL: https://github.com/ray-project/ray/issues/54428
- Title: [Data] Inconsistent Serialization of pd.DataFrame Field in Dataclass When Using asdict with Ray Data

### github:redis/redis-py#3741

- Repository: `redis/redis-py`
- Kind: `external_bug_repair`
- Score: 3.000
- Labels: bug
- URL: https://github.com/redis/redis-py/issues/3741
- Title: Timeout writing to socket when using redis-py with configured timeouts and health check

### github:scikit-learn/scikit-learn#33541

- Repository: `scikit-learn/scikit-learn`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: Bug
- URL: https://github.com/scikit-learn/scikit-learn/issues/33541
- Title: TruncatedSVD infinite wait state

### github:sqlalchemy/sqlalchemy#10827

- Repository: `sqlalchemy/sqlalchemy`
- Kind: `external_regression_repair`
- Score: 3.000
- Labels: bug, lambda sql
- URL: https://github.com/sqlalchemy/sqlalchemy/issues/10827
- Title: Extending lambda statements with non-lambda expressions creates bad bind parameters

