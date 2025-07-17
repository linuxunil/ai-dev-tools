#!/usr/bin/env python3
"""
Standalone Safety Checker CLI - AI-optimized interface

Demonstrates exit-code-first design for AI agents
"""

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union


# Embedded safety checker implementation
class RiskLevel(Enum):
    """Risk levels for code modifications"""

    SAFE = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class SafetyResult:
    """Result of a safety check"""

    risk_level: RiskLevel
    reasons: List[str]
    safe_to_modify: bool
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Union[str, int, bool, List[str]]]:
        """Convert to dictionary for JSON serialization"""
        return {
            "risk_level": self.risk_level.value,
            "risk_name": self.risk_level.name,
            "safe_to_modify": self.safe_to_modify,
            "reasons": self.reasons,
            "recommendations": self.recommendations,
        }

    def to_ai_format(self) -> Dict[str, Union[str, int, bool, List[str]]]:
        """Convert to AI-optimized compact format"""
        result = {
            "r": self.risk_level.value,  # Short key for risk
            "s": self.safe_to_modify,  # Short key for safe
        }

        # Only include non-empty lists to save tokens
        if self.reasons:
            result["reasons"] = self.reasons
        if self.recommendations:
            result["recs"] = self.recommendations

        return result


class SafetyChecker:
    """AI-optimized safety checker for code modifications"""

    def __init__(self):
        """Initialize safety checker"""
        # Critical files (exit code 3)
        self.critical_files = {
            "flake.nix",
            "flake.lock",
        }

        # High risk files (exit code 2)
        self.high_risk_files = {
            "configuration.nix",
            "hardware-configuration.nix",
        }

        # High risk patterns in content
        self.high_risk_patterns = [
            "system.stateVersion",
            "ids.gids",
            "ids.uids",
            "boot.loader",
            "networking.hostName",
        ]

        # Medium risk patterns (exit code 1)
        self.medium_risk_extensions = {".nix", ".toml", ".json", ".yml", ".yaml"}
        self.medium_risk_patterns = [
            "environment.systemPackages",
            "services.",
            "programs.",
        ]

    def check_file_safety(self, file_path: str) -> SafetyResult:
        """Check if a file is safe to modify"""
        path = Path(file_path)
        reasons = []
        recommendations = []

        # Check if file exists
        if not path.exists():
            return SafetyResult(
                risk_level=RiskLevel.CRITICAL,
                reasons=["File does not exist"],
                safe_to_modify=False,
                recommendations=["Check file path"],
            )

        # Check if file is critical (exit code 3)
        if path.name in self.critical_files:
            reasons.append(f"🛑 Critical system file: {path.name}")
            recommendations.append("Create backup and test in VM first")
            risk_level = RiskLevel.CRITICAL
        # Check if file is high risk (exit code 2)
        elif path.name in self.high_risk_files:
            reasons.append(f"🚨 High-risk system file: {path.name}")
            recommendations.append("Make backup before modifying")
            risk_level = RiskLevel.HIGH
        else:
            # Start with safe assumption
            risk_level = RiskLevel.SAFE

        # Check file extension for medium risk
        if path.suffix in self.medium_risk_extensions and risk_level == RiskLevel.SAFE:
            risk_level = RiskLevel.MEDIUM
            reasons.append(f"⚠️ Configuration file: {path.suffix}")

        # Check file contents for high-risk patterns
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check for high-risk patterns
            for pattern in self.high_risk_patterns:
                if pattern in content:
                    reasons.append(f"🚨 Contains critical pattern: {pattern}")
                    recommendations.append(f"Be very careful when modifying {pattern}")
                    if risk_level.value < RiskLevel.HIGH.value:
                        risk_level = RiskLevel.HIGH

            # Check for medium-risk patterns (only if not already high/critical)
            if risk_level.value < RiskLevel.HIGH.value:
                for pattern in self.medium_risk_patterns:
                    if pattern in content:
                        reasons.append(f"⚠️ Contains system pattern: {pattern}")
                        if risk_level == RiskLevel.SAFE:
                            risk_level = RiskLevel.MEDIUM

        except Exception as e:
            reasons.append(f"Could not read file: {str(e)}")
            if risk_level == RiskLevel.SAFE:
                risk_level = RiskLevel.MEDIUM

        # Determine if safe to modify
        safe_to_modify = risk_level.value <= RiskLevel.MEDIUM.value

        # Add appropriate recommendations
        if risk_level == RiskLevel.SAFE:
            recommendations.append("✅ Safe to modify")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("⚠️ Proceed with caution, test changes")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("🚨 High risk - make backups, test thoroughly")
        else:  # CRITICAL
            recommendations.append("🛑 Critical risk - consider alternative approach")

        return SafetyResult(
            risk_level=risk_level,
            reasons=reasons,
            safe_to_modify=safe_to_modify,
            recommendations=recommendations,
        )


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


def demo():
    """Demonstrate the safety checker functionality"""
    print("🔍 AI Development Tools - Safety Checker Demo")
    print("=" * 50)

    checker = SafetyChecker()

    # Create temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Demo directory: {temp_dir}")

    # Demo files
    demo_files = [
        ("utils.py", "def helper(): return True", "Safe source code"),
        ("config.json", '{"debug": true}', "Medium risk config"),
        (
            "configuration.nix",
            "{ boot.loader.systemd-boot.enable = true; }",
            "High risk system config",
        ),
        ("flake.nix", '{ description = "test"; }', "Critical system file"),
    ]

    print("\n🧪 Testing different file types:")
    print("-" * 40)

    for filename, content, description in demo_files:
        # Create file
        file_path = temp_dir / filename
        file_path.write_text(content)

        # Check safety
        result = checker.check_file_safety(str(file_path))

        # Display result
        risk_emoji = ["✅", "⚠️", "🚨", "🛑"][result.risk_level.value]
        print(
            f"{risk_emoji} {filename:15} | Risk: {result.risk_level.name:8} | Exit: {result.risk_level.value} | {description}"
        )

    print("\n🤖 AI Usage Example:")
    print("-" * 40)
    print("# AI can make decisions using only exit codes:")
    print("import subprocess")
    print("result = subprocess.run(['python', 'standalone_safety_check.py', 'file.nix'])")
    print("risk_level = result.returncode")
    print("if risk_level <= 1:  # Safe or medium risk")
    print("    # Proceed with modifications")
    print("    pass")
    print("else:")
    print("    # Too risky, skip or get human approval")
    print("    pass")

    print("\n💾 Token Efficiency:")
    print("-" * 40)
    print("Silent mode (default): 0 tokens, exit code only")
    print("Compact mode: ~20-50 tokens, essential info only")
    print("Human mode: ~100-200 tokens, full explanation")

    print("\n🎯 Exit Code Patterns:")
    print("-" * 40)
    print("0 = SAFE      (proceed freely)")
    print("1 = MEDIUM    (proceed with caution)")
    print("2 = HIGH      (make backups first)")
    print("3 = CRITICAL  (avoid or get approval)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        main()
