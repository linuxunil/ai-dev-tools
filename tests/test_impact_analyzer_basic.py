"""
Basic tests for ImpactAnalyzer - Core functionality validation
"""

import tempfile
from pathlib import Path

import pytest

from ai_dev_tools.core.impact_analyzer import (
    ImpactAnalyzer,
    ImpactSeverity,
    ImpactType,
)


class TestImpactAnalyzer:
    """Test ImpactAnalyzer core functionality"""

    def test_analyzer_initialization(self):
        """Test analyzer can be initialized with project path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ImpactAnalyzer(Path(temp_dir))
            assert analyzer.project_path == Path(temp_dir).resolve()

    def test_analyzer_invalid_path(self):
        """Test analyzer raises error for invalid paths"""
        with pytest.raises(FileNotFoundError):
            ImpactAnalyzer(Path("nonexistent_directory"))

    def test_analyzer_file_as_project_path(self):
        """Test analyzer raises error when project path is a file"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(NotADirectoryError):
                ImpactAnalyzer(Path(temp_file.name))

    def test_isolated_file_no_impact(self):
        """Test analyzing an isolated file with no dependencies"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create an isolated file
            isolated_file = temp_path / "isolated.txt"
            isolated_file.write_text("This is an isolated file with no dependencies.")

            analysis = analyzer.analyze_file_impact(isolated_file)

            assert analysis.target_file == "isolated.txt"
            assert analysis.total_impacted_files == 0
            assert analysis.severity_score == 0
            assert analysis.max_severity == ImpactSeverity.NONE
            assert len(analysis.impacted_files) == 0
            assert "No impact detected" in analysis.summary

    def test_dependency_impact_detection(self):
        """Test detection of dependency impact"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create a module file
            module_file = temp_path / "utils.py"
            module_file.write_text("def helper_function():\n    return 'helper'")

            # Create a file that imports the module
            dependent_file = temp_path / "main.py"
            dependent_file.write_text("from utils import helper_function\n\nprint(helper_function())")

            analysis = analyzer.analyze_file_impact(module_file)

            assert analysis.total_impacted_files > 0
            assert analysis.severity_score > 0
            assert any(impact.impact_type == ImpactType.DEPENDENCY_IMPACT for impact in analysis.impacted_files)

            # Check that main.py is identified as impacted
            impacted_paths = [impact.path for impact in analysis.impacted_files]
            assert "main.py" in impacted_paths

    def test_api_impact_detection(self):
        """Test detection of API impact"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create an API file with function definitions
            api_file = temp_path / "api.py"
            api_file.write_text("""
def public_function():
    return "public"

class PublicClass:
    def method(self):
        return "method"
""")

            # Create a file that uses the API
            consumer_file = temp_path / "consumer.py"
            consumer_file.write_text("""
from api import public_function, PublicClass

result = public_function()
obj = PublicClass()
obj.method()
""")

            analysis = analyzer.analyze_file_impact(api_file)

            assert analysis.total_impacted_files > 0
            api_impacts = [impact for impact in analysis.impacted_files if impact.impact_type == ImpactType.API_IMPACT]
            assert len(api_impacts) > 0

            # Check that consumer.py is identified as impacted
            impacted_paths = [impact.path for impact in analysis.impacted_files]
            assert "consumer.py" in impacted_paths

    def test_configuration_impact_detection(self):
        """Test detection of configuration impact"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create a configuration file
            config_file = temp_path / "config.json"
            config_file.write_text('{"setting": "value"}')

            # Create a build file that might be affected
            build_file = temp_path / "package.json"
            build_file.write_text('{"name": "test", "scripts": {"build": "build"}}')

            analysis = analyzer.analyze_file_impact(config_file)

            assert analysis.total_impacted_files > 0
            config_impacts = [
                impact for impact in analysis.impacted_files if impact.impact_type == ImpactType.CONFIGURATION_IMPACT
            ]
            assert len(config_impacts) > 0

    def test_build_impact_detection(self):
        """Test detection of build system impact"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create some code files
            (temp_path / "src").mkdir()
            (temp_path / "src" / "main.py").write_text("print('hello')")
            (temp_path / "src" / "utils.py").write_text("def util(): pass")

            # Create a build file
            build_file = temp_path / "pyproject.toml"
            build_file.write_text("""
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
""")

            analysis = analyzer.analyze_file_impact(build_file)

            assert analysis.total_impacted_files > 0
            assert analysis.max_severity == ImpactSeverity.CRITICAL
            build_impacts = [
                impact for impact in analysis.impacted_files if impact.impact_type == ImpactType.BUILD_IMPACT
            ]
            assert len(build_impacts) > 0

    def test_test_impact_detection(self):
        """Test detection of test-related impact"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create a code file
            code_file = temp_path / "calculator.py"
            code_file.write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")

            # Create a test file
            test_file = temp_path / "test_calculator.py"
            test_file.write_text("""
from calculator import add, multiply

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(2, 3) == 6
""")

            # Test impact of changing the code file
            analysis = analyzer.analyze_file_impact(code_file)

            test_impacts = [
                impact for impact in analysis.impacted_files if impact.impact_type == ImpactType.TEST_IMPACT
            ]
            assert len(test_impacts) > 0

            # Check that test file is identified
            impacted_paths = [impact.path for impact in analysis.impacted_files]
            assert "test_calculator.py" in impacted_paths

    def test_severity_calculation(self):
        """Test severity score calculation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create a file with multiple types of impact
            central_file = temp_path / "central.py"
            central_file.write_text("""
