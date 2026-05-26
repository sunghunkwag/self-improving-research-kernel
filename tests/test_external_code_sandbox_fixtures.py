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
                        "task_id": "github:psf/requests#4965",
                        "title": "Accessing response.content twice forgets read error",
                        "body_excerpt": "```python\nassert response.content == b''\n```",
                        "labels": ["Bug"],
                        "url": "https://github.com/psf/requests/issues/4965",
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
        if "contents/src/requests/models.py" in url:
            return {
                "type": "file",
                "download_url": "https://example.test/requests/models.py",
            }
        raise AssertionError(f"unexpected GitHub request: {url}")

    def fake_read_url_text(url, **_kwargs):
        assert url == "https://example.test/requests/models.py"
        return (
            "class Response:\n"
            "    def iter_content(self):\n"
            "        return b''\n"
            "    @property\n"
            "    def content(self):\n"
            "        return self._content\n"
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
    assert fixture.source_snippet_path.endswith(".txt")
    assert fixture.failure_excerpt_path.endswith(".txt")
    assert fixture.field_values[0] == "response_content"
    assert "response" in fixture.field_values
    assert payload["fixtures"][0]["source_repository"] == "psf/requests"
    assert (tmp_path / "fixtures" / fixture.source_snippet_path).exists()
    assert (tmp_path / "fixtures" / fixture.failure_excerpt_path).exists()


def test_fixture_slug_is_filesystem_safe():
    assert fixture_slug("pandas-dev/pandas") == "pandas_dev_pandas"
