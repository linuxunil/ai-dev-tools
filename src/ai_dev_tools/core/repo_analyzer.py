"""
Repository Analyzer - AI-optimized repository analysis

Provides libraries for analyzing repository structure and health.
Designed for AI agents to understand project context quickly.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import subprocess
import json


@dataclass
class RepoHealth:
    """Repository health status"""

    is_clean: bool
    has_uncommitted_changes: bool
    syntax_errors: int
    total_files: int
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "is_clean": self.is_clean,
            "has_uncommitted_changes": self.has_uncommitted_changes,
            "syntax_errors": self.syntax_errors,
            "total_files": self.total_files,
            "summary": self.summary,
        }


class RepoAnalyzer:
    """
    AI-optimized repository analyzer

    Designed for AI agents to quickly understand repository state
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize repository analyzer

        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path)

    def get_repo_health(self) -> RepoHealth:
        """
        Get overall repository health status

        Returns:
            RepoHealth with current status
        """
        is_clean = self._check_git_clean()
        has_uncommitted = not is_clean
        syntax_errors = self._count_syntax_errors()
        total_files = self._count_nix_files()

        # Generate summary
        if is_clean and syntax_errors == 0:
            summary = "Repository is healthy"
        elif not is_clean and syntax_errors == 0:
            summary = "Repository has uncommitted changes but no syntax errors"
        elif is_clean and syntax_errors > 0:
            summary = f"Repository is clean but has {syntax_errors} syntax errors"
        else:
            summary = (
                f"Repository has uncommitted changes and {syntax_errors} syntax errors"
            )

        return RepoHealth(
            is_clean=is_clean,
            has_uncommitted_changes=has_uncommitted,
            syntax_errors=syntax_errors,
            total_files=total_files,
            summary=summary,
        )

    def _check_git_clean(self) -> bool:
        """Check if git repository is clean"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return len(result.stdout.strip()) == 0
        except Exception:
            return False

    def _count_syntax_errors(self) -> int:
        """Count syntax errors in Nix files"""
        error_count = 0

        for nix_file in self.repo_path.rglob("*.nix"):
            try:
                result = subprocess.run(
                    ["nix-instantiate", "--parse", str(nix_file)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    error_count += 1
            except Exception:
                continue

        return error_count

    def _count_nix_files(self) -> int:
        """Count total Nix files in repository"""
        return len(list(self.repo_path.rglob("*.nix")))
