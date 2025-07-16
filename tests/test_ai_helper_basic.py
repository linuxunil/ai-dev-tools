"""
Basic tests for AI Helper core functionality

Tests the core AIHelper class and its workflow methods
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from src.ai_dev_tools.core.ai_helper import AIHelper, HelperWorkflowResult


class TestAIHelper:
    """Test AIHelper core functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.helper = AIHelper(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test AIHelper initialization"""
        assert self.helper.repo_path == Path(self.temp_dir)
        assert hasattr(self.helper, "pattern_scanner")
        assert hasattr(self.helper, "safety_checker")
        assert hasattr(self.helper, "repo_analyzer")
        assert hasattr(self.helper, "difference_analyzer")

    def test_init_default_path(self):
        """Test AIHelper initialization with default path"""
        helper = AIHelper()
        assert helper.repo_path == Path(".")

    @patch("src.ai_dev_tools.core.ai_helper.RepoAnalyzer")
    @patch("src.ai_dev_tools.core.ai_helper.ContextAnalyzer")
    @patch("src.ai_dev_tools.core.ai_helper.ProjectValidator")
    def test_analyze_project_success(self, mock_validator, mock_context, mock_repo):
        """Test successful project analysis"""
        # Mock repository health
        mock_repo_health = Mock()
        mock_repo_health.health_score = 0.8
        mock_repo_health.syntax_errors = 0
        mock_repo_health.missing_files = []
        mock_repo_health.summary = "Good health"
        mock_repo_health.recommendations = ["Keep up good work"]

        mock_repo.return_value.get_repo_health.return_value = mock_repo_health

        # Mock context analysis
        mock_context_result = Mock()
        mock_context_result.complexity_score = 30
        mock_context_result.project_type.value = "python"
        mock_context_result.framework.value = "unknown"
        mock_context_result.dependencies = []

        mock_context.return_value.analyze.return_value = mock_context_result

        # Mock validation
        mock_validation_result = Mock()
        mock_validation_result.issues = []
        mock_validation_result.is_valid = True
        mock_validation_result.summary = "All good"
        mock_validation_result.total_files_checked = 10

        mock_validator.return_value.validate_project.return_value = (
            mock_validation_result
        )

        # Test analysis
        result = self.helper.analyze_project()

        assert isinstance(result, HelperWorkflowResult)
        assert result.workflow_type == "analyze_project"
        assert result.success is True
        assert "ready for AI assistance" in result.summary
        assert result.context["ready_for_ai"] is True
        assert result.exit_code > 0  # Should be health score * 100

    @patch("src.ai_dev_tools.core.ai_helper.RepoAnalyzer")
    def test_analyze_project_with_syntax_errors(self, mock_repo):
        """Test project analysis with syntax errors"""
        # Mock repository health with errors
        mock_repo_health = Mock()
        mock_repo_health.health_score = 0.5
        mock_repo_health.syntax_errors = 5
        mock_repo_health.missing_files = []
        mock_repo_health.summary = "Has errors"
        mock_repo_health.recommendations = ["Fix syntax errors"]

        mock_repo.return_value.get_repo_health.return_value = mock_repo_health

        # Test analysis (skip validation and context for simplicity)
        result = self.helper.analyze_project(
            include_validation=False, include_context=False
        )

        assert result.success is True
        assert "syntax errors" in result.summary
        assert result.context["ready_for_ai"] is False
        assert "Fix syntax errors" in result.recommendations

    def test_analyze_project_exception_handling(self):
        """Test project analysis exception handling"""
        # Force an exception by using invalid path
        helper = AIHelper("/nonexistent/path")

        result = helper.analyze_project()

        assert result.success is False
        assert result.exit_code == 255
        assert "failed" in result.summary.lower()
        assert "Fix analysis error" in result.recommendations

    @patch("src.ai_dev_tools.core.ai_helper.SafetyChecker")
    @patch("src.ai_dev_tools.core.ai_helper.ImpactAnalyzer")
    def test_plan_changes_success(self, mock_impact, mock_safety):
        """Test successful change planning"""
        # Mock safety checker
        mock_safety_result = Mock()
        mock_safety_result.risk_level.name = "SAFE"
        mock_safety_result.risk_level.value = 0
        mock_safety_result.safe_to_modify = True
        mock_safety_result.reasons = []

        mock_safety.return_value.check_file_safety.return_value = mock_safety_result

        # Mock impact analyzer
        mock_impact_result = Mock()
        mock_impact_result.impacted_files = []
        mock_impact_result.overall_risk.name = "LOW"
        mock_impact_result.recommendations = ["Proceed with caution"]

        mock_impact.return_value.analyze_file_impact.return_value = mock_impact_result

        # Test planning
        result = self.helper.plan_changes(
            target_files=["test.py", "test2.py"], change_description="Test changes"
        )

        assert result.workflow_type == "plan_changes"
        assert result.success is True
        assert result.context["safe_to_proceed"] is True
        assert result.context["target_files_count"] == 2
        assert result.exit_code == 0  # Safe risk level

    @patch("src.ai_dev_tools.core.ai_helper.SafetyChecker")
    def test_plan_changes_high_risk(self, mock_safety):
        """Test change planning with high-risk files"""
        # Mock high-risk safety result
        mock_safety_result = Mock()
        mock_safety_result.risk_level.name = "CRITICAL"
        mock_safety_result.risk_level.value = 3
        mock_safety_result.safe_to_modify = False
        mock_safety_result.reasons = ["Critical system file"]

        mock_safety.return_value.check_file_safety.return_value = mock_safety_result

        # Test planning
        result = self.helper.plan_changes(
            target_files=["critical_file.py"],
            assess_impact=False,  # Skip impact analysis
        )

        assert result.success is True
        assert result.context["safe_to_proceed"] is False
        assert result.exit_code == 3  # Critical risk level
        assert "CAUTION" in result.recommendations[0]

    @patch("src.ai_dev_tools.core.ai_helper.PatternScanner")
    @patch("src.ai_dev_tools.core.ai_helper.SafetyChecker")
    def test_systematic_fix_workflow_success(self, mock_safety, mock_pattern):
        """Test successful systematic fix workflow"""
        # Mock pattern scanner
        mock_match = Mock()
        mock_match.file = "similar.py"
        mock_match.line = 10
        mock_match.confidence = 0.9

        mock_pattern_result = Mock()
        mock_pattern_result.count = 3
        mock_pattern_result.matches = [mock_match]
        mock_pattern_result.to_dict.return_value = {"count": 3}

        mock_pattern.return_value.scan_for_similar_patterns.return_value = (
            mock_pattern_result
        )

        # Mock safety checker
        mock_safety_result = Mock()
        mock_safety_result.risk_level.name = "SAFE"
        mock_safety_result.risk_level.value = 0
        mock_safety_result.safe_to_modify = True

        mock_safety.return_value.check_file_safety.return_value = mock_safety_result

        # Test systematic fix
        result = self.helper.systematic_fix_workflow(fixed_file="test.py", fixed_line=5)

        assert result.workflow_type == "systematic_fix"
        assert result.success is True
        assert result.context["patterns_found"] == 3
        assert result.context["safe_files"] == 1
        assert result.exit_code == 3  # Pattern count

    @patch("src.ai_dev_tools.core.ai_helper.PatternScanner")
    def test_systematic_fix_workflow_no_patterns(self, mock_pattern):
        """Test systematic fix workflow with no patterns found"""
        # Mock pattern scanner with no results
        mock_pattern_result = Mock()
        mock_pattern_result.count = 0
        mock_pattern_result.matches = []
        mock_pattern_result.to_dict.return_value = {"count": 0}

        mock_pattern.return_value.scan_for_similar_patterns.return_value = (
            mock_pattern_result
        )

        # Test systematic fix
        result = self.helper.systematic_fix_workflow(fixed_file="test.py", fixed_line=5)

        assert result.success is True
        assert result.context["patterns_found"] == 0
        assert result.exit_code == 0
        assert "unique" in result.summary

    @patch("src.ai_dev_tools.core.ai_helper.DifferenceAnalyzer")
    def test_compare_configurations_success(self, mock_diff):
        """Test successful configuration comparison"""
        # Mock difference analyzer
        mock_difference = Mock()
        mock_difference.significance.name = "MAJOR"

        mock_diff_result = Mock()
        mock_diff_result.differences = [mock_difference]
        mock_diff_result.to_dict.return_value = {"differences": 1}

        mock_diff.return_value.compare_files.return_value = mock_diff_result

        # Test comparison
        result = self.helper.compare_configurations("file1.py", "file2.py")

        assert result.workflow_type == "compare_configurations"
        assert result.success is True
        assert result.context["differences_found"] == 1
        assert result.context["semantic_changes"] == 1
        assert result.exit_code == 1

    @patch("src.ai_dev_tools.core.ai_helper.DifferenceAnalyzer")
    def test_compare_configurations_identical(self, mock_diff):
        """Test configuration comparison with identical files"""
        # Mock difference analyzer with no differences
        mock_diff_result = Mock()
        mock_diff_result.differences = []
        mock_diff_result.to_dict.return_value = {"differences": 0}

        mock_diff.return_value.compare_files.return_value = mock_diff_result

        # Test comparison
        result = self.helper.compare_configurations("file1.py", "file2.py")

        assert result.success is True
        assert result.context["differences_found"] == 0
        assert result.exit_code == 0
        assert "identical" in result.recommendations[0]

    def test_helper_workflow_result_to_dict(self):
        """Test HelperWorkflowResult serialization"""
        result = HelperWorkflowResult(
            workflow_type="test",
            success=True,
            summary="Test summary",
            context={"key": "value"},
            recommendations=["Do this"],
            exit_code=42,
            details={"detail": "info"},
        )

        result_dict = result.to_dict()

        assert result_dict["workflow"] == "test"
        assert result_dict["success"] is True
        assert result_dict["summary"] == "Test summary"
        assert result_dict["context"]["key"] == "value"
        assert result_dict["recommendations"] == ["Do this"]
        assert result_dict["exit_code"] == 42
        assert result_dict["details"]["detail"] == "info"


if __name__ == "__main__":
    pytest.main([__file__])
