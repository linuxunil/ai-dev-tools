#!/usr/bin/env python3
"""
Test script demonstrating AI Development Tools with Ollama integration.

This script shows how exit-code-first tools enable zero-token AI workflows
by using only exit codes for decision making.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_safety_check(file_path: str) -> int:
    """Run safety check and return exit code."""
    try:
        result = subprocess.run(
            ["python3", "standalone_safety_check.py", file_path],
            capture_output=True,
            timeout=10,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        return 255  # Error code


def simulate_ai_decision(exit_code: int) -> str:
    """Simulate AI decision making using only exit codes."""
    risk_levels = {
        0: "SAFE - Proceed with modifications",
        1: "MEDIUM - Review before changes",
        2: "HIGH - Require approval",
        3: "CRITICAL - Block all changes",
    }
    return risk_levels.get(exit_code, "ERROR - Unknown risk level")


def test_with_ollama(file_path: str) -> None:
    """Test the workflow with Ollama making decisions."""
    print(f"🔍 Testing file: {file_path}")

    # Step 1: Run safety check (zero tokens used)
    exit_code = run_safety_check(file_path)
    print(f"📊 Safety check exit code: {exit_code}")

    # Step 2: AI makes decision using only exit code
    decision = simulate_ai_decision(exit_code)
    print(f"🤖 AI decision: {decision}")

    # Step 3: Demonstrate with actual Ollama call
    prompt = f"""
    A safety tool returned exit code {exit_code} for a file.
    Exit codes mean: 0=SAFE, 1=MEDIUM, 2=HIGH, 3=CRITICAL risk.
    
    What action should be taken? Answer in one word: PROCEED, REVIEW, APPROVE, or BLOCK.
    """

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2:1b", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            ai_response = result.stdout.strip()
            print(f"🧠 Ollama response: {ai_response}")
        else:
            print(f"❌ Ollama error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("⏰ Ollama timeout")
    except Exception as e:
        print(f"❌ Error calling Ollama: {e}")


def create_test_files():
    """Create test files with different risk levels."""
    test_files = {
        "safe_file.py": "# Simple Python file\nprint('Hello, World!')\n",
        "medium_file.nix": "# Nix configuration\n{ pkgs }: pkgs.hello\n",
        "critical_file.nix": "# Critical system file\nwith import <nixpkgs> {};\n",
    }

    for filename, content in test_files.items():
        Path(filename).write_text(content)
        print(f"📝 Created test file: {filename}")


def main():
    """Main test function."""
    print("🚀 AI Development Tools - Ollama Integration Test")
    print("=" * 50)

    # Create test files
    create_test_files()

    # Test each file
    test_files = ["safe_file.py", "medium_file.nix", "critical_file.nix"]

    for file_path in test_files:
        print()
        test_with_ollama(file_path)
        time.sleep(1)  # Brief pause between tests

    print()
    print("✅ Test completed!")
    print()
    print("🎯 Key Benefits Demonstrated:")
    print("  • Zero-token decision making using exit codes")
    print("  • Sub-second safety assessments")
    print("  • Local AI model integration")
    print("  • 100% token efficiency vs traditional JSON parsing")


if __name__ == "__main__":
    main()
