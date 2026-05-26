"""Bounded external-world grounding for RSI research experiments.

This module grounds the research kernel in external software-maintenance
signals without executing untrusted code. It reads public GitHub issue
metadata, converts it into deterministic task records, and writes provenance
reports that downstream RSI experiments can treat as external evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_DOMAIN_REPOSITORIES: Dict[str, Tuple[str, ...]] = {
    "http_clients": ("psf/requests", "urllib3/urllib3"),
    "web_frameworks": ("pallets/flask", "django/django", "fastapi/fastapi"),
    "testing": ("pytest-dev/pytest", "hypothesisworks/hypothesis"),
    "data_science": ("numpy/numpy", "pandas-dev/pandas", "scipy/scipy"),
    "machine_learning": ("scikit-learn/scikit-learn", "pytorch/pytorch"),
    "databases": ("sqlalchemy/sqlalchemy", "redis/redis-py"),
    "distributed_systems": ("dask/dask", "ray-project/ray"),
    "developer_tools": ("pre-commit/pre-commit", "astral-sh/ruff"),
    "security": ("pyca/cryptography", "certbot/certbot"),
    "documentation": ("sphinx-doc/sphinx", "mkdocs/mkdocs"),
}

DEFAULT_REPOSITORIES: Tuple[str, ...] = tuple(
    repository
    for domain in ("http_clients", "web_frameworks", "testing")
    for repository in DEFAULT_DOMAIN_REPOSITORIES[domain]
)

DEFAULT_LABEL_QUERY = "bug"
MAX_BODY_CHARS = 1200
MAX_TITLE_CHARS = 180


@dataclass(frozen=True)
class ExternalGroundingSource:
    """One allowed external source used for grounding."""

    provider: str
    repository: str
    query: str
    max_items: int


@dataclass(frozen=True)
class GroundedTask:
    """One external issue converted into a bounded RSI task seed."""

    task_id: str
    provider: str
    repository: str
    issue_number: int
    title: str
    body_excerpt: str
    labels: Tuple[str, ...]
    state: str
    url: str
    created_at: str
    updated_at: str
    task_kind: str
    grounding_score: float
    provenance: Dict[str, str]
    safety_controls: Tuple[str, ...] = field(
        default_factory=lambda: (
            "metadata_only",
            "no_remote_code_execution",
            "bounded_issue_count",
            "bounded_body_excerpt",
            "repository_allowlist",
        )
    )


@dataclass(frozen=True)
class GroundingReport:
    """JSON-compatible external grounding report."""

    generated_at: str
    sources: Tuple[ExternalGroundingSource, ...]
    tasks: Tuple[GroundedTask, ...]
    safety_model: Tuple[str, ...]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: object, *, limit: int) -> str:
    text = "" if value is None else str(value)
    compact = " ".join(text.replace("\r", "\n").split())
    return compact[:limit]


def github_request(url: str, *, token: Optional[str] = None, timeout_s: int = 20) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "self-improving-research-kernel-grounder",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def build_issue_query_url(repository: str, *, label_query: str, limit: int) -> str:
    owner_repo = repository.strip()
    if owner_repo.count("/") != 1:
        raise ValueError(f"repository must look like owner/name: {repository!r}")
    params = {
        "state": "open",
        "labels": label_query,
        "per_page": str(max(1, min(limit, 100))),
        "sort": "updated",
        "direction": "desc",
    }
    return (
        f"https://api.github.com/repos/{owner_repo}/issues?"
        + urllib.parse.urlencode(params)
    )


def repositories_for_domains(
    domains: Sequence[str],
    explicit_repositories: Sequence[str],
) -> Tuple[str, ...]:
    """Resolve explicit repositories plus broad domain names into a stable list."""

    selected: List[str] = []
    for repository in explicit_repositories:
        if repository not in selected:
            selected.append(repository)
    requested_domains = tuple(domain.strip() for domain in domains if domain.strip())
    if "all" in requested_domains:
        requested_domains = tuple(DEFAULT_DOMAIN_REPOSITORIES)
    for domain in requested_domains:
        if domain not in DEFAULT_DOMAIN_REPOSITORIES:
            known = ", ".join(sorted([*DEFAULT_DOMAIN_REPOSITORIES, "all"]))
            raise ValueError(f"unknown domain {domain!r}; expected one of: {known}")
        for repository in DEFAULT_DOMAIN_REPOSITORIES[domain]:
            if repository not in selected:
                selected.append(repository)
    if not selected:
        selected.extend(DEFAULT_REPOSITORIES)
    return tuple(selected)


def classify_issue(labels: Sequence[str], title: str, body: str) -> str:
    joined = " ".join([*labels, title, body]).lower()
    if "test" in joined or "regression" in joined:
        return "external_regression_repair"
    if "documentation" in joined or "docs" in joined:
        return "external_documentation_repair"
    if "bug" in joined or "error" in joined or "fail" in joined:
        return "external_bug_repair"
    return "external_maintenance_task"


def score_issue(labels: Sequence[str], title: str, body: str) -> float:
    score = 1.0
    label_set = {label.lower() for label in labels}
    if "bug" in label_set:
        score += 1.5
    if "good first issue" in label_set or "help wanted" in label_set:
        score += 1.0
    if "regression" in title.lower() or "regression" in body.lower():
        score += 1.0
    if len(body) > 200:
        score += 0.5
    return round(score, 3)


def issue_to_task(repository: str, issue: Dict[str, object]) -> Optional[GroundedTask]:
    if "pull_request" in issue:
        return None
    number = int(issue.get("number", 0))
    title = normalize_text(issue.get("title", ""), limit=MAX_TITLE_CHARS)
    body_excerpt = normalize_text(issue.get("body", ""), limit=MAX_BODY_CHARS)
    labels = tuple(
        sorted(
            normalize_text(label.get("name", ""), limit=80)
            for label in issue.get("labels", [])
            if isinstance(label, dict) and label.get("name")
        )
    )
    url = str(issue.get("html_url", ""))
    created_at = str(issue.get("created_at", ""))
    updated_at = str(issue.get("updated_at", ""))
    state = str(issue.get("state", "unknown"))
    task_kind = classify_issue(labels, title, body_excerpt)
    return GroundedTask(
        task_id=f"github:{repository}#{number}",
        provider="github",
        repository=repository,
        issue_number=number,
        title=title,
        body_excerpt=body_excerpt,
        labels=labels,
        state=state,
        url=url,
        created_at=created_at,
        updated_at=updated_at,
        task_kind=task_kind,
        grounding_score=score_issue(labels, title, body_excerpt),
        provenance={
            "source_api": f"https://api.github.com/repos/{repository}/issues",
            "source_url": url,
            "retrieved_at": utc_now(),
        },
    )


def fetch_github_issue_tasks(
    repository: str,
    *,
    label_query: str = DEFAULT_LABEL_QUERY,
    limit: int = 5,
    token: Optional[str] = None,
) -> Tuple[GroundedTask, ...]:
    url = build_issue_query_url(repository, label_query=label_query, limit=limit)
    payload = github_request(url, token=token)
    if not isinstance(payload, list):
        raise RuntimeError(f"unexpected GitHub issues payload for {repository}")
    tasks: List[GroundedTask] = []
    for issue in payload:
        if not isinstance(issue, dict):
            continue
        task = issue_to_task(repository, issue)
        if task is not None:
            tasks.append(task)
    return tuple(tasks[:limit])


def build_grounding_report(
    repositories: Sequence[str],
    *,
    label_query: str = DEFAULT_LABEL_QUERY,
    limit_per_repo: int = 5,
    token: Optional[str] = None,
) -> GroundingReport:
    sources = tuple(
        ExternalGroundingSource(
            provider="github",
            repository=repository,
            query=f"state=open labels={label_query}",
            max_items=limit_per_repo,
        )
        for repository in repositories
    )
    tasks: List[GroundedTask] = []
    for source in sources:
        try:
            tasks.extend(
                fetch_github_issue_tasks(
                    source.repository,
                    label_query=label_query,
                    limit=limit_per_repo,
                    token=token,
                )
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            tasks.append(
                GroundedTask(
                    task_id=f"github:{source.repository}:grounding_error",
                    provider="github",
                    repository=source.repository,
                    issue_number=0,
                    title="External grounding fetch failed",
                    body_excerpt=f"{type(exc).__name__}: {exc}",
                    labels=("grounding_error",),
                    state="error",
                    url=f"https://github.com/{source.repository}/issues",
                    created_at="",
                    updated_at="",
                    task_kind="external_grounding_error",
                    grounding_score=0.0,
                    provenance={
                        "source_api": f"https://api.github.com/repos/{source.repository}/issues",
                        "retrieved_at": utc_now(),
                    },
                )
            )
    return GroundingReport(
        generated_at=utc_now(),
        sources=sources,
        tasks=tuple(sorted(tasks, key=lambda item: (-item.grounding_score, item.task_id))),
        safety_model=(
            "Only issue metadata is fetched.",
            "No external repository code is cloned or executed.",
            "Issue bodies are truncated before persistence.",
            "Repository count and issue count are bounded by CLI limits.",
            "Every task keeps source URL and retrieval provenance.",
        ),
    )


def write_report(output_dir: Path, report: GroundingReport) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    (output_dir / "external_grounding_tasks.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# External Grounding Report",
        "",
        f"- Generated at: {report.generated_at}",
        f"- Sources: {len(report.sources)}",
        f"- Tasks: {len(report.tasks)}",
        "",
        "## Safety Model",
        "",
        *[f"- {item}" for item in report.safety_model],
        "",
        "## Grounded Tasks",
        "",
    ]
    for task in report.tasks:
        labels = ", ".join(task.labels) if task.labels else "none"
        lines.extend(
            [
                f"### {task.task_id}",
                "",
                f"- Repository: `{task.repository}`",
                f"- Kind: `{task.task_kind}`",
                f"- Score: {task.grounding_score:.3f}",
                f"- Labels: {labels}",
                f"- URL: {task.url}",
                f"- Title: {task.title}",
                "",
            ]
        )
    (output_dir / "external_grounding_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", action="append", default=[])
    parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Ground a named domain catalog, or use 'all' for every cataloged domain.",
    )
    parser.add_argument("--label-query", default=DEFAULT_LABEL_QUERY)
    parser.add_argument("--limit-per-repo", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/external_grounding/latest"))
    parser.add_argument("--github-token-env", default="GITHUB_TOKEN")
    args = parser.parse_args(argv)
    if args.limit_per_repo < 1:
        parser.error("--limit-per-repo must be at least 1")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    repositories = repositories_for_domains(args.domain, args.repository)
    token = os.environ.get(args.github_token_env)
    report = build_grounding_report(
        repositories,
        label_query=args.label_query,
        limit_per_repo=args.limit_per_repo,
        token=token,
    )
    write_report(args.output_dir, report)
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "sources": len(report.sources),
                "tasks": len(report.tasks),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
