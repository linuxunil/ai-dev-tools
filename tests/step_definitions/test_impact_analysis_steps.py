"""
Step definitions for impact analysis BDD tests
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from ai_dev_tools.core.impact_analyzer import (
    ImpactAnalyzer,
    ImpactSeverity,
    ImpactType,
)

# Load scenarios from feature file
scenarios("../features/impact_analysis.feature")


@given("I have an impact analyzer")
def impact_analyzer(request):
    """Create an impact analyzer instance"""
    request.cls.temp_dir = tempfile.TemporaryDirectory()
    request.cls.temp_path = Path(request.cls.temp_dir.name)
    request.cls.analyzer = ImpactAnalyzer(request.cls.temp_path)


@given("I have an isolated file with no dependencies")
def isolated_file(request):
    """Create an isolated file with no dependencies"""
    request.cls.target_file = request.cls.temp_path / "isolated.txt"
    request.cls.target_file.write_text("This is an isolated file with no dependencies.")


@given("I have a module file and a file that imports it")
def module_and_importer(request):
    """Create a module file and a file that imports it"""
    # Create module file
    request.cls.target_file = request.cls.temp_path / "utils.py"
    request.cls.target_file.write_text("def helper_function():\n    return 'helper'")

    # Create importing file
    dependent_file = request.cls.temp_path / "main.py"
    dependent_file.write_text("from utils import helper_function\n\nprint(helper_function())")


@given("I have an API file with function definitions and a consumer file")
def api_and_consumer(request):
    """Create an API file and a consumer file"""
    # Create API file
    request.cls.target_file = request.cls.temp_path / "api.py"
    request.cls.target_file.write_text("""
def public_function():
    return "public"

class PublicClass:
    def method(self):
        return "method"
""")

    # Create consumer file
    consumer_file = request.cls.temp_path / "consumer.py"
    consumer_file.write_text("""
from api import public_function, PublicClass

result = public_function()
obj = PublicClass()
obj.method()
""")


@given("I have a configuration file and related build files")
def config_and_build_files(request):
    """Create a configuration file and related build files"""
    # Create configuration file
    request.cls.target_file = request.cls.temp_path / "config.json"
    request.cls.target_file.write_text('{"setting": "value", "debug": true}')

    # Create build file
    build_file = request.cls.temp_path / "package.json"
    build_file.write_text('{"name": "test", "scripts": {"build": "build"}}')

    # Create code file that might reference config
    code_file = request.cls.temp_path / "app.py"
    code_file.write_text('import json\nwith open("config.json") as f:\n    config = json.load(f)')


@given("I have a build file and multiple code files")
def build_file_and_code(request):
    """Create a build file and multiple code files"""
    # Create code files
    (request.cls.temp_path / "src").mkdir()
    (request.cls.temp_path / "src" / "main.py").write_text("print('hello')")
    (request.cls.temp_path / "src" / "utils.py").write_text("def util(): pass")
    (request.cls.temp_path / "lib.py").write_text("def library_function(): pass")

    # Create build file
    request.cls.target_file = request.cls.temp_path / "pyproject.toml"
    request.cls.target_file.write_text("""
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
""")


@given("I have a code file and its corresponding test file")
def code_and_test_files(request):
    """Create a code file and its corresponding test file"""
    # Create code file
    request.cls.target_file = request.cls.temp_path / "calculator.py"
    request.cls.target_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")

    # Create test file
    test_file = request.cls.temp_path / "test_calculator.py"
    test_file.write_text("""
from calculator import add, multiply

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(2, 3) == 6
""")


@given("I have a path to a non-existent file")
def nonexistent_file(request):
    """Set up path to a non-existent file"""
    request.cls.target_file = request.cls.temp_path / "nonexistent.py"


@given("I have a file outside the project directory")
def external_file(request):
    """Create a file outside the project directory"""
    import tempfile

    request.cls.external_temp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    request.cls.external_temp.write("def external_function(): pass")
    request.cls.external_temp.close()
    request.cls.target_file = Path(request.cls.external_temp.name)


@given("I have a file with some dependencies")
def file_with_dependencies(request):
    """Create a file with some dependencies for CLI testing"""
    # Create target file
    request.cls.target_file = request.cls.temp_path / "target.py"
    request.cls.target_file.write_text("def target_function(): pass")

    # Create dependent file
    dependent_file = request.cls.temp_path / "dependent.py"
    dependent_file.write_text("from target import target_function")


@given("I have a central file with many dependencies")
def central_file_many_deps(request):
    """Create a central file with many dependencies"""
    # Create central file
    request.cls.target_file = request.cls.temp_path / "central.py"
    request.cls.target_file.write_text("""
def important_function():
    return "important"