def important_function():
    return "important"

class CriticalClass:
    pass
""")

            # Create multiple dependent files
            for i in range(5):
                dependent = temp_path / f"dependent_{i}.py"
                dependent.write_text("from central import important_function\nresult = important_function()")

            analysis = analyzer.analyze_file_impact(central_file)

            # Should have a significant severity score due to multiple dependencies
            assert analysis.severity_score > 10
            assert analysis.max_severity in [ImpactSeverity.MEDIUM, ImpactSeverity.HIGH]

    def test_recommendations_generation(self):
        """Test that appropriate recommendations are generated"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create an API file
            api_file = temp_path / "api.py"
            api_file.write_text("def api_function(): pass")

            # Create a consumer
            consumer_file = temp_path / "consumer.py"
            consumer_file.write_text("from api import api_function")

            analysis = analyzer.analyze_file_impact(api_file)

            assert len(analysis.recommendations) > 0
            # Should contain API-related recommendations
            rec_text = " ".join(analysis.recommendations).lower()
            assert "api" in rec_text or "compatibility" in rec_text

    def test_file_outside_project(self):
        """Test analyzing a file outside the project directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create a file outside the project
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as external_file:
                external_file.write("def external_function(): pass")
                external_file_path = Path(external_file.name)

            try:
                analysis = analyzer.analyze_file_impact(external_file_path)

                # Should still work, but likely show no impact
                assert analysis.target_file == str(external_file_path)
                assert analysis.total_impacted_files == 0

            finally:
                external_file_path.unlink()  # Clean up

    def test_nonexistent_file_error(self):
        """Test error handling for non-existent target file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            with pytest.raises(FileNotFoundError):
                analyzer.analyze_file_impact(temp_path / "nonexistent.py")

    def test_file_type_detection(self):
        """Test file type detection methods"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Test code file detection
            code_files = ["test.py", "test.js", "test.ts", "test.rs", "test.go"]
            for filename in code_files:
                path = temp_path / filename
                assert analyzer._is_code_file(path), f"{filename} should be detected as code file"

            # Test config file detection
            config_files = [
                "config.json",
                "settings.yaml",
                "package.json",
                "pyproject.toml",
            ]
            for filename in config_files:
                path = temp_path / filename
                assert analyzer._is_config_file(path), f"{filename} should be detected as config file"

            # Test test file detection
            test_files = [
                "test_module.py",
                "module_test.py",
                "test.spec.js",
                "component.test.ts",
            ]
            for filename in test_files:
                path = temp_path / filename
                assert analyzer._is_test_file(path), f"{filename} should be detected as test file"

    def test_api_extraction(self):
        """Test API definition extraction"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Test Python API extraction
            python_file = temp_path / "api.py"
            python_content = """
def function_one():
    pass

class ClassOne:
    pass

variable_one = "value"
"""
            python_file.write_text(python_content)

            apis = analyzer._extract_api_definitions(python_file, python_content)
            assert "function_one" in apis
            assert "ClassOne" in apis
            assert "variable_one" in apis

    def test_summary_generation(self):
        """Test impact summary generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            analyzer = ImpactAnalyzer(temp_path)

            # Create a simple impact scenario
            target_file = temp_path / "target.py"
            target_file.write_text("def target_function(): pass")

            dependent_file = temp_path / "dependent.py"
            dependent_file.write_text("from target import target_function")

            analysis = analyzer.analyze_file_impact(target_file)

            assert "target.py" in analysis.summary
            assert "impact" in analysis.summary.lower()
            if analysis.total_impacted_files > 0:
                assert str(analysis.total_impacted_files) in analysis.summary
