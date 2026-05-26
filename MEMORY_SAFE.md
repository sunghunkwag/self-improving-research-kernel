# Memory-Safe Local Operation

This repository is configured for an 8GB local PC by default.

Rules:

- Do not run the full test suite locally.
- Do not enable `OMEGA_THDSE_ENABLE_RUST` locally.
- Use `python scripts/memory_safe_validate.py --quick` for the smallest smoke check.
- Use `python scripts/memory_safe_validate.py` for the normal 8GB-safe check.
- Run full THDSE validation only on Colab or another high-memory runtime.

Colab entry point:

```bash
python scripts/colab_validate.py --full
```

The local Python corpus has already been connected as static evidence under:

```text
reports/omega_local_python_corpus_index.json
reports/omega_local_python_corpus_report.md
```
