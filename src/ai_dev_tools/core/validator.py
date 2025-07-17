"""
Project Validator - AI-optimized project validation framework

Provides comprehensive project validation including syntax, structure,
dependencies, and best practices. Designed for AI agents to assess
project health and identify issues systematically.
"""

import ast
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationLevel(Enum):
    """Validation severity levels"""

    PASS = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


@dataclass
class ValidationIssue:
    """Individual validation issue"""

    level: ValidationLevel
    category: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "level": self.level.value,
            "level_name": self.level.name,
            "category": self.category,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of project validation"""

    is_valid: bool
    issues: List[ValidationIssue]
    summary: str
    total_files_checked: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "is_valid": self.is_valid,
            "total_issues": len(self.issues),
            "issues_by_level": {
                level.name: len([i for i in self.issues if i.level == level])
                for level in ValidationLevel
            },
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": self.summary,
            "total_files_checked": self.total_files_checked,
        }

    def get_exit_code(self) -> int:
        """Get exit code based on validation results"""
        if not self.issues:
            return 0

        # Return highest severity level found
        max_level = max(issue.level.value for issue in self.issues)
        return min(max_level, 3)  # Cap at 3 for critical


class ProjectValidator:
    """
    AI-optimized project validator

    Validates project structure, syntax, dependencies, and best practices
    """

    def __init__(self, project_path: str = "."):
        """
        Initialize project validator

        Args:
            project_path: Path to the project root
        """
        self.project_path = Path(project_path)
        self.issues: List[ValidationIssue] = []
        self.files_checked = 0

    def validate_project(
        self,
        check_syntax: bool = True,
        check_structure: bool = True,
        check_dependencies: bool = True,
        check_security: bool = True,
    ) -> ValidationResult:
        """
        Perform comprehensive project validation

        Args:
            check_syntax: Check syntax errors in source files
            check_structure: Check project structure and organization
            check_dependencies: Check dependency issues
            check_security: Check for security issues

        Returns:
            ValidationResult with all issues found
        """
        self.issues = []
        self.files_checked = 0

        if check_syntax:
            self._validate_syntax()

        if check_structure:
            self._validate_structure()

        if check_dependencies:
            self._validate_dependencies()

        if check_security:
            self._validate_security()

        # Determine if project is valid (no errors or critical issues)
        is_valid = not any(
            issue.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]
            for issue in self.issues
        )

        summary = self._generate_summary()

        return ValidationResult(
            is_valid=is_valid,
            issues=self.issues,
            summary=summary,
            total_files_checked=self.files_checked,
        )

    def _validate_syntax(self) -> None:
        """Validate syntax of source files"""
        # Python files
        for py_file in self.project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            self.files_checked += 1
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="syntax",
                        message=f"Python syntax error: {e.msg}",
                        file_path=str(py_file.relative_to(self.project_path)),
                        line_number=e.lineno,
                        suggestion="Fix syntax error before proceeding",
                    )
                )
            except Exception as e:
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="syntax",
                        message=f"Could not parse Python file: {str(e)}",
                        file_path=str(py_file.relative_to(self.project_path)),
                    )
                )

        # JSON files
        for json_file in self.project_path.rglob("*.json"):
            if self._should_skip_file(json_file):
                continue

            self.files_checked += 1
            try:
                with open(json_file, encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="syntax",
                        message=f"JSON syntax error: {e.msg}",
                        file_path=str(json_file.relative_to(self.project_path)),
                        line_number=e.lineno,
                        suggestion="Fix JSON syntax error",
                    )
                )

    def _validate_structure(self) -> None:
        """Validate project structure and organization"""
        # Check for common project files
        expected_files = {
            "README.md": "Add README.md for project documentation",
            ".gitignore": "Add .gitignore to exclude unwanted files",
        }

        for filename, suggestion in expected_files.items():
            if not (self.project_path / filename).exists():
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="structure",
                        message=f"Missing {filename}",
                        suggestion=suggestion,
                    )
                )

        # Check for Python project structure
        if (self.project_path / "pyproject.toml").exists() or (
            self.project_path / "setup.py"
        ).exists():
            self._validate_python_structure()

        # Check for JavaScript/Node.js project
        if (self.project_path / "package.json").exists():
            self._validate_js_structure()

    def _validate_python_structure(self) -> None:
        """Validate Python project structure"""
        # Check for source directory
        src_dirs = ["src", "lib"]
        has_src_dir = any((self.project_path / d).exists() for d in src_dirs)

        if not has_src_dir:
            # Check if Python files are in root (less ideal)
            py_files_in_root = list(self.project_path.glob("*.py"))
            if py_files_in_root:
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="structure",
                        message="Python files in project root, consider using src/ directory",
                        suggestion="Move Python modules to src/ directory for better organization",
                    )
                )

        # Check for tests directory
        test_dirs = ["tests", "test"]
        has_test_dir = any((self.project_path / d).exists() for d in test_dirs)

        if not has_test_dir:
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="structure",
                    message="No tests directory found",
                    suggestion="Add tests/ directory with test files",
                )
            )

    def _validate_js_structure(self) -> None:
        """Validate JavaScript/Node.js project structure"""
        # Check for main entry point
        package_json_path = self.project_path / "package.json"
        try:
            with open(package_json_path) as f:
                package_data = json.load(f)

            main_file = package_data.get("main", "index.js")
            if not (self.project_path / main_file).exists():
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="structure",
                        message=f"Main entry point {main_file} not found",
                        suggestion=f"Create {main_file} or update package.json main field",
                    )
                )
        except Exception:
            pass  # Already handled in syntax validation

    def _validate_dependencies(self) -> None:
        """Validate project dependencies"""
        # Python dependencies
        if (self.project_path / "pyproject.toml").exists():
            self._validate_python_dependencies()
        elif (self.project_path / "requirements.txt").exists():
            self._validate_requirements_txt()

        # JavaScript dependencies
        if (self.project_path / "package.json").exists():
            self._validate_npm_dependencies()

    def _validate_python_dependencies(self) -> None:
        """Validate Python dependencies in pyproject.toml"""
        try:
            import tomllib
        except ImportError:
            # For Python < 3.11, we'll skip detailed TOML validation
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="dependencies",
                    message="Cannot validate pyproject.toml - tomllib not available",
                    suggestion="Upgrade to Python 3.11+ for full TOML validation",
                )
            )
            return

        try:
            with open(self.project_path / "pyproject.toml", "rb") as f:
                data = tomllib.load(f)

            # Check for basic project metadata
            project = data.get("project", {})
            if not project.get("name"):
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="dependencies",
                        message="Missing project name in pyproject.toml",
                        suggestion="Add project.name field",
                    )
                )

            if not project.get("version"):
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="dependencies",
                        message="Missing project version in pyproject.toml",
                        suggestion="Add project.version field",
                    )
                )

        except Exception as e:
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="dependencies",
                    message=f"Error reading pyproject.toml: {str(e)}",
                    suggestion="Fix pyproject.toml format",
                )
            )

    def _validate_requirements_txt(self) -> None:
        """Validate requirements.txt file"""
        try:
            with open(self.project_path / "requirements.txt") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Basic validation of requirement format
                    if not re.match(
                        r"^[a-zA-Z0-9_-]+([><=!]+[0-9.]+)?$", line.split()[0]
                    ):
                        self.issues.append(
                            ValidationIssue(
                                level=ValidationLevel.WARNING,
                                category="dependencies",
                                message=f"Potentially invalid requirement format: {line}",
                                file_path="requirements.txt",
                                line_number=i,
                                suggestion="Check requirement format",
                            )
                        )

        except Exception as e:
            self.issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="dependencies",
                    message=f"Error reading requirements.txt: {str(e)}",
                    suggestion="Fix requirements.txt format",
                )
            )

    def _validate_npm_dependencies(self) -> None:
        """Validate npm dependencies in package.json"""
        try:
            with open(self.project_path / "package.json") as f:
                data = json.load(f)

            # Check for basic fields
            required_fields = ["name", "version"]
            for field in required_fields:
                if not data.get(field):
                    self.issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category="dependencies",
                            message=f"Missing {field} in package.json",
                            suggestion=f"Add {field} field to package.json",
                        )
                    )

            # Check if node_modules exists but package-lock.json doesn't
            if (self.project_path / "node_modules").exists() and not (
                self.project_path / "package-lock.json"
            ).exists():
                self.issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="dependencies",
                        message="node_modules exists but package-lock.json missing",
                        suggestion="Run 'npm install' to generate package-lock.json",
                    )
                )

        except Exception:
            pass  # Already handled in syntax validation

    def _validate_security(self) -> None:
        """Validate security aspects of the project"""
        # Check for common security issues
        security_patterns = {
            r'password\s*=\s*["\'][^"\']+["\']': "Hardcoded password detected",
            r'api_key\s*=\s*["\'][^"\']+["\']': "Hardcoded API key detected",
            r'secret\s*=\s*["\'][^"\']+["\']': "Hardcoded secret detected",
            r'token\s*=\s*["\'][^"\']+["\']': "Hardcoded token detected",
        }

        for py_file in self.project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                for pattern, message in security_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        self.issues.append(
                            ValidationIssue(
                                level=ValidationLevel.CRITICAL,
                                category="security",
                                message=message,
                                file_path=str(py_file.relative_to(self.project_path)),
                                line_number=line_num,
                                suggestion="Use environment variables or secure configuration",
                            )
                        )

            except Exception:
                continue  # Skip files that can't be read

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during validation"""
        skip_patterns = [
            ".git/",
            "__pycache__/",
            ".pytest_cache/",
            "node_modules/",
            ".venv/",
            "venv/",
            ".env/",
            "build/",
            "dist/",
            ".tox/",
        ]

        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def _generate_summary(self) -> str:
        """Generate validation summary"""
        if not self.issues:
            return f"Project validation passed - {self.files_checked} files checked"

        by_level = {}
        for issue in self.issues:
            level_name = issue.level.name
            by_level[level_name] = by_level.get(level_name, 0) + 1

        parts = []
        for level in ["CRITICAL", "ERROR", "WARNING"]:
            if level in by_level:
                parts.append(f"{by_level[level]} {level.lower()}")

        return f"Found {len(self.issues)} issues ({', '.join(parts)}) in {self.files_checked} files"
