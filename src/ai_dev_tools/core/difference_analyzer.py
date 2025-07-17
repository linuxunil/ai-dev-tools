"""
Difference Analyzer - Exit-code-first configuration and code difference analysis

Analyzes differences between files, directories, or configurations to identify changes.
Designed for zero-token AI decision making with optional verbose output.

Exit Codes:
- 0-254: Number of significant differences found (0=identical, 254=maximum differences)
- 255: Error (file not found, invalid input, etc.)
"""

import difflib
import hashlib
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class DifferenceType(Enum):
    """Types of differences that can be detected"""

    IDENTICAL = "identical"
    CONTENT_CHANGED = "content_changed"
    STRUCTURE_CHANGED = "structure_changed"
    ADDED = "added"
    REMOVED = "removed"
    RENAMED = "renamed"
    PERMISSION_CHANGED = "permission_changed"


class ChangeSignificance(Enum):
    """Significance levels for changes"""

    TRIVIAL = "trivial"  # Whitespace, comments
    MINOR = "minor"  # Small content changes
    MAJOR = "major"  # Structural changes
    CRITICAL = "critical"  # Breaking changes


@dataclass
class FileDifference:
    """Information about a single file difference"""

    path: str
    difference_type: DifferenceType
    significance: ChangeSignificance
    line_changes: int = 0
    added_lines: int = 0
    removed_lines: int = 0
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["difference_type"] = self.difference_type.value
        result["significance"] = self.significance.value
        return result


@dataclass
class DifferenceAnalysis:
    """Complete difference analysis result"""

    total_differences: int
    significant_differences: int
    files_compared: int
    files_added: int
    files_removed: int
    files_modified: int
    differences: List[FileDifference]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["differences"] = [diff.to_dict() for diff in self.differences]
        return result


