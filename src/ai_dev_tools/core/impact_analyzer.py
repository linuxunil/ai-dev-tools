"""
Impact Analyzer - Exit-code-first change impact assessment for AI workflows

Analyzes the potential impact of changes across a project by examining dependencies,
usage patterns, and structural relationships. Designed for zero-token AI decision making.

Exit Codes:
- 0-254: Impact severity score (0=no impact, 254=maximum impact)
- 255: Error (file not found, invalid input, etc.)
"""

import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ImpactType(Enum):
    """Types of impact that can be detected"""

    NO_IMPACT = "no_impact"
    DEPENDENCY_IMPACT = "dependency_impact"
    API_IMPACT = "api_impact"
    CONFIGURATION_IMPACT = "configuration_impact"
    BUILD_IMPACT = "build_impact"
    TEST_IMPACT = "test_impact"
    BREAKING_CHANGE = "breaking_change"


class ImpactSeverity(Enum):
    """Severity levels for impact assessment"""

    NONE = "none"  # No impact detected
    LOW = "low"  # Minimal impact, isolated changes
    MEDIUM = "medium"  # Moderate impact, affects related components
    HIGH = "high"  # Significant impact, affects multiple systems
    CRITICAL = "critical"  # Breaking changes, major refactoring needed


@dataclass
class ImpactedFile:
    """Information about a file impacted by changes"""

    path: str
    impact_type: ImpactType
    severity: ImpactSeverity
    reason: str
    line_numbers: Optional[List[int]] = None
    suggestions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["impact_type"] = self.impact_type.value
        result["severity"] = self.severity.value
        return result


@dataclass
class ImpactAnalysis:
    """Complete impact analysis result"""

    target_file: str
    total_impacted_files: int
    severity_score: int
    max_severity: ImpactSeverity
    impacted_files: List[ImpactedFile]
    summary: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["max_severity"] = self.max_severity.value
        result["impacted_files"] = [file.to_dict() for file in self.impacted_files]
        return result


