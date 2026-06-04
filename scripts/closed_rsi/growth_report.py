"""Render an honest closed-loop growth report from persisted RSI records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _records_from_state(state: Mapping[str, object]) -> List[Mapping[str, object]]:
    records: List[Mapping[str, object]] = []
    for bucket in ("accepted", "rejected", "quarantine_exploration"):
        for item in state.get(bucket, []):
            if isinstance(item, Mapping):
                records.append(item)
    return records


def build_growth_report(summary: Mapping[str, object], state: Mapping[str, object]) -> Dict[str, object]:
    """Build JSON-compatible growth accounting from loop summary and state."""

    generations = [
        dict(item)
        for item in summary.get("generations", [])
        if isinstance(item, Mapping)
    ]
    records = _records_from_state(state)
    accepted_records = [record for record in records if record.get("accepted") is True]
    families = sorted(
        {
            str(record.get("capability_delta", {}).get("family", ""))
            for record in accepted_records
            if isinstance(record.get("capability_delta"), Mapping)
            and record.get("capability_delta", {}).get("family")
        }
        | {
            family
            for generation in generations
            for family in generation.get("capability_families", [])
            if family
        }
    )
    totals = {
        "generated_candidates": sum(int(item.get("generated_candidates", 0) or 0) for item in generations),
        "attempted_candidates": sum(int(item.get("attempted_candidates", 0) or 0) for item in generations),
        "compiled_candidates": sum(int(item.get("compiled_candidates", 0) or 0) for item in generations),
        "pre_full_gate_passed_candidates": sum(
            int(item.get("pre_full_gate_passed_candidates", 0) or 0) for item in generations
        ),
        "full_suite_passed_candidates": sum(
            int(item.get("full_suite_passed_candidates", 0) or 0) for item in generations
        ),
        "solved_new_tasks": sum(int(item.get("solved_new_tasks", 0) or 0) for item in generations),
        "hidden_transfer": sum(int(item.get("hidden_transfer", 0) or 0) for item in generations),
        "operator_reuse": sum(int(item.get("operator_reuse", 0) or 0) for item in generations),
    }
    plateau_reason = str(summary.get("plateau_reason", "") or "unknown")
    if generations:
        last = generations[-1]
        plateau_detail = str(last.get("stop_reason", "") or plateau_reason)
    else:
        plateau_detail = "no_generation_records"
    return {
        "dry_run": bool(summary.get("dry_run", False)),
        "full_test_command": str(summary.get("full_test_command", "python -m pytest -q")),
        "full_test_required": bool(summary.get("full_test_required", True)),
        "full_test_exit_code": summary.get("full_test_exit_code"),
        "active_generation": int(summary.get("active_generation", 0) or 0),
        "active_base": str(summary.get("active_base", "initial")),
        "plateau_reason": plateau_reason,
        "plateau_detail": plateau_detail,
        "generations": generations,
        "totals": totals,
        "capability_families_touched": families,
        "accepted_count": len(accepted_records),
        "rejected_count": len([record for record in records if record.get("accepted") is False]),
        "quarantine_count": len(
            [
                record
                for record in state.get("quarantine_exploration", [])
                if isinstance(record, Mapping)
            ]
        ),
    }


def render_growth_markdown(report: Mapping[str, object]) -> str:
    """Render the growth report as Markdown without claiming unbounded progress."""

    totals = report.get("totals", {})
    generations = report.get("generations", [])
    lines = [
        "# Closed RSI Growth Report",
        "",
        "This report is generated from `.omega_rsi_runs` records produced by an actual closed-loop run. "
        "It does not claim unbounded self-improvement.",
        "",
        "## Summary",
        "",
        f"- Active generation: {report.get('active_generation')}",
        f"- Active base: `{report.get('active_base')}`",
        f"- Full test command: `{report.get('full_test_command')}`",
        f"- Full test required: {report.get('full_test_required')}",
        f"- Final full test exit code: {report.get('full_test_exit_code')}",
        f"- Plateau reason: `{report.get('plateau_reason')}`",
        f"- Plateau detail: `{report.get('plateau_detail')}`",
        "",
        "## Candidate Accounting",
        "",
        "| Generated | Attempted | Compiled | Pre-full Gates Passed | Full-suite Passed | Solved Tasks | Hidden Transfer | Operator Reuse |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| {totals.get('generated_candidates', 0)} | {totals.get('attempted_candidates', 0)} | "
            f"{totals.get('compiled_candidates', 0)} | {totals.get('pre_full_gate_passed_candidates', 0)} | "
            f"{totals.get('full_suite_passed_candidates', 0)} | {totals.get('solved_new_tasks', 0)} | "
            f"{totals.get('hidden_transfer', 0)} | {totals.get('operator_reuse', 0)} |"
        ),
        "",
        "## Per Generation",
        "",
        "| Generation | Generated | Attempted | Compiled | Pre-full Passed | Full-suite Passed | Promoted | Stop Reason | Capabilities |",
        "|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    if generations:
        for generation in generations:
            capabilities = ", ".join(generation.get("capability_families", []) or [])
            promoted = ", ".join(generation.get("accepted_candidates", []) or [])
            lines.append(
                f"| {generation.get('generation')} | {generation.get('generated_candidates', 0)} | "
                f"{generation.get('attempted_candidates', 0)} | {generation.get('compiled_candidates', 0)} | "
                f"{generation.get('pre_full_gate_passed_candidates', 0)} | "
                f"{generation.get('full_suite_passed_candidates', 0)} | "
                f"`{promoted}` | `{generation.get('stop_reason', '')}` | `{capabilities}` |"
            )
    else:
        lines.append("| 0 | 0 | 0 | 0 | 0 | 0 | `` | `no_generation_records` | `` |")

    capabilities = report.get("capability_families_touched", [])
    lines.extend(
        [
            "",
            "## Capability Movement",
            "",
            (
                "Touched capability families: "
                + (", ".join(f"`{family}`" for family in capabilities) if capabilities else "none recorded")
            ),
            "",
            "## Plateau Analysis",
            "",
            f"The run stopped at `{report.get('plateau_reason')}` / `{report.get('plateau_detail')}`. "
            "This is the reported ceiling for this run configuration, not evidence of unlimited growth.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=Path(".omega_rsi_runs"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    summary = read_json(args.state_dir / "closed_rsi_summary.json", {})
    state = read_json(args.state_dir / "closed_rsi_state.json", {})
    report = build_growth_report(summary, state)
    markdown = render_growth_markdown(report)

    output = args.output or args.state_dir / "closed_rsi_growth_report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown + "\n", encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "plateau_reason": report["plateau_reason"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
