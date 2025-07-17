"""
Step definitions for difference analysis BDD tests
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from ai_dev_tools.core.difference_analyzer import (
    ChangeSignificance,
    DifferenceAnalyzer,
    DifferenceType,
)

# Load scenarios from feature file
scenarios("../features/difference_analysis.feature")


@given("I have a difference analyzer")
def difference_analyzer(request):
    """Create a difference analyzer instance"""
    request.cls.analyzer = DifferenceAnalyzer()
    request.cls.temp_dir = tempfile.TemporaryDirectory()
    request.cls.temp_path = Path(request.cls.temp_dir.name)


@given("I have two identical text files")
def identical_text_files(request):
    """Create two identical text files"""
    content = "Hello, world!\nThis is a test file.\nWith multiple lines.\n"

    request.cls.file1 = request.cls.temp_path / "file1.txt"
    request.cls.file2 = request.cls.temp_path / "file2.txt"

    request.cls.file1.write_text(content)
    request.cls.file2.write_text(content)


@given("I have two text files with minor content differences")
def minor_different_text_files(request):
    """Create two text files with minor differences"""
    content1 = "Hello, world!\nThis is a test file.\nWith multiple lines.\n"
    content2 = "Hello, world!\nThis is a test file.\nWith some different lines.\n"

    request.cls.file1 = request.cls.temp_path / "file1.txt"
    request.cls.file2 = request.cls.temp_path / "file2.txt"

    request.cls.file1.write_text(content1)
    request.cls.file2.write_text(content2)


@given("I have two Python files with function definition changes")
def critical_different_python_files(request):
    """Create two Python files with critical differences"""
    content1 = "def old_function():\n    return 'old'\n\nprint('test')\n"
    content2 = "def new_function():\n    return 'new'\n\nprint('test')\n"

    request.cls.file1 = request.cls.temp_path / "file1.py"
    request.cls.file2 = request.cls.temp_path / "file2.py"

    request.cls.file1.write_text(content1)
    request.cls.file2.write_text(content2)


@given("I have two files that differ only in whitespace")
def whitespace_different_files(request):
    """Create two files that differ only in whitespace"""
    content1 = "Hello, world!\nThis is a test.\n"
    content2 = "Hello, world!   \n  This is a test.  \n"  # Extra whitespace

    request.cls.file1 = request.cls.temp_path / "file1.txt"
    request.cls.file2 = request.cls.temp_path / "file2.txt"

    request.cls.file1.write_text(content1)
    request.cls.file2.write_text(content2)


@given("I have two directories with added, removed, and modified files")
def mixed_directories(request):
    """Create two directories with various types of changes"""
    request.cls.dir1 = request.cls.temp_path / "dir1"
    request.cls.dir2 = request.cls.temp_path / "dir2"

    request.cls.dir1.mkdir()
    request.cls.dir2.mkdir()

    # Common file (identical)
    (request.cls.dir1 / "common.txt").write_text("Common content\n")
    (request.cls.dir2 / "common.txt").write_text("Common content\n")

    # Modified file
    (request.cls.dir1 / "modified.txt").write_text("Original content\n")
    (request.cls.dir2 / "modified.txt").write_text("Modified content\n")

    # File only in dir1 (removed)
    (request.cls.dir1 / "removed.txt").write_text("This will be removed\n")

    # File only in dir2 (added)
    (request.cls.dir2 / "added.txt").write_text("This is new\n")


@given("I have paths to non-existent files")
def nonexistent_files(request):
    """Set up paths to non-existent files"""
    request.cls.file1 = request.cls.temp_path / "nonexistent1.txt"
    request.cls.file2 = request.cls.temp_path / "nonexistent2.txt"


@given("I have two different binary files")
def different_binary_files(request):
    """Create two different binary files"""
    request.cls.file1 = request.cls.temp_path / "binary1.bin"
    request.cls.file2 = request.cls.temp_path / "binary2.bin"

    request.cls.file1.write_bytes(b"\\x00\\x01\\x02\\x03")
    request.cls.file2.write_bytes(b"\\x00\\x01\\x02\\x04")  # Different last byte


@given("I have two different text files")
def different_text_files(request):
    """Create two different text files for CLI testing"""
    content1 = "Hello, world!\nThis is file 1.\n"
    content2 = "Hello, universe!\nThis is file 2.\n"

    request.cls.file1 = request.cls.temp_path / "file1.txt"
    request.cls.file2 = request.cls.temp_path / "file2.txt"

    request.cls.file1.write_text(content1)
    request.cls.file2.write_text(content2)


@given("I have two directories with many differences")
def many_differences_directories(request):
    """Create directories with many differences to test exit code capping"""
    request.cls.dir1 = request.cls.temp_path / "dir1"
    request.cls.dir2 = request.cls.temp_path / "dir2"

    request.cls.dir1.mkdir()
    request.cls.dir2.mkdir()

    # Create many different files to test exit code capping
    for i in range(300):  # More than 254 to test capping
        (request.cls.dir1 / f"file{i}.txt").write_text(f"Content {i} original\n")
        (request.cls.dir2 / f"file{i}.txt").write_text(f"Content {i} modified\n")


@when("I compare the files")
def compare_files(request):
    """Compare the files using the analyzer"""
    request.cls.analysis = request.cls.analyzer.compare_files(request.cls.file1, request.cls.file2)


@when("I compare the files with whitespace ignored")
def compare_files_ignore_whitespace(request):
    """Compare files with whitespace ignored"""
    analyzer = DifferenceAnalyzer(ignore_whitespace=True)
    request.cls.analysis = analyzer.compare_files(request.cls.file1, request.cls.file2)


@when("I compare the files with whitespace not ignored")
def compare_files_strict_whitespace(request):
    """Compare files with strict whitespace handling"""
    analyzer = DifferenceAnalyzer(ignore_whitespace=False)
    request.cls.analysis = analyzer.compare_files(request.cls.file1, request.cls.file2)


@when("I compare the directories")
def compare_directories(request):
    """Compare the directories using the analyzer"""
    request.cls.analysis = request.cls.analyzer.compare_directories(request.cls.dir1, request.cls.dir2)


@when("I attempt to compare the files")
def attempt_compare_files(request):
    """Attempt to compare files (may fail)"""
    try:
        request.cls.analysis = request.cls.analyzer.compare_files(request.cls.file1, request.cls.file2)
        request.cls.error = None
    except Exception as e:
        request.cls.error = e
        request.cls.analysis = None


@when("I run the comparison in silent mode")
def run_comparison_silent(request):
    """Run comparison using CLI in silent mode"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.difference_analyze",
            str(request.cls.file1),
            str(request.cls.file2),
            "--format",
            "silent",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@when("I run the comparison with JSON output")
