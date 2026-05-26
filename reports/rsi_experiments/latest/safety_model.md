# Safety Model

- Execution is bounded by workflow timeout, loop wall-clock budget, and per-command timeout.
- Candidates are deterministic source patches, not unbounded autonomous processes.
- Rejected candidates are rolled back by default.
- A kill-switch file at `.omega_rsi_runs/STOP_CLOSED_RSI` stops the loop.
- Accepted and rejected records are persisted as JSON provenance.
- Benchmark trials run inside isolated disposable repository fixtures.
- Dangerous ablations such as no rollback run only in disposable experiment copies.
- The main workflow commits only accepted state and validated source changes.
