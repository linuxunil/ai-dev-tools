#!/usr/bin/env python3
"""
Simple CLI for safety checking - AI-optimized interface (no external dependencies)

Provides command-line interface for safety analysis with AI-friendly output
"""

import sys
import json
import argparse
from pathlib import Path

from ..core.safety_checker import SafetyChecker


def main():
    """
    Check if a file is safe to modify

    Exit code: risk level (0=SAFE, 1=MEDIUM, 2=HIGH, 3=CRITICAL)
    """
    parser = argparse.ArgumentParser(
        description="Check if a file is safe to modify",
        epilog="Exit code: risk level (0=SAFE, 1=MEDIUM, 2=HIGH, 3=CRITICAL)",
    )
    parser.add_argument("file_path", help="File to check for safety")
    parser.add_argument(
        "--format",
        choices=["silent", "compact", "json", "human"],
        default="silent",
        help="Output format (default: silent for maximum efficiency - exit code only)",
    )

    args = parser.parse_args()

    # Run safety check
    checker = SafetyChecker()
    result = checker.check_file_safety(args.file_path)

    # Output results using exit-code-first strategy
    if args.format == "silent":
        # No output - exit code only (maximum efficiency)
        pass
    elif args.format == "compact":
        # AI-optimized compact JSON
        print(json.dumps(result.to_ai_format(), separators=(",", ":")))
    elif args.format == "json":
        # Pretty JSON for debugging
        print(json.dumps(result.to_dict(), indent=2))
    elif args.format == "human":
        # Human-readable output
        print(f"Risk Level: {result.risk_level.name}")
        print(f"Safe to Modify: {result.safe_to_modify}")
        if result.reasons:
            print("Reasons:")
            for reason in result.reasons:
                print(f"  - {reason}")
        if result.recommendations:
            print("Recommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")

    # Exit with risk level (most efficient communication)
    sys.exit(result.risk_level.value)


if __name__ == "__main__":
    main()
