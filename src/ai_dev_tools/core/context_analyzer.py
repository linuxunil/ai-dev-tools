"""
Context Analyzer - Exit-code-first project context analysis for AI workflows

Analyzes project structure, dependencies, and configuration to provide context.
Designed for zero-token AI decision making with optional verbose output.

Exit Codes:
- 0-254: Context complexity score (0=simple, 254=very complex)
- 255: Error (directory not found, invalid input, etc.)
"""

from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import json
import sys
from dataclasses import dataclass, asdict
from enum import Enum
import re


class ProjectType(Enum):
    """Detected project types"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    NIX = "nix"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FrameworkType(Enum):
    """Detected framework types"""

    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    EXPRESS = "express"
    NEXTJS = "nextjs"
    UNKNOWN = "unknown"


@dataclass
class DependencyInfo:
    """Information about project dependencies"""

    name: str
    version: Optional[str] = None
    dev_dependency: bool = False
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class ProjectContext:
    """Complete project context analysis"""

    project_type: ProjectType
    framework: FrameworkType
    complexity_score: int
    total_files: int
    code_files: int
    config_files: int
    dependencies: List[DependencyInfo]
    entry_points: List[str]
    build_tools: List[str]
    test_frameworks: List[str]
    key_directories: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["project_type"] = self.project_type.value
        result["framework"] = self.framework.value
        result["dependencies"] = [dep.to_dict() for dep in self.dependencies]
        return result


class ContextAnalyzer:
    """Analyzes project context for AI decision making"""

    # File patterns for different project types
    PROJECT_INDICATORS = {
        ProjectType.PYTHON: [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
        ],
        ProjectType.JAVASCRIPT: ["package.json", "yarn.lock", "npm-shrinkwrap.json"],
        ProjectType.TYPESCRIPT: ["tsconfig.json", "package.json"],
        ProjectType.NIX: ["flake.nix", "default.nix", "shell.nix"],
        ProjectType.RUST: ["Cargo.toml", "Cargo.lock"],
        ProjectType.GO: ["go.mod", "go.sum"],
        ProjectType.JAVA: ["pom.xml", "build.gradle", "gradle.properties"],
    }

    # Framework detection patterns
    FRAMEWORK_INDICATORS = {
        FrameworkType.DJANGO: ["manage.py", "django", "Django"],
        FrameworkType.FLASK: ["flask", "Flask"],
        FrameworkType.FASTAPI: ["fastapi", "FastAPI"],
        FrameworkType.REACT: ["react", "React"],
        FrameworkType.VUE: ["vue", "Vue"],
        FrameworkType.ANGULAR: ["@angular", "angular"],
        FrameworkType.EXPRESS: ["express"],
        FrameworkType.NEXTJS: ["next", "Next.js"],
    }

    # Build tool patterns
    BUILD_TOOLS = {
        "webpack": ["webpack.config.js", "webpack.config.ts"],
        "vite": ["vite.config.js", "vite.config.ts"],
        "rollup": ["rollup.config.js"],
        "parcel": [".parcelrc"],
        "esbuild": ["esbuild.config.js"],
        "poetry": ["pyproject.toml"],
        "pip": ["requirements.txt", "setup.py"],
        "npm": ["package.json"],
        "yarn": ["yarn.lock"],
        "cargo": ["Cargo.toml"],
        "go": ["go.mod"],
        "maven": ["pom.xml"],
        "gradle": ["build.gradle"],
        "nix": ["flake.nix", "default.nix"],
    }

    # Test framework patterns
    TEST_FRAMEWORKS = {
        "pytest": ["pytest", "conftest.py"],
        "unittest": ["unittest"],
        "jest": ["jest", "jest.config.js"],
        "mocha": ["mocha"],
        "vitest": ["vitest"],
        "cypress": ["cypress"],
        "playwright": ["playwright"],
        "cargo-test": ["Cargo.toml"],
    }

    def __init__(self, project_path: Path):
        """Initialize analyzer for given project path"""
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        if not self.project_path.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {project_path}")

    def analyze(self) -> ProjectContext:
        """Perform complete project context analysis"""
        # Collect all files
        all_files = self._collect_files()

        # Detect project type
        project_type = self._detect_project_type(all_files)

        # Detect framework
        framework = self._detect_framework(all_files)

        # Analyze dependencies
        dependencies = self._analyze_dependencies(all_files, project_type)

        # Find entry points
        entry_points = self._find_entry_points(all_files, project_type)

        # Detect build tools
        build_tools = self._detect_build_tools(all_files)

        # Detect test frameworks
        test_frameworks = self._detect_test_frameworks(all_files, dependencies)

        # Find key directories
        key_directories = self._find_key_directories()

        # Calculate complexity score
        complexity_score = self._calculate_complexity(
            all_files, dependencies, build_tools, test_frameworks
        )

        # Count file types
        code_files = len([f for f in all_files if self._is_code_file(f)])
        config_files = len([f for f in all_files if self._is_config_file(f)])

        return ProjectContext(
            project_type=project_type,
            framework=framework,
            complexity_score=complexity_score,
            total_files=len(all_files),
            code_files=code_files,
            config_files=config_files,
            dependencies=dependencies,
            entry_points=entry_points,
            build_tools=build_tools,
            test_frameworks=test_frameworks,
            key_directories=key_directories,
        )

    def _collect_files(self) -> List[Path]:
        """Collect all relevant files in the project"""
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
        }

        for file_path in self.project_path.rglob("*"):
            if file_path.is_file():
                # Skip ignored directories
                if any(part in ignore_patterns for part in file_path.parts):
                    continue
                files.append(file_path)

        return files

    def _detect_project_type(self, files: List[Path]) -> ProjectType:
        """Detect the primary project type"""
        type_scores = {ptype: 0 for ptype in ProjectType}

        for file_path in files:
            file_name = file_path.name

            for ptype, indicators in self.PROJECT_INDICATORS.items():
                if any(indicator in file_name for indicator in indicators):
                    type_scores[ptype] += 1

            # Check file extensions
            suffix = file_path.suffix.lower()
            if suffix == ".py":
                type_scores[ProjectType.PYTHON] += 1
            elif suffix in [".js", ".jsx"]:
                type_scores[ProjectType.JAVASCRIPT] += 1
            elif suffix in [".ts", ".tsx"]:
                type_scores[ProjectType.TYPESCRIPT] += 1
            elif suffix == ".nix":
                type_scores[ProjectType.NIX] += 1
            elif suffix == ".rs":
                type_scores[ProjectType.RUST] += 1
            elif suffix == ".go":
                type_scores[ProjectType.GO] += 1
            elif suffix in [".java", ".kt"]:
                type_scores[ProjectType.JAVA] += 1

        # Find the type with highest score
        max_score = max(type_scores.values())
        if max_score == 0:
            return ProjectType.UNKNOWN

        # Check if multiple types have high scores (mixed project)
        high_score_types = [t for t, s in type_scores.items() if s >= max_score * 0.7]
        if len(high_score_types) > 1:
            return ProjectType.MIXED

        return max(type_scores, key=lambda x: type_scores[x])

    def _detect_framework(self, files: List[Path]) -> FrameworkType:
        """Detect the primary framework"""
        framework_scores = {ftype: 0 for ftype in FrameworkType}

        # Check file contents for framework indicators
        for file_path in files:
            if file_path.suffix.lower() in [".json", ".py", ".js", ".ts"]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for ftype, indicators in self.FRAMEWORK_INDICATORS.items():
                        for indicator in indicators:
                            if indicator in content:
                                framework_scores[ftype] += content.count(indicator)
                except (UnicodeDecodeError, PermissionError):
                    continue

        max_score = max(framework_scores.values())
        if max_score == 0:
            return FrameworkType.UNKNOWN

        return max(framework_scores, key=lambda x: framework_scores[x])

    def _analyze_dependencies(
        self, files: List[Path], project_type: ProjectType
    ) -> List[DependencyInfo]:
        """Analyze project dependencies"""
        dependencies = []

        for file_path in files:
            file_name = file_path.name

            try:
                if file_name == "package.json" and project_type in [
                    ProjectType.JAVASCRIPT,
                    ProjectType.TYPESCRIPT,
                ]:
                    content = json.loads(file_path.read_text())
                    deps = content.get("dependencies", {})
                    dev_deps = content.get("devDependencies", {})

                    for name, version in deps.items():
                        dependencies.append(
                            DependencyInfo(name, version, False, str(file_path))
                        )
                    for name, version in dev_deps.items():
                        dependencies.append(
                            DependencyInfo(name, version, True, str(file_path))
                        )

                elif (
                    file_name == "requirements.txt"
                    and project_type == ProjectType.PYTHON
                ):
                    content = file_path.read_text()
                    for line in content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Parse requirement line (name==version or name>=version, etc.)
                            match = re.match(r"([a-zA-Z0-9_-]+)([>=<~!]+.*)?", line)
                            if match:
                                name = match.group(1)
                                version = match.group(2) if match.group(2) else None
                                dependencies.append(
                                    DependencyInfo(name, version, False, str(file_path))
                                )

                elif (
                    file_name == "pyproject.toml" and project_type == ProjectType.PYTHON
                ):
                    # Basic TOML parsing for dependencies
                    content = file_path.read_text()
                    in_dependencies = False
                    in_project_deps = False

                    for line in content.splitlines():
                        line = line.strip()

                        # Check for section headers
                        if line == "[tool.poetry.dependencies]":
                            in_dependencies = True
                            in_project_deps = False
                        elif line.startswith("dependencies = ["):
                            in_project_deps = True
                            in_dependencies = False
                            # Parse inline array
                            deps_line = line[len("dependencies = [") :].rstrip("]")
                            if deps_line:
                                for dep in deps_line.split(","):
                                    dep = dep.strip().strip("\"'")
                                    if dep:
                                        name = re.match(r"([a-zA-Z0-9_-]+)", dep)
                                        if name:
                                            dependencies.append(
                                                DependencyInfo(
                                                    name.group(1),
                                                    None,
                                                    False,
                                                    str(file_path),
                                                )
                                            )
                        elif line.startswith("[") and (
                            in_dependencies or in_project_deps
                        ):
                            in_dependencies = False
                            in_project_deps = False
                        elif (
                            in_project_deps
                            and line.startswith('"')
                            and line.endswith('",')
                        ):
                            # Multi-line dependencies array
                            dep = line.strip().strip('",')
                            name = re.match(r"([a-zA-Z0-9_-]+)", dep)
                            if name:
                                dependencies.append(
                                    DependencyInfo(
                                        name.group(1), None, False, str(file_path)
                                    )
                                )
                        elif in_dependencies and "=" in line:
                            name = line.split("=")[0].strip().strip('"')
                            if name != "python":
                                dependencies.append(
                                    DependencyInfo(name, None, False, str(file_path))
                                )

            except (json.JSONDecodeError, UnicodeDecodeError, PermissionError):
                continue

        return dependencies

    def _find_entry_points(
        self, files: List[Path], project_type: ProjectType
    ) -> List[str]:
        """Find project entry points"""
        entry_points = []

        common_entry_points = [
            "main.py",
            "app.py",
            "server.py",
            "index.js",
            "index.ts",
            "main.js",
            "main.ts",
            "src/main.py",
            "src/index.js",
        ]

        for file_path in files:
            rel_path = str(file_path.relative_to(self.project_path))
            if any(entry in rel_path for entry in common_entry_points):
                entry_points.append(rel_path)

        return entry_points

    def _detect_build_tools(self, files: List[Path]) -> List[str]:
        """Detect build tools used in the project"""
        detected_tools = []

        for tool, indicators in self.BUILD_TOOLS.items():
            for file_path in files:
                if any(indicator in file_path.name for indicator in indicators):
                    detected_tools.append(tool)
                    break

        return detected_tools

    def _detect_test_frameworks(
        self, files: List[Path], dependencies: List[DependencyInfo]
    ) -> List[str]:
        """Detect test frameworks"""
        detected_frameworks = []

        # Check dependencies
        dep_names = {dep.name.lower() for dep in dependencies}
        for framework, indicators in self.TEST_FRAMEWORKS.items():
            if any(indicator.lower() in dep_names for indicator in indicators):
                detected_frameworks.append(framework)

        # Check for test files
        for file_path in files:
            file_name = file_path.name.lower()
            if "test" in file_name or "spec" in file_name:
                if file_path.suffix == ".py" and "pytest" not in detected_frameworks:
                    detected_frameworks.append("pytest")
                elif (
                    file_path.suffix in [".js", ".ts"]
                    and "jest" not in detected_frameworks
                ):
                    detected_frameworks.append("jest")

        return detected_frameworks

    def _find_key_directories(self) -> List[str]:
        """Find key project directories"""
        key_dirs = []
        common_dirs = [
            "src",
            "lib",
            "app",
            "components",
            "utils",
            "tests",
            "docs",
            "config",
        ]

        for dir_path in self.project_path.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith("."):
                if dir_path.name in common_dirs or any(
                    keyword in dir_path.name.lower()
                    for keyword in ["test", "spec", "doc"]
                ):
                    key_dirs.append(dir_path.name)

        return key_dirs

    def _calculate_complexity(
        self,
        files: List[Path],
        dependencies: List[DependencyInfo],
        build_tools: List[str],
        test_frameworks: List[str],
    ) -> int:
        """Calculate project complexity score (0-254)"""
        score = 0

        # File count contribution (0-50)
        file_count = len(files)
        score += min(50, file_count // 10)

        # Dependency count contribution (0-100)
        dep_count = len(dependencies)
        score += min(100, dep_count * 2)

        # Build tool complexity (0-50)
        score += min(50, len(build_tools) * 10)

        # Test framework complexity (0-30)
        score += min(30, len(test_frameworks) * 10)

        # Directory depth complexity (0-24)
        max_depth = 0
        for file_path in files:
            depth = len(file_path.relative_to(self.project_path).parts)
            max_depth = max(max_depth, depth)
        score += min(24, max_depth * 3)

        return min(254, score)

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".rs",
            ".go",
            ".java",
            ".kt",
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
        return file_path.suffix.lower() in code_extensions

    def _is_config_file(self, file_path: Path) -> bool:
        """Check if file is a configuration file"""
        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
        config_names = {
            "dockerfile",
            "makefile",
            "rakefile",
            "gemfile",
            "pipfile",
            ".gitignore",
            ".dockerignore",
            ".env",
        }

        return (
            file_path.suffix.lower() in config_extensions
            or file_path.name.lower() in config_names
        )
