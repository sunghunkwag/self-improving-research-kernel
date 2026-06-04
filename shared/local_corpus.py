"""Static local Python corpus indexing for OMEGA-THDSE.

This module connects arbitrary local Python files as evidence, not as live
imports.  It reads files, hashes them, parses AST when possible, extracts
symbols and import edges, and assigns capability markers that downstream
bridges can reason over safely.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


FEATURE_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "self_improvement": re.compile(
        r"\b(rsi|recursive self[-_ ]?improvement|self[-_ ]?modify|autopatch|rollback|mutation|mutator|candidate_search)\b",
        re.IGNORECASE,
    ),
    "agi_asi_claim": re.compile(
        r"\b(agi|asi|superintelligence|singularity|intelligence explosion|human[-_ ]level)\b",
        re.IGNORECASE,
    ),
    "neural_learning": re.compile(
        r"\b(torch|tensorflow|keras|jax|numpy|neural|maml|gradient|optimizer|transformer|attention|nas|embedding)\b",
        re.IGNORECASE,
    ),
    "symbolic_synthesis": re.compile(
        r"\b(ast\.|program synthesis|symbolic regression|dsl|genome|grammar|smt|z3|evolution|primitive|synthes)\b",
        re.IGNORECASE,
    ),
    "planning_memory_agent": re.compile(
        r"\b(agent|planner|planning|memory|episodic|world_model|goal|tool|orchestrator|swarm|policy)\b",
        re.IGNORECASE,
    ),
    "validation": re.compile(
        r"\b(benchmark|eval|validation|holdout|stress|pytest|arc[-_ ]?agi|humaneval|scorecard|anti[-_ ]?cheat|falsif)\b",
        re.IGNORECASE,
    ),
    "safety_governance": re.compile(
        r"\b(governance|sandbox|safe_exec|safe_eval|critic|guard|rollback|blocked|unsafe|wireheading|bounded)\b",
        re.IGNORECASE,
    ),
    "external_action": re.compile(
        r"\b(subprocess|os\.system|powershell|cmd\.exe|selenium|pyautogui|requests\.get|urllib\.request|socket)\b",
        re.IGNORECASE,
    ),
    "explicit_limit": re.compile(
        r"\b(no external llm|no llm|zero llms|dependency[- ]free|offline|not agi|not human-level|not.*singularity|not.*superintelligence)\b",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class LocalPythonFileRecord:
    """One local Python file represented as static corpus evidence."""

    path: str
    sha256: str
    size_bytes: int
    line_count: int
    syntax_ok: bool
    syntax_error: str = ""
    imports: Tuple[str, ...] = ()
    definitions: Tuple[str, ...] = ()
    feature_flags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportEdge:
    """A static import relationship between a file and an imported module."""

    source_path: str
    imported_module: str


@dataclass(frozen=True)
class LocalCorpusSummary:
    """Aggregate view of the connected local Python corpus."""

    file_count: int
    syntax_ok_count: int
    syntax_error_count: int
    unique_sha256_count: int
    duplicate_file_instances: int
    feature_counts: Dict[str, int]
    import_edge_count: int
    definition_count: int


@dataclass(frozen=True)
class LocalCorpusIndex:
    """Full static connection result for arbitrary local Python files."""

    summary: LocalCorpusSummary
    records: Tuple[LocalPythonFileRecord, ...]
    import_edges: Tuple[ImportEdge, ...]
    duplicate_groups: Tuple[Tuple[str, ...], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        return {
            "summary": asdict(self.summary),
            "records": [asdict(record) for record in self.records],
            "import_edges": [asdict(edge) for edge in self.import_edges],
            "duplicate_groups": [list(group) for group in self.duplicate_groups],
        }

    def records_with_feature(self, feature: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records carrying a static feature flag."""

        if not isinstance(feature, str) or not feature:
            raise ValueError("feature must be a non-empty string")
        return tuple(record for record in self.records if feature in record.feature_flags)

    def records_importing(self, module_name: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records that statically import ``module_name``."""

        if not isinstance(module_name, str) or not module_name:
            raise ValueError("module_name must be a non-empty string")
        return tuple(record for record in self.records if module_name in record.imports)

    def records_with_definition(self, definition: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records whose ``definitions`` contain ``definition``."""

        if not isinstance(definition, str) or not definition:
            raise ValueError("definition must be a non-empty string")
        return tuple(record for record in self.records if definition in record.definitions)

    def records_matching_definitions(self, definition: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records whose ``definitions`` contain ``definition``."""

        if not isinstance(definition, str) or not definition:
            raise ValueError("definition must be a non-empty string")
        return tuple(record for record in self.records if definition in record.definitions)

    def records_matching_feature_flags(self, feature: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records whose ``feature_flags`` contain ``feature``."""

        if not isinstance(feature, str) or not feature:
            raise ValueError("feature must be a non-empty string")
        return tuple(record for record in self.records if feature in record.feature_flags)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def write_markdown(self, path: Path, *, top_n: int = 25) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Local Python Corpus Connection Report",
            "",
            f"- Files connected: {self.summary.file_count}",
            f"- Syntax OK: {self.summary.syntax_ok_count}",
            f"- Syntax errors: {self.summary.syntax_error_count}",
            f"- Unique file contents: {self.summary.unique_sha256_count}",
            f"- Duplicate file instances: {self.summary.duplicate_file_instances}",
            f"- Static import edges: {self.summary.import_edge_count}",
            f"- Top-level definitions: {self.summary.definition_count}",
            "",
            "## Feature Counts",
        ]
        for name, count in sorted(self.summary.feature_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {name}: {count}")
        lines.extend(["", "## Highest-Signal Files"])
        ranked = sorted(
            self.records,
            key=lambda record: (len(record.feature_flags), record.syntax_ok, record.size_bytes),
            reverse=True,
        )
        for record in ranked[:top_n]:
            flags = ", ".join(record.feature_flags) if record.feature_flags else "none"
            lines.append(f"- `{record.path}` ({record.line_count} lines, flags: {flags})")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_inventory(path: Path) -> List[Path]:
    """Load a text inventory containing one Python file path per line."""

    rows = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    paths: List[Path] = []
    seen: set[str] = set()
    for row in rows:
        inventory_path = _normalize_inventory_line(row)
        if inventory_path is None:
            continue
        key = str(inventory_path)
        if key in seen:
            continue
        seen.add(key)
        paths.append(inventory_path)
    return paths


def _normalize_inventory_line(row: str) -> Optional[Path]:
    """Normalize one inventory row into a Python path, or skip it."""

    candidate = row.strip()
    if not candidate or candidate.startswith("#"):
        return None
    if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in {"'", '"'}:
        candidate = candidate[1:-1].strip()
    if not candidate.lower().endswith(".py"):
        return None
    return Path(candidate).expanduser()


def scan_paths(paths: Iterable[Path], *, feature_scan_limit: int = 500_000) -> LocalCorpusIndex:
    """Connect all provided Python files into one static corpus index."""

    records: List[LocalPythonFileRecord] = []
    import_edges: List[ImportEdge] = []
    by_hash: Dict[str, List[str]] = {}
    feature_counts: Dict[str, int] = {name: 0 for name in FEATURE_PATTERNS}
    definition_count = 0

    for path in sorted({Path(p) for p in paths}, key=lambda item: str(item).lower()):
        record, edges = scan_file(path, feature_scan_limit=feature_scan_limit)
        records.append(record)
        import_edges.extend(edges)
        by_hash.setdefault(record.sha256, []).append(record.path)
        definition_count += len(record.definitions)
        for flag in record.feature_flags:
            feature_counts[flag] = feature_counts.get(flag, 0) + 1

    duplicate_groups = tuple(
        tuple(group) for group in by_hash.values() if len(group) > 1
    )
    duplicate_file_instances = sum(len(group) for group in duplicate_groups)
    syntax_ok_count = sum(1 for record in records if record.syntax_ok)
    summary = LocalCorpusSummary(
        file_count=len(records),
        syntax_ok_count=syntax_ok_count,
        syntax_error_count=len(records) - syntax_ok_count,
        unique_sha256_count=len(by_hash),
        duplicate_file_instances=duplicate_file_instances,
        feature_counts={key: value for key, value in feature_counts.items() if value},
        import_edge_count=len(import_edges),
        definition_count=definition_count,
    )
    return LocalCorpusIndex(
        summary=summary,
        records=tuple(records),
        import_edges=tuple(import_edges),
        duplicate_groups=duplicate_groups,
    )


def scan_file(path: Path, *, feature_scan_limit: int = 500_000) -> Tuple[LocalPythonFileRecord, List[ImportEdge]]:
    """Scan one Python file without importing or executing it."""

    try:
        data = path.read_bytes()
    except OSError as exc:
        return (
            LocalPythonFileRecord(
                path=str(path),
                sha256="unreadable",
                size_bytes=0,
                line_count=0,
                syntax_ok=False,
                syntax_error=f"{type(exc).__name__}: {exc}",
            ),
            [],
        )

    text = data.decode("utf-8", errors="ignore")
    digest = hashlib.sha256(data).hexdigest()
    scan_text = f"{path}\n{text[:feature_scan_limit]}"
    feature_flags = tuple(
        name for name, pattern in FEATURE_PATTERNS.items() if pattern.search(scan_text)
    )
    imports: List[str] = []
    definitions: List[str] = []
    syntax_error = ""
    syntax_ok = False

    try:
        tree = ast.parse(text)
        syntax_ok = True
        imports = _extract_imports(tree)
        definitions = _extract_definitions(tree)
    except SyntaxError as exc:
        syntax_error = f"SyntaxError: {exc.msg} at line {exc.lineno}"
    except ValueError as exc:
        syntax_error = f"ValueError: {exc}"

    record = LocalPythonFileRecord(
        path=str(path),
        sha256=digest,
        size_bytes=len(data),
        line_count=text.count("\n") + (1 if text else 0),
        syntax_ok=syntax_ok,
        syntax_error=syntax_error,
        imports=tuple(sorted(set(imports))),
        definitions=tuple(definitions),
        feature_flags=feature_flags,
    )
    edges = [ImportEdge(source_path=str(path), imported_module=name) for name in record.imports]
    return record, edges


def _extract_imports(tree: ast.AST) -> List[str]:
    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    return imports


def _extract_definitions(tree: ast.AST) -> List[str]:
    definitions: List[str] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.ClassDef):
            definitions.append(f"class:{node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.append(f"function:{node.name}")
    return definitions
