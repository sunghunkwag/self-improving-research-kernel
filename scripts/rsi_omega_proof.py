"""Machine-check the Systemtest-backed grammar-growth omega proof."""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import rsi_omega


def run_proof(*, budget: int, seeds: int, cold_seeds: int) -> dict:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = rsi_omega.run(budget=budget, seeds=seeds, cold_seeds=cold_seeds)
    result = dict(result)
    result.update(
        {
            "budget": budget,
            "seeds": seeds,
            "cold_seeds": cold_seeds,
            "output": buffer.getvalue(),
        }
    )
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=4000)
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--cold-seeds", type=int, default=12)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--require-confirmed", action="store_true")
    args = parser.parse_args(argv)

    result = run_proof(budget=args.budget, seeds=args.seeds, cold_seeds=args.cold_seeds)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(result["output"], end="")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "budget",
                    "seeds",
                    "cold_seeds",
                    "confirmed",
                    "cold_solved",
                    "warm_solved",
                    "warm_source",
                    "learned_operator_count",
                )
            },
            sort_keys=True,
        )
    )
    if args.require_confirmed and not result["confirmed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
