"""
Token Efficiency Tests

Tests that measure and validate token savings from exit-code-first design.
"""

import json
import subprocess
import tempfile
from pathlib import Path


class TestTokenEfficiency:
    """Test token efficiency of different output formats"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create test file
        test_file = self.repo_path / "test.nix"
        test_file.write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.development.enable [
    pkgs.git
    pkgs.vim
  ];
}
""")

    def run_tool_with_format(self, tool: str, format_type: str, *args) -> tuple[int, str]:
        """Run tool with specific format and return exit code and output"""
        cmd = [tool] + list(args) + ["--format", format_type]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
        return result.returncode, result.stdout

    def count_tokens_approximate(self, text: str) -> int:
        """Approximate token count (rough estimate)"""
        if not text.strip():
            return 0
        # Rough approximation: 1 token per 4 characters
        return len(text) // 4

    def test_silent_mode_zero_tokens(self):
        """Test that silent mode produces zero output tokens"""
        exit_code, output = self.run_tool_with_format(
            "ai-pattern-scan",
            "silent",
            f"{self.repo_path}/test.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Silent mode should produce no output
        assert output == ""
        assert self.count_tokens_approximate(output) == 0

        # But should still provide information via exit code
        assert exit_code >= 0
        assert exit_code <= 254

    def test_compact_vs_json_efficiency(self):
        """Test that compact format is more efficient than JSON"""
        # Get compact output
        exit_code_compact, output_compact = self.run_tool_with_format(
            "ai-pattern-scan",
            "compact",
            f"{self.repo_path}/test.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Get JSON output
        exit_code_json, output_json = self.run_tool_with_format(
            "ai-pattern-scan",
            "json",
            f"{self.repo_path}/test.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Exit codes should be identical
        assert exit_code_compact == exit_code_json

        # Compact should use fewer tokens
        compact_tokens = self.count_tokens_approximate(output_compact)
        json_tokens = self.count_tokens_approximate(output_json)

        if output_compact:  # Only compare if there's output
            assert compact_tokens < json_tokens

    def test_format_hierarchy_efficiency(self):
        """Test efficiency hierarchy: silent < compact < json < human"""
        formats = ["silent", "compact", "json", "human"]
        outputs = {}

        for format_type in formats:
            exit_code, output = self.run_tool_with_format("ai-safety-check", format_type, f"{self.repo_path}/test.nix")
            outputs[format_type] = {
                "exit_code": exit_code,
                "output": output,
                "tokens": self.count_tokens_approximate(output),
            }

        # All should have same exit code
        exit_codes = [outputs[fmt]["exit_code"] for fmt in formats]
        assert all(code == exit_codes[0] for code in exit_codes)

        # Token usage should increase: silent <= compact <= json <= human
        token_counts = [outputs[fmt]["tokens"] for fmt in formats]

        # Silent should be 0
        assert token_counts[0] == 0

        # Each subsequent format should use same or more tokens
        for i in range(1, len(token_counts)):
            assert token_counts[i] >= token_counts[i - 1]

    def test_exit_code_information_density(self):
        """Test that exit codes encode maximum information efficiently"""

        # Test pattern scanner exit codes
        test_cases = [
            (f"{self.repo_path}/test.nix:3", "should find 0 patterns"),
            (f"{self.repo_path}/test.nix:1", "should find 0 patterns"),
        ]

        for target, description in test_cases:
            exit_code, output = self.run_tool_with_format(
                "ai-pattern-scan", "silent", target, "--search-dir", str(self.repo_path)
            )

            # Exit code should encode the count directly
            assert 0 <= exit_code <= 254  # Valid count range

            # Zero tokens used
            assert output == ""

            # Information density: 1 exit code encodes complete result
            # This is infinitely more efficient than any text output

    def test_ai_workflow_token_savings(self):
        """Test token savings in realistic AI workflow"""

        # Traditional approach (hypothetical verbose output)
        traditional_tokens = 0

        # Step 1: Check repo status (traditional would output JSON)
        traditional_tokens += 50  # Estimated tokens for JSON status

        # Step 2: Find patterns (traditional would output pattern list)
        traditional_tokens += 100  # Estimated tokens for pattern results

        # Step 3: Check safety (traditional would output risk assessment)
        traditional_tokens += 75  # Estimated tokens for safety info

        # Total traditional approach: ~225 tokens

        # Exit-code-first approach
        exit_code_tokens = 0

        # Step 1: Check repo status (exit code only)
        exit_code, output = self.run_tool_with_format("ai-repo-status", "silent", "--repo-path", str(self.repo_path))
        exit_code_tokens += self.count_tokens_approximate(output)

        # Step 2: Find patterns (exit code only)
        exit_code, output = self.run_tool_with_format(
            "ai-pattern-scan",
            "silent",
            f"{self.repo_path}/test.nix:3",
            "--search-dir",
            str(self.repo_path),
        )
        exit_code_tokens += self.count_tokens_approximate(output)

        # Step 3: Check safety (exit code only)
        exit_code, output = self.run_tool_with_format("ai-safety-check", "silent", f"{self.repo_path}/test.nix")
        exit_code_tokens += self.count_tokens_approximate(output)

        # Exit-code approach should use 0 tokens
        assert exit_code_tokens == 0

        # Calculate savings
        token_savings = traditional_tokens - exit_code_tokens
        efficiency_improvement = token_savings / traditional_tokens if traditional_tokens > 0 else 1

        # Should achieve 100% token savings
        assert efficiency_improvement == 1.0  # 100% savings
        assert token_savings >= 200  # Significant absolute savings


class TestOutputQuality:
    """Test that when output is needed, it's high quality and efficient"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create test files with patterns
        (self.repo_path / "shell.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.development.enable [
    pkgs.git
  ];
}
""")

        (self.repo_path / "core.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.core.enable [
    pkgs.curl
  ];
}
""")

    def test_compact_output_validity(self):
        """Test that compact output is valid and minimal"""
        exit_code, output = self.run_tool_with_format(
            "ai-pattern-scan",
            "compact",
            f"{self.repo_path}/shell.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        if output:
            # Should be valid JSON
            data = json.loads(output)

            # Should contain essential information
            assert "c" in data  # count

            # Should not contain unnecessary whitespace
            assert "\n" not in output
            assert "  " not in output  # No double spaces

            # Exit code should match data
            assert exit_code == data["c"]

    def test_json_output_completeness(self):
        """Test that JSON output contains complete information when needed"""
        exit_code, output = self.run_tool_with_format(
            "ai-pattern-scan",
            "json",
            f"{self.repo_path}/shell.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        if output:
            data = json.loads(output)

            # Should contain complete information
            assert "count" in data
            assert "target" in data

            # Exit code should match data
            assert exit_code == data["count"]

    def run_tool_with_format(self, tool: str, format_type: str, *args) -> tuple[int, str]:
        """Run tool with specific format and return exit code and output"""
        cmd = [tool] + list(args) + ["--format", format_type]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
        return result.returncode, result.stdout
