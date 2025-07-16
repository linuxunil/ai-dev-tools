"""
Step definitions for Output Strategy BDD tests
"""

import json
from pytest_bdd import scenarios, given, when, then, parsers

from ai_dev_tools.core.output_strategy import (
    OutputFormatter,
    OutputFormat,
    create_ai_optimized_result,
)

# Load scenarios
scenarios("../features/output_strategy.feature")


@given("I have data to output")
def data_to_output(test_context):
    """Set up test data"""
    test_context["data"] = {
        "count": 3,
        "items": [
            {"file": "test.nix", "line": 10, "confidence": 0.95},
            {"file": "core.nix", "line": 15, "confidence": 0.87},
        ],
        "metadata": {"pattern_type": "mkIf_home_packages"},
    }


@when("I format with compact strategy")
def format_compact(test_context):
    """Format with compact strategy"""
    result = OutputFormatter.format_output(test_context["data"], OutputFormat.COMPACT)
    test_context["output"] = result


@when("I format with human strategy")
def format_human(test_context):
    """Format with human strategy"""
    result = OutputFormatter.format_output(test_context["data"], OutputFormat.HUMAN)
    test_context["output"] = result


@when("I create AI-optimized result")
def create_ai_result(test_context):
    """Create AI-optimized result"""
    data = test_context["data"]
    result = create_ai_optimized_result(
        count=data["count"], items=data["items"], metadata=data["metadata"]
    )
    test_context["ai_result"] = result


@then("the output should be compact JSON")
def output_is_compact_json(test_context):
    """Output should be compact JSON"""
    output = test_context["output"]
    # Should be valid JSON
    parsed = json.loads(output)
    # Should not contain whitespace (compact)
    assert "\n" not in output
    assert "  " not in output


@then("the output should be human-readable")
def output_is_human_readable(test_context):
    """Output should be human-readable"""
    output = test_context["output"]
    # Should contain readable text
    assert "Found" in output or "Risk" in output or "Health" in output


@then("the AI result should use short keys")
def ai_result_short_keys(test_context):
    """AI result should use short keys to save tokens"""
    result = test_context["ai_result"]
    # Should use short keys
    assert "c" in result  # count
    assert "items" in result
    # Items should have short keys
    if result["items"]:
        item = result["items"][0]
        assert "f" in item  # file
        assert "l" in item  # line


@then("empty values should be omitted")
def empty_values_omitted(test_context):
    """Empty values should be omitted to save tokens"""
    result = test_context["ai_result"]
    # Should not contain empty lists or null values
    for value in result.values():
        assert value is not None
        if isinstance(value, list):
            assert len(value) > 0
