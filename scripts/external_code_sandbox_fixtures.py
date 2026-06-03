"""Build bounded sandbox fixtures from actual external repository code.

The fixture builder fetches small text excerpts from allowlisted public GitHub
repositories and pairs them with already-grounded issue failure excerpts. It
does not clone, import, install, or execute external code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


MAX_SOURCE_SNIPPET_CHARS = 1800
MAX_FAILURE_SNIPPET_CHARS = 2200
MAX_FETCH_BYTES = 260_000
MAX_FIELD_VALUES = 8


@dataclass(frozen=True)
class ExternalCodeSourceSpec:
    """One allowlisted external source surface for a sandbox fixture."""

    repository: str
    field_name: str
    fallback_value: str
    path_candidates: Tuple[str, ...]
    anchor_terms: Tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ExternalCodeSandboxFixture:
    """One bounded source/failure fixture derived from external repositories."""

    fixture_id: str
    source_repository: str
    source_ref: str
    source_commit_sha: str
    source_file_path: str
    source_url: str
    issue_task_id: str
    issue_url: str
    issue_title: str
    field_name: str
    field_values: Tuple[str, ...]
    source_symbols: Tuple[str, ...]
    source_snippet_path: str
    failure_excerpt_path: str
    source_snippet_sha256: str
    failure_excerpt_sha256: str
    source_snippet_line_count: int
    failure_excerpt_line_count: int
    source_line_start: int
    source_line_end: int
    safety_controls: Tuple[str, ...] = field(
        default_factory=lambda: (
            "text_fixture_only",
            "no_external_code_execution",
            "bounded_source_excerpt",
            "bounded_failure_excerpt",
            "repository_allowlist",
            "source_url_provenance",
        )
    )


EXTERNAL_CODE_SOURCE_SPECS: Tuple[ExternalCodeSourceSpec, ...] = (
    ExternalCodeSourceSpec(
        repository="psf/requests",
        field_name="external_requests_code_signals",
        fallback_value="merge_setting_none_header",
        path_candidates=("src/requests/sessions.py",),
        anchor_terms=("merge_setting", "Session", "headers", "None"),
        description="requests session merge_setting source surface paired with an inherited-header removal bug fixture.",
    ),
    ExternalCodeSourceSpec(
        repository="hypothesisworks/hypothesis",
        field_name="external_hypothesis_code_signals",
        fallback_value="pytest_patch",
        path_candidates=(
            "hypothesis/src/_hypothesis_pytestplugin.py",
            "hypothesis/src/hypothesis/extra/pytestplugin.py",
        ),
        anchor_terms=("make_patch", "unified_diff", "pytest", "patch"),
        description="Hypothesis pytest plugin source surface paired with a corrupt-patch issue fixture.",
    ),
    ExternalCodeSourceSpec(
        repository="pandas-dev/pandas",
        field_name="external_pandas_code_signals",
        fallback_value="series_map_dtype",
        path_candidates=("pandas/core/series.py",),
        anchor_terms=("map", "_map_values", "Series", "dtype"),
        description="pandas Series source surface paired with a dynamic dtype issue fixture.",
    ),
    ExternalCodeSourceSpec(
        repository="dask/dask",
        field_name="external_dask_code_signals",
        fallback_value="array_cumsum",
        path_candidates=("dask/array/reductions.py", "dask/array/core.py"),
        anchor_terms=("cumsum", "cumreduction", "array", "chunk"),
        description="dask array source surface paired with a cumsum numerical-divergence issue fixture.",
    ),
)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def normalize_fixture_token(value: object, *, fallback: str) -> str:
    text = str(value or "").lower()
    compact = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not compact:
        compact = fallback
    if compact and compact[0].isdigit():
        compact = f"x_{compact}"
    return compact[:48]


def fixture_slug(repository: str) -> str:
    return normalize_fixture_token(repository.replace("/", "_"), fallback="external_repo")


def github_json_request(url: str, *, token: Optional[str] = None, timeout_s: int = 20) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "self-improving-research-kernel-code-fixture",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def read_url_text(
    url: str,
    *,
    token: Optional[str] = None,
    timeout_s: int = 20,
    max_bytes: int = MAX_FETCH_BYTES,
) -> str:
    headers = {"User-Agent": "self-improving-research-kernel-code-fixture"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        data = response.read(max_bytes + 1)
    return data[:max_bytes].decode("utf-8", errors="replace")


def repository_default_branch(repository: str, *, token: Optional[str]) -> str:
    payload = github_json_request(f"https://api.github.com/repos/{repository}", token=token)
    if isinstance(payload, dict) and payload.get("default_branch"):
        return str(payload["default_branch"])
    return "main"


def github_contents_url(repository: str, path: str, ref: str) -> str:
    quoted_path = urllib.parse.quote(path.strip("/"), safe="/")
    query = urllib.parse.urlencode({"ref": ref})
    return f"https://api.github.com/repos/{repository}/contents/{quoted_path}?{query}"


def github_latest_file_commit(repository: str, path: str, ref: str, *, token: Optional[str]) -> str:
    quoted_path = urllib.parse.quote(path.strip("/"), safe="/")
    query = urllib.parse.urlencode({"path": path, "sha": ref, "per_page": 1})
    payload = github_json_request(
        f"https://api.github.com/repos/{repository}/commits?{query}",
        token=token,
    )
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        sha = str(payload[0].get("sha", "") or "")
        if sha:
            return sha
    return ref


def fetch_external_source(
    spec: ExternalCodeSourceSpec,
    *,
    token: Optional[str],
) -> Tuple[str, str, str, str, str]:
    """Return ``(ref, commit_sha, path, source_url, text)`` for the first existing path."""

    ref = repository_default_branch(spec.repository, token=token)
    errors: List[str] = []
    for path in spec.path_candidates:
        try:
            payload = github_json_request(
                github_contents_url(spec.repository, path, ref),
                token=token,
            )
            if not isinstance(payload, dict) or payload.get("type") != "file":
                errors.append(f"{path}: not a file")
                continue
            download_url = str(payload.get("download_url") or "")
            if not download_url:
                errors.append(f"{path}: missing download_url")
                continue
            try:
                commit_sha = github_latest_file_commit(spec.repository, path, ref, token=token)
            except Exception:
                commit_sha = str(payload.get("sha", "") or ref)
            return ref, commit_sha, path, download_url, read_url_text(download_url, token=token)
        except Exception as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
    joined = "; ".join(errors) if errors else "no path candidates"
    raise RuntimeError(f"could not fetch external source for {spec.repository}: {joined}")


def load_grounding_tasks(path: Path) -> Tuple[Dict[str, object], ...]:
    payload = read_json(path, {})
    tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
    return tuple(task for task in tasks if isinstance(task, dict))


def select_grounding_task(
    tasks: Sequence[Dict[str, object]],
    repository: str,
) -> Dict[str, object]:
    matches = [
        task
        for task in tasks
        if task.get("repository") == repository
        and task.get("task_kind") != "external_grounding_error"
    ]
    if not matches:
        return {
            "repository": repository,
            "task_id": f"github:{repository}:fallback",
            "title": "Fallback external code sandbox fixture",
            "body_excerpt": "",
            "labels": (),
            "task_kind": "external_code_fixture_fallback",
            "url": f"https://github.com/{repository}/issues",
            "grounding_score": 0.0,
        }
    return max(
        matches,
        key=lambda task: (
            float(task.get("grounding_score", 0.0) or 0.0),
            str(task.get("task_id", "")),
        ),
    )


def extract_fenced_blocks(text: str, *, max_chars: int = MAX_FAILURE_SNIPPET_CHARS) -> Tuple[str, ...]:
    blocks: List[str] = []
    for match in re.finditer(r"```(?P<lang>[A-Za-z0-9_+-]*)\s*(?P<body>.*?)```", text, flags=re.DOTALL):
        lang = match.group("lang").strip()
        body = match.group("body").strip()
        if not body:
            continue
        header = f"[{lang}]\n" if lang else ""
        blocks.append((header + body)[:max_chars])
        if sum(len(block) for block in blocks) >= max_chars:
            break
    return tuple(blocks)


def excerpt_around_failure_terms(text: str, *, max_chars: int) -> str:
    lower = text.lower()
    anchors = ("traceback", "fail", "error", "assert", "exception", "pytest", "expected", "actual")
    indexes = [lower.find(anchor) for anchor in anchors if lower.find(anchor) >= 0]
    if not indexes:
        return text[:max_chars]
    center = min(indexes)
    start = max(0, center - max_chars // 3)
    end = min(len(text), start + max_chars)
    return text[start:end].strip()


def extract_failure_excerpt(task: Dict[str, object], *, max_chars: int) -> str:
    body = str(task.get("body_excerpt", "") or "")
    blocks = extract_fenced_blocks(body, max_chars=max_chars)
    if blocks:
        joined = "\n\n---\n\n".join(blocks)
        return joined[:max_chars]
    return excerpt_around_failure_terms(body, max_chars=max_chars)


def line_number_at_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def bounded_source_window(
    text: str,
    anchor_terms: Sequence[str],
    *,
    max_chars: int,
) -> Tuple[str, int, int]:
    lower = text.lower()
    center = 0
    for term in anchor_terms:
        index = lower.find(term.lower())
        if index >= 0:
            center = index
            break
    start = max(0, center - max_chars // 3)
    if start:
        start = text.rfind("\n", 0, start) + 1
    end = min(len(text), start + max_chars)
    newline_end = text.find("\n", end)
    if 0 <= newline_end <= end + 200:
        end = newline_end
    snippet = text[start:end].strip("\n")
    return snippet, line_number_at_offset(text, start), line_number_at_offset(text, end)


def extract_source_symbols(snippet: str, source_path: str) -> Tuple[str, ...]:
    values: List[str] = []
    for raw in re.findall(r"^\s*(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", snippet, flags=re.MULTILINE):
        token = normalize_fixture_token(raw, fallback="")
        if token and token not in values:
            values.append(token)
    for raw in Path(source_path).with_suffix("").parts[-3:]:
        token = normalize_fixture_token(raw, fallback="")
        if token and token not in values:
            values.append(token)
    return tuple(values[:MAX_FIELD_VALUES])


def extract_text_terms(text: str, *, fallback: str, limit: int = 5) -> Tuple[str, ...]:
    stopwords = {
        "actual",
        "because",
        "expected",
        "false",
        "issue",
        "latest",
        "output",
        "result",
        "should",
        "source",
        "there",
        "this",
        "true",
        "when",
        "with",
    }
    values: List[str] = []
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text.lower()):
        token = normalize_fixture_token(raw, fallback=fallback)
        if token in stopwords or token in values:
            continue
        values.append(token)
        if len(values) >= limit:
            break
    return tuple(values or (fallback,))


def fixture_field_values(
    spec: ExternalCodeSourceSpec,
    task: Dict[str, object],
    source_symbols: Sequence[str],
    failure_excerpt: str,
) -> Tuple[str, ...]:
    fallback = normalize_fixture_token(spec.fallback_value, fallback="external_code")
    values: List[str] = [fallback]
    for source in (
        source_symbols,
        spec.anchor_terms,
        task.get("labels", ()),
        extract_text_terms(str(task.get("title", "")), fallback=fallback),
        extract_text_terms(failure_excerpt, fallback=fallback),
    ):
        for raw in source:
            token = normalize_fixture_token(raw, fallback="")
            if token and token not in values:
                values.append(token)
            if len(values) >= MAX_FIELD_VALUES:
                return tuple(values)
    return tuple(values)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_text_fixture(path: Path, *, header: Sequence[str], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([*header, "", body]).rstrip() + "\n", encoding="utf-8")


def build_external_code_sandbox_report(
    repositories: Sequence[str],
    *,
    grounding_path: Path,
    output_dir: Path,
    token: Optional[str] = None,
    max_source_chars: int = MAX_SOURCE_SNIPPET_CHARS,
    max_failure_chars: int = MAX_FAILURE_SNIPPET_CHARS,
) -> Tuple[ExternalCodeSandboxFixture, ...]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_repositories = set(repositories)
    specs = tuple(
        spec
        for spec in EXTERNAL_CODE_SOURCE_SPECS
        if not selected_repositories or spec.repository in selected_repositories
    )
    tasks = load_grounding_tasks(grounding_path)
    fixtures: List[ExternalCodeSandboxFixture] = []

    for spec in specs:
        task = select_grounding_task(tasks, spec.repository)
        ref, commit_sha, source_path, source_url, source_text = fetch_external_source(spec, token=token)
        source_snippet, line_start, line_end = bounded_source_window(
            source_text,
            spec.anchor_terms,
            max_chars=max_source_chars,
        )
        failure_excerpt = extract_failure_excerpt(task, max_chars=max_failure_chars)
        source_symbols = extract_source_symbols(source_snippet, source_path)
        field_values = fixture_field_values(spec, task, source_symbols, failure_excerpt)
        slug = fixture_slug(spec.repository)
        source_relative = f"snippets/{slug}_source.txt"
        failure_relative = f"failures/{slug}_failure.txt"
        source_fixture_path = output_dir / source_relative
        failure_fixture_path = output_dir / failure_relative
        write_text_fixture(
            source_fixture_path,
            header=(
                f"Repository: {spec.repository}",
                f"Source: {source_url}",
                f"Ref: {ref}",
                f"Commit: {commit_sha}",
                f"Path: {source_path}",
                f"Lines: {line_start}-{line_end}",
                "Safety: text fixture only; not imported or executed.",
            ),
            body=source_snippet,
        )
        write_text_fixture(
            failure_fixture_path,
            header=(
                f"Repository: {spec.repository}",
                f"Issue: {task.get('url', '')}",
                f"Task: {task.get('task_id', '')}",
                "Safety: bounded failure excerpt only; not executed.",
            ),
            body=failure_excerpt,
        )
        fixtures.append(
            ExternalCodeSandboxFixture(
                fixture_id=f"external-code:{spec.repository}",
                source_repository=spec.repository,
                source_ref=ref,
                source_commit_sha=commit_sha,
                source_file_path=source_path,
                source_url=source_url,
                issue_task_id=str(task.get("task_id", "")),
                issue_url=str(task.get("url", "")),
                issue_title=str(task.get("title", "")),
                field_name=spec.field_name,
                field_values=field_values,
                source_symbols=source_symbols,
                source_snippet_path=source_relative,
                failure_excerpt_path=failure_relative,
                source_snippet_sha256=sha256_text(source_snippet),
                failure_excerpt_sha256=sha256_text(failure_excerpt),
                source_snippet_line_count=len(source_snippet.splitlines()),
                failure_excerpt_line_count=len(failure_excerpt.splitlines()),
                source_line_start=line_start,
                source_line_end=line_end,
            )
        )

    payload = {
        "generated_at": utc_now(),
        "fixture_kind": "external_code_sandbox",
        "grounding_path": str(grounding_path),
        "safety_model": [
            "External code is fetched only as bounded text excerpts.",
            "No external repository code is cloned, installed, imported, or executed.",
            "Failure excerpts come from bounded issue metadata already captured by the grounding step.",
            "Every fixture records source URL, branch ref, file commit, path, hashes, and safety controls.",
            "Downstream experiments execute only local sandbox fixture tests.",
        ],
        "fixtures": [asdict(fixture) for fixture in fixtures],
    }
    write_json(output_dir / "external_code_sandbox_fixtures.json", payload)
    write_markdown_report(output_dir / "external_code_sandbox_report.md", fixtures)
    return tuple(fixtures)


def write_markdown_report(path: Path, fixtures: Sequence[ExternalCodeSandboxFixture]) -> None:
    lines = [
        "# External Code Sandbox Fixtures",
        "",
        "These fixtures transfer bounded source excerpts and issue failure excerpts from real external repositories into text-only sandbox artifacts. No third-party code is executed.",
        "",
        "| Repository | Source Path | Issue | Field | Values | Source Lines |",
        "|---|---|---|---|---|---:|",
    ]
    for fixture in fixtures:
        values = ", ".join(fixture.field_values[:5])
        lines.append(
            f"| `{fixture.source_repository}` | `{fixture.source_file_path}` | "
            f"[issue]({fixture.issue_url}) | `{fixture.field_name}` | `{values}` | "
            f"{fixture.source_line_start}-{fixture.source_line_end} |"
        )
    lines.extend(
        [
            "",
            "## Safety Controls",
            "",
            "- Source snippets are stored as `.txt` fixture artifacts.",
            "- The builder never imports, installs, or executes external repository code.",
            "- Excerpts are bounded by CLI limits and recorded with SHA-256 hashes.",
            "- Downstream RSI experiments consume only local schema fields and provenance metadata.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def repository_names(specs: Iterable[ExternalCodeSourceSpec]) -> Tuple[str, ...]:
    return tuple(spec.repository for spec in specs)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        action="append",
        default=[],
        help="Allowlisted owner/repo to include. Defaults to all code fixture repositories.",
    )
    parser.add_argument(
        "--grounding-path",
        type=Path,
        default=Path("reports/external_grounding/external_transfer/latest/external_grounding_tasks.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/external_code_fixtures/latest"),
    )
    parser.add_argument("--max-source-chars", type=int, default=MAX_SOURCE_SNIPPET_CHARS)
    parser.add_argument("--max-failure-chars", type=int, default=MAX_FAILURE_SNIPPET_CHARS)
    args = parser.parse_args(argv)

    allowed = set(repository_names(EXTERNAL_CODE_SOURCE_SPECS))
    repositories = tuple(args.repository or sorted(allowed))
    unknown = sorted(set(repositories) - allowed)
    if unknown:
        raise SystemExit(f"unknown repository for external code sandbox fixture: {', '.join(unknown)}")

    fixtures = build_external_code_sandbox_report(
        repositories,
        grounding_path=args.grounding_path,
        output_dir=args.output_dir,
        token=os.environ.get("GITHUB_TOKEN"),
        max_source_chars=max(500, args.max_source_chars),
        max_failure_chars=max(200, args.max_failure_chars),
    )
    print(f"wrote {len(fixtures)} external code sandbox fixtures to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
