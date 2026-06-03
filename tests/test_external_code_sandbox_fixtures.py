import json

from scripts.external_code_sandbox_fixtures import (
    bounded_source_window,
    build_external_code_sandbox_report,
    extract_failure_excerpt,
    extract_fenced_blocks,
    fixture_slug,
)


def test_extract_fenced_blocks_preserves_bounded_failure_snippets():
    text = "before ```python\nassert response.content\n``` after ```diff\n- old\n+ new\n```"

    blocks = extract_fenced_blocks(text, max_chars=200)

    assert blocks[0].startswith("[python]")
    assert "assert response.content" in blocks[0]
    assert blocks[1].startswith("[diff]")


def test_extract_failure_excerpt_falls_back_to_failure_window():
    task = {"body_excerpt": "setup text " * 20 + "FAILURES assert content was empty"}

    excerpt = extract_failure_excerpt(task, max_chars=80)

    assert "FAILURES" in excerpt
    assert len(excerpt) <= 80


def test_bounded_source_window_uses_anchor_terms_and_line_numbers():
    source = "\n".join([f"line {index}" for index in range(30)])
    source = source.replace("line 18", "def content(self):")

    snippet, line_start, line_end = bounded_source_window(source, ("content",), max_chars=80)

    assert "def content" in snippet
    assert 1 <= line_start <= line_end


def test_build_external_code_sandbox_report_writes_text_only_fixtures(tmp_path, monkeypatch):
    grounding_path = tmp_path / "external_grounding_tasks.json"
    grounding_path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "repository": "psf/requests",
                        "task_id": "github:psf/requests#2109",
                        "title": "[idea] Change how we merge request and session settings",
                        "body_excerpt": "```python\nassert 'User-Agent' not in merge_setting({'User-Agent': None}, session_headers)\n```",
                        "labels": ["Bug"],
                        "url": "https://github.com/psf/requests/issues/2109",
                        "grounding_score": 3.0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_github_json_request(url, **_kwargs):
        if url == "https://api.github.com/repos/psf/requests":
            return {"default_branch": "main"}
        if url == "https://api.github.com/repos/psf/requests/issues/2109":
            return {
                "title": "[idea] Change how we merge request and session settings",
                "body": "```python\nassert 'Content-Type' not in merge_setting({'Content-Type': None}, session_headers)\n```",
                "labels": [{"name": "Bug"}],
                "html_url": "https://github.com/psf/requests/issues/2109",
            }
        if "contents/src/requests/sessions.py" in url:
            return {
                "type": "file",
                "download_url": "https://example.test/requests/sessions.py",
                "sha": "source-blob-sha",
            }
        if "commits?" in url and "path=src%2Frequests%2Fsessions.py" in url:
            return [{"sha": "0123456789abcdef0123456789abcdef01234567"}]
        raise AssertionError(f"unexpected GitHub request: {url}")

    def fake_read_url_text(url, **_kwargs):
        assert url == "https://example.test/requests/sessions.py"
        return (
            "def merge_setting(request_setting, session_setting, dict_class=OrderedDict):\n"
            "    merged_setting = dict_class(to_key_val_list(session_setting))\n"
            "    merged_setting.update(to_key_val_list(request_setting))\n"
            "    none_keys = [k for k, v in merged_setting.items() if v is None]\n"
            "    for key in none_keys:\n"
            "        del merged_setting[key]\n"
            "    return merged_setting\n"
        )

    monkeypatch.setattr(
        "scripts.external_code_sandbox_fixtures.github_json_request",
        fake_github_json_request,
    )
    monkeypatch.setattr(
        "scripts.external_code_sandbox_fixtures.read_url_text",
        fake_read_url_text,
    )

    fixtures = build_external_code_sandbox_report(
        ("psf/requests",),
        grounding_path=grounding_path,
        output_dir=tmp_path / "fixtures",
    )

    fixture = fixtures[0]
    payload = json.loads((tmp_path / "fixtures" / "external_code_sandbox_fixtures.json").read_text())
    assert fixture.fixture_id == "external-code:psf/requests"
    assert fixture.issue_task_id == "github:psf/requests#2109"
    assert fixture.issue_url == "https://github.com/psf/requests/issues/2109"
    assert fixture.source_snippet_path.endswith(".txt")
    assert fixture.failure_excerpt_path.endswith(".txt")
    assert fixture.source_commit_sha == "0123456789abcdef0123456789abcdef01234567"
    assert fixture.field_values[0] == "merge_setting_none_header"
    assert "merge_setting" in fixture.field_values
    assert payload["fixtures"][0]["source_repository"] == "psf/requests"
    assert payload["fixtures"][0]["source_commit_sha"] == "0123456789abcdef0123456789abcdef01234567"
    assert (tmp_path / "fixtures" / fixture.source_snippet_path).exists()
    assert (tmp_path / "fixtures" / fixture.failure_excerpt_path).exists()


def test_fixture_slug_is_filesystem_safe():
    assert fixture_slug("pandas-dev/pandas") == "pandas_dev_pandas"
