from pathlib import Path

from scripts.closed_recursive_self_improvement_loop import (
    ClosedRecursiveSelfImprovementLoop,
    add_records_importing,
    add_records_with_feature,
)


LOCAL_CORPUS_STUB = '''
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple


@dataclass(frozen=True)
class LocalPythonFileRecord:
    path: str
    feature_flags: Tuple[str, ...] = ()
    imports: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalCorpusIndex:
    records: Tuple[LocalPythonFileRecord, ...]

    def to_dict(self) -> Dict[str, object]:
        return {"records": [record.path for record in self.records]}

    def write_json(self, path: Path) -> None:
        path.write_text("{}", encoding="utf-8")
'''


def test_transforms_add_query_methods_once():
    once = add_records_with_feature(LOCAL_CORPUS_STUB)
    twice = add_records_with_feature(once)

    assert "def records_with_feature(" in once
    assert once == twice

    import_query = add_records_importing(once)
    assert "def records_importing(" in import_query


def test_loop_discovers_real_source_candidates_in_temp_tree(tmp_path):
    repo = tmp_path / "OMEGA-THDSE"
    shared = repo / "shared"
    tests = repo / "tests"
    thdse = repo / "thdse"
    shared.mkdir(parents=True)
    tests.mkdir()
    thdse.mkdir()
    (shared / "local_corpus.py").write_text(LOCAL_CORPUS_STUB, encoding="utf-8")

    loop = ClosedRecursiveSelfImprovementLoop(repo, state_dir=tmp_path / "state")
    candidates = loop.invent_candidates(generation=1)

    assert [candidate.name for candidate in candidates] == [
        "local_corpus_feature_query_v1",
        "local_corpus_import_query_v1",
    ]
