"""Closed recursive self-improvement loop package."""

from scripts.closed_rsi.evaluators.capability import (
    candidate_capability_delta,
    candidate_failure_residue,
    capability_operator_names,
    load_capability_operators,
    operator_specs_for,
    top_level_function_source,
)
from scripts.closed_rsi.gates.results import (
    FULL_TEST_COMMAND,
    GateResult,
    full_test_exit_code,
    full_test_passed,
    is_full_test_gate,
)
from scripts.closed_rsi.generators.ast_synthesis import (
    AstMutationPlan,
    apply_mapping_none_deletion_mutation,
    ast_synthesis_candidates,
    ast_synthesis_compile_count,
    ast_synthesis_summary,
    discover_mapping_none_deletion_plans,
)
from scripts.closed_rsi.generators.capability import (
    CAPABILITY_OPERATOR_BLUEPRINTS,
    CapabilityOperatorBlueprint,
    add_capability_operator,
    build_capability_operator_test,
    capability_operator_candidates,
)
from scripts.closed_rsi.generators.common import insert_before, names_from_state, replace_once
from scripts.closed_rsi.generators.external_code import (
    external_code_repair_candidates,
    repair_external_merge_empty_only,
    repair_external_merge_general,
    repair_external_merge_user_agent_casefold,
    repair_external_merge_visible_header_set,
    repair_external_merge_visible_only,
)
from scripts.closed_rsi.generators.local_corpus import (
    LOCAL_CORPUS_QUERY_SPECS,
    add_autonomous_record_query,
    add_records_importing,
    add_records_with_feature,
    ast_annotation_mentions_tuple_of_strings,
    autonomous_local_corpus_candidates,
    build_autonomous_query_test,
    build_schema_batch_query_test,
    candidates_from_specs,
    discover_local_corpus_query_blueprints,
    query_blueprint_for_field,
    score_query_blueprints,
    schema_batch_query_candidates,
)
from scripts.closed_rsi.generators.policy_registry import (
    POLICY_REGISTRY_ACTIVE,
    POLICY_REGISTRY_ACTIVE_MARKER,
    POLICY_REGISTRY_SOURCE,
    POLICY_REGISTRY_TEST,
    add_policy_registry_hook,
    load_policy_registry,
)
from scripts.closed_rsi.loop import ClosedRecursiveSelfImprovementLoop, find_repo_root, main
from scripts.closed_rsi.records import (
    AutonomousQueryBlueprint,
    CandidateFactorySpec,
    CandidatePatch,
    CandidateRecord,
    Goal,
    Transform,
    generator_feedback,
    read_json,
    source_sha256,
    utc_now,
    write_json,
)

__all__ = [name for name in globals() if not name.startswith("_")]