def run_comparison_json(request):
    """Run comparison using CLI with JSON output"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.difference_analyze",
            str(request.cls.file1),
            str(request.cls.file2),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@when("I run the comparison with human-readable output")
def run_comparison_human(request):
    """Run comparison using CLI with human-readable output"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.difference_analyze",
            str(request.cls.file1),
            str(request.cls.file2),
            "--format",
            "human",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@then("the analysis should show no differences")
def analysis_no_differences(request):
    """Verify analysis shows no differences"""
    assert request.cls.analysis.total_differences == 0
    assert request.cls.analysis.significant_differences == 0


@then("the analysis should show 1 difference")
def analysis_one_difference(request):
    """Verify analysis shows exactly one difference"""
    assert request.cls.analysis.total_differences == 1
    assert len(request.cls.analysis.differences) == 1


@then("the analysis should show multiple differences")
def analysis_multiple_differences(request):
    """Verify analysis shows multiple differences"""
    assert request.cls.analysis.total_differences > 1
    assert len(request.cls.analysis.differences) > 1


@then("the difference should be marked as minor or major significance")
def difference_minor_or_major(request):
    """Verify difference significance is minor or major"""
    diff = request.cls.analysis.differences[0]
    assert diff.significance in [ChangeSignificance.MINOR, ChangeSignificance.MAJOR]


