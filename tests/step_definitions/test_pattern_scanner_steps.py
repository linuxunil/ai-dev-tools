"""
Step definitions for Pattern Scanner BDD tests
"""

import json
import subprocess
from pathlib import Path

from pytest_bdd import scenarios, given, when, then, parsers

from ai_dev_tools.core.pattern_scanner import PatternScanner, PatternType

# Load scenarios
scenarios("../features/pattern_scanner.feature")


@given("I have a repository with multiple files")
def repository_with_files(sample_files):
    """Repository is set up with sample files"""
    pass


@given("the files contain similar code patterns")
def files_contain_patterns(sample_files):
    """Files contain similar patterns"""
    pass


@given(parsers.parse('I have a file "{filename}" with mkIf pattern at line {line:d}'))
def file_with_mkif_pattern(sample_files, filename, line, test_context):
    """Set up file with mkIf pattern"""
    test_context["target_file"] = str(sample_files[filename])
    test_context["target_line"] = line


@given(
    parsers.parse('I have a file "{filename}" with a unique pattern at line {line:d}')
)
def file_with_unique_pattern(sample_files, filename, line, test_context):
    """Set up file with unique pattern"""
    test_context["target_file"] = str(sample_files[filename])
    test_context["target_line"] = line


@given(parsers.parse('I have a file with "home.packages" and "mkIf" at line {line:d}'))
def file_with_home_packages_mkif(sample_files, line, test_context):
    """Set up file with home.packages mkIf pattern"""
    test_context["target_file"] = str(sample_files["shell.nix"])
    test_context["target_line"] = line


@given("I have 3 files with similar mkIf patterns")
def three_files_with_mkif(sample_files, test_context):
    """Set up scenario with 3 similar patterns"""
    test_context["target_file"] = str(sample_files["shell.nix"])
    test_context["target_line"] = 3
    test_context["expected_count"] = (
        2  # shell.nix + core.nix (development.nix has different pattern)
    )


@given(parsers.parse('I provide an invalid target format "{target}"'))
def invalid_target_format(target, test_context):
    """Set up invalid target format"""
    test_context["invalid_target"] = target


@given(parsers.parse('I provide a target "{target}"'))
def nonexistent_target(target, test_context):
    """Set up nonexistent target"""
    test_context["target"] = target


@when("I scan for similar patterns in the current directory")
def scan_patterns_current_dir(pattern_scanner, test_context, temp_repo):
    """Scan for patterns in current directory"""
    result = pattern_scanner.scan_for_similar_patterns(
        target_file=test_context["target_file"],
        target_line=test_context["target_line"],
        search_dir=str(temp_repo),
    )
    test_context["scan_result"] = result


@when("I scan for similar patterns")
def scan_patterns(pattern_scanner, test_context, temp_repo):
    """Scan for patterns"""
    result = pattern_scanner.scan_for_similar_patterns(
        target_file=test_context["target_file"],
        target_line=test_context["target_line"],
        search_dir=str(temp_repo),
    )
    test_context["scan_result"] = result


@when("I run the pattern scanner")
def run_pattern_scanner_cli(test_context, temp_repo):
    """Run pattern scanner CLI"""
    if "invalid_target" in test_context:
        target = test_context["invalid_target"]
    else:
        target = test_context["target"]

    cmd = [
        "ai-pattern-scan",
        target,
        "--search-dir",
        str(temp_repo),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    test_context["cli_result"] = result


@then("I should find other mkIf patterns")
def should_find_mkif_patterns(test_context):
    """Should find mkIf patterns"""
    result = test_context["scan_result"]
    assert result.count > 0
    assert result.pattern_type == PatternType.MKIF_HOME_PACKAGES


@then(parsers.parse("I should find {count:d} similar patterns"))
def should_find_pattern_count(test_context, count):
    """Should find specific number of patterns"""
    result = test_context["scan_result"]
    assert result.count == count


@then("the exit code should equal the number of patterns found")
def exit_code_equals_pattern_count(test_context):
    """Exit code should equal pattern count"""
    if "cli_result" in test_context:
        result = test_context["cli_result"]
        scan_result = json.loads(result.stdout) if result.stdout else {"count": 0}
        assert result.returncode == scan_result["count"]


@then("the output should be valid JSON")
def output_should_be_json(test_context):
    """Output should be valid JSON"""
    if "scan_result" in test_context:
        result = test_context["scan_result"]
        json_str = result.to_json()
        json.loads(json_str)  # Should not raise exception
    elif "cli_result" in test_context:
        result = test_context["cli_result"]
        if result.stdout:
            json.loads(result.stdout)  # Should not raise exception


@then(parsers.parse("the exit code should be {code:d}"))
def exit_code_should_be(test_context, code):
    """Exit code should be specific value"""
    if "cli_result" in test_context:
        result = test_context["cli_result"]
        assert result.returncode == code


@then('the pattern type should be detected as "mkIf_home_packages"')
def pattern_type_should_be_mkif_home_packages(test_context):
    """Pattern type should be mkIf_home_packages"""
    result = test_context["scan_result"]
    assert result.pattern_type == PatternType.MKIF_HOME_PACKAGES


@then("only similar mkIf home.packages patterns should be found")
def only_mkif_home_packages_found(test_context):
    """Only mkIf home.packages patterns should be found"""
    result = test_context["scan_result"]
    for match in result.matches:
        assert match.pattern_type == PatternType.MKIF_HOME_PACKAGES


@then(parsers.parse("the JSON output should show count as {count:d}"))
def json_output_count(test_context, count):
    """JSON output should show specific count"""
    if "scan_result" in test_context:
        result = test_context["scan_result"]
        json_data = json.loads(result.to_json())
        assert json_data["count"] == count
    elif "cli_result" in test_context:
        result = test_context["cli_result"]
        json_data = json.loads(result.stdout)
        assert json_data["count"] == count


@then("the output should indicate no patterns found")
def output_indicates_no_patterns(test_context):
    """Output should indicate no patterns found"""
    result = test_context["scan_result"]
    assert result.count == 0


@then("an error message should be displayed")
def error_message_displayed(test_context):
    """Error message should be displayed"""
    result = test_context["cli_result"]
    assert result.stderr or result.returncode != 0


@then("an error message should indicate file not found")
def error_message_file_not_found(test_context):
    """Error message should indicate file not found"""
    result = test_context["cli_result"]
    assert "not found" in result.stderr.lower() or result.returncode == 255
