#!/usr/bin/env python3
"""
Test CLI tools
"""

import sys
import subprocess
import tempfile
from pathlib import Path


def test_safety_cli():
    """Test the safety checker CLI"""
    print("Testing Safety Checker CLI...")

    # Create test files
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Testing in: {temp_dir}")

    # Test file
    test_file = temp_dir / "test.nix"
    test_file.write_text("{ programs.git.enable = true; }")

    # Critical file
    critical_file = temp_dir / "flake.nix"
    critical_file.write_text('{ description = "test"; }')

    # Test 1: Silent mode (default) - should produce no output
    print("\n1. Testing silent mode (default)...")
    result = subprocess.run(
        [sys.executable, "-m", "ai_dev_tools.cli.safety_check", str(test_file)],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    print(f"   Stdout: '{result.stdout}'")
    print(f"   Stderr: '{result.stderr}'")
    assert result.stdout == "", "Silent mode should produce no output"
    assert result.returncode == 1, (
        f"Expected exit code 1 (medium risk), got {result.returncode}"
    )

    # Test 2: Human format
    print("\n2. Testing human format...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.safety_check",
            str(test_file),
            "--format",
            "human",
        ],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    print(f"   Output: {result.stdout}")
    assert "Risk Level: MEDIUM" in result.stdout
    assert result.returncode == 1

    # Test 3: Compact format
    print("\n3. Testing compact format...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_dev_tools.cli.safety_check",
            str(test_file),
            "--format",
            "compact",
        ],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    print(f"   Output: {result.stdout}")
    assert '"r":1' in result.stdout, "Compact format should contain risk level"
    assert result.returncode == 1

    # Test 4: Critical file
    print("\n4. Testing critical file...")
    result = subprocess.run(
        [sys.executable, "-m", "ai_dev_tools.cli.safety_check", str(critical_file)],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    assert result.returncode == 3, (
        f"Expected exit code 3 (critical), got {result.returncode}"
    )

    # Test 5: Non-existent file
    print("\n5. Testing non-existent file...")
    result = subprocess.run(
        [sys.executable, "-m", "ai_dev_tools.cli.safety_check", "nonexistent.txt"],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    assert result.returncode == 3, (
        f"Expected exit code 3 (critical), got {result.returncode}"
    )

    print("\n✅ All CLI tests passed!")
    return True


if __name__ == "__main__":
    try:
        test_safety_cli()
        print("🎉 Safety checker CLI is working correctly!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
