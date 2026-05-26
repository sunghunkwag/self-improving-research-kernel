"""Bridge that connects local Python corpus evidence into OMEGA-THDSE."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from shared.local_corpus import LocalCorpusIndex, load_inventory, scan_paths


class LocalCorpusBridge:
    """Build and persist a static index for arbitrary local Python files."""

    def __init__(self, inventory_path: str | Path):
        self.inventory_path = Path(inventory_path)
        self.index: Optional[LocalCorpusIndex] = None

    def connect(self) -> LocalCorpusIndex:
        paths = load_inventory(self.inventory_path)
        self.index = scan_paths(paths)
        return self.index

    def write_outputs(self, output_dir: str | Path) -> Dict[str, str]:
        if self.index is None:
            self.connect()
        assert self.index is not None
        target = Path(output_dir)
        json_path = target / "omega_local_python_corpus_index.json"
        markdown_path = target / "omega_local_python_corpus_report.md"
        self.index.write_json(json_path)
        self.index.write_markdown(markdown_path)
        return {"json": str(json_path), "markdown": str(markdown_path)}
