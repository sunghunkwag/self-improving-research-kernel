"""Local-corpus query candidate generators."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from scripts.closed_rsi.evaluators.capability import operator_specs_for
from scripts.closed_rsi.generators.common import insert_before, names_from_state
from scripts.closed_rsi.records import (
    AutonomousQueryBlueprint,
    CandidateFactorySpec,
    CandidatePatch,
    Goal,
    generator_feedback,
)


def add_records_with_feature(text: str) -> str:
    if "def records_with_feature(" in text:
        return text
    marker = "    def write_json(self, path: Path) -> None:\n"
    insertion = '''    def records_with_feature(self, feature: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records carrying a static feature flag."""

        if not isinstance(feature, str) or not feature:
            raise ValueError("feature must be a non-empty string")
        return tuple(record for record in self.records if feature in record.feature_flags)

'''
    return insert_before(text, marker, insertion, "local_corpus_feature_query_v1")


def add_records_importing(text: str) -> str:
    if "def records_importing(" in text:
        return text
    marker = "    def write_json(self, path: Path) -> None:\n"
    insertion = '''    def records_importing(self, module_name: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records that statically import ``module_name``."""

        if not isinstance(module_name, str) or not module_name:
            raise ValueError("module_name must be a non-empty string")
        return tuple(record for record in self.records if module_name in record.imports)

'''
    return insert_before(text, marker, insertion, "local_corpus_import_query_v1")


def singularize_identifier(name: str) -> str:
    """Derive a conservative singular parameter name from a record field."""

    if name.endswith("_flags"):
        return name[:-6]
    if name.endswith("ies"):
        return f"{name[:-3]}y"
    if name.endswith("s") and len(name) > 1:
        return name[:-1]
    return name


def query_blueprint_for_field(field_name: str, *, style: str = "canonical") -> AutonomousQueryBlueprint:
    """Create a query candidate blueprint from a tuple-valued record field."""

    element_name = singularize_identifier(field_name)
    sample_values = {
        "definition": "function:scan_file",
        "feature": "self_improvement",
    }
    if style == "alternate":
        method_name = f"records_matching_{field_name}"
        if field_name == "imports":
            method_name = "records_with_import"
        return AutonomousQueryBlueprint(
            field_name=field_name,
            method_name=method_name,
            parameter_name=element_name if field_name != "imports" else "module_name",
            sample_value=sample_values.get(element_name, "json" if field_name == "imports" else f"sample_{element_name}"),
            candidate_name=f"emergent_local_corpus_{field_name}_membership_v1",
            goal_name=f"emergently_query_local_corpus_{field_name}",
            rationale=(
                f"The bounded emergent planner generated an alternate membership "
                f"query hypothesis for {field_name}."
            ),
            strategy="alternate_tuple_membership",
        )
    if field_name == "imports":
        return AutonomousQueryBlueprint(
            field_name=field_name,
            method_name="records_importing",
            parameter_name="module_name",
            sample_value="json",
            candidate_name="autonomous_local_corpus_imports_query_v1",
            goal_name="autonomously_query_local_corpus_imports",
            rationale="The planner found a tuple-valued imports field without a matching query API.",
        )
    return AutonomousQueryBlueprint(
        field_name=field_name,
        method_name=f"records_with_{element_name}",
        parameter_name=element_name,
        sample_value=sample_values.get(element_name, f"sample_{element_name}"),
        candidate_name=f"autonomous_local_corpus_{field_name}_query_v1",
        goal_name=f"autonomously_query_local_corpus_{field_name}",
        rationale=(
            f"The planner found a tuple-valued {field_name} field without a matching "
            "query API on LocalCorpusIndex."
        ),
    )


def query_blueprint_hypotheses_for_field(field_name: str) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Generate bounded competing query hypotheses for one record field."""

    return (
        query_blueprint_for_field(field_name, style="canonical"),
        query_blueprint_for_field(field_name, style="alternate"),
    )


def ast_annotation_mentions_tuple_of_strings(annotation: ast.AST) -> bool:
    """Return whether an annotation looks like a tuple of strings."""

    try:
        rendered = ast.unparse(annotation)
    except Exception:
        return False
    normalized = rendered.replace("typing.", "")
    return "Tuple" in normalized and "str" in normalized


def names_from_state(state: Optional[dict], bucket: str) -> Tuple[str, ...]:
    """Return candidate names from persisted state records."""

    if not isinstance(state, dict):
        return ()
    names: List[str] = []
    for record in state.get(bucket, []):
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            names.append(str(record["name"]))
    return tuple(names)


def score_query_blueprints(
    blueprints: Sequence[AutonomousQueryBlueprint],
    *,
    state: Optional[dict] = None,
) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Score bounded planner hypotheses against accepted/rejected provenance."""

    accepted_names = set(names_from_state(state, "accepted"))
    rejected_names = set(names_from_state(state, "rejected"))
    scored: List[AutonomousQueryBlueprint] = []
    for index, blueprint in enumerate(blueprints):
        score = 10.0
        evidence = [
            f"field:{blueprint.field_name}",
            f"method:{blueprint.method_name}",
            f"strategy:{blueprint.strategy}",
        ]
        if blueprint.strategy == "tuple_membership":
            score += 2.0
            evidence.append("canonical_strategy_bonus")
        if blueprint.candidate_name in rejected_names:
            score -= 8.0
            evidence.append("rejected_history_penalty")
        if blueprint.candidate_name in accepted_names:
            score -= 4.0
            evidence.append("accepted_history_penalty")
        score -= index * 0.001
        scored.append(
            replace(
                blueprint,
                planner_score=round(score, 3),
                evidence=tuple(evidence),
            )
        )
    return tuple(
        sorted(
            scored,
            key=lambda item: (-item.planner_score, item.field_name, item.method_name),
        )
    )


def discover_local_corpus_query_blueprints(
    text: str,
    *,
    state: Optional[dict] = None,
    max_hypotheses: int = 3,
) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Infer missing LocalCorpusIndex query APIs from LocalPythonFileRecord fields."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ()
    record_fields: List[str] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if not isinstance(node, ast.ClassDef) or node.name != "LocalPythonFileRecord":
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if ast_annotation_mentions_tuple_of_strings(item.annotation):
                    record_fields.append(item.target.id)
        break
    blueprints: List[AutonomousQueryBlueprint] = []
    for field_name in record_fields:
        for blueprint in query_blueprint_hypotheses_for_field(field_name):
            if f"def {blueprint.method_name}(" not in text:
                blueprints.append(blueprint)
    return score_query_blueprints(blueprints, state=state)[:max_hypotheses]


def add_autonomous_record_query(text: str, blueprint: AutonomousQueryBlueprint) -> str:
    """Insert a planner-inferred LocalCorpusIndex query method."""

    if f"def {blueprint.method_name}(" in text:
        return text
    marker = "    def write_json(self, path: Path) -> None:\n"
    insertion = f'''    def {blueprint.method_name}(self, {blueprint.parameter_name}: str) -> Tuple[LocalPythonFileRecord, ...]:
        """Return records whose ``{blueprint.field_name}`` contain ``{blueprint.parameter_name}``."""

        if not isinstance({blueprint.parameter_name}, str) or not {blueprint.parameter_name}:
            raise ValueError("{blueprint.parameter_name} must be a non-empty string")
        return tuple(record for record in self.records if {blueprint.parameter_name} in record.{blueprint.field_name})

'''
    return insert_before(text, marker, insertion, blueprint.candidate_name)


def build_autonomous_query_test(blueprint: AutonomousQueryBlueprint) -> str:
    """Build a regression test for a planner-inferred LocalCorpusIndex query."""

    return f'''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_{blueprint.method_name}_filters_{blueprint.field_name}():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            {blueprint.field_name}=("{blueprint.sample_value}",),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            {blueprint.field_name}=("other_value",),
        ),
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=2,
            syntax_ok_count=2,
            syntax_error_count=0,
            unique_sha256_count=2,
            duplicate_file_instances=0,
            feature_counts={{}},
            import_edge_count=0,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.{blueprint.method_name}("{blueprint.sample_value}")) == ("a.py",)
'''


def canonical_query_blueprints_for_schema(
    text: str,
    *,
    state: Optional[dict] = None,
) -> Tuple[AutonomousQueryBlueprint, ...]:
    """Return one canonical missing query blueprint per tuple-valued field."""

    candidates = discover_local_corpus_query_blueprints(text, state=state, max_hypotheses=64)
    selected: Dict[str, AutonomousQueryBlueprint] = {}
    for blueprint in candidates:
        if blueprint.strategy != "tuple_membership":
            continue
        selected.setdefault(blueprint.field_name, blueprint)
    return tuple(selected[field] for field in sorted(selected))


def build_schema_batch_query_test(blueprints: Sequence[AutonomousQueryBlueprint]) -> str:
    """Build a focused regression test for a multi-field schema query patch."""

    field_lines = []
    assertion_lines = []
    for index, blueprint in enumerate(blueprints):
        field_lines.append(
            f"            {blueprint.field_name}=(\"{blueprint.sample_value}\",),"
        )
        assertion_lines.append(
            f"    assert tuple(record.path for record in index.{blueprint.method_name}(\"{blueprint.sample_value}\")) == (\"record_{index}.py\",)"
        )
    records = []
    for index, blueprint in enumerate(blueprints):
        records.append(
            "\n".join(
                [
                    "        LocalPythonFileRecord(",
                    f"            path=\"record_{index}.py\",",
                    f"            sha256=\"{index}\",",
                    "            size_bytes=1,",
                    "            line_count=1,",
                    "            syntax_ok=True,",
                    f"            {blueprint.field_name}=(\"{blueprint.sample_value}\",),",
                    "        ),",
                ]
            )
        )
    return f'''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_recursive_schema_batch_queries_filter_all_declared_fields():
    records = (
{chr(10).join(records)}
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=len(records),
            syntax_ok_count=len(records),
            syntax_error_count=0,
            unique_sha256_count=len(records),
            duplicate_file_instances=0,
            feature_counts={{}},
            import_edge_count=0,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

{chr(10).join(assertion_lines)}
'''


def add_schema_batch_record_queries(text: str, blueprints: Sequence[AutonomousQueryBlueprint]) -> str:
    """Insert every missing canonical query method for a schema-transfer fixture."""

    rewritten = text
    for blueprint in blueprints:
        rewritten = add_autonomous_record_query(rewritten, blueprint)
    return rewritten


def schema_batch_query_candidates(
    repo_root: Path,
    generation: int,
    *,
    state: Optional[dict] = None,
) -> List[CandidatePatch]:
    """Plan a general multi-field schema-transfer patch when a fixture demands it."""

    manifest = repo_root / "schema_transfer_manifest.json"
    if not manifest.exists():
        return []
    local_corpus = repo_root / "shared" / "local_corpus.py"
    if not local_corpus.exists():
        return []
    text = local_corpus.read_text(encoding="utf-8")
    blueprints = canonical_query_blueprints_for_schema(text, state=state)
    if len(blueprints) < 2:
        return []
    field_names = tuple(blueprint.field_name for blueprint in blueprints)
    method_names = ", ".join(blueprint.method_name for blueprint in blueprints)
    return [
        CandidatePatch(
            name="recursive_schema_batch_query_transfer_v1",
            generation=generation,
            goal=Goal(
                name="repair_composite_schema_transfer_surface",
                target="shared.local_corpus.LocalCorpusIndex",
                metric="all held-out tuple fields gain general membership queries in one full-suite patch",
                rationale=(
                    "A composite transfer fixture requires a general schema-level repair; "
                    "single-field partial repairs cannot pass the unmodified full test suite."
                ),
            ),
            target_path=local_corpus,
            test_path=repo_root / "tests" / "test_recursive_schema_batch_query_transfer_v1.py",
            transform=lambda source, plans=blueprints: add_schema_batch_record_queries(source, plans),
            test_source=build_schema_batch_query_test(blueprints),
            focused_tests=("tests/test_recursive_schema_batch_query_transfer_v1.py",),
            capability_family="schema_query_batch_repair",
            operator_specs=operator_specs_for("schema_query_batch_repair", "schema_tuple_membership_batch"),
            generator_improvement=generator_feedback(
                "schema-level transfer planner",
                "synthesizes a reusable batch of tuple-membership query operators from dataclass schema",
                f"one candidate repairs {len(blueprints)} missing query surfaces: {method_names}",
            ),
            schema_fields=field_names,
        )
    ]


def autonomous_local_corpus_candidates(
    repo_root: Path,
    generation: int,
    *,
    state: Optional[dict] = None,
) -> List[CandidatePatch]:
    """Plan LocalCorpusIndex candidates from source schema instead of fixed candidate names."""

    local_corpus = repo_root / "shared" / "local_corpus.py"
    if not local_corpus.exists():
        return []
    text = local_corpus.read_text(encoding="utf-8")
    candidates: List[CandidatePatch] = []
    for blueprint in discover_local_corpus_query_blueprints(text, state=state):
        candidates.append(
            CandidatePatch(
                name=blueprint.candidate_name,
                generation=generation,
                goal=Goal(
                    name=blueprint.goal_name,
                    target="shared.local_corpus.LocalCorpusIndex",
                    metric=f"planner score {blueprint.planner_score} plus generated regression test",
                    rationale=f"{blueprint.rationale} Evidence: {', '.join(blueprint.evidence)}.",
                ),
                target_path=local_corpus,
                test_path=repo_root / "tests" / f"test_{blueprint.candidate_name}.py",
                transform=lambda source, plan=blueprint: add_autonomous_record_query(source, plan),
                test_source=build_autonomous_query_test(blueprint),
                focused_tests=(f"tests/test_{blueprint.candidate_name}.py",),
                capability_family="schema_query_repair",
                operator_specs=operator_specs_for("schema_query_repair", blueprint.method_name),
                generator_improvement=generator_feedback(
                    "schema-driven query planner",
                    "adds a reusable tuple-membership operator surface inferred from dataclass fields",
                    f"{blueprint.method_name} is generated from {blueprint.field_name} and locked by a focused test",
                ),
                schema_fields=(blueprint.field_name,),
            )
        )
    return candidates

FEATURE_QUERY_TEST = '''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_records_with_feature_filters_static_flags():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            feature_flags=("validation", "self_improvement"),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            feature_flags=("validation",),
        ),
    )
    index = LocalCorpusIndex(
        summary=LocalCorpusSummary(
            file_count=2,
            syntax_ok_count=2,
            syntax_error_count=0,
            unique_sha256_count=2,
            duplicate_file_instances=0,
            feature_counts={"validation": 2, "self_improvement": 1},
            import_edge_count=0,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.records_with_feature("self_improvement")) == ("a.py",)
'''


IMPORT_QUERY_TEST = '''from shared.local_corpus import LocalCorpusIndex, LocalCorpusSummary, LocalPythonFileRecord


def test_records_importing_filters_static_imports():
    records = (
        LocalPythonFileRecord(
            path="a.py",
            sha256="a",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            imports=("json", "pathlib"),
        ),
        LocalPythonFileRecord(
            path="b.py",
            sha256="b",
            size_bytes=1,
            line_count=1,
            syntax_ok=True,
            imports=("math",),
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
            import_edge_count=3,
            definition_count=0,
        ),
        records=records,
        import_edges=(),
    )

    assert tuple(record.path for record in index.records_importing("json")) == ("a.py",)
'''


LOCAL_CORPUS_QUERY_SPECS: Tuple[CandidateFactorySpec, ...] = (
    CandidateFactorySpec(
        candidate_name="local_corpus_feature_query_v1",
        missing_symbol="def records_with_feature(",
        goal_name="make_local_corpus_queryable_by_feature",
        target="shared.local_corpus.LocalCorpusIndex",
        metric="new query API plus focused regression test",
        rationale="The corpus index already extracts feature flags but lacks a stable query API.",
        target_relative_path="shared/local_corpus.py",
        test_relative_path="tests/test_local_corpus_feature_query_rewrite.py",
        transform=add_records_with_feature,
        test_source=FEATURE_QUERY_TEST,
        focused_tests=("tests/test_local_corpus_feature_query_rewrite.py",),
    ),
    CandidateFactorySpec(
        candidate_name="local_corpus_import_query_v1",
        missing_symbol="def records_importing(",
        goal_name="make_local_corpus_queryable_by_import",
        target="shared.local_corpus.LocalCorpusIndex",
        metric="new import query API plus focused regression test",
        rationale="The corpus index stores static imports but lacks a direct import lookup API.",
        target_relative_path="shared/local_corpus.py",
        test_relative_path="tests/test_local_corpus_import_query_rewrite.py",
        transform=add_records_importing,
        test_source=IMPORT_QUERY_TEST,
        focused_tests=("tests/test_local_corpus_import_query_rewrite.py",),
    ),
)


def candidates_from_specs(
    repo_root: Path,
    generation: int,
    specs: Sequence[CandidateFactorySpec],
) -> List[CandidatePatch]:
    """Generate source candidates from declarative missing-capability specs."""

    candidates: List[CandidatePatch] = []
    source_cache: Dict[str, str] = {}
    for spec in specs:
        target_path = repo_root / spec.target_relative_path
        if spec.target_relative_path not in source_cache:
            source_cache[spec.target_relative_path] = target_path.read_text(encoding="utf-8")
        if spec.missing_symbol in source_cache[spec.target_relative_path]:
            continue
        candidates.append(
            CandidatePatch(
                name=spec.candidate_name,
                generation=generation,
                goal=Goal(
                    name=spec.goal_name,
                    target=spec.target,
                    metric=spec.metric,
                    rationale=spec.rationale,
                ),
                target_path=target_path,
                test_path=repo_root / spec.test_relative_path,
                transform=spec.transform,
                test_source=spec.test_source,
                focused_tests=spec.focused_tests,
                capability_family="schema_query_repair",
                operator_specs=operator_specs_for("schema_query_repair", spec.missing_symbol.strip("def (")),
                generator_improvement=generator_feedback(
                    "declarative candidate factories",
                    "keeps fixed repair recipes available as reusable generator fallbacks",
                    f"{spec.candidate_name} repairs {spec.target} with a focused regression test",
                ),
            )
        )
    return candidates
