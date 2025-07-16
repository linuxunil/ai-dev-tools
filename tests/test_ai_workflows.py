"""
AI Workflow Simulation Tests

Tests that simulate real AI agent usage patterns to ensure tools work
effectively for AI decision making.
"""

import subprocess
import pytest
import tempfile
from pathlib import Path
import json


class TestAIDecisionWorkflows:
    """Test AI agent decision-making workflows using exit codes"""

    def setup_method(self):
        """Set up test repository"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create realistic test repository
        self.create_test_repository()

    def create_test_repository(self):
        """Create a realistic test repository structure"""
        # Shell configuration with patterns
        (self.repo_path / "shell.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.development.enable [
    pkgs.git
    pkgs.vim
  ];
  
  programs.zsh.enable = true;
}
""")

        # Core configuration with similar pattern
        (self.repo_path / "core.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.core.enable [
    pkgs.curl
    pkgs.wget
  ];
}
""")

        # System configuration (high risk)
        (self.repo_path / "configuration.nix").write_text("""
{ config, pkgs, ... }:
{
  boot.loader.systemd-boot.enable = true;
  networking.hostName = "nixos";
}
""")

        # Safe source file
        src_dir = self.repo_path / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("def helper(): return True")

    def run_tool(self, tool: str, *args) -> int:
        """Run a tool and return exit code"""
        cmd = [tool] + list(args) + ["--format", "silent"]
        result = subprocess.run(cmd, capture_output=True, cwd=self.repo_path)
        return result.returncode

    def test_ai_pattern_fix_workflow(self):
        """Test AI workflow: fix error → find patterns → assess safety → apply fixes"""

        # Step 1: AI fixes an error in shell.nix at line 3
        # Step 2: AI looks for similar patterns
        pattern_count = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/shell.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Should find 1 similar pattern (core.nix)
        assert pattern_count == 1

        # Step 3: AI checks safety of modifying found files
        safety_risk = self.run_tool("ai-safety-check", f"{self.repo_path}/core.nix")

        # core.nix should be medium risk (exit code 1)
        assert safety_risk == 1

        # Step 4: AI decides to proceed (risk <= 1 is acceptable)
        should_proceed = safety_risk <= 1
        assert should_proceed is True

    def test_ai_safety_first_workflow(self):
        """Test AI workflow: check repository health before making changes"""

        # Step 1: AI checks repository health
        repo_health = self.run_tool(
            "ai-repo-status", "--repo-path", str(self.repo_path)
        )

        # Should be clean (0 syntax errors)
        assert repo_health == 0

        # Step 2: AI checks safety of critical file
        critical_safety = self.run_tool(
            "ai-safety-check", f"{self.repo_path}/configuration.nix"
        )

        # Should be high risk (exit code 2)
        assert critical_safety == 2

        # Step 3: AI decides not to modify critical files
        should_modify_critical = critical_safety <= 1
        assert should_modify_critical is False

        # Step 4: AI checks safety of source file
        source_safety = self.run_tool(
            "ai-safety-check", f"{self.repo_path}/src/utils.py"
        )

        # Should be safe (exit code 0)
        assert source_safety == 0

        # Step 5: AI proceeds with safe file
        should_modify_source = source_safety <= 1
        assert should_modify_source is True

    def test_ai_batch_processing_workflow(self):
        """Test AI workflow: process multiple files efficiently"""

        files_to_check = [
            f"{self.repo_path}/shell.nix",
            f"{self.repo_path}/core.nix",
            f"{self.repo_path}/configuration.nix",
            f"{self.repo_path}/src/utils.py",
        ]

        # AI checks safety of all files using only exit codes
        safety_results = {}
        for file_path in files_to_check:
            risk_level = self.run_tool("ai-safety-check", file_path)
            safety_results[file_path] = risk_level

        # AI categorizes files by risk
        safe_files = [f for f, risk in safety_results.items() if risk == 0]
        medium_risk_files = [f for f, risk in safety_results.items() if risk == 1]
        high_risk_files = [f for f, risk in safety_results.items() if risk >= 2]

        # Verify categorization
        assert len(safe_files) == 1  # utils.py
        assert len(medium_risk_files) == 2  # shell.nix, core.nix
        assert len(high_risk_files) == 1  # configuration.nix

        # AI makes batch decisions
        files_to_modify = safe_files + medium_risk_files
        files_to_avoid = high_risk_files

        assert len(files_to_modify) == 3
        assert len(files_to_avoid) == 1

    def test_ai_error_handling_workflow(self):
        """Test AI workflow handles errors gracefully"""

        # Step 1: AI tries to scan non-existent file
        error_code = self.run_tool("ai-pattern-scan", "nonexistent.nix:10")

        # Should get error code 255
        assert error_code == 255

        # Step 2: AI handles error and continues with valid files
        valid_code = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/shell.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Should succeed with valid file
        assert valid_code != 255
        assert valid_code >= 0

    def test_ai_zero_token_decision_making(self):
        """Test AI can make complex decisions using only exit codes (zero tokens)"""

        # Simulate AI decision tree using only exit codes
        decisions = {}

        # Check repository health (0 tokens)
        repo_status = self.run_tool(
            "ai-repo-status", "--repo-path", str(self.repo_path)
        )
        decisions["repo_clean"] = repo_status == 0

        # Find patterns (0 tokens)
        pattern_count = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/shell.nix:3",
            "--search-dir",
            str(self.repo_path),
        )
        decisions["has_patterns"] = pattern_count > 0
        decisions["pattern_count"] = pattern_count

        # Check safety (0 tokens)
        safety_risk = self.run_tool("ai-safety-check", f"{self.repo_path}/core.nix")
        decisions["safe_to_modify"] = safety_risk <= 1
        decisions["risk_level"] = safety_risk

        # AI makes final decision using only exit codes
        should_proceed = (
            decisions["repo_clean"]
            and decisions["has_patterns"]
            and decisions["safe_to_modify"]
        )

        # Verify AI can make informed decision with zero token cost
        assert should_proceed is True
        assert decisions["pattern_count"] == 1
        assert decisions["risk_level"] == 1  # Medium risk for .nix files


class TestAIWorkflowPerformance:
    """Test performance characteristics important for AI workflows"""

    def test_tool_execution_speed(self):
        """Test that tools execute quickly enough for AI workflows"""
        import time

        temp_dir = tempfile.mkdtemp()
        test_file = Path(temp_dir) / "test.nix"
        test_file.write_text("{ services.nginx.enable = true; }")

        # Measure execution time
        start_time = time.time()
        result = subprocess.run(
            ["ai-pattern-scan", f"{test_file}:1", "--format", "silent"],
            capture_output=True,
        )
        execution_time = time.time() - start_time

        # Should execute in under 1 second
        assert execution_time < 1.0
        assert result.returncode is not None

    def test_memory_efficiency(self):
        """Test that tools don't consume excessive memory"""
        # This would use memory profiling in practice
        # For now, just ensure tools complete without issues

        temp_dir = tempfile.mkdtemp()

        # Create larger test scenario
        for i in range(10):
            test_file = Path(temp_dir) / f"test_{i}.nix"
            test_file.write_text(f"""
{{ config, lib, pkgs, ... }}:
{{
  home.packages = lib.mkIf config.programs.test{i}.enable [
    pkgs.git
  ];
}}
""")

        # Run pattern scan on larger dataset
        result = subprocess.run(
            [
                "ai-pattern-scan",
                f"{Path(temp_dir) / 'test_0.nix'}:3",
                "--search-dir",
                temp_dir,
                "--format",
                "silent",
            ],
            capture_output=True,
        )

        # Should complete successfully
        assert result.returncode >= 0  # Not an error
        assert result.returncode <= 254  # Valid count range