class ImpactAnalyzer:
    """Analyzes the potential impact of changes to files across a project"""

    # File extensions that indicate different types of files
    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".rs",
        ".go",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".php",
        ".rb",
        ".swift",
        ".nix",
    }

    CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}

    BUILD_FILES = {
        "Makefile",
        "makefile",
        "CMakeLists.txt",
        "build.gradle",
        "pom.xml",
        "package.json",
        "pyproject.toml",
        "setup.py",
        "Cargo.toml",
        "go.mod",
        "flake.nix",
        "default.nix",
        "shell.nix",
    }

    TEST_PATTERNS = [
        r"test_.*\.py$",
        r".*_test\.py$",
        r".*\.test\.js$",
        r".*\.spec\.js$",
        r".*\.test\.ts$",
        r".*\.spec\.ts$",
        r"test.*\.rs$",
        r".*_test\.go$",
    ]

    # Patterns that indicate API definitions
    API_PATTERNS = {
        "python": [
            r"^def\s+(\w+)",  # Function definitions
            r"^class\s+(\w+)",  # Class definitions
            r"^(\w+)\s*=",  # Variable assignments
        ],
        "javascript": [
            r"^export\s+(?:function\s+)?(\w+)",  # Exported functions
            r"^export\s+(?:const|let|var)\s+(\w+)",  # Exported variables
            r"^(?:function\s+)?(\w+)\s*\(",  # Function definitions
            r"^class\s+(\w+)",  # Class definitions
        ],
        "typescript": [
            r"^export\s+(?:function\s+)?(\w+)",  # Exported functions
            r"^export\s+(?:const|let|var)\s+(\w+)",  # Exported variables
            r"^export\s+interface\s+(\w+)",  # Exported interfaces
            r"^export\s+type\s+(\w+)",  # Exported types
        ],
    }

    def __init__(self, project_path: Path):
        """Initialize analyzer for given project path"""
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        if not self.project_path.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {project_path}")

    def analyze_file_impact(self, target_file: Path) -> ImpactAnalysis:
        """Analyze the impact of changes to a specific file"""
        target_path = Path(target_file).resolve()

        if not target_path.exists():
            raise FileNotFoundError(f"Target file does not exist: {target_file}")

        # Make path relative to project if it's within the project
        try:
            relative_target = target_path.relative_to(self.project_path)
        except ValueError:
            # File is outside project, use absolute path
            relative_target = target_path

        impacted_files = []

        # Analyze different types of impact
        impacted_files.extend(self._analyze_dependency_impact(target_path))
        impacted_files.extend(self._analyze_api_impact(target_path))
        impacted_files.extend(self._analyze_configuration_impact(target_path))
        impacted_files.extend(self._analyze_build_impact(target_path))
        impacted_files.extend(self._analyze_test_impact(target_path))

        # Calculate severity score and max severity
        severity_score = self._calculate_severity_score(impacted_files)
        max_severity = self._get_max_severity(impacted_files)

        # Generate summary and recommendations
        summary = self._generate_summary(impacted_files, str(relative_target))
        recommendations = self._generate_recommendations(impacted_files, target_path)

        return ImpactAnalysis(
            target_file=str(relative_target),
            total_impacted_files=len(impacted_files),
            severity_score=severity_score,
            max_severity=max_severity,
            impacted_files=impacted_files,
            summary=summary,
            recommendations=recommendations,
        )

    def _analyze_dependency_impact(self, target_file: Path) -> List[ImpactedFile]:
        """Analyze impact on files that depend on the target file"""
        impacted = []
        target_name = target_file.stem

        # Search for files that import or reference the target file
        for file_path in self._get_project_files():
            if file_path == target_file:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Check for various import patterns
                import_patterns = [
                    rf"import\s+.*{re.escape(target_name)}",  # Python imports
                    rf"from\s+.*{re.escape(target_name)}",  # Python from imports
                    rf"require\s*\(\s*['\"].*{re.escape(target_name)}",  # JS require
                    rf"import\s+.*from\s+['\"].*{re.escape(target_name)}",  # JS/TS imports
                    rf"#include\s+[\"<].*{re.escape(target_name)}",  # C/C++ includes
                ]

                line_numbers = []
                for i, line in enumerate(content.splitlines(), 1):
                    if any(
                        re.search(pattern, line, re.IGNORECASE)
                        for pattern in import_patterns
                    ):
                        line_numbers.append(i)

                if line_numbers:
                    severity = (
                        ImpactSeverity.MEDIUM
                        if len(line_numbers) > 3
                        else ImpactSeverity.LOW
                    )

                    rel_path = self._get_relative_path(file_path)
                    impacted.append(
                        ImpactedFile(
                            path=str(rel_path),
                            impact_type=ImpactType.DEPENDENCY_IMPACT,
                            severity=severity,
                            reason=f"Imports or references {target_file.name}",
                            line_numbers=line_numbers,
                            suggestions=[f"Review imports in {rel_path}"],
                        )
                    )

            except (UnicodeDecodeError, PermissionError):
                continue

        return impacted

    def _analyze_api_impact(self, target_file: Path) -> List[ImpactedFile]:
        """Analyze impact on API consumers if target file defines APIs"""
        impacted = []

        if not self._is_code_file(target_file):
            return impacted

        try:
            content = target_file.read_text(encoding="utf-8", errors="ignore")

            # Extract API definitions from target file
            api_definitions = self._extract_api_definitions(target_file, content)

            if not api_definitions:
                return impacted

            # Search for usage of these APIs in other files
            for file_path in self._get_project_files():
                if file_path == target_file:
                    continue

                try:
                    file_content = file_path.read_text(
                        encoding="utf-8", errors="ignore"
                    )

                    usage_lines = []
                    for i, line in enumerate(file_content.splitlines(), 1):
                        for api_name in api_definitions:
                            if re.search(rf"\b{re.escape(api_name)}\b", line):
                                usage_lines.append(i)

                    if usage_lines:
                        severity = (
                            ImpactSeverity.HIGH
                            if len(usage_lines) > 5
                            else ImpactSeverity.MEDIUM
                        )

                        rel_path = self._get_relative_path(file_path)
                        impacted.append(
                            ImpactedFile(
                                path=str(rel_path),
                                impact_type=ImpactType.API_IMPACT,
                                severity=severity,
                                reason=f"Uses APIs defined in {target_file.name}",
                                line_numbers=usage_lines[:10],  # Limit to first 10
                                suggestions=[
                                    f"Review API usage in {rel_path}",
                                    "Check for breaking changes",
                                ],
                            )
                        )

                except (UnicodeDecodeError, PermissionError):
                    continue

        except (UnicodeDecodeError, PermissionError):
            pass

        return impacted

    def _analyze_configuration_impact(self, target_file: Path) -> List[ImpactedFile]:
        """Analyze impact of configuration file changes"""
        impacted = []

        if not self._is_config_file(target_file):
            return impacted

        # Configuration files can impact the entire project
        config_impact_files = []

        # Find files that might be affected by configuration changes
        for file_path in self._get_project_files():
            if file_path == target_file:
                continue

            # Build files are highly impacted by config changes
            if file_path.name in self.BUILD_FILES:
                config_impact_files.append(
                    (file_path, ImpactSeverity.HIGH, "Build configuration dependency")
                )

            # Code files may read configuration
            elif self._is_code_file(file_path):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    config_name = target_file.stem

                    # Look for references to the config file
                    if re.search(
                        rf"\b{re.escape(config_name)}\b", content, re.IGNORECASE
                    ):
                        config_impact_files.append(
                            (
                                file_path,
                                ImpactSeverity.MEDIUM,
                                "References configuration",
                            )
                        )

                except (UnicodeDecodeError, PermissionError):
                    continue

        for file_path, severity, reason in config_impact_files:
            rel_path = self._get_relative_path(file_path)
            impacted.append(
                ImpactedFile(
                    path=str(rel_path),
                    impact_type=ImpactType.CONFIGURATION_IMPACT,
                    severity=severity,
                    reason=reason,
                    suggestions=[f"Verify configuration compatibility in {rel_path}"],
                )
            )

        return impacted

    def _analyze_build_impact(self, target_file: Path) -> List[ImpactedFile]:
        """Analyze impact on build system"""
        impacted = []

        if target_file.name in self.BUILD_FILES:
            # Build file changes impact the entire project
            severity = ImpactSeverity.CRITICAL

            # Find all code files that could be affected
            affected_files = [
                f
                for f in self._get_project_files()
                if self._is_code_file(f) and f != target_file
            ]

            # Limit to representative sample to avoid overwhelming output
            for file_path in affected_files[:20]:
                rel_path = self._get_relative_path(file_path)
                impacted.append(
                    ImpactedFile(
                        path=str(rel_path),
                        impact_type=ImpactType.BUILD_IMPACT,
                        severity=severity,
                        reason="Build system change affects compilation/packaging",
                        suggestions=[
                            "Run full build and test suite",
                            "Check for build errors",
                        ],
                    )
                )

        return impacted

    def _analyze_test_impact(self, target_file: Path) -> List[ImpactedFile]:
        """Analyze impact on test files"""
        impacted = []

        # If target is a test file, find what it tests
        if self._is_test_file(target_file):
            tested_file = self._find_tested_file(target_file)
            if tested_file and tested_file.exists():
                rel_path = self._get_relative_path(tested_file)
                impacted.append(
                    ImpactedFile(
                        path=str(rel_path),
                        impact_type=ImpactType.TEST_IMPACT,
                        severity=ImpactSeverity.MEDIUM,
                        reason="Test file changes may indicate issues with tested code",
                        suggestions=[f"Review implementation in {rel_path}"],
                    )
                )

        # If target is a code file, find its tests
        elif self._is_code_file(target_file):
            test_files = self._find_test_files(target_file)
            for test_file in test_files:
                rel_path = self._get_relative_path(test_file)
                impacted.append(
                    ImpactedFile(
                        path=str(rel_path),
                        impact_type=ImpactType.TEST_IMPACT,
                        severity=ImpactSeverity.MEDIUM,
                        reason="Code changes may require test updates",
                        suggestions=[f"Update tests in {rel_path}", "Run test suite"],
                    )
                )

        return impacted

    def _get_project_files(self) -> List[Path]:
        """Get all relevant files in the project"""
        files = []
        ignore_patterns = {
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "target",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".DS_Store",
        }

        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                if any(part in ignore_patterns for part in file_path.parts):
                    continue
                files.append(file_path)

        return files

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file"""
        return file_path.suffix.lower() in self.CODE_EXTENSIONS

    def _is_config_file(self, file_path: Path) -> bool:
        """Check if file is a configuration file"""
        return (
            file_path.suffix.lower() in self.CONFIG_EXTENSIONS
            or file_path.name in self.BUILD_FILES
        )

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file"""
        filename = file_path.name
        return any(re.match(pattern, filename) for pattern in self.TEST_PATTERNS)

    def _extract_api_definitions(self, file_path: Path, content: str) -> List[str]:
        """Extract API definitions from file content"""
        api_names = []
        file_ext = file_path.suffix.lower()

        # Determine language and extract APIs
        if file_ext == ".py":
            patterns = self.API_PATTERNS.get("python", [])
        elif file_ext in [".js", ".jsx"]:
            patterns = self.API_PATTERNS.get("javascript", [])
        elif file_ext in [".ts", ".tsx"]:
            patterns = self.API_PATTERNS.get("typescript", [])
        else:
            return api_names

        for line in content.splitlines():
            for pattern in patterns:
                match = re.search(pattern, line.strip())
                if match:
                    api_names.append(match.group(1))

        return api_names

    def _find_test_files(self, target_file: Path) -> List[Path]:
        """Find test files for a given code file"""
        test_files = []
        target_stem = target_file.stem

        for file_path in self._get_project_files():
            if self._is_test_file(file_path):
                # Check if test file name suggests it tests the target
                if target_stem in file_path.stem:
                    test_files.append(file_path)

        return test_files

    def _find_tested_file(self, test_file: Path) -> Optional[Path]:
        """Find the file that a test file is testing"""
        test_stem = test_file.stem

        # Remove test prefixes/suffixes
        tested_name = re.sub(r"^test_|_test$|\.test$|\.spec$", "", test_stem)

        # Look for corresponding code file
        for file_path in self._get_project_files():
            if self._is_code_file(file_path) and file_path.stem == tested_name:
                return file_path

        return None

    def _get_relative_path(self, file_path: Path) -> Path:
        """Get path relative to project root"""
        try:
            return file_path.relative_to(self.project_path)
        except ValueError:
            return file_path

    def _calculate_severity_score(self, impacted_files: List[ImpactedFile]) -> int:
        """Calculate overall severity score (0-254)"""
        if not impacted_files:
            return 0

        severity_weights = {
            ImpactSeverity.NONE: 0,
            ImpactSeverity.LOW: 1,
            ImpactSeverity.MEDIUM: 5,
            ImpactSeverity.HIGH: 15,
            ImpactSeverity.CRITICAL: 50,
        }

        total_score = sum(
            severity_weights.get(file.severity, 0) for file in impacted_files
        )

        # Add bonus for number of files impacted
        file_count_bonus = min(50, len(impacted_files) * 2)
        total_score += file_count_bonus

        return min(254, total_score)

    def _get_max_severity(self, impacted_files: List[ImpactedFile]) -> ImpactSeverity:
        """Get the maximum severity level from impacted files"""
        if not impacted_files:
            return ImpactSeverity.NONE

        severity_order = [
            ImpactSeverity.NONE,
            ImpactSeverity.LOW,
            ImpactSeverity.MEDIUM,
            ImpactSeverity.HIGH,
            ImpactSeverity.CRITICAL,
        ]

        max_severity = ImpactSeverity.NONE
        for file in impacted_files:
            if severity_order.index(file.severity) > severity_order.index(max_severity):
                max_severity = file.severity

        return max_severity

    def _generate_summary(
        self, impacted_files: List[ImpactedFile], target_file: str
    ) -> str:
        """Generate a summary of the impact analysis"""
        if not impacted_files:
            return f"No impact detected for changes to {target_file}"

        total_files = len(impacted_files)
        impact_types = {}
        severity_counts = {}

        for file in impacted_files:
            impact_type = file.impact_type.value
            severity = file.severity.value

            impact_types[impact_type] = impact_types.get(impact_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        summary_parts = [f"Changes to {target_file} impact {total_files} files"]

        if impact_types:
            type_summary = ", ".join(
                f"{count} {itype}" for itype, count in impact_types.items()
            )
            summary_parts.append(f"Impact types: {type_summary}")

        if severity_counts:
            severity_summary = ", ".join(
                f"{count} {sev}" for sev, count in severity_counts.items()
            )
            summary_parts.append(f"Severity: {severity_summary}")

        return "; ".join(summary_parts)

    def _generate_recommendations(
        self, impacted_files: List[ImpactedFile], target_file: Path
    ) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []

        if not impacted_files:
            recommendations.append("No specific actions required - isolated change")
            return recommendations

        # General recommendations based on impact types
        impact_types = {file.impact_type for file in impacted_files}

        if (
            ImpactType.BREAKING_CHANGE in impact_types
            or ImpactType.BUILD_IMPACT in impact_types
        ):
            recommendations.append("Run full test suite before deploying")
            recommendations.append("Consider creating a migration guide")

        if ImpactType.API_IMPACT in impact_types:
            recommendations.append("Review API compatibility and versioning")
            recommendations.append("Update documentation for API changes")

        if ImpactType.DEPENDENCY_IMPACT in impact_types:
            recommendations.append("Check all import statements and dependencies")

        if ImpactType.TEST_IMPACT in impact_types:
            recommendations.append("Update and run affected tests")

        if ImpactType.CONFIGURATION_IMPACT in impact_types:
            recommendations.append(
                "Verify configuration compatibility across environments"
            )

        # Add specific file recommendations
        high_impact_files = [
            f
            for f in impacted_files
            if f.severity in [ImpactSeverity.HIGH, ImpactSeverity.CRITICAL]
        ]
        if high_impact_files:
            recommendations.append(
                f"Pay special attention to {len(high_impact_files)} high-impact files"
            )

        return recommendations
