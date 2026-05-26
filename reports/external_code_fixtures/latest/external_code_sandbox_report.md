# External Code Sandbox Fixtures

These fixtures transfer bounded source excerpts and issue failure excerpts from real external repositories into text-only sandbox artifacts. No third-party code is executed.

| Repository | Source Path | Issue | Field | Values | Source Lines |
|---|---|---|---|---|---:|
| `psf/requests` | `src/requests/models.py` | [issue](https://github.com/psf/requests/issues/4965) | `external_requests_code_signals` | `response_content, src, requests, models, content` | 35-105 |
| `hypothesisworks/hypothesis` | `hypothesis/src/_hypothesis_pytestplugin.py` | [issue](https://github.com/HypothesisWorks/hypothesis/issues/4744) | `external_hypothesis_code_signals` | `pytest_patch, pytest_collection_modifyitems, hypothesis, src, hypothesis_pytestplugin` | 396-440 |
| `pandas-dev/pandas` | `pandas/core/series.py` | [issue](https://github.com/pandas-dev/pandas/issues/65735) | `external_pandas_code_signals` | `series_map_dtype, pandas, core, series, map` | 1-89 |
| `dask/dask` | `dask/array/reductions.py` | [issue](https://github.com/dask/dask/issues/12359) | `external_dask_code_signals` | `array_cumsum, nanprod, nancumsum, nancumprod, dask` | 187-247 |

## Safety Controls

- Source snippets are stored as `.txt` fixture artifacts.
- The builder never imports, installs, or executes external repository code.
- Excerpts are bounded by CLI limits and recorded with SHA-256 hashes.
- Downstream RSI experiments consume only local schema fields and provenance metadata.
