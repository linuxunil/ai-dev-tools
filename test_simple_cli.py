#!/usr/bin/env python3
"""
Test simple CLI tools
"""

import sys
import subprocess
import tempfile
from pathlib import Path


def test_simple_safety_cli():
    """Test the simple safety checker CLI"""
    print("Testing Simple Safety Checker CLI...")

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
        [sys.executable, "src/ai_dev_tools/cli/simple_safety_check.py", str(test_file)],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    print(f"   Stdout: '{result.stdout}'")
    print(f"   Stderr: '{result.stderr}'")
    assert result.stdout.strip() == "", "Silent mode should produce no output"
    assert result.returncode == 1, (
        f"Expected exit code 1 (medium risk), got {result.returncode}"
    )

    # Test 2: Human format
    print("\n2. Testing human format...")
    result = subprocess.run(
        [
            sys.executable,
            "src/ai_dev_tools/cli/simple_safety_check.py",
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
            "src/ai_dev_tools/cli/simple_safety_check.py",
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
        [
            sys.executable,
            "src/ai_dev_tools/cli/simple_safety_check.py",
            str(critical_file),
        ],
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
        [
            sys.executable,
            "src/ai_dev_tools/cli/simple_safety_check.py",
            "nonexistent.txt",
        ],
        capture_output=True,
        text=True,
        cwd="/Users/disco/projects/ai-dev-tools",
    )

    print(f"   Exit code: {result.returncode}")
    assert result.returncode == 3, (
        f"Expected exit code 3 (critical), got {result.returncode}"
    )

    # Test 6: AI workflow simulation
    print("\n6. Testing AI workflow simulation...")

    # AI checks multiple files using only exit codes
    files_to_check = [
        (str(test_file), 1),  # Medium risk
        (str(critical_file), 3),  # Critical risk
        ("nonexistent.txt", 3),  # Critical (not found)
    ]

    ai_decisions = []
    for file_path, expected_risk in files_to_check:
        result = subprocess.run(
            [sys.executable, "src/ai_dev_tools/cli/simple_safety_check.py", file_path],
            capture_output=True,
            text=True,
            cwd="/Users/disco/projects/ai-dev-tools",
        )

        risk_level = result.returncode
        should_modify = (
            risk_level <= 1
        )  # AI decision: only modify safe/medium risk files
        ai_decisions.append((file_path, risk_level, should_modify))

        assert risk_level == expected_risk, (
            f"Expected risk {expected_risk}, got {risk_level}"
        )

    print("   AI decisions based on exit codes:")
    for file_path, risk, should_modify in ai_decisions:
        print(f"     {Path(file_path).name}: risk={risk}, modify={should_modify}")

    # AI should decide to modify only the medium risk file
    safe_to_modify = [decision for decision in ai_decisions if decision[2]]
    assert len(safe_to_modify) == 1, (
        f"Expected 1 file safe to modify, got {len(safe_to_modify)}"
    )

    print("\n✅ All CLI tests passed!")
    return True


if __name__ == "__main__":
    try:
        test_simple_safety_cli()
        print("🎉 Simple Safety checker CLI is working correctly!")
        print("🤖 AI can make decisions using only exit codes - zero tokens used!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