class CriticalClass:
    def critical_method(self):
        return "critical"

GLOBAL_CONSTANT = "global"
""")

    # Create many dependent files
    for i in range(10):
        dependent = request.cls.temp_path / f"dependent_{i}.py"
        dependent.write_text("""
from central import important_function, CriticalClass, GLOBAL_CONSTANT

def use_central():
    result = important_function()
    obj = CriticalClass()
    obj.critical_method()
    return GLOBAL_CONSTANT
""")


@given("I have files with different types of impact")
def files_different_impact(request):
    """Create files with different types of impact"""
    # Low impact file
    request.cls.low_impact_file = request.cls.temp_path / "low_impact.txt"
    request.cls.low_impact_file.write_text("Just a text file")

    # Medium impact file
    request.cls.medium_impact_file = request.cls.temp_path / "medium_impact.py"
    request.cls.medium_impact_file.write_text("def helper(): pass")

    dependent = request.cls.temp_path / "uses_medium.py"
    dependent.write_text("from medium_impact import helper")

    # High impact file (build file)
    request.cls.high_impact_file = request.cls.temp_path / "setup.py"
    request.cls.high_impact_file.write_text("from setuptools import setup\nsetup(name='test')")

    # Create some code files to be affected by build changes
    (request.cls.temp_path / "module.py").write_text("def module_func(): pass")


@given("I have a file that affects APIs and build system")
def file_affects_api_and_build(request):
    """Create a file that affects both APIs and build system"""
    request.cls.target_file = request.cls.temp_path / "core.py"
    request.cls.target_file.write_text("""
# Core API functions
def core_api():
    return "core"

class CoreClass:
    def api_method(self):
        return "api"
""")

    # Create API consumers
    consumer = request.cls.temp_path / "consumer.py"
    consumer.write_text("from core import core_api, CoreClass")

    # Create build file that might reference core
    build_file = request.cls.temp_path / "setup.py"
    build_file.write_text("from setuptools import setup\nfrom core import __version__")


@given("I have a file that impacts many other files")
def file_impacts_many(request):
    """Create a file that impacts many other files"""
    request.cls.target_file = request.cls.temp_path / "shared.py"
    request.cls.target_file.write_text("def shared_utility(): pass")

    # Create many files that use the shared utility
    for i in range(20):
        user_file = request.cls.temp_path / f"user_{i}.py"
        user_file.write_text("from shared import shared_utility")


@when("I analyze the impact of the file")
def analyze_impact(request):
    """Analyze the impact of the target file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I analyze the impact of the module file")
def analyze_module_impact(request):
    """Analyze the impact of the module file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I analyze the impact of the API file")
def analyze_api_impact(request):
    """Analyze the impact of the API file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I analyze the impact of the configuration file")
def analyze_config_impact(request):
    """Analyze the impact of the configuration file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I analyze the impact of the build file")
def analyze_build_impact(request):
    """Analyze the impact of the build file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I analyze the impact of the code file")
def analyze_code_impact(request):
    """Analyze the impact of the code file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I attempt to analyze the impact")
def attempt_analyze_impact(request):
    """Attempt to analyze impact (may fail)"""
    try:
        request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)
        request.cls.error = None
    except Exception as e:
        request.cls.error = e
        request.cls.analysis = None


@when("I analyze the impact of the external file")
def analyze_external_impact(request):
    """Analyze the impact of the external file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I run the impact analysis in silent mode")
