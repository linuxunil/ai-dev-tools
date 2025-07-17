"""
AI Agent - High-level interface for AI-assisted development workflows

Provides composable workflows for pattern-based systematic fixes
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ..core.pattern_scanner import PatternScanner, PatternScanResult
from ..core.repo_analyzer import RepoAnalyzer, RepoHealth
from ..core.safety_checker import RiskLevel, SafetyChecker, SafetyResult


@dataclass
class WorkflowResult:
    """Result of an AI workflow execution"""

    workflow_type: str
    success: bool
    summary: str
    similar_patterns: Dict[str, Any]
    safety_assessment: Dict[str, Any]
    recommendations: List[str]
    exit_code: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "workflow": self.workflow_type,
            "success": self.success,
            "summary": self.summary,
            "patterns": self.similar_patterns,
            "safety": self.safety_assessment,
            "recommendations": self.recommendations,
            "exit_code": self.exit_code,
        }


class AIAgent:
    """
    High-level AI agent interface for development workflows

    Designed for AI agents to perform systematic code improvements:
    1. Fix one error/issue
    2. Find similar patterns
    3. Assess safety of changes
    4. Apply fixes systematically
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize AI agent with repository context

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        self.pattern_scanner = PatternScanner()
        self.safety_checker = SafetyChecker()
        self.repo_analyzer = RepoAnalyzer()

    def fix_and_propagate_workflow(
        self,
        fixed_file: str,
        fixed_line: int,
        search_scope: str = ".",
        max_patterns: int = 50,
    ) -> WorkflowResult:
        """
        Core AI workflow: Fix one error → find similar patterns → assess safety

        This is the primary use case for AI agents:
        1. After fixing an error at a specific location
        2. Find all similar patterns in the codebase
        3. Assess safety of applying the same fix
        4. Return actionable recommendations

        Args:
            fixed_file: File where the fix was applied
            fixed_line: Line number of the fix
            search_scope: Directory scope for pattern search
            max_patterns: Maximum patterns to find

        Returns:
            WorkflowResult with patterns, safety assessment, and recommendations
        """
        try:
            # Step 1: Find similar patterns
            pattern_result = self.pattern_scanner.scan_for_similar_patterns(
                target_file=fixed_file,
                target_line=fixed_line,
                search_dir=search_scope,
                max_results=max_patterns,
            )

            # Step 2: Assess safety of each pattern location
            safety_results = []
            high_risk_files = []
            safe_files = []

            for match in pattern_result.matches:
                safety = self.safety_checker.check_file_safety(match.file)
                safety_results.append(
                    {
                        "file": match.file,
                        "line": match.line,
                        "risk_level": safety.risk_level.name,
                        "safe_to_modify": safety.safe_to_modify,
                        "confidence": match.confidence,
                    }
                )

                if safety.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    high_risk_files.append(match.file)
                elif safety.safe_to_modify:
                    safe_files.append(match.file)

            # Step 3: Generate recommendations
            recommendations = self._generate_recommendations(
                pattern_result, safety_results, high_risk_files, safe_files
            )

            # Step 4: Calculate overall success and exit code
            success = len(pattern_result.matches) > 0
            exit_code = min(pattern_result.count, 254) if success else 255

            # Step 5: Create summary
            summary = self._create_workflow_summary(
                pattern_result.count, len(safe_files), len(high_risk_files)
            )

            return WorkflowResult(
                workflow_type="fix_and_propagate",
                success=success,
                summary=summary,
                similar_patterns={
                    "count": pattern_result.count,
                    "matches": [match.to_dict() for match in pattern_result.matches],
                    "pattern_type": pattern_result.pattern_type.value,
                },
                safety_assessment={
                    "safe_files": len(safe_files),
                    "high_risk_files": len(high_risk_files),
                    "total_assessed": len(safety_results),
                    "details": safety_results,
                },
                recommendations=recommendations,
                exit_code=exit_code,
            )

        except Exception as e:
            return WorkflowResult(
                workflow_type="fix_and_propagate",
                success=False,
                summary=f"Workflow failed: {str(e)}",
                similar_patterns={"count": 0, "matches": []},
                safety_assessment={"error": str(e)},
                recommendations=["Fix workflow error before proceeding"],
                exit_code=255,
            )

    def get_repository_context(self) -> Dict[str, Any]:
        """
        Get comprehensive repository context for AI decision making

        Returns:
            Dictionary with repository health, readiness for changes, etc.
        """
        try:
            # Get repository health
            health = self.repo_analyzer.get_repo_health(str(self.repo_path))

            # Determine readiness for changes
            ready_for_changes = health.syntax_errors == 0 and health.health_score > 0.7

            # Identify blocking issues
            blocking_issues = []
            if health.syntax_errors > 0:
                blocking_issues.append(
                    f"{health.syntax_errors} syntax errors need fixing"
                )
            if health.health_score <= 0.5:
                blocking_issues.append("Repository health score too low")
            if health.missing_files:
                blocking_issues.append(
                    f"Missing essential files: {', '.join(health.missing_files)}"
                )

            # Generate recommendations
            recommendations = health.recommendations.copy()
            if not ready_for_changes:
                recommendations.insert(0, "Fix blocking issues before making changes")

            return {
                "ready_for_changes": ready_for_changes,
                "blocking_issues": blocking_issues,
                "health_score": health.health_score,
                "syntax_errors": health.syntax_errors,
                "missing_files": health.missing_files,
                "summary": health.summary,
                "recommendations": recommendations,
                "exit_code": min(health.syntax_errors, 254),
            }

        except Exception as e:
            return {
                "ready_for_changes": False,
                "blocking_issues": [f"Failed to assess repository: {str(e)}"],
                "health_score": 0.0,
                "error": str(e),
                "recommendations": ["Fix repository analysis error"],
                "exit_code": 255,
            }

    def assess_change_safety(self, files_to_modify: List[str]) -> Dict[str, Any]:
        """
        Assess safety of modifying multiple files

        Args:
            files_to_modify: List of file paths to check

        Returns:
            Safety assessment for the proposed changes
        """
        try:
            safety_results = []
            risk_levels = []
            critical_files = []
            warnings = []

            for file_path in files_to_modify:
                safety = self.safety_checker.check_file_safety(file_path)
                safety_results.append(
                    {
                        "file": file_path,
                        "risk_level": safety.risk_level.name,
                        "safe_to_modify": safety.safe_to_modify,
                        "warnings": safety.warnings,
                    }
                )

                risk_levels.append(safety.risk_level.value)
                warnings.extend(safety.warnings)

                if safety.risk_level == RiskLevel.CRITICAL:
                    critical_files.append(file_path)

            # Determine overall safety
            max_risk = max(risk_levels) if risk_levels else 0
            safe_to_proceed = (
                max_risk <= RiskLevel.MEDIUM.value and len(critical_files) == 0
            )

            # Map risk level to name
            risk_level_names = {0: "safe", 1: "medium", 2: "high", 3: "critical"}
            overall_risk = risk_level_names.get(max_risk, "unknown")

            return {
                "safe_to_proceed": safe_to_proceed,
                "risk_level": overall_risk,
                "max_risk_value": max_risk,
                "warnings": list(set(warnings)),  # Remove duplicates
                "critical_files": critical_files,
                "file_assessments": safety_results,
                "total_files": len(files_to_modify),
                "exit_code": max_risk,
            }

        except Exception as e:
            return {
                "safe_to_proceed": False,
                "risk_level": "error",
                "error": str(e),
                "warnings": [f"Safety assessment failed: {str(e)}"],
                "critical_files": [],
                "exit_code": 255,
            }

    def _generate_recommendations(
        self,
        pattern_result: PatternScanResult,
        safety_results: List[Dict[str, Any]],
        high_risk_files: List[str],
        safe_files: List[str],
    ) -> List[str]:
        """Generate actionable recommendations based on analysis results"""
        recommendations = []

        if pattern_result.count == 0:
            recommendations.append("No similar patterns found - fix may be unique")
            return recommendations

        if safe_files:
            recommendations.append(f"Apply fix to {len(safe_files)} safe files first")

        if high_risk_files:
            recommendations.append(
                f"Review {len(high_risk_files)} high-risk files manually"
            )
            recommendations.append(
                "Consider creating backups before modifying critical files"
            )

        if pattern_result.count > 10:
            recommendations.append(
                "Large number of patterns found - consider batch processing"
            )

        # Pattern-specific recommendations
        if pattern_result.pattern_type.value == "mkIf_home_packages":
            recommendations.append(
                "Nix home-manager package pattern - verify package availability"
            )
        elif pattern_result.pattern_type.value == "homebrew_list":
            recommendations.append(
                "Homebrew configuration - check package names and availability"
            )

        return recommendations

    def _create_workflow_summary(
        self, total_patterns: int, safe_files: int, high_risk_files: int
    ) -> str:
        """Create human-readable workflow summary"""
        if total_patterns == 0:
            return "No similar patterns found in codebase"

        summary = f"Found {total_patterns} similar patterns"

        if safe_files > 0:
            summary += f" ({safe_files} safe to modify"

        if high_risk_files > 0:
            summary += f", {high_risk_files} high-risk"

        if safe_files > 0:
            summary += ")"

        return summary

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
                f"Found {pattern_result.count} similar patterns - "
                "consider applying same fix"
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
                f"⚠️  {len(high_risk_files)} high-risk files found - "
                "proceed with caution"
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

        return (
            f"Found {pattern_result.count} similar patterns, "
            f"{safe_count} safe to modify"
        )

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
