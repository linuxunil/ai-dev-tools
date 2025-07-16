"""
AI Agent Interface - High-level API for AI agents

Provides a unified interface for AI agents to use all development tools
with optimized workflows and decision-making support.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json

from ..core.pattern_scanner import PatternScanner, PatternScanResult, PatternType
from ..core.safety_checker import SafetyChecker, SafetyResult, RiskLevel
from ..core.repo_analyzer import RepoAnalyzer, RepoHealth


class AIAgent:
    """
    High-level interface for AI agents to use development tools

    Provides optimized workflows for common AI development patterns:
    1. Fix one error → find similar patterns → apply fixes everywhere
    2. Check safety before making changes
    3. Understand repository context quickly
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize AI agent with repository context

        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path)
        self.pattern_scanner = PatternScanner()
        self.safety_checker = SafetyChecker()
        self.repo_analyzer = RepoAnalyzer(str(repo_path))

    def fix_and_propagate_workflow(
        self,
        fixed_file: str,
        fixed_line: int,
        search_scope: str = ".",
        safety_check: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete workflow: After fixing one error, find and assess similar patterns

        This is the core AI workflow for consistent fixes across a codebase.

        Args:
            fixed_file: File where you just fixed an error
            fixed_line: Line number of the fix
            search_scope: Directory to search for similar patterns
            safety_check: Whether to run safety checks on found patterns

        Returns:
            Dict with pattern analysis and safety assessment
        """
        # Step 1: Find similar patterns
        pattern_result = self.pattern_scanner.scan_for_similar_patterns(
            target_file=fixed_file, target_line=fixed_line, search_dir=search_scope
        )

        # Step 2: Safety check each found pattern (if requested)
        safety_results = []
        if safety_check:
            for match in pattern_result.matches:
                safety_result = self.safety_checker.check_file_safety(match.file)
                safety_results.append(
                    {
                        "file": match.file,
                        "line": match.line,
                        "safety": safety_result.to_dict(),
                    }
                )

        # Step 3: Generate recommendations
        recommendations = self._generate_fix_recommendations(
            pattern_result, safety_results
        )

        return {
            "workflow": "fix_and_propagate",
            "original_fix": {
                "file": fixed_file,
                "line": fixed_line,
                "pattern_type": pattern_result.pattern_type.value,
            },
            "similar_patterns": pattern_result.to_dict(),
            "safety_analysis": safety_results,
            "recommendations": recommendations,
            "summary": self._generate_workflow_summary(pattern_result, safety_results),
        }

    def assess_change_safety(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Assess safety of making changes to multiple files

        Args:
            file_paths: List of files to assess

        Returns:
            Dict with safety assessment and recommendations
        """
        results = []
        overall_risk = RiskLevel.SAFE

        for file_path in file_paths:
            safety_result = self.safety_checker.check_file_safety(file_path)
            results.append({"file": file_path, "safety": safety_result.to_dict()})

            # Track highest risk level
            if safety_result.risk_level.value > overall_risk.value:
                overall_risk = safety_result.risk_level

        return {
            "overall_risk": overall_risk.value,
            "overall_risk_name": overall_risk.name,
            "safe_to_proceed": overall_risk.value <= RiskLevel.MEDIUM.value,
            "file_assessments": results,
            "recommendations": self._generate_safety_recommendations(
                results, overall_risk
            ),
        }

    def get_repository_context(self) -> Dict[str, Any]:
        """
        Get comprehensive repository context for AI decision-making

        Returns:
            Dict with repository health and context information
        """
        health = self.repo_analyzer.get_repo_health()

        return {
            "repository_health": health.to_dict(),
            "ready_for_changes": health.is_clean and health.syntax_errors == 0,
            "blocking_issues": self._identify_blocking_issues(health),
            "recommendations": self._generate_repo_recommendations(health),
        }

    def find_similar_patterns(
        self, target_file: str, target_line: int, search_dir: str = "."
    ) -> PatternScanResult:
        """
        Find patterns similar to the one at target location

        Args:
            target_file: File containing the pattern
            target_line: Line number of the pattern
            search_dir: Directory to search

        Returns:
            PatternScanResult with found matches
        """
        return self.pattern_scanner.scan_for_similar_patterns(
            target_file=target_file, target_line=target_line, search_dir=search_dir
        )

    def check_file_safety(self, file_path: str) -> SafetyResult:
        """
        Check if a file is safe to modify

        Args:
            file_path: Path to the file

        Returns:
            SafetyResult with risk assessment
        """
        return self.safety_checker.check_file_safety(file_path)

    def get_repo_health(self) -> RepoHealth:
        """
        Get repository health status

        Returns:
            RepoHealth with current status
        """
        return self.repo_analyzer.get_repo_health()

    def _generate_fix_recommendations(
        self, pattern_result: PatternScanResult, safety_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for applying fixes"""
        recommendations = []

        if pattern_result.count == 0:
            recommendations.append("No similar patterns found - fix is isolated")
        elif pattern_result.count <= 5:
            recommendations.append(
                f"Found {pattern_result.count} similar patterns - consider applying same fix"
            )
        else:
            recommendations.append(
                f"Found {pattern_result.count} similar patterns - batch fix recommended"
            )

        # Safety-based recommendations
        high_risk_files = [
            sr
            for sr in safety_results
            if sr["safety"]["risk_level"] >= RiskLevel.HIGH.value
        ]

        if high_risk_files:
            recommendations.append(
                f"⚠️  {len(high_risk_files)} high-risk files found - proceed with caution"
            )

        return recommendations

    def _generate_safety_recommendations(
        self, results: List[Dict[str, Any]], overall_risk: RiskLevel
    ) -> List[str]:
        """Generate safety recommendations"""
        recommendations = []

        if overall_risk == RiskLevel.SAFE:
            recommendations.append("✅ All files are safe to modify")
        elif overall_risk == RiskLevel.MEDIUM:
            recommendations.append(
                "⚠️  Medium risk - proceed with caution and test changes"
            )
        elif overall_risk == RiskLevel.HIGH:
            recommendations.append("🚨 High risk - make backups and test thoroughly")
        else:
            recommendations.append("🛑 Critical risk - consider alternative approach")

        return recommendations

    def _generate_workflow_summary(
        self, pattern_result: PatternScanResult, safety_results: List[Dict[str, Any]]
    ) -> str:
        """Generate a summary of the fix and propagate workflow"""
        if pattern_result.count == 0:
            return "Fix is isolated - no similar patterns found"

        safe_count = len(
            [sr for sr in safety_results if sr["safety"]["safe_to_modify"]]
        )

        return f"Found {pattern_result.count} similar patterns, {safe_count} safe to modify"

    def _identify_blocking_issues(self, health: RepoHealth) -> List[str]:
        """Identify issues that block making changes"""
        issues = []

        if health.has_uncommitted_changes:
            issues.append("Repository has uncommitted changes")

        if health.syntax_errors > 0:
            issues.append(f"Repository has {health.syntax_errors} syntax errors")

        return issues

    def _generate_repo_recommendations(self, health: RepoHealth) -> List[str]:
        """Generate repository-level recommendations"""
        recommendations = []

        if health.is_clean and health.syntax_errors == 0:
            recommendations.append("✅ Repository is ready for changes")
        else:
            if health.has_uncommitted_changes:
                recommendations.append("Commit or stash changes before proceeding")
            if health.syntax_errors > 0:
                recommendations.append("Fix syntax errors before making changes")

        return recommendations
