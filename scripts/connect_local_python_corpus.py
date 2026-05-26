"""Connect a local Python inventory to OMEGA-THDSE as static evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "thdse", ROOT / "thdse" / "src", ROOT / "Cognitive-Core-Engine-Test"):
    text = str(candidate)
    if candidate.exists() and text not in sys.path:
        sys.path.insert(0, text)

from bridges.local_corpus_bridge import LocalCorpusBridge  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Connect local Python files into an OMEGA-THDSE static corpus index.")
    parser.add_argument("--inventory", required=True, help="Text file containing one Python path per line.")
    parser.add_argument("--output-dir", default=str(ROOT / "reports"), help="Directory for JSON and Markdown reports.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bridge = LocalCorpusBridge(args.inventory)
    index = bridge.connect()
    outputs = bridge.write_outputs(args.output_dir)
    payload = {
        "summary": index.to_dict()["summary"],
        "outputs": outputs,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        summary = index.summary
        print(f"Connected files: {summary.file_count}")
        print(f"Syntax OK: {summary.syntax_ok_count}")
        print(f"Syntax errors: {summary.syntax_error_count}")
        print(f"Unique SHA-256 contents: {summary.unique_sha256_count}")
        print(f"Static import edges: {summary.import_edge_count}")
        print(f"JSON report: {outputs['json']}")
        print(f"Markdown report: {outputs['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
