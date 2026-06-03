# External Code Sandbox Fixtures

These fixtures transfer bounded source excerpts and issue failure excerpts from real external repositories into text-only sandbox artifacts. No third-party code is executed.

| Repository | Source Path | Issue | Field | Values | Source Lines |
|---|---|---|---|---|---:|
| `psf/requests` | `src/requests/sessions.py` | [issue](https://github.com/psf/requests/issues/4965) | `external_requests_code_signals` | `merge_setting_none_header, merge_setting, merge_hooks, src, requests` | 51-109 |

## Safety Controls

- Source snippets are stored as `.txt` fixture artifacts.
- The builder never imports, installs, or executes external repository code.
- Excerpts are bounded by CLI limits and recorded with SHA-256 hashes.
- Downstream RSI experiments consume only local schema fields and provenance metadata.
