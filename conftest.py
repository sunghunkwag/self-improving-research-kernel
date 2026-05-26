"""Repository-wide pytest import setup for the integrated OMEGA-THDSE tree."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
IMPORT_ROOTS = (
    ROOT,
    ROOT / "thdse",
    ROOT / "thdse" / "src",
    ROOT / "Cognitive-Core-Engine-Test",
)

for path in reversed(IMPORT_ROOTS):
    text = str(path)
    if path.exists() and text not in sys.path:
        sys.path.insert(0, text)
