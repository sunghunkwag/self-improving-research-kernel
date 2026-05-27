from scripts.external_world_grounding import (
    build_grounding_report,
    build_issue_query_url,
    classify_issue,
    issue_to_task,
    normalize_text,
    repositories_for_domains,
    score_issue,
)


SAMPLE_ISSUE = {
    "number": 123,
    "title": "Regression when parsing retry headers",
    "body": "The latest release fails when retry headers contain an empty value.",
    "labels": [{"name": "bug"}, {"name": "regression"}],
    "state": "open",
    "html_url": "https://github.com/example/project/issues/123",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def test_normalize_text_compacts_and_bounds_text():
    assert normalize_text("a\n  b\r\nc", limit=4) == "a b "


def test_build_issue_query_url_bounds_limit_and_encodes_label():
    url = build_issue_query_url("owner/repo", label_query="good first issue", limit=999)

    assert "owner/repo/issues" in url
    assert "per_page=100" in url
    assert "labels=good+first+issue" in url


def test_issue_to_task_preserves_provenance_and_safety_controls():
    task = issue_to_task("example/project", SAMPLE_ISSUE)

    assert getattr(task, "repository", "") == "example/project"
    assert task.task_id == "github:example/project#123"
    assert task.task_kind == "external_regression_repair"
    assert "no_remote_code_execution" in task.safety_controls
    assert task.provenance["source_url"] == SAMPLE_ISSUE["html_url"]


def test_issue_to_task_skips_pull_requests():
    issue = dict(SAMPLE_ISSUE)
    issue["pull_request"] = {"url": "https://api.github.com/pr"}

    assert issue_to_task("example/project", issue) is None


def test_classify_issue_prefers_regression_repair():
    assert (
        classify_issue(("bug",), "Regression in parser", "fails on latest release")
        == "external_regression_repair"
    )


def test_score_issue_rewards_bug_and_regression_signals():
    assert score_issue(("bug",), "Regression in parser", "long body" * 30) > 3.0


def test_build_grounding_report_uses_fetch_errors_as_provenance_tasks(monkeypatch):
    def fail_request(*_args, **_kwargs):
        raise RuntimeError("network disabled")

    monkeypatch.setattr("scripts.external_world_grounding.github_request", fail_request)

    report = build_grounding_report(("example/project",), limit_per_repo=1)

    assert len(report.tasks) == 1
    assert report.tasks[0].task_kind == "external_grounding_error"
    assert "No external repository code is cloned or executed." in report.safety_model


def test_repositories_for_domains_expands_all_domain_catalogs_without_duplicates():
    repositories = repositories_for_domains(("all",), ("psf/requests",))

    assert repositories.count("psf/requests") == 1
    assert "pytorch/pytorch" in repositories
    assert "sphinx-doc/sphinx" in repositories
