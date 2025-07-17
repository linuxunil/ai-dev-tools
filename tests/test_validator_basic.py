"""
Basic tests for ProjectValidator functionality
"""

import json
import tempfile
from pathlib import Path

from ai_dev_tools.core.validator import (
    ProjectValidator,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
)


class TestProjectValidator:
    """Test ProjectValidator core functionality"""

    def test_valid_python_project(self):
        """Test validation of a valid Python project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create valid Python project structure
            (project_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "1.0.0"
dependencies = ["requests>=2.0.0"]
""")
            (project_path / "README.md").write_text("# Test Project")
            (project_path / ".gitignore").write_text("__pycache__/")
            (project_path / "src").mkdir()
            (project_path / "src" / "main.py").write_text("print('Hello World')")
            (project_path / "tests").mkdir()
            (project_path / "tests" / "test_main.py").write_text("def test_main(): pass")

            validator = ProjectValidator(project_path)
            result = validator.validate_project()

            assert result.is_valid
            assert result.total_files_checked >= 3
            assert result.get_exit_code() == 0

    def test_python_syntax_error(self):
        """Test detection of Python syntax errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create Python file with syntax error
            (project_path / "bad_syntax.py").write_text("def broken_function(\n    print('missing closing paren')")

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_structure=False, check_dependencies=False, check_security=False)

            assert not result.is_valid
            assert len(result.issues) >= 1
            syntax_issues = [i for i in result.issues if i.category == "syntax"]
            assert len(syntax_issues) >= 1
            assert syntax_issues[0].level == ValidationLevel.ERROR
            assert result.get_exit_code() == 2

    def test_json_syntax_error(self):
        """Test detection of JSON syntax errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create JSON file with syntax error
            (project_path / "bad.json").write_text('{"key": "value",}')  # Trailing comma

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_structure=False, check_dependencies=False, check_security=False)

            assert not result.is_valid
            syntax_issues = [i for i in result.issues if i.category == "syntax"]
            assert len(syntax_issues) >= 1
            assert syntax_issues[0].level == ValidationLevel.ERROR

    def test_missing_structure_files(self):
        """Test detection of missing structure files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create minimal project without README or .gitignore
            (project_path / "main.py").write_text("print('Hello')")

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_syntax=False, check_dependencies=False, check_security=False)

            structure_issues = [i for i in result.issues if i.category == "structure"]
            assert len(structure_issues) >= 2  # Missing README.md and .gitignore

            readme_issue = next((i for i in structure_issues if "README.md" in i.message), None)
            assert readme_issue is not None
            assert readme_issue.level == ValidationLevel.WARNING

    def test_python_project_structure(self):
        """Test Python-specific structure validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create Python project with files in root (not ideal)
            (project_path / "pyproject.toml").write_text("""
[project]
name = "test"
version = "1.0.0"
""")
            (project_path / "main.py").write_text("print('Hello')")
            (project_path / "utils.py").write_text("def helper(): pass")

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_syntax=False, check_dependencies=False, check_security=False)

            structure_issues = [i for i in result.issues if i.category == "structure"]
            root_files_issue = next((i for i in structure_issues if "root" in i.message), None)
            assert root_files_issue is not None
            assert root_files_issue.level == ValidationLevel.WARNING

    def test_security_hardcoded_secrets(self):
        """Test detection of hardcoded secrets"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create Python file with hardcoded secrets
            (project_path / "config.py").write_text("""