@then("the difference should be marked as critical significance")
def difference_critical(request):
    """Verify difference significance is critical"""
    diff = request.cls.analysis.differences[0]
    assert diff.significance == ChangeSignificance.CRITICAL


@then("the analysis should correctly count added, removed, and modified files")
def analysis_correct_counts(request):
    """Verify file change counts are correct"""
    analysis = request.cls.analysis
    assert analysis.files_added == 1  # added.txt
    assert analysis.files_removed == 1  # removed.txt
    assert analysis.files_modified == 1  # modified.txt


@then("the operation should fail with file not found error")
def operation_file_not_found(request):
    """Verify operation failed with FileNotFoundError"""
    assert request.cls.error is not None
    assert isinstance(request.cls.error, FileNotFoundError)


@then("the analysis should detect binary file changes")
def analysis_binary_changes(request):
    """Verify binary file changes are detected"""
    assert request.cls.analysis.total_differences == 1
    diff = request.cls.analysis.differences[0]
    assert diff.difference_type == DifferenceType.CONTENT_CHANGED
    assert "Binary file changed" in diff.details


@then("the exit code should be 0")
def exit_code_zero(request):
    """Verify exit code is 0 (no differences)"""
    if hasattr(request.cls, "cli_result"):
        assert request.cls.cli_result.returncode == 0
    else:
        # For direct API calls, check significant differences
        assert request.cls.analysis.significant_differences == 0


@then("the exit code should be 1")
def exit_code_one(request):
    """Verify exit code is 1 (one significant difference)"""
    if hasattr(request.cls, "cli_result"):
        assert request.cls.cli_result.returncode == 1
    else:
        # For direct API calls, check significant differences
        assert request.cls.analysis.significant_differences == 1


@then("the exit code should reflect the number of significant differences")
def exit_code_reflects_differences(request):
    """Verify exit code reflects number of significant differences"""
    if hasattr(request.cls, "cli_result"):
        expected_code = min(254, request.cls.analysis.significant_differences)
        assert request.cls.cli_result.returncode == expected_code
    else:
        # For direct API calls, just verify we have differences
        assert request.cls.analysis.significant_differences > 0


@then("the exit code should be 255")
def exit_code_error(request):
    """Verify exit code is 255 (error)"""
    assert hasattr(request.cls, "cli_result")
    assert request.cls.cli_result.returncode == 255


@then("the exit code should be capped at 254")
def exit_code_capped(request):
    """Verify exit code is capped at 254"""
    if hasattr(request.cls, "cli_result"):
        assert request.cls.cli_result.returncode <= 254
    else:
        # For direct API calls, verify we handle large numbers
        assert request.cls.analysis.significant_differences > 254


@then("there should be no output")
def no_output(request):
    """Verify there is no output in silent mode"""
    assert request.cls.cli_result.stdout == ""


@then("the output should be valid JSON")
def output_valid_json(request):
    """Verify output is valid JSON"""
    try:
        json.loads(request.cls.cli_result.stdout)
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"


@then("the JSON should contain difference details")
def json_contains_details(request):
    """Verify JSON output contains difference details"""
    data = json.loads(request.cls.cli_result.stdout)
    assert "total_differences" in data
    assert "significant_differences" in data
    assert "differences" in data


@then("the output should contain a summary")
def output_contains_summary(request):
    """Verify human-readable output contains a summary"""
    output = request.cls.cli_result.stdout
    assert "Difference Analysis" in output
    assert "Summary:" in output


@then("the output should list individual differences")
def output_lists_differences(request):
    """Verify human-readable output lists individual differences"""
    output = request.cls.cli_result.stdout
    assert "Details:" in output or "differences" in output.lower()


@then("the analysis should handle large numbers of differences gracefully")
def analysis_handles_large_numbers(request):
    """Verify analysis handles large numbers of differences"""
    # Should not crash and should provide meaningful results
    assert request.cls.analysis is not None
    assert request.cls.analysis.total_differences > 0
    assert request.cls.analysis.files_compared > 0
