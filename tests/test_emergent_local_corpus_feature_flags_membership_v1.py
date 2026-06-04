from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_records_matching_feature_flags_filters_feature_flags():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            feature_flags=("self_improvement",),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            feature_flags=("other_value",),
        ),
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=2,
            syntax_ok_count=2,
            syntax_error_count=0,
            unique_sha256_count=2,
            duplicate_file_instances=0,
            feature_counts={},
            import_edge_count=0,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.records_matching_feature_flags("self_improvement")) == ("a.py",)
