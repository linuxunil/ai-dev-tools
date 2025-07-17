#!/usr/bin/env python3
"""
Simple test script for safety checker
"""

import sys
import tempfile
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, "src")

from ai_dev_tools.core.safety_checker import SafetyChecker


def test_safety_checker():
    """Test the safety checker functionality"""
    print("Testing Safety Checker...")

    checker = SafetyChecker()

    # Create temporary directory for tests
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Testing in: {temp_dir}")

    # Test 1: Safe file (Python source)
    safe_file = temp_dir / "utils.py"
    safe_file.write_text("def helper(): return True")
    result = checker.check_file_safety(str(safe_file))
    print(f"✅ Safe file: risk={result.risk_level.value} ({result.risk_level.name}), safe={result.safe_to_modify}")
    assert result.risk_level.value == 0, f"Expected risk 0, got {result.risk_level.value}"

    # Test 2: Critical file (flake.nix)
    critical_file = temp_dir / "flake.nix"
    critical_file.write_text('{ description = "test flake"; }')
    result = checker.check_file_safety(str(critical_file))
    print(f"🛑 Critical file: risk={result.risk_level.value} ({result.risk_level.name}), safe={result.safe_to_modify}")
    assert result.risk_level.value == 3, f"Expected risk 3, got {result.risk_level.value}"

    # Test 3: High risk file (configuration.nix)
    high_file = temp_dir / "configuration.nix"
    high_file.write_text("{ boot.loader.systemd-boot.enable = true; }")
    result = checker.check_file_safety(str(high_file))
    print(f"🚨 High risk file: risk={result.risk_level.value} ({result.risk_level.name}), safe={result.safe_to_modify}")
    assert result.risk_level.value == 2, f"Expected risk 2, got {result.risk_level.value}"

    # Test 4: Medium risk file (.nix extension)
    medium_file = temp_dir / "module.nix"
    medium_file.write_text("{ programs.git.enable = true; }")
    result = checker.check_file_safety(str(medium_file))
    print(
        f"⚠️  Medium risk file: risk={result.risk_level.value} ({result.risk_level.name}), safe={result.safe_to_modify}"
    )
    assert result.risk_level.value == 1, f"Expected risk 1, got {result.risk_level.value}"

    # Test 5: Non-existent file
    result = checker.check_file_safety("nonexistent.txt")
    print(
        f"❌ Non-existent file: risk={result.risk_level.value} ({result.risk_level.name}), safe={result.safe_to_modify}"
    )
    assert result.risk_level.value == 3, f"Expected risk 3, got {result.risk_level.value}"

    # Test AI format
    ai_result = result.to_ai_format()
    print(f"🤖 AI format: {ai_result}")
    assert "r" in ai_result, "AI format should have 'r' key"
    assert "s" in ai_result, "AI format should have 's' key"

    print("\n✅ All safety checker tests passed!")
    return True


if __name__ == "__main__":
    try:
        test_safety_checker()
        print("🎉 Safety checker is working correctly!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
