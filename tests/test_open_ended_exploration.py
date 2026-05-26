from scripts.open_ended_exploration import (
    DEFAULT_DOMAIN_SEEDS,
    DEFAULT_EXPLORATION_AXES,
    build_open_exploration_report,
    materialize_candidates,
    search_space_signature,
)


def test_open_exploration_materializes_bounded_prefix_from_open_space():
    report = build_open_exploration_report(max_candidates=5, meta_depth=3)

    assert report.materialized_candidate_count == 5
    assert "open-ended" in report.open_space_claim
    assert len(report.domains) >= 8
    assert len(report.axes) >= 5
    assert all(candidate.closure_state == "open_loop_not_applied" for candidate in report.candidates)


def test_unverified_self_modification_is_recorded_but_not_applied():
    report = build_open_exploration_report(max_candidates=12, meta_depth=3, include_unverified=True)
    unverified = [
        candidate
        for candidate in report.candidates
        if candidate.validation_status == "explicitly_unverified_allowed"
    ]

    assert unverified
    assert all("no_auto_patch" in candidate.safety_controls for candidate in unverified)
    assert all(candidate.proposal_kind == "speculative_unverified_self_modification" for candidate in unverified)


def test_meta_meta_meta_limit_layers_are_present():
    candidate = build_open_exploration_report(max_candidates=1, meta_depth=3).candidates[0]

    assert [layer.label for layer in candidate.meta_limit_layers] == [
        "meta",
        "meta_meta",
        "meta_meta_meta",
    ]
    assert all(layer.transferable_question for layer in candidate.meta_limit_layers)


def test_candidate_ids_are_deterministic_for_same_prefix():
    left = materialize_candidates(
        DEFAULT_DOMAIN_SEEDS,
        DEFAULT_EXPLORATION_AXES,
        max_candidates=6,
        meta_depth=4,
        include_unverified=True,
    )
    right = materialize_candidates(
        DEFAULT_DOMAIN_SEEDS,
        DEFAULT_EXPLORATION_AXES,
        max_candidates=6,
        meta_depth=4,
        include_unverified=True,
    )

    assert [candidate.candidate_id for candidate in left] == [
        candidate.candidate_id for candidate in right
    ]


def test_cross_domain_transfer_targets_exclude_source_domain():
    report = build_open_exploration_report(max_candidates=10, meta_depth=2)

    for candidate in report.candidates:
        assert candidate.domain not in candidate.transfer_targets
        assert candidate.transfer_targets


def test_search_space_signature_changes_when_axes_change():
    original = search_space_signature(DEFAULT_DOMAIN_SEEDS, DEFAULT_EXPLORATION_AXES)
    reduced = search_space_signature(DEFAULT_DOMAIN_SEEDS, DEFAULT_EXPLORATION_AXES[:1])

    assert original != reduced
