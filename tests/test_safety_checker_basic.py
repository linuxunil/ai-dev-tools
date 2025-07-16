"""
Basic Safety Checker Tests

Tests core safety checking functionality to ensure it works correctly.
"""

import pytest
import tempfile
from pathlib import Path

from src.ai_dev_tools.core.safety_checker import SafetyChecker, RiskLevel


class TestSafetyCheckerBasic:
    """Test basic safety checker functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        self.checker = SafetyChecker()

    def test_checker_initialization(self):
        """Test checker initializes correctly"""
        checker = SafetyChecker()
        assert hasattr(checker, "critical_files")
        assert hasattr(checker, "dangerous_patterns")

    def test_check_nonexistent_file(self):
        """Test checking nonexistent file returns critical risk"""
        result = self.checker.check_file_safety("nonexistent.nix")
        assert result.risk_level == RiskLevel.CRITICAL
        assert not result.safe_to_modify
        assert "does not exist" in str(result.warnings)

    def test_check_safe_file(self):
        """Test checking safe file returns safe risk"""
        safe_file = self.test_path / "safe.py"
        safe_file.write_text("""
# Safe Python file
def hello():
    print("Hello, world!")
""")

        result = self.checker.check_file_safety(str(safe_file))
        assert result.risk_level == RiskLevel.SAFE
        assert result.safe_to_modify

    def test_check_critical_file(self):
        """Test checking critical file returns high risk"""
        critical_file = self.test_path / "configuration.nix"
        critical_file.write_text("""
{ config, pkgs, ... }:
{
  system.stateVersion = "23.05";
  boot.loader.systemd-boot.enable = true;
}
""")

        result = self.checker.check_file_safety(str(critical_file))
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert not result.safe_to_modify

    def test_check_dangerous_patterns(self):
        """Test detection of dangerous patterns"""
        dangerous_file = self.test_path / "dangerous.nix"
        dangerous_file.write_text("""
{
  # This contains dangerous operations
  system.activationScripts.dangerous = "rm -rf /tmp/test";
}
""")

        result = self.checker.check_file_safety(str(dangerous_file))
        assert result.risk_level >= RiskLevel.HIGH
        assert len(result.critical_sections) > 0

    def test_risk_level_exit_codes(self):
        """Test that risk levels map to correct exit codes"""
        # Test safe file
        safe_file = self.test_path / "safe.txt"
        safe_file.write_text("safe content")

        result = self.checker.check_file_safety(str(safe_file))
        assert result.risk_level.value == 0  # SAFE = 0

        # Test critical file name
        critical_file = self.test_path / "flake.nix"
        critical_file.write_text("{ }")

        result = self.checker.check_file_safety(str(critical_file))
        assert result.risk_level.value >= 2  # HIGH or CRITICAL

    def test_file_extension_risk_assessment(self):
        """Test that file extensions affect risk assessment"""
        # Test .nix file (higher risk)
        nix_file = self.test_path / "test.nix"
        nix_file.write_text("{ }")

        nix_result = self.checker.check_file_safety(str(nix_file))

        # Test .txt file (lower risk)
        txt_file = self.test_path / "test.txt"
        txt_file.write_text("plain text")

        txt_result = self.checker.check_file_safety(str(txt_file))

        # Nix files should generally be higher risk
        assert nix_result.risk_level.value >= txt_result.risk_level.value
