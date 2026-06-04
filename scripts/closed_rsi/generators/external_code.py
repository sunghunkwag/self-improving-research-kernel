"""External-code repair candidate generators."""

from __future__ import annotations

from pathlib import Path
from typing import List

from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.generators.common import replace_once
from scripts.closed_rsi.records import CandidatePatch, Goal, generator_feedback


EXTERNAL_MERGE_BUGGY_BODY = '''    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))
    return merged_setting
'''


EXTERNAL_MERGE_VISIBLE_ONLY_BODY = '''    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))
    if merged_setting.get("User-Agent") is None:
        del merged_setting["User-Agent"]
    return merged_setting
'''


EXTERNAL_MERGE_USER_AGENT_CASEFOLD_BODY = '''    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))
    for key in list(merged_setting):
        if str(key).lower() == "user-agent" and merged_setting[key] is None:
            del merged_setting[key]
    return merged_setting
'''


EXTERNAL_MERGE_VISIBLE_HEADER_SET_BODY = '''    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))
    visible_headers = {"User-Agent", "Content-Type"}
    for key in tuple(visible_headers):
        if merged_setting.get(key) is None:
            del merged_setting[key]
    return merged_setting
'''


EXTERNAL_MERGE_EMPTY_ONLY_BODY = '''    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))
    return dict_class((key, value) for key, value in merged_setting.items() if value != "")
'''


EXTERNAL_MERGE_GENERAL_BODY = '''    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))
    return dict_class((key, value) for key, value in merged_setting.items() if value is not None)
'''


EXTERNAL_REPAIR_TEST = '''from pathlib import Path

from shared.external_repair_target import merge_setting


def test_requests_header_none_removes_session_header_visible_case():
    session_headers = {"User-Agent": "session-agent", "Accept": "application/json"}
    request_headers = {"User-Agent": None, "Content-Type": "text/plain"}

    merged = merge_setting(request_headers, session_headers)

    assert "User-Agent" not in merged
    assert merged["Accept"] == "application/json"
    assert merged["Content-Type"] == "text/plain"


def test_external_source_and_failure_fixtures_are_local_inputs():
    root = Path.cwd() / "external_sandbox"

    assert (root / "source_snippet.txt").read_text(encoding="utf-8")
    assert (root / "failure_excerpt.txt").read_text(encoding="utf-8")
'''


def replace_external_merge_body(text: str, new_body: str, candidate_name: str) -> str:
    """Replace only the buggy merge-setting body with a candidate implementation."""

    if new_body in text:
        return text
    return replace_once(text, EXTERNAL_MERGE_BUGGY_BODY, new_body, candidate_name)


def repair_external_merge_general(text: str) -> str:
    return replace_external_merge_body(
        text,
        EXTERNAL_MERGE_GENERAL_BODY,
        "external_code_repair_requests_merge_setting_general_v1",
    )


def repair_external_merge_visible_only(text: str) -> str:
    return replace_external_merge_body(
        text,
        EXTERNAL_MERGE_VISIBLE_ONLY_BODY,
        "external_code_repair_requests_merge_setting_visible_only_v1",
    )


def repair_external_merge_user_agent_casefold(text: str) -> str:
    return replace_external_merge_body(
        text,
        EXTERNAL_MERGE_USER_AGENT_CASEFOLD_BODY,
        "external_code_repair_requests_merge_setting_user_agent_casefold_v1",
    )


def repair_external_merge_visible_header_set(text: str) -> str:
    return replace_external_merge_body(
        text,
        EXTERNAL_MERGE_VISIBLE_HEADER_SET_BODY,
        "external_code_repair_requests_merge_setting_visible_header_set_v1",
    )


def repair_external_merge_empty_only(text: str) -> str:
    return replace_external_merge_body(
        text,
        EXTERNAL_MERGE_EMPTY_ONLY_BODY,
        "external_code_repair_requests_merge_setting_empty_only_v1",
    )


