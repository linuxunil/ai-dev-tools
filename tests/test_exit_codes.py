"""
Exit Code Validation Tests

Tests that ensure exit codes accurately encode information and are reliable
for AI agent decision making.
"""

import subprocess
import pytest
from pathlib import Path
import tempfile
import json

from ai_dev_tools.core.exit_codes import ExitCodeEncoder, ExitCodeDecoder


class TestExitCodeEncoding:
    """Test exit code encoding functions"""

    def test_encode_count_valid_range(self):
        """Test count encoding within valid range"""
        assert ExitCodeEncoder.encode_count(0) == 0
        assert ExitCodeEncoder.encode_count(1) == 1
        assert ExitCodeEncoder.encode_count(254) == 254

    def test_encode_count_overflow(self):
        """Test count encoding handles overflow"""
        assert ExitCodeEncoder.encode_count(255) == 254
        assert ExitCodeEncoder.encode_count(1000) == 254

    def test_encode_count_negative(self):
        """Test count encoding handles negative values"""
        assert ExitCodeEncoder.encode_count(-1) == 0
        assert ExitCodeEncoder.encode_count(-100) == 0

    def test_encode_risk_level(self):
        """Test risk level encoding"""
        assert ExitCodeEncoder.encode_risk_level(0) == 0  # SAFE
        assert ExitCodeEncoder.encode_risk_level(1) == 1  # MEDIUM
        assert ExitCodeEncoder.encode_risk_level(2) == 2  # HIGH
        assert ExitCodeEncoder.encode_risk_level(3) == 3  # CRITICAL

    def test_encode_risk_level_bounds(self):
        """Test risk level encoding bounds"""
        assert ExitCodeEncoder.encode_risk_level(-1) == 0
        assert ExitCodeEncoder.encode_risk_level(4) == 3
        assert ExitCodeEncoder.encode_risk_level(100) == 3

    def test_encode_boolean(self):
        """Test boolean encoding"""
        assert ExitCodeEncoder.encode_boolean(True) == 1
        assert ExitCodeEncoder.encode_boolean(False) == 0

    def test_encode_error(self):
        """Test error encoding"""
        assert ExitCodeEncoder.encode_error() == 255


class TestExitCodeDecoding:
    """Test exit code decoding functions"""

    def test_decode_count(self):
        """Test count decoding"""
        assert ExitCodeDecoder.decode_count(0) == 0
        assert ExitCodeDecoder.decode_count(10) == 10
        assert ExitCodeDecoder.decode_count(254) == 254
        assert ExitCodeDecoder.decode_count(255) is None  # Error code

    def test_decode_risk_level(self):
        """Test risk level decoding"""
        assert ExitCodeDecoder.decode_risk_level(0) == "SAFE"
        assert ExitCodeDecoder.decode_risk_level(1) == "MEDIUM"
        assert ExitCodeDecoder.decode_risk_level(2) == "HIGH"
        assert ExitCodeDecoder.decode_risk_level(3) == "CRITICAL"
        assert ExitCodeDecoder.decode_risk_level(4) is None

    def test_decode_boolean(self):
        """Test boolean decoding"""
        assert ExitCodeDecoder.decode_boolean(0) is False
        assert ExitCodeDecoder.decode_boolean(1) is True
        assert ExitCodeDecoder.decode_boolean(2) is None

    def test_is_error(self):
        """Test error detection"""
        assert ExitCodeDecoder.is_error(255) is True
        assert ExitCodeDecoder.is_error(0) is False
        assert ExitCodeDecoder.is_error(1) is False
        assert ExitCodeDecoder.is_error(254) is False


class TestCLIExitCodes:
    """Test CLI tools produce correct exit codes"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def create_test_file(self, filename: str, content: str) -> Path:
        """Create a test file with content"""
        file_path = self.temp_path / filename
        file_path.write_text(content)
        return file_path

    def test_pattern_scanner_exit_codes(self):
        """Test pattern scanner exit codes"""
        # Create test files
        shell_nix = self.create_test_file(
            "shell.nix",
            """
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.development.enable [
    pkgs.git
  ];
}
""",
        )

        core_nix = self.create_test_file(
            "core.nix",
            """
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.core.enable [
    pkgs.curl
  ];
}
""",
        )

        # Test pattern scanning
        result = subprocess.run(
            [
                "ai-pattern-scan",
                f"{shell_nix}:3",
                "--search-dir",
                str(self.temp_path),
                "--format",
                "silent",
            ],
            capture_output=True,
        )

        # Should find 1 similar pattern (core.nix)
        assert result.returncode == 1
        assert result.stdout == b""  # Silent mode

    def test_pattern_scanner_no_patterns(self):
        """Test pattern scanner when no patterns found"""
        unique_file = self.create_test_file(
            "unique.nix",
            """
{
  services.nginx.enable = true;
}
""",
        )

        result = subprocess.run(
            [
                "ai-pattern-scan",
                f"{unique_file}:2",
                "--search-dir",
                str(self.temp_path),
                "--format",
                "silent",
            ],
            capture_output=True,
        )

        # Should find 0 patterns
        assert result.returncode == 0
        assert result.stdout == b""

    def test_pattern_scanner_invalid_input(self):
        """Test pattern scanner with invalid input"""
        result = subprocess.run(
            ["ai-pattern-scan", "nonexistent.nix:10", "--format", "silent"],
            capture_output=True,
        )

        # Should return error code
        assert result.returncode == 255

    def test_safety_checker_exit_codes(self):
        """Test safety checker exit codes"""
        # Test safe file
        safe_file = self.create_test_file("utils.py", "def helper(): pass")
        result = subprocess.run(
            ["ai-safety-check", str(safe_file), "--format", "silent"],
            capture_output=True,
        )
        assert result.returncode == 0  # SAFE

        # Test critical file
        critical_file = self.create_test_file("flake.nix", "{}")
        result = subprocess.run(
            ["ai-safety-check", str(critical_file), "--format", "silent"],
            capture_output=True,
        )
        assert result.returncode == 3  # CRITICAL

    def test_repo_analyzer_exit_codes(self):
        """Test repository analyzer exit codes"""
        # Test clean repository
        result = subprocess.run(
            [
                "ai-repo-status",
                "--repo-path",
                str(self.temp_path),
                "--format",
                "silent",
            ],
            capture_output=True,
        )

        # Should return syntax error count (0 for clean repo)
        assert result.returncode == 0


class TestExitCodeConsistency:
    """Test that exit codes are consistent across runs"""

    def test_deterministic_exit_codes(self):
        """Test that same input produces same exit code"""
        # Create consistent test scenario
        temp_dir = tempfile.mkdtemp()
        test_file = Path(temp_dir) / "test.nix"
        test_file.write_text("{ services.nginx.enable = true; }")

        # Run same command multiple times
        results = []
        for _ in range(5):
            result = subprocess.run(
                ["ai-pattern-scan", f"{test_file}:1", "--format", "silent"],
                capture_output=True,
            )
            results.append(result.returncode)

        # All results should be identical
        assert all(code == results[0] for code in results)

    def test_exit_code_ranges(self):
        """Test that exit codes stay within valid ranges"""
        # This would be a property-based test in practice
        for count in [0, 1, 10, 100, 254, 255, 1000]:
            encoded = ExitCodeEncoder.encode_count(count)
            assert 0 <= encoded <= 255

        for risk in [-1, 0, 1, 2, 3, 4, 100]:
            encoded = ExitCodeEncoder.encode_risk_level(risk)
            assert 0 <= encoded <= 3
