"""
BDD step definitions for context analysis feature
"""

import json
import tempfile
import subprocess
from pathlib import Path
from pytest_bdd import given, when, then, scenarios, parsers

from ai_dev_tools.core.context_analyzer import (
    ContextAnalyzer,
    ProjectType,
    FrameworkType,
)

# Load scenarios from feature file
scenarios("../features/context_analysis.feature")


@given("I have a context analyzer")
def context_analyzer():
    """Create a context analyzer instance"""
    return ContextAnalyzer


@given("I have a temporary project directory")
def temp_project_dir():
    """Create a temporary directory for testing"""
    return tempfile.mkdtemp()


@given(parsers.parse("I create a Python project with:\n{table}"))
def create_python_project(temp_project_dir, table):
    """Create a Python project with specified files"""
    project_path = Path(temp_project_dir)

    # Parse the table and create files
    lines = table.strip().split("\n")
    for line in lines[1:]:  # Skip header
        parts = [part.strip(" |") for part in line.split("|")]
        if len(parts) >= 2:
            file_path = parts[0].strip()
            content = parts[1].strip()

            # Create directory if needed
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            full_path.write_text(content)

    return project_path


@given(parsers.parse("I create a JavaScript project with:\n{table}"))
def create_javascript_project(temp_project_dir, table):
    """Create a JavaScript project with specified files"""
    return create_python_project(temp_project_dir, table)  # Same logic


@given(parsers.parse("I create a mixed project with:\n{table}"))
def create_mixed_project(temp_project_dir, table):
    """Create a mixed-language project with specified files"""
    return create_python_project(temp_project_dir, table)  # Same logic


@given(parsers.parse("I create a simple project with:\n{table}"))
def create_simple_project(temp_project_dir, table):
    """Create a simple project with specified files"""
    return create_python_project(temp_project_dir, table)  # Same logic


@when("I analyze the project context")
def analyze_context(context_analyzer, create_python_project):
    """Analyze the project context"""
    analyzer = context_analyzer(create_python_project)
    context = analyzer.analyze()
    return context


@when("I run the context analyzer CLI in silent mode")
def run_cli_silent(create_simple_project):
    """Run the context analyzer CLI in silent mode"""
    result = subprocess.run(
        [
            "python",
            "-m",
            "ai_dev_tools.cli.context_analyze",
            str(create_simple_project),
            "--format",
            "silent",
        ],
        capture_output=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )
    return result


@when(parsers.parse('I run the context analyzer with format "{format_type}"'))
def run_cli_with_format(create_simple_project, format_type):
    """Run the context analyzer CLI with specified format"""
    result = subprocess.run(
        [
            "python",
            "-m",
            "ai_dev_tools.cli.context_analyze",
            str(create_simple_project),
            "--format",
            format_type,
        ],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )
    return result


@then(parsers.parse('the project type should be "{expected_type}"'))
def check_project_type(analysis_result, expected_type):
    """Check that the project type matches expected value"""
    assert analysis_result.project_type.value == expected_type


@then(parsers.parse('the framework should be "{expected_framework}"'))
def check_framework(analysis_result, expected_framework):
    """Check that the framework matches expected value"""
    assert analysis_result.framework.value == expected_framework


@then(parsers.parse("there should be at least {min_count:d} dependencies"))
def check_dependency_count(analysis_result, min_count):
    """Check that there are at least the specified number of dependencies"""
    assert len(analysis_result.dependencies) >= min_count


@then("the complexity score should be greater than 0")
def check_complexity_score(analysis_result):
    """Check that complexity score is greater than 0"""
    assert analysis_result.complexity_score > 0


@then("the exit code should be the complexity score")
def check_exit_code_is_complexity(run_cli_silent, analyze_context):
    """Check that exit code matches complexity score"""
    # We need to run the analysis to get the expected complexity
    analyzer = ContextAnalyzer(Path(run_cli_silent.args[2]))
    context = analyzer.analyze()
    assert run_cli_silent.returncode == context.complexity_score


@then(parsers.parse("the exit code should be between {min_val:d} and {max_val:d}"))
def check_exit_code_range(run_cli_silent, min_val, max_val):
    """Check that exit code is within specified range"""
    assert min_val <= run_cli_silent.returncode <= max_val


@then("the output should be valid JSON")
def check_valid_json(run_cli_with_format):
    """Check that output is valid JSON"""
    try:
        json.loads(run_cli_with_format.stdout)
    except json.JSONDecodeError:
        assert False, f"Output is not valid JSON: {run_cli_with_format.stdout}"


@then(parsers.parse('the JSON should contain "{key}"'))
def check_json_contains_key(run_cli_with_format, key):
    """Check that JSON output contains specified key"""
    output = json.loads(run_cli_with_format.stdout)
    assert key in output, f"JSON output missing key '{key}': {output}"