def external_code_repair_candidates(
    repo_root: Path,
    generation: int,
    *,
    include_recursive_general: bool = False,
) -> List[CandidatePatch]:
    """Plan local executable repairs derived from external-code failure fixtures."""

    target = repo_root / "shared" / "external_repair_target.py"
    if not target.exists():
        return []
    text = target.read_text(encoding="utf-8")
    if EXTERNAL_MERGE_GENERAL_BODY in text:
        return []
    candidates = [
        CandidatePatch(
            name="external_code_repair_requests_merge_setting_visible_only_v1",
            generation=generation,
            goal=Goal(
                name="repair_requests_merge_setting_visible_header_none",
                target="shared.external_repair_target.merge_setting",
                metric="visible requests header-removal regression passes without full-suite weakening",
                rationale=(
                    "A visible failing test from a ported requests header-merge bug "
                    "suggests removing a per-request header set to None."
                ),
            ),
            target_path=target,
            test_path=repo_root / "tests" / "test_external_code_repair_task.py",
            transform=repair_external_merge_visible_only,
            test_source=EXTERNAL_REPAIR_TEST,
            focused_tests=("tests/test_external_code_repair_task.py",),
            capability_family="external_code_repair",
            operator_specs=operator_specs_for("external_code_repair", "merge_setting_visible_only"),
            generator_improvement=generator_feedback(
                "external-code failing tests",
                "tries a narrow candidate first so hidden seed-derived cases can expose overfit repairs",
                "future external-code repairs record seen-pass hidden-fail residue instead of silent promotion",
            ),
        ),
        CandidatePatch(
            name="external_code_repair_requests_merge_setting_user_agent_casefold_v1",
            generation=generation,
            goal=Goal(
                name="repair_requests_merge_setting_user_agent_casefold",
                target="shared.external_repair_target.merge_setting",
                metric="visible requests header-removal regression passes without full-suite weakening",
                rationale=(
                    "A narrow hypothesis treats the visible User-Agent header as the "
                    "only removable inherited key; hidden seed-derived headers must reject it."
                ),
            ),
            target_path=target,
            test_path=repo_root / "tests" / "test_external_code_repair_task.py",
            transform=repair_external_merge_user_agent_casefold,
            test_source=EXTERNAL_REPAIR_TEST,
            focused_tests=("tests/test_external_code_repair_task.py",),
            capability_family="external_code_repair",
            operator_specs=operator_specs_for("external_code_repair", "merge_setting_user_agent_casefold"),
            generator_improvement=generator_feedback(
                "external-code overfit detection",
                "keeps a visible-case candidate in the seed-varied search space",
                "hidden probes reject header-name special cases before promotion",
            ),
        ),
        CandidatePatch(
            name="external_code_repair_requests_merge_setting_visible_header_set_v1",
            generation=generation,
            goal=Goal(
                name="repair_requests_merge_setting_visible_header_set",
                target="shared.external_repair_target.merge_setting",
                metric="visible requests header-removal regression passes without full-suite weakening",
                rationale=(
                    "A second narrow hypothesis only considers headers named in the "
                    "visible fixture; seeded hidden counterexamples must reject it."
                ),
            ),
            target_path=target,
            test_path=repo_root / "tests" / "test_external_code_repair_task.py",
            transform=repair_external_merge_visible_header_set,
            test_source=EXTERNAL_REPAIR_TEST,
            focused_tests=("tests/test_external_code_repair_task.py",),
            capability_family="external_code_repair",
            operator_specs=operator_specs_for("external_code_repair", "merge_setting_visible_header_set"),
            generator_improvement=generator_feedback(
                "external-code anti-hardcoding guard",
                "records seen-pass hidden-fail residue for visible-header special cases",
                "only general mapping semantics can survive the hidden evaluator and full pytest",
            ),
        ),
        CandidatePatch(
            name="external_code_repair_requests_merge_setting_empty_only_v1",
            generation=generation,
            goal=Goal(
                name="repair_requests_merge_setting_empty_values",
                target="shared.external_repair_target.merge_setting",
                metric="visible requests header-removal regression passes without full-suite weakening",
                rationale=(
                    "A competing candidate removes empty-string values; it should fail "
                    "the visible None-removal regression rather than being promoted."
                ),
            ),
            target_path=target,
            test_path=repo_root / "tests" / "test_external_code_repair_task.py",
            transform=repair_external_merge_empty_only,
            test_source=EXTERNAL_REPAIR_TEST,
            focused_tests=("tests/test_external_code_repair_task.py",),
            capability_family="external_code_repair",
            operator_specs=operator_specs_for("external_code_repair", "merge_setting_empty_only"),
            generator_improvement=generator_feedback(
                "external-code candidate ranking",
                "keeps a plausible but wrong repair in the seed-varied search space",
                "accepted-rate estimates now vary by real candidate order and failures",
            ),
        ),
    ]
    if include_recursive_general:
        candidates.append(
            CandidatePatch(
                name="external_code_repair_requests_merge_setting_general_v1",
                generation=generation,
                goal=Goal(
                    name="repair_requests_merge_setting_general_none_removal",
                    target="shared.external_repair_target.merge_setting",
                    metric="visible and hidden requests header-removal regressions pass under full pytest",
                    rationale=(
                        "The recursive loop promotes a general repair: any request-level "
                        "mapping key set to None removes the inherited session value."
                    ),
                ),
                target_path=target,
                test_path=repo_root / "tests" / "test_external_code_repair_task.py",
                transform=repair_external_merge_general,
                test_source=EXTERNAL_REPAIR_TEST,
                focused_tests=("tests/test_external_code_repair_task.py",),
                capability_family="external_code_repair",
                operator_specs=operator_specs_for("external_code_repair", "merge_setting_general_none_removal"),
                generator_improvement=generator_feedback(
                    "external-code bug repair",
                    "repairs an executable port of requests merge_setting without reading the held-out reference",
                    "future external-code tasks can be scored on hidden counterexamples and full pytest evidence",
                ),
            )
        )
    return candidates
