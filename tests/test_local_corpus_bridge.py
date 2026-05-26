from __future__ import annotations

from pathlib import Path

from bridges.local_corpus_bridge import LocalCorpusBridge
from shared.local_corpus import scan_paths


def test_scan_paths_connects_valid_and_invalid_files(tmp_path: Path):
    valid = tmp_path / "valid_agent.py"
    invalid = tmp_path / "invalid_rsi.py"
    valid.write_text("import ast\nclass Agent:\n    pass\ndef plan():\n    return ast.parse('x=1')\n", encoding="utf-8")
    invalid.write_text("def broken(:\n    pass\n", encoding="utf-8")

    index = scan_paths([valid, invalid])

    assert index.summary.file_count == 2
    assert index.summary.syntax_ok_count == 1
    assert index.summary.syntax_error_count == 1
    assert index.summary.import_edge_count == 1
    assert "planning_memory_agent" in index.summary.feature_counts
    assert any(record.syntax_error for record in index.records)


def test_local_corpus_bridge_writes_outputs(tmp_path: Path):
    source = tmp_path / "source.py"
    inventory = tmp_path / "inventory.txt"
    output_dir = tmp_path / "out"
    source.write_text("import json\n\ndef benchmark():\n    return json.dumps({'ok': True})\n", encoding="utf-8")
    inventory.write_text(str(source), encoding="utf-8")

    bridge = LocalCorpusBridge(inventory)
    index = bridge.connect()
    outputs = bridge.write_outputs(output_dir)

    assert index.summary.file_count == 1
    assert Path(outputs["json"]).is_file()
    assert Path(outputs["markdown"]).is_file()
