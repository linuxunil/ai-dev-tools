"""
Basic AI Agent Tests

Tests core AI Agent functionality to ensure workflows work correctly.
"""

import pytest
import tempfile
from pathlib import Path

from src.ai_dev_tools.agents.ai_agent import AIAgent


class TestAIAgentBasic:
    """Test basic AI Agent functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        self.agent = AIAgent(str(self.test_path))

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        agent = AIAgent()
        assert hasattr(agent, "pattern_scanner")
        assert hasattr(agent, "safety_checker")
        assert hasattr(agent, "repo_analyzer")

    def test_fix_and_propagate_workflow_no_patterns(self):
        """Test workflow with no similar patterns"""
        # Create a unique file
        target_file = self.test_path / "unique.nix"
        target_file.write_text("unique content that won't match anything")

        result = self.agent.fix_and_propagate_workflow(
            fixed_file=str(target_file), fixed_line=1, search_scope=str(self.test_path)
        )

        assert result.success
        assert result.similar_patterns["count"] == 0
        assert "No similar patterns found" in result.summary

    def test_fix_and_propagate_workflow_with_patterns(self):
        """Test workflow finds and assesses similar patterns"""
        # Create target file
        target_file = self.test_path / "target.nix"
        target_file.write_text(
            "mkIf config.programs.git.enable home.packages = with pkgs; [ git ];"
        )

        # Create similar file
        similar_file = self.test_path / "similar.nix"
        similar_file.write_text(
            "mkIf config.programs.vim.enable home.packages = with pkgs; [ vim ];"
        )

        result = self.agent.fix_and_propagate_workflow(
            fixed_file=str(target_file), fixed_line=1, search_scope=str(self.test_path)
        )

        assert result.success
        assert result.similar_patterns["count"] >= 1
        assert len(result.safety_assessment["details"]) >= 1
        assert len(result.recommendations) > 0

    def test_repository_context(self):
        """Test repository context assessment"""
        context = self.agent.get_repository_context()

        assert "ready_for_changes" in context
        assert "health_score" in context
        assert "syntax_errors" in context
        assert "summary" in context
        assert isinstance(context["exit_code"], int)

    def test_assess_change_safety_single_file(self):
        """Test safety assessment for single file"""
        # Create test file
        test_file = self.test_path / "test.py"
        test_file.write_text("print('hello')")

        safety = self.agent.assess_change_safety([str(test_file)])

        assert "safe_to_proceed" in safety
        assert "risk_level" in safety
        assert "file_assessments" in safety
        assert len(safety["file_assessments"]) == 1
        assert isinstance(safety["exit_code"], int)

    def test_assess_change_safety_multiple_files(self):
        """Test safety assessment for multiple files"""
        # Create safe file
        safe_file = self.test_path / "safe.py"
        safe_file.write_text("print('safe')")

        # Create risky file
        risky_file = self.test_path / "configuration.nix"
        risky_file.write_text('{ system.stateVersion = "23.05"; }')

        safety = self.agent.assess_change_safety([str(safe_file), str(risky_file)])

        assert len(safety["file_assessments"]) == 2
        # Should reflect the highest risk level
        assert safety["risk_level"] in ["safe", "medium", "high", "critical"]

    def test_workflow_exit_codes(self):
        """Test that workflows return meaningful exit codes"""
        # Create test file
        test_file = self.test_path / "test.nix"
        test_file.write_text("test content")

        # Test fix_and_propagate workflow
        result = self.agent.fix_and_propagate_workflow(
            fixed_file=str(test_file), fixed_line=1
        )
        assert 0 <= result.exit_code <= 255

        # Test repository context
        context = self.agent.get_repository_context()
        assert 0 <= context["exit_code"] <= 255

        # Test safety assessment
        safety = self.agent.assess_change_safety([str(test_file)])
        assert 0 <= safety["exit_code"] <= 255

    def test_error_handling(self):
        """Test error handling in workflows"""
        # Test with invalid file path
        result = self.agent.fix_and_propagate_workflow(
            fixed_file="/nonexistent/path.nix", fixed_line=1
        )

        assert not result.success
        assert result.exit_code == 255
        assert "error" in result.summary.lower() or "fail" in result.summary.lower()
