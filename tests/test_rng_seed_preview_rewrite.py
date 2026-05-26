from shared.deterministic_rng import DeterministicRNG


def test_preview_child_seeds_is_stable_and_non_advancing():
    rng = DeterministicRNG(master_seed=123)
    preview = rng.preview_child_seeds(["alpha", "beta", "alpha"])

    assert list(preview) == ["alpha", "beta"]
    assert preview["alpha"] == rng.child_seed("alpha")
    assert preview["beta"] == rng.child_seed("beta")
    assert rng.active_namespaces == ()


def test_preview_child_seeds_matches_recreated_rng():
    left = DeterministicRNG(master_seed=987).preview_child_seeds(["serl", "arena"])
    right = DeterministicRNG(master_seed=987).preview_child_seeds(["serl", "arena"])

    assert left == right
