from shared.semantic_encoder import SemanticEncoder


def test_cache_size_and_clear_cache_do_not_change_backend():
    encoder = SemanticEncoder(prefer="hash")
    backend = encoder.backend
    assert encoder.cache_size == 0

    encoder.encode("machine learning")
    encoder.encode("machine learning")
    assert encoder.cache_size == 1

    encoder.clear_cache()
    assert encoder.cache_size == 0
    assert encoder.backend == backend
