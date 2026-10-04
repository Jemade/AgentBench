import pytest
from app import config
from app.runner import evaluate


@pytest.mark.parametrize(
    "source,value,expected,mutated,passed",
    [
        ("def solve(value): return [True]", None, [1], False, 0),
        ("def solve(value): return {'value': [True]}", None, {"value": [1]}, False, 0),
        ("def solve(value): value[0] = True; return 1", [1], 1, True, 0),
        ("def solve(value): return {'value': [1]}", None, {"value": [1]}, False, 1),
    ],
)
def test_nested_types_and_mutations(source, value, expected, mutated, passed, monkeypatch):
    monkeypatch.setattr(config, "RUNNER", "trusted-local")
    monkeypatch.setattr(config, "ALLOW_TRUSTED_LOCAL", True)
    result = evaluate(source, {"reference": source, "cases": [[value, expected]]}, "reference")
    assert result["passed"] == passed
    assert result["cases"][0]["mutated_input"] is mutated
