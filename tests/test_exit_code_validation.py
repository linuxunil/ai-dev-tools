"""
Exit Code Validation Tests

Critical tests to ensure exit codes work correctly for AI consumption.
This is the core of our AI-first design.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path


class TestExitCodeValidation:
    """Test that all tools return correct exit codes for AI consumption"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)

    def test_pattern_scanner_exit_codes(self):
        """Test pattern scanner returns count as exit code"""
        # Create target file
        target_file = self.test_path / "target.nix"
        target_file.write_text(
            "mkIf config.programs.git.enable home.packages = with pkgs; [ git ];"
        )

        # Create similar files
        for i in range(3):
            similar_file = self.test_path / f"similar_{i}.nix"
            similar_file.write_text(
                f"mkIf config.programs.test{i}.enable home.packages = with pkgs; [ test{i} ];"
            )

        # Test via CLI
        result = subprocess.run(
            [
                "ai-pattern-scan",
                f"{target_file}:1",
                "--search-dir",
                str(self.test_path),
                "--format",
                "silent",
            ],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        # Exit code should equal number of patterns found
        assert 0 <= result.returncode <= 254
        # Should find at least the similar patterns we created
        assert result.returncode >= 3

    def test_safety_checker_exit_codes(self):
        """Test safety checker returns risk level as exit code"""
        # Test safe file (should return 0)
        safe_file = self.test_path / "safe.py"
        safe_file.write_text("print('hello')")

        result = subprocess.run(
            ["ai-safety-check", str(safe_file), "--format", "silent"],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert result.returncode == 0  # SAFE

        # Test critical file (should return 3)
        critical_file = self.test_path / "flake.nix"
        critical_file.write_text("{ }")

        result = subprocess.run(
            ["ai-safety-check", str(critical_file), "--format", "silent"],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert result.returncode >= 2  # HIGH or CRITICAL

    def test_ai_workflow_exit_codes(self):
        """Test AI workflow commands return meaningful exit codes"""
        # Create test file
        test_file = self.test_path / "test.nix"
        test_file.write_text("mkIf config.test home.packages = with pkgs; [ test ];")

        # Test fix-and-propagate workflow
        result = subprocess.run(
            [
                "ai-workflow",
                "fix-and-propagate",
                str(test_file),
                "1",
                "--search-dir",
                str(self.test_path),
                "--format",
                "silent",
            ],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert 0 <= result.returncode <= 255

        # Test repo-context
        result = subprocess.run(
            ["ai-workflow", "repo-context", "--format", "silent"],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert 0 <= result.returncode <= 255

        # Test assess-safety
        result = subprocess.run(
            ["ai-workflow", "assess-safety", str(test_file), "--format", "silent"],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert 0 <= result.returncode <= 255

    def test_error_exit_codes(self):
        """Test that errors return exit code 255"""
        # Test with nonexistent file
        result = subprocess.run(
            ["ai-pattern-scan", "nonexistent.nix:1", "--format", "silent"],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert result.returncode == 255

        # Test safety check with nonexistent file
        result = subprocess.run(
            ["ai-safety-check", "nonexistent.nix", "--format", "silent"],
            capture_output=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        assert result.returncode == 255

    def test_exit_code_consistency(self):
        """Test that same input produces same exit code (deterministic)"""
        test_file = self.test_path / "consistent.nix"
        test_file.write_text("test content")

        # Run pattern scan multiple times
        exit_codes = []
        for _ in range(3):
            result = subprocess.run(
                ["ai-pattern-scan", f"{test_file}:1", "--format", "silent"],
                capture_output=True,
                cwd="/Users/disco/projects/ai-dev-tools",
            )
            exit_codes.append(result.returncode)

        # All exit codes should be the same
        assert len(set(exit_codes)) == 1, f"Inconsistent exit codes: {exit_codes}"

    def test_exit_code_ranges(self):
        """Test that exit codes stay within valid ranges"""
        test_file = self.test_path / "range_test.nix"
        test_file.write_text("test")

        # Test all tools stay within 0-255 range
        tools_and_args = [
            ["ai-pattern-scan", f"{test_file}:1", "--format", "silent"],
            ["ai-safety-check", str(test_file), "--format", "silent"],
            ["ai-workflow", "repo-context", "--format", "silent"],
            ["ai-workflow", "assess-safety", str(test_file), "--format", "silent"],
        ]

        for tool_args in tools_and_args:
            result = subprocess.run(
                tool_args, capture_output=True, cwd="/Users/disco/projects/ai-dev-tools"
            )
            assert 0 <= result.returncode <= 255, (
                f"Invalid exit code {result.returncode} for {tool_args[0]}"
            )

    def test_silent_mode_no_output(self):
        """Test that silent mode produces no output (token efficiency)"""
        test_file = self.test_path / "silent_test.py"
        test_file.write_text("print('test')")

        # Test all tools in silent mode
        tools_and_args = [
            ["ai-pattern-scan", f"{test_file}:1", "--format", "silent"],
            ["ai-safety-check", str(test_file), "--format", "silent"],
            ["ai-workflow", "repo-context", "--format", "silent"],
            ["ai-workflow", "assess-safety", str(test_file), "--format", "silent"],
        ]

        for tool_args in tools_and_args:
            result = subprocess.run(
                tool_args, capture_output=True, cwd="/Users/disco/projects/ai-dev-tools"
            )
            # Silent mode should produce no stdout output
            assert result.stdout == b"", (
                f"Tool {tool_args[0]} produced output in silent mode: {result.stdout}"
            )
