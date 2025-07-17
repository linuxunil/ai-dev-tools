"""
AI Helper - Unified AI assistant with tool orchestration and workflow automation

Provides high-level workflows that orchestrate all AI development tools:
- Project analysis and health assessment
- Change planning and impact analysis
- Systematic fix workflows
- Decision support for AI agents
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .context_analyzer import ContextAnalyzer
from .difference_analyzer import DifferenceAnalyzer
from .impact_analyzer import ImpactAnalyzer
from .pattern_scanner import PatternScanner
from .repo_analyzer import RepoAnalyzer
from .safety_checker import RiskLevel, SafetyChecker
from .validator import ProjectValidator


@dataclass
class HelperWorkflowResult:
    """Result of an AI Helper workflow execution"""

    workflow_type: str
    success: bool
    summary: str
    context: Dict[str, Any]
    recommendations: List[str]
    exit_code: int
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "workflow": self.workflow_type,
            "success": self.success,
            "summary": self.summary,
            "context": self.context,
            "recommendations": self.recommendations,
            "exit_code": self.exit_code,
            "details": self.details,
        }


class AIHelper:
    """
    Unified AI assistant that orchestrates all development tools

    Provides high-level workflows for:
    - Project analysis and understanding
    - Change planning and validation
    - Systematic code improvements
    - Decision support for AI agents
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize AI Helper with repository context

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)

        # Initialize tools that don't need parameters
        self.pattern_scanner = PatternScanner()
        self.safety_checker = SafetyChecker()
        self.repo_analyzer = RepoAnalyzer()
        self.difference_analyzer = DifferenceAnalyzer()

    def analyze_project(self, include_validation: bool = True, include_context: bool = True) -> HelperWorkflowResult:
        """
        Comprehensive project analysis workflow

        Combines context analysis, validation, and health assessment
        to provide complete project understanding for AI decision making.

        Args:
            include_validation: Whether to include validation checks
            include_context: Whether to include context analysis

        Returns:
            HelperWorkflowResult with comprehensive project analysis
        """
        try:
            analysis_results = {}
            recommendations = []
            overall_score = 0.0

            # Step 1: Repository health assessment
            repo_health = self.repo_analyzer.get_repo_health()
            analysis_results["health"] = {
                "score": repo_health.health_score,
                "syntax_errors": repo_health.syntax_errors,
                "missing_files": repo_health.missing_files,
                "summary": repo_health.summary,
            }
            overall_score += repo_health.health_score * 0.3

            # Step 2: Context analysis (if requested)
            if include_context:
                context_analyzer = ContextAnalyzer(str(self.repo_path))
                context_result = context_analyzer.analyze()
                analysis_results["context"] = {
                    "complexity_score": context_result.complexity_score,
                    "project_type": context_result.project_type.value,
                    "framework": context_result.framework.value,
                    "dependencies": [dep.to_dict() for dep in context_result.dependencies],
                }
                # Normalize complexity score (lower is better for overall score)
                normalized_complexity = max(0, 1.0 - (context_result.complexity_score / 100))
                overall_score += normalized_complexity * 0.3

            # Step 3: Validation (if requested)
            if include_validation:
                validator = ProjectValidator(Path(str(self.repo_path)))
                validation_result = validator.validate_project()
                issues_count = len(validation_result.issues)
                analysis_results["validation"] = {
                    "issues_found": issues_count,
                    "is_valid": validation_result.is_valid,
                    "summary": validation_result.summary,
                    "total_files_checked": validation_result.total_files_checked,
                }
                # Validation score based on issues found (fewer issues = better)
                validation_score = max(0, 1.0 - (issues_count / 50))
                overall_score += validation_score * 0.4

            # Step 4: Generate unified recommendations
            recommendations.extend(repo_health.recommendations)
            if include_validation:
                # Add validation-based recommendations
                if not validation_result.is_valid:
                    recommendations.append("Fix validation issues before proceeding")

            # Add AI-specific recommendations
            if repo_health.syntax_errors > 0:
                recommendations.insert(0, "Fix syntax errors before AI-assisted changes")
            if overall_score < 0.6:
                recommendations.insert(0, "Project health below recommended threshold for AI changes")

            # Step 5: Determine readiness for AI assistance
            ready_for_ai = (
                repo_health.syntax_errors == 0
                and overall_score >= 0.6
                and (not include_validation or issues_count < 20)
            )

            summary = self._generate_project_summary(overall_score, ready_for_ai, repo_health.syntax_errors)

            # Exit code: overall health score * 100 (0-100 range)
            exit_code = min(int(overall_score * 100), 254)

            return HelperWorkflowResult(
                workflow_type="analyze_project",
                success=True,
                summary=summary,
                context={
                    "ready_for_ai": ready_for_ai,
                    "overall_score": overall_score,
                    "repo_path": str(self.repo_path),
                },
                recommendations=recommendations[:5],  # Top 5 recommendations
                exit_code=exit_code,
                details=analysis_results,
            )

        except Exception as e:
            return HelperWorkflowResult(
                workflow_type="analyze_project",
                success=False,
                summary=f"Project analysis failed: {str(e)}",
                context={"error": str(e)},
                recommendations=["Fix analysis error before proceeding"],
                exit_code=255,
                details={"error": str(e)},
            )

    def plan_changes(
        self,
        target_files: List[str],
        change_description: str = "",
        assess_impact: bool = True,
    ) -> HelperWorkflowResult:
        """
        Change planning workflow with impact analysis and safety assessment

        Args:
            target_files: Files that will be modified
            change_description: Description of planned changes
            assess_impact: Whether to perform impact analysis

        Returns:
            HelperWorkflowResult with change plan and safety assessment
        """
        try:
            planning_results = {}
            recommendations = []

            # Step 1: Safety assessment for target files
            safety_results = []
            max_risk = 0
            critical_files = []

            for file_path in target_files:
                safety = self.safety_checker.check_file_safety(file_path)
                safety_results.append(
                    {
                        "file": file_path,
                        "risk_level": safety.risk_level.name,
                        "safe_to_modify": safety.safe_to_modify,
                        "reasons": safety.reasons,
                    }
                )

                max_risk = max(max_risk, safety.risk_level.value)
                if safety.risk_level == RiskLevel.CRITICAL:
                    critical_files.append(file_path)

            planning_results["safety"] = {
                "max_risk": max_risk,
                "critical_files": critical_files,
                "assessments": safety_results,
            }

            # Step 2: Impact analysis (if requested)
            if assess_impact and target_files:
                impact_analyzer = ImpactAnalyzer(Path(str(self.repo_path)))
                impact_result = impact_analyzer.analyze_file_impact(Path(target_files[0]))
                planning_results["impact"] = {
                    "affected_files": len(impact_result.impacted_files),
                    "risk_level": impact_result.overall_risk.name,
                    "impacted_files": [f.to_dict() for f in impact_result.impacted_files],
                    "recommendations": impact_result.recommendations,
                }
                recommendations.extend(impact_result.recommendations[:2])

            # Step 3: Generate change plan recommendations
            if max_risk <= RiskLevel.MEDIUM.value and not critical_files:
                recommendations.insert(0, "Changes appear safe to proceed")
            elif critical_files:
                recommendations.insert(0, f"CAUTION: {len(critical_files)} critical files detected")
                recommendations.append("Create backups before modifying critical files")

            if len(target_files) > 10:
                recommendations.append("Consider batch processing for large change sets")

            # Step 4: Determine change safety
            safe_to_proceed = max_risk <= RiskLevel.MEDIUM.value and len(critical_files) == 0

            summary = self._generate_change_plan_summary(len(target_files), max_risk, safe_to_proceed)

            return HelperWorkflowResult(
                workflow_type="plan_changes",
                success=True,
                summary=summary,
                context={
                    "safe_to_proceed": safe_to_proceed,
                    "target_files_count": len(target_files),
                    "max_risk_level": max_risk,
                    "change_description": change_description,
                },
                recommendations=recommendations[:5],
                exit_code=max_risk,  # Risk level as exit code
                details=planning_results,
            )

        except Exception as e:
            return HelperWorkflowResult(
                workflow_type="plan_changes",
                success=False,
                summary=f"Change planning failed: {str(e)}",
                context={"error": str(e)},
                recommendations=["Fix planning error before proceeding"],
                exit_code=255,
                details={"error": str(e)},
            )

    def systematic_fix_workflow(
        self,
        fixed_file: str,
        fixed_line: int,
        search_scope: str = ".",
        max_patterns: int = 50,
    ) -> HelperWorkflowResult:
        """
        Systematic fix workflow: find similar patterns and assess safety

        This is the core AI workflow for applying fixes systematically:
        1. Find patterns similar to the fixed location
        2. Assess safety of each potential fix location
        3. Generate prioritized recommendations

        Args:
            fixed_file: File where fix was applied
            fixed_line: Line number of the fix
            search_scope: Directory scope for pattern search
            max_patterns: Maximum patterns to find

        Returns:
            HelperWorkflowResult with systematic fix plan
        """
        try:
            # Step 1: Find similar patterns
            pattern_result = self.pattern_scanner.scan_for_similar_patterns(
                target_file=fixed_file,
                target_line=fixed_line,
                search_dir=search_scope,
                max_results=max_patterns,
            )

            if pattern_result.count == 0:
                return HelperWorkflowResult(
                    workflow_type="systematic_fix",
                    success=True,
                    summary="No similar patterns found - fix appears unique",
                    context={"patterns_found": 0},
                    recommendations=["Fix is isolated - no further action needed"],
                    exit_code=0,
                    details={"patterns": pattern_result.to_dict()},
                )

            # Step 2: Assess safety for each pattern location
            safety_assessments = []
            safe_files = []
            high_risk_files = []

            for match in pattern_result.matches:
                safety = self.safety_checker.check_file_safety(match.file)
                assessment = {
                    "file": match.file,
                    "line": match.line,
                    "confidence": match.confidence,
                    "risk_level": safety.risk_level.name,
                    "safe_to_modify": safety.safe_to_modify,
                }
                safety_assessments.append(assessment)

                if safety.safe_to_modify and safety.risk_level.value <= RiskLevel.MEDIUM.value:
                    safe_files.append(match.file)
                elif safety.risk_level.value >= RiskLevel.HIGH.value:
                    high_risk_files.append(match.file)

            # Step 3: Generate systematic fix recommendations
            recommendations = []
            if safe_files:
                recommendations.append(f"Apply fix to {len(safe_files)} safe files first")
            if high_risk_files:
                recommendations.append(f"Review {len(high_risk_files)} high-risk files manually")
            if pattern_result.count > 20:
                recommendations.append("Large pattern set - consider batch processing")

            # Step 4: Create workflow summary
            summary = (
                f"Found {pattern_result.count} similar patterns ({len(safe_files)} safe, "
                f"{len(high_risk_files)} high-risk)"
            )

            return HelperWorkflowResult(
                workflow_type="systematic_fix",
                success=True,
                summary=summary,
                context={
                    "patterns_found": pattern_result.count,
                    "safe_files": len(safe_files),
                    "high_risk_files": len(high_risk_files),
                    "original_fix": {"file": fixed_file, "line": fixed_line},
                },
                recommendations=recommendations,
                exit_code=min(pattern_result.count, 254),
                details={
                    "patterns": pattern_result.to_dict(),
                    "safety_assessments": safety_assessments,
                    "safe_files": safe_files,
                    "high_risk_files": high_risk_files,
                },
            )

        except Exception as e:
            return HelperWorkflowResult(
                workflow_type="systematic_fix",
                success=False,
                summary=f"Systematic fix workflow failed: {str(e)}",
                context={"error": str(e)},
                recommendations=["Fix workflow error before proceeding"],
                exit_code=255,
                details={"error": str(e)},
            )

    def compare_configurations(self, file1: str, file2: str, context_lines: int = 3) -> HelperWorkflowResult:
        """
        Configuration comparison workflow with semantic analysis

        Args:
            file1: First file to compare
            file2: Second file to compare
            context_lines: Lines of context around differences

        Returns:
            HelperWorkflowResult with comparison analysis
        """
        try:
            # Perform difference analysis
            diff_result = self.difference_analyzer.compare_files(Path(file1), Path(file2))

            recommendations = []
            diff_count = len(diff_result.differences)
            semantic_count = 0
            if diff_count > 0:
                recommendations.append(f"Found {diff_count} differences")
                semantic_count = len([d for d in diff_result.differences if d.significance.name == "MAJOR"])
                if semantic_count > 0:
                    recommendations.append(f"{semantic_count} major changes detected")
                # Add basic recommendations
                recommendations.append("Review differences carefully before applying")
            else:
                recommendations.append("Files are identical")

            summary = f"Compared {file1} vs {file2}: {diff_count} differences"

            return HelperWorkflowResult(
                workflow_type="compare_configurations",
                success=True,
                summary=summary,
                context={
                    "file1": file1,
                    "file2": file2,
                    "differences_found": diff_count,
                    "semantic_changes": semantic_count,
                },
                recommendations=recommendations,
                exit_code=min(diff_count, 254),
                details={"comparison": diff_result.to_dict()},
            )

        except Exception as e:
            return HelperWorkflowResult(
                workflow_type="compare_configurations",
                success=False,
                summary=f"Configuration comparison failed: {str(e)}",
                context={"error": str(e)},
                recommendations=["Fix comparison error before proceeding"],
                exit_code=255,
                details={"error": str(e)},
            )

    def _generate_project_summary(self, overall_score: float, ready_for_ai: bool, syntax_errors: int) -> str:
        """Generate human-readable project analysis summary"""
        if syntax_errors > 0:
            return f"Project has {syntax_errors} syntax errors - fix before AI assistance"
        elif ready_for_ai:
            return f"Project ready for AI assistance (health: {overall_score:.1%})"
        else:
            return f"Project needs improvement before AI assistance (health: {overall_score:.1%})"

    def _generate_change_plan_summary(self, file_count: int, max_risk: int, safe_to_proceed: bool) -> str:
        """Generate human-readable change plan summary"""
        risk_names = {0: "safe", 1: "medium", 2: "high", 3: "critical"}
        risk_name = risk_names.get(max_risk, "unknown")

        if safe_to_proceed:
            return f"Change plan for {file_count} files: {risk_name} risk - safe to proceed"
        else:
            return f"Change plan for {file_count} files: {risk_name} risk - proceed with caution"
