from shared.capability_primitives import classify_residue_feedback_policy_surface_generator_feedback_polic_runtimeerror_pressure


def test_classify_residue_feedback_policy_surface_generator_feedback_polic_runtimeerror_pressure_private_case_1():
    payload = {'family': 'residue_feedback_policy_surface_generator_feedback_polic_runtimeerror', 'signals': ('feedback_policy_surface', 'generator_feedback_policy_v1_immutable_boundary', 'runtimeerror', 'immutable', 'boundary', 'seed_160', 'feedback_policy_surface'), 'residue_count': 1, 'seed_pressure': 4, 'hidden': True, 'difficulty': 1, 'case_index': 0}

    assert classify_residue_feedback_policy_surface_generator_feedback_polic_runtimeerror_pressure(payload) == {'family': 'residue_feedback_policy_surface_generator_feedback_polic_runtimeerror', 'dominant_signal': 'feedback_policy_surface', 'pressure': 5, 'difficulty': 1, 'evidence_width': 6}