API_KEY = "sk-1234567890abcdef"
password = "secret123"
DATABASE_TOKEN = "token_abc123"
""")

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_syntax=False, check_structure=False, check_dependencies=False)

            security_issues = [i for i in result.issues if i.category == "security"]
            assert len(security_issues) >= 2  # API key and password

            # All security issues should be critical
            for issue in security_issues:
                assert issue.level == ValidationLevel.CRITICAL

            assert result.get_exit_code() == 3

    def test_javascript_project_structure(self):
        """Test JavaScript project structure validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create package.json without main file
            (project_path / "package.json").write_text("""
{
    "name": "test-project",
    "version": "1.0.0",
    "main": "app.js"
}
""")

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_syntax=False, check_dependencies=False, check_security=False)

            structure_issues = [i for i in result.issues if i.category == "structure"]
            main_file_issue = next((i for i in structure_issues if "app.js" in i.message), None)
            assert main_file_issue is not None
            assert main_file_issue.level == ValidationLevel.ERROR

    def test_dependency_validation_pyproject(self):
        """Test Python dependency validation with pyproject.toml"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create pyproject.toml without required fields
            (project_path / "pyproject.toml").write_text("""
[project]
dependencies = ["requests"]
""")

            validator = ProjectValidator(project_path)
            result = validator.validate_project(check_syntax=False, check_structure=False, check_security=False)

            dep_issues = [i for i in result.issues if i.category == "dependencies"]
            assert len(dep_issues) >= 2  # Missing name and version

            name_issue = next((i for i in dep_issues if "name" in i.message), None)
            version_issue = next((i for i in dep_issues if "version" in i.message), None)
            assert name_issue is not None
            assert version_issue is not None

    def test_validation_result_serialization(self):
        """Test ValidationResult serialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create project with some issues
            (project_path / "bad_syntax.py").write_text("def broken(")

            validator = ProjectValidator(project_path)
            result = validator.validate_project()

            # Test to_dict serialization
            result_dict = result.to_dict()
            assert "is_valid" in result_dict
            assert "total_issues" in result_dict
            assert "issues" in result_dict
            assert "summary" in result_dict
            assert "total_files_checked" in result_dict

            # Should be JSON serializable
            json_str = json.dumps(result_dict)
            assert len(json_str) > 0

    def test_validation_issue_serialization(self):
        """Test ValidationIssue serialization"""
        issue = ValidationIssue(
            level=ValidationLevel.ERROR,
            category="test",
            message="Test message",
            file_path="test.py",
            line_number=42,
            suggestion="Fix it",
        )

        issue_dict = issue.to_dict()
        assert issue_dict["level"] == 2
        assert issue_dict["level_name"] == "ERROR"
        assert issue_dict["category"] == "test"
        assert issue_dict["message"] == "Test message"
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 42
        assert issue_dict["suggestion"] == "Fix it"

    def test_exit_code_calculation(self):
        """Test exit code calculation based on issue levels"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            ProjectValidator(project_path)

            # Test no issues
            result = ValidationResult(is_valid=True, issues=[], summary="No issues", total_files_checked=0)
            assert result.get_exit_code() == 0

            # Test warning only
            result = ValidationResult(
                is_valid=True,
                issues=[ValidationIssue(ValidationLevel.WARNING, "test", "warning")],
                summary="Warning",
                total_files_checked=1,
            )
            assert result.get_exit_code() == 1

            # Test error
            result = ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(ValidationLevel.ERROR, "test", "error")],
                summary="Error",
                total_files_checked=1,
            )
            assert result.get_exit_code() == 2

            # Test critical
            result = ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(ValidationLevel.CRITICAL, "test", "critical")],
                summary="Critical",
                total_files_checked=1,
            )
            assert result.get_exit_code() == 3

    def test_skip_validation_options(self):
        """Test skipping different validation types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create file with syntax error and security issue
            (project_path / "bad.py").write_text("""
def broken(
password = "secret123"
""")

            validator = ProjectValidator(project_path)

            # Skip syntax validation
            result = validator.validate_project(check_syntax=False)
            syntax_issues = [i for i in result.issues if i.category == "syntax"]
            assert len(syntax_issues) == 0

            # Skip security validation
            result = validator.validate_project(check_security=False)
            security_issues = [i for i in result.issues if i.category == "security"]
            assert len(security_issues) == 0