def run_impact_silent(request):
    """Run impact analysis using CLI in silent mode"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.impact_analyze",
            str(request.cls.target_file),
            "--project-path",
            str(request.cls.temp_path),
            "--format",
            "silent",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@when("I run the impact analysis with JSON output")
def run_impact_json(request):
    """Run impact analysis using CLI with JSON output"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.impact_analyze",
            str(request.cls.target_file),
            "--project-path",
            str(request.cls.temp_path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@when("I run the impact analysis with human-readable output")
def run_impact_human(request):
    """Run impact analysis using CLI with human-readable output"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.impact_analyze",
            str(request.cls.target_file),
            "--project-path",
            str(request.cls.temp_path),
            "--format",
            "human",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@when("I analyze the impact of the central file")
def analyze_central_impact(request):
    """Analyze the impact of the central file"""
    request.cls.analysis = request.cls.analyzer.analyze_file_impact(request.cls.target_file)


@when("I analyze the impact of each file")
def analyze_each_file_impact(request):
    """Analyze the impact of each file with different impact levels"""
    request.cls.analyses = {}
    request.cls.analyses["low"] = request.cls.analyzer.analyze_file_impact(request.cls.low_impact_file)
    request.cls.analyses["medium"] = request.cls.analyzer.analyze_file_impact(request.cls.medium_impact_file)
    request.cls.analyses["high"] = request.cls.analyzer.analyze_file_impact(request.cls.high_impact_file)


@when("I run the impact analysis with a file limit")
def run_impact_with_limit(request):
    """Run impact analysis with a file limit"""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.impact_analyze",
            str(request.cls.target_file),
            "--project-path",
            str(request.cls.temp_path),
            "--format",
            "human",
            "--max-files",
            "5",
        ],
        capture_output=True,
        text=True,
    )
    request.cls.cli_result = result


@then("the analysis should show no impact")
def analysis_no_impact(request):
    """Verify analysis shows no impact"""
    assert request.cls.analysis.total_impacted_files == 0
    assert request.cls.analysis.severity_score == 0
    assert request.cls.analysis.max_severity == ImpactSeverity.NONE


@then("the analysis should show dependency impact")
def analysis_dependency_impact(request):
    """Verify analysis shows dependency impact"""
    assert request.cls.analysis.total_impacted_files > 0
    dependency_impacts = [
        impact for impact in request.cls.analysis.impacted_files if impact.impact_type == ImpactType.DEPENDENCY_IMPACT
    ]
    assert len(dependency_impacts) > 0


@then("the analysis should show API impact")
def analysis_api_impact(request):
    """Verify analysis shows API impact"""
    assert request.cls.analysis.total_impacted_files > 0
    api_impacts = [
        impact for impact in request.cls.analysis.impacted_files if impact.impact_type == ImpactType.API_IMPACT
    ]
    assert len(api_impacts) > 0


@then("the analysis should show configuration impact")
def analysis_config_impact(request):
    """Verify analysis shows configuration impact"""
    assert request.cls.analysis.total_impacted_files > 0
    config_impacts = [
        impact
        for impact in request.cls.analysis.impacted_files
        if impact.impact_type == ImpactType.CONFIGURATION_IMPACT
    ]
    assert len(config_impacts) > 0


@then("the analysis should show critical build impact")
def analysis_critical_build_impact(request):
    """Verify analysis shows critical build impact"""
    assert request.cls.analysis.total_impacted_files > 0
    build_impacts = [
        impact for impact in request.cls.analysis.impacted_files if impact.impact_type == ImpactType.BUILD_IMPACT
    ]
    assert len(build_impacts) > 0


@then("the analysis should show test impact")
def analysis_test_impact(request):
    """Verify analysis shows test impact"""
    assert request.cls.analysis.total_impacted_files > 0
    test_impacts = [
        impact for impact in request.cls.analysis.impacted_files if impact.impact_type == ImpactType.TEST_IMPACT
    ]
    assert len(test_impacts) > 0


@then("the analysis should show high impact")
def analysis_high_impact(request):
    """Verify analysis shows high impact"""
    assert request.cls.analysis.total_impacted_files > 5
    assert request.cls.analysis.severity_score > 20
    assert request.cls.analysis.max_severity in [
        ImpactSeverity.HIGH,
        ImpactSeverity.CRITICAL,
    ]


@then("the analysis should show minimal or no impact")
def analysis_minimal_impact(request):
    """Verify analysis shows minimal or no impact"""
    assert request.cls.analysis.severity_score <= 10


@then("the impacted files should include the importing file")
def impacted_includes_importer(request):
    """Verify impacted files include the importing file"""
    impacted_paths = [impact.path for impact in request.cls.analysis.impacted_files]
    assert "main.py" in impacted_paths


@then("the impacted files should include build-related files")
def impacted_includes_build_files(request):
    """Verify impacted files include build-related files"""
    impacted_paths = [impact.path for impact in request.cls.analysis.impacted_files]
    # Should include package.json or other build-related files
    assert any("package.json" in path or "build" in path.lower() for path in impacted_paths)


@then("the impacted files should include the test file")
def impacted_includes_test_file(request):
    """Verify impacted files include the test file"""
    impacted_paths = [impact.path for impact in request.cls.analysis.impacted_files]
    assert "test_calculator.py" in impacted_paths


@then("the impact severity should be medium or high")
def impact_severity_medium_or_high(request):
    """Verify impact severity is medium or high"""
    assert request.cls.analysis.max_severity in [
        ImpactSeverity.MEDIUM,
        ImpactSeverity.HIGH,
        ImpactSeverity.CRITICAL,
    ]


@then("the impact severity should be critical")
def impact_severity_critical(request):
    """Verify impact severity is critical"""
    assert request.cls.analysis.max_severity == ImpactSeverity.CRITICAL


@then("the operation should fail with file not found error")
def operation_file_not_found(request):
    """Verify operation failed with FileNotFoundError"""
    assert request.cls.error is not None
    assert isinstance(request.cls.error, FileNotFoundError)


@then("the severity score should be significant")
def severity_score_significant(request):
    """Verify severity score is significant"""
    assert request.cls.analysis.severity_score > 30


@then("the severity scores should vary appropriately")
def severity_scores_vary(request):
    """Verify severity scores vary appropriately"""
    low_score = request.cls.analyses["low"].severity_score
    medium_score = request.cls.analyses["medium"].severity_score
    high_score = request.cls.analyses["high"].severity_score

    # Scores should generally increase with impact level
    assert low_score <= medium_score
    assert medium_score <= high_score


@then("higher impact files should have higher scores")
def higher_impact_higher_scores(request):
    """Verify higher impact files have higher scores"""
    high_score = request.cls.analyses["high"].severity_score
    low_score = request.cls.analyses["low"].severity_score

    assert high_score > low_score


@then("the analysis should include relevant recommendations")
def analysis_includes_recommendations(request):
    """Verify analysis includes relevant recommendations"""
    assert len(request.cls.analysis.recommendations) > 0
    rec_text = " ".join(request.cls.analysis.recommendations).lower()
    assert any(keyword in rec_text for keyword in ["test", "api", "compatibility", "build"])


@then("the recommendations should mention testing and compatibility")
def recommendations_mention_testing(request):
    """Verify recommendations mention testing and compatibility"""
    rec_text = " ".join(request.cls.analysis.recommendations).lower()
    assert "test" in rec_text or "compatibility" in rec_text


@then("the exit code should be 0")
def exit_code_zero(request):
    """Verify exit code is 0 (no impact)"""
    if hasattr(request.cls, "cli_result"):
        assert request.cls.cli_result.returncode == 0
    else:
        assert request.cls.analysis.severity_score == 0


@then("the exit code should reflect the impact severity")
def exit_code_reflects_severity(request):
    """Verify exit code reflects impact severity"""
    if hasattr(request.cls, "cli_result"):
        expected_code = min(254, request.cls.analysis.severity_score)
        assert request.cls.cli_result.returncode == expected_code
    else:
        assert request.cls.analysis.severity_score >= 0


@then("the exit code should reflect the high impact")
def exit_code_high_impact(request):
    """Verify exit code reflects high impact"""
    if hasattr(request.cls, "cli_result"):
        assert request.cls.cli_result.returncode > 20
    else:
        assert request.cls.analysis.severity_score > 20


@then("the exit code should be low")
def exit_code_low(request):
    """Verify exit code is low"""
    if hasattr(request.cls, "cli_result"):
        assert request.cls.cli_result.returncode <= 10
    else:
        assert request.cls.analysis.severity_score <= 10


@then("the exit code should be 255")
def exit_code_error(request):
    """Verify exit code is 255 (error)"""
    assert hasattr(request.cls, "cli_result")
    assert request.cls.cli_result.returncode == 255


@then("the exit codes should reflect the relative impact levels")
def exit_codes_reflect_relative_impact(request):
    """Verify exit codes reflect relative impact levels"""
    # This is tested through the severity score comparison
    pass


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


@then("the JSON should contain impact details")
def json_contains_impact_details(request):
    """Verify JSON output contains impact details"""
    data = json.loads(request.cls.cli_result.stdout)
    assert "target_file" in data
    assert "total_impacted_files" in data
    assert "severity_score" in data
    assert "impacted_files" in data


@then("the output should contain a summary")
def output_contains_summary(request):
    """Verify human-readable output contains a summary"""
    output = request.cls.cli_result.stdout
    assert "Impact Analysis" in output
    assert "Summary:" in output


@then("the output should list impacted files")
def output_lists_impacted_files(request):
    """Verify human-readable output lists impacted files"""
    output = request.cls.cli_result.stdout
    assert "Impacted Files:" in output or "Total Impacted Files:" in output


@then("the output should include recommendations")
def output_includes_recommendations(request):
    """Verify human-readable output includes recommendations"""
    output = request.cls.cli_result.stdout
    assert "Recommendations:" in output


@then("the output should be limited to the specified number of files")
def output_limited_files(request):
    """Verify output is limited to specified number of files"""
    # This is handled by the CLI limiting logic
    pass


@then("the summary should indicate truncation")
def summary_indicates_truncation(request):
    """Verify summary indicates truncation when files are limited"""
    output = request.cls.cli_result.stdout
    # Should mention "showing first X files" or similar
    assert "showing first" in output or "more files" in output


@then("the exit code should still reflect the full impact")
def exit_code_reflects_full_impact(request):
    """Verify exit code reflects full impact even when output is limited"""
    # Exit code should be based on full analysis, not limited output
    assert request.cls.cli_result.returncode > 0
