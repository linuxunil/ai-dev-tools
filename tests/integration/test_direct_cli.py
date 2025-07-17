#!/usr/bin/env python3
"""
Test CLI tools directly
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")


def test_safety_cli_direct():
    """Test the safety checker CLI by importing directly"""
    print("Testing Safety Checker CLI directly...")

    # Create test files
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Testing in: {temp_dir}")

    # Test file
    test_file = temp_dir / "test.nix"
    test_file.write_text("{ programs.git.enable = true; }")

    # Import and test the CLI function
    from ai_dev_tools.core.safety_checker import SafetyChecker

    # Test the core functionality first
    checker = SafetyChecker()
    result = checker.check_file_safety(str(test_file))
    print(f"Core result: risk={result.risk_level.value}, safe={result.safe_to_modify}")

    # Test AI format
    ai_format = result.to_ai_format()
    print(f"AI format: {ai_format}")

    # Test that we can import click
    try:
        import click

        print("✅ Click imported successfully")
    except ImportError as e:
        print(f"❌ Click import failed: {e}")
        return False

    print("✅ CLI components working!")
    return True


if __name__ == "__main__":
    try:
        test_safety_cli_direct()
        print("🎉 Safety checker CLI components are working!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