class DifferenceAnalyzer:
    """Analyzes differences between files, directories, or configurations"""

    # File types that should be treated as text for line-by-line comparison
    TEXT_EXTENSIONS = {
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
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".md",
        ".txt",
        ".html",
        ".css",
        ".scss",
        ".less",
        ".xml",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
    }

    # Patterns that indicate trivial changes
    TRIVIAL_PATTERNS = [
        r"^\s*$",  # Empty lines
        r"^\s*#.*$",  # Comments (Python, shell)
        r"^\s*//.*$",  # Comments (C-style)
        r"^\s*/\*.*\*/$",  # Single-line block comments
    ]

    # Patterns that indicate critical changes
    CRITICAL_PATTERNS = [
        r"class\s+\w+",  # Class definitions
        r"def\s+\w+",  # Function definitions (Python)
        r"function\s+\w+",  # Function definitions (JS)
        r"interface\s+\w+",  # Interface definitions
        r"import\s+",  # Import statements
        r"from\s+\w+\s+import",  # Import statements
        r"export\s+",  # Export statements
        r"@\w+",  # Decorators/annotations
    ]

    def __init__(self, ignore_whitespace: bool = True, ignore_comments: bool = False):
        """Initialize analyzer with comparison options"""
        self.ignore_whitespace = ignore_whitespace
        self.ignore_comments = ignore_comments

    def compare_files(self, file1: Path, file2: Path) -> DifferenceAnalysis:
        """Compare two files and return difference analysis"""
        file1_path = Path(file1).resolve()
        file2_path = Path(file2).resolve()

        if not file1_path.exists():
            raise FileNotFoundError(f"File does not exist: {file1}")
        if not file2_path.exists():
            raise FileNotFoundError(f"File does not exist: {file2}")

        differences = []

        # Compare file content
        diff = self._compare_file_content(file1_path, file2_path)
        if diff:
            differences.append(diff)

        # Calculate summary statistics
        total_differences = len(differences)
        significant_differences = len(
            [d for d in differences if d.significance != ChangeSignificance.TRIVIAL]
        )

        summary = self._generate_summary(differences)

        return DifferenceAnalysis(
            total_differences=total_differences,
            significant_differences=significant_differences,
            files_compared=2,
            files_added=0,
            files_removed=0,
            files_modified=1 if differences else 0,
            differences=differences,
            summary=summary,
        )

    def compare_directories(self, dir1: Path, dir2: Path) -> DifferenceAnalysis:
        """Compare two directories and return difference analysis"""
        dir1_path = Path(dir1).resolve()
        dir2_path = Path(dir2).resolve()

        if not dir1_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {dir1}")
        if not dir2_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {dir2}")
        if not dir1_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {dir1}")
        if not dir2_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {dir2}")

        differences = []

        # Get all files in both directories
        files1 = self._get_directory_files(dir1_path)
        files2 = self._get_directory_files(dir2_path)

        # Find relative paths
        rel_files1 = {f.relative_to(dir1_path): f for f in files1}
        rel_files2 = {f.relative_to(dir2_path): f for f in files2}

        all_rel_paths = set(rel_files1.keys()) | set(rel_files2.keys())

        files_added = 0
        files_removed = 0
        files_modified = 0

        for rel_path in sorted(all_rel_paths):
            if rel_path in rel_files1 and rel_path in rel_files2:
                # File exists in both directories - compare content
                diff = self._compare_file_content(
                    rel_files1[rel_path], rel_files2[rel_path]
                )
                if diff:
                    diff.path = str(rel_path)
                    differences.append(diff)
                    files_modified += 1
            elif rel_path in rel_files1:
                # File only in first directory (removed)
                differences.append(
                    FileDifference(
                        path=str(rel_path),
                        difference_type=DifferenceType.REMOVED,
                        significance=ChangeSignificance.MAJOR,
                        details="File removed",
                    )
                )
                files_removed += 1
            else:
                # File only in second directory (added)
                differences.append(
                    FileDifference(
                        path=str(rel_path),
                        difference_type=DifferenceType.ADDED,
                        significance=ChangeSignificance.MAJOR,
                        details="File added",
                    )
                )
                files_added += 1

        # Calculate summary statistics
        total_differences = len(differences)
        significant_differences = len(
            [d for d in differences if d.significance != ChangeSignificance.TRIVIAL]
        )

        summary = self._generate_summary(differences)

        return DifferenceAnalysis(
            total_differences=total_differences,
            significant_differences=significant_differences,
            files_compared=len(all_rel_paths),
            files_added=files_added,
            files_removed=files_removed,
            files_modified=files_modified,
            differences=differences,
            summary=summary,
        )

    def _get_directory_files(self, directory: Path) -> List[Path]:
        """Get all files in a directory, excluding common ignore patterns"""
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

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Skip ignored directories
                if any(part in ignore_patterns for part in file_path.parts):
                    continue
                files.append(file_path)

        return files

    def _compare_file_content(
        self, file1: Path, file2: Path
    ) -> Optional[FileDifference]:
        """Compare content of two files"""
        try:
            # Check if files are identical by hash first (fast check)
            if self._files_identical_by_hash(file1, file2):
                return None

            # For text files, do line-by-line comparison
            if self._is_text_file(file1) and self._is_text_file(file2):
                return self._compare_text_files(file1, file2)
            else:
                # Binary files - just check if different
                return FileDifference(
                    path=str(file1.name),
                    difference_type=DifferenceType.CONTENT_CHANGED,
                    significance=ChangeSignificance.MAJOR,
                    details="Binary file changed",
                )

        except (UnicodeDecodeError, PermissionError) as e:
            return FileDifference(
                path=str(file1.name),
                difference_type=DifferenceType.CONTENT_CHANGED,
                significance=ChangeSignificance.MINOR,
                details=f"Could not compare: {e}",
            )

    def _files_identical_by_hash(self, file1: Path, file2: Path) -> bool:
        """Check if files are identical using hash comparison"""
        try:
            hash1 = hashlib.md5(file1.read_bytes()).hexdigest()
            hash2 = hashlib.md5(file2.read_bytes()).hexdigest()
            return hash1 == hash2
        except (OSError, PermissionError):
            return False

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file should be treated as text"""
        return file_path.suffix.lower() in self.TEXT_EXTENSIONS

    def _compare_text_files(self, file1: Path, file2: Path) -> Optional[FileDifference]:
        """Compare two text files line by line"""
        try:
            content1 = file1.read_text(encoding="utf-8", errors="ignore")
            content2 = file2.read_text(encoding="utf-8", errors="ignore")

            lines1 = content1.splitlines()
            lines2 = content2.splitlines()

            # Apply preprocessing if needed
            if self.ignore_whitespace:
                lines1 = [line.strip() for line in lines1]
                lines2 = [line.strip() for line in lines2]

            if self.ignore_comments:
                lines1 = self._filter_comments(lines1)
                lines2 = self._filter_comments(lines2)

            # Calculate differences
            differ = difflib.unified_diff(lines1, lines2, lineterm="")
            diff_lines = list(differ)

            if not diff_lines:
                return None

            # Count changes
            added_lines = len([line for line in diff_lines if line.startswith("+")])
            removed_lines = len([line for line in diff_lines if line.startswith("-")])
            line_changes = added_lines + removed_lines

            # Determine significance
            significance = self._determine_significance(diff_lines, lines1, lines2)

            return FileDifference(
                path=str(file1.name),
                difference_type=DifferenceType.CONTENT_CHANGED,
                significance=significance,
                line_changes=line_changes,
                added_lines=added_lines,
                removed_lines=removed_lines,
                details=f"{line_changes} line changes",
            )

        except (UnicodeDecodeError, PermissionError):
            return FileDifference(
                path=str(file1.name),
                difference_type=DifferenceType.CONTENT_CHANGED,
                significance=ChangeSignificance.MINOR,
                details="Could not compare text content",
            )

    def _filter_comments(self, lines: List[str]) -> List[str]:
        """Filter out comment lines"""
        filtered = []
        for line in lines:
            is_comment = any(
                re.match(pattern, line) for pattern in self.TRIVIAL_PATTERNS
            )
            if not is_comment:
                filtered.append(line)
        return filtered

    def _determine_significance(
        self, diff_lines: List[str], lines1: List[str], lines2: List[str]
    ) -> ChangeSignificance:
        """Determine the significance of changes"""
        total_lines = max(len(lines1), len(lines2))
        changed_lines = len(
            [line for line in diff_lines if line.startswith(("+", "-"))]
        )

        if total_lines == 0:
            return ChangeSignificance.TRIVIAL

        change_ratio = changed_lines / total_lines

        # Check for critical patterns
        critical_changes = any(
            any(re.search(pattern, line) for pattern in self.CRITICAL_PATTERNS)
            for line in diff_lines
            if line.startswith(("+", "-"))
        )

        if critical_changes:
            return ChangeSignificance.CRITICAL

        # Check for trivial changes only
        trivial_only = all(
            any(
                re.match(pattern, line[1:].strip()) for pattern in self.TRIVIAL_PATTERNS
            )
            for line in diff_lines
            if line.startswith(("+", "-"))
        )

        if trivial_only:
            return ChangeSignificance.TRIVIAL

        # Determine by change ratio
        if change_ratio > 0.5:
            return ChangeSignificance.CRITICAL
        elif change_ratio > 0.2:
            return ChangeSignificance.MAJOR
        else:
            return ChangeSignificance.MINOR

    def _generate_summary(self, differences: List[FileDifference]) -> str:
        """Generate a summary of differences"""
        if not differences:
            return "No differences found"

        total = len(differences)
        by_type = {}
        by_significance = {}

        for diff in differences:
            diff_type = diff.difference_type.value
            significance = diff.significance.value

            by_type[diff_type] = by_type.get(diff_type, 0) + 1
            by_significance[significance] = by_significance.get(significance, 0) + 1

        summary_parts = [f"{total} differences found"]

        if by_type:
            type_summary = ", ".join(
                f"{count} {dtype}" for dtype, count in by_type.items()
            )
            summary_parts.append(f"Types: {type_summary}")

        if by_significance:
            sig_summary = ", ".join(
                f"{count} {sig}" for sig, count in by_significance.items()
            )
            summary_parts.append(f"Significance: {sig_summary}")

        return "; ".join(summary_parts)
