from src.execution.sandbox import ExecutionSandbox


def test_execution_profile_to_dict_is_json_ready():
    profile = ExecutionSandbox().execute("def f(x):\n    return x\n")
    data = profile.to_dict()

    assert data["compiled"] is True
    assert data["executed"] is True
    assert data["fitness"] == profile.fitness
    assert isinstance(data["returned_values"], dict)
