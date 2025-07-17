"""
Safety Checker - AI-optimized repository safety analysis

Provides libraries for checking if code changes are safe to make.
Designed for AI agents to assess risk before making modifications.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union


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
    """
    AI-optimized safety checker for code modifications

    Designed for AI agents to assess risk before making changes
    """

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
        """
        Check the safety of modifying a specific file

        Args:
            file_path: Path to the file to check

        Returns:
            SafetyResult with risk assessment
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return SafetyResult(
                risk_level=RiskLevel.CRITICAL,
                reasons=["File does not exist"],
                safe_to_modify=False,
                recommendations=["Ensure file exists before modification"],
            )

        try:
            with open(file_path_obj, encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()
        except (OSError, UnicodeDecodeError) as e:
            return SafetyResult(
                risk_level=RiskLevel.HIGH,
                reasons=[f"Cannot read file: {e}"],
                safe_to_modify=False,
                recommendations=["Fix file access issues before modification"],
            )

        # Analyze file for risk factors
        risk_level, reasons, recommendations = self._analyze_file_content(file_path_obj, content, lines)

        return SafetyResult(
            risk_level=risk_level,
            reasons=reasons,
            safe_to_modify=risk_level in [RiskLevel.SAFE, RiskLevel.MEDIUM],
            recommendations=recommendations,
        )

    def _analyze_file_content(
        self, file_path_obj: Path, content: str, lines: List[str]
    ) -> tuple[RiskLevel, List[str], List[str]]:
        """Analyze file content for risk factors"""
        reasons = []
        recommendations = []
        risk_level = RiskLevel.SAFE

        # Check if file is critical (exit code 3)
        if file_path_obj.name in self.critical_files:
            reasons.append(f"🛑 Critical system file: {file_path_obj.name}")
            recommendations.append("Create backup and test in VM first")
            risk_level = RiskLevel.CRITICAL
        # Check if file is high risk (exit code 2)
        elif file_path_obj.name in self.high_risk_files:
            reasons.append(f"🚨 High-risk system file: {file_path_obj.name}")
            recommendations.append("Make backup before modifying")
            risk_level = RiskLevel.HIGH
        else:
            # Start with safe assumption
            risk_level = RiskLevel.SAFE

        # Check file extension for medium risk
        if file_path_obj.suffix in self.medium_risk_extensions and risk_level == RiskLevel.SAFE:
            risk_level = RiskLevel.MEDIUM
            reasons.append(f"⚠️ Configuration file: {file_path_obj.suffix}")

        # Check file contents for high-risk patterns
        try:
            with open(file_path_obj, encoding="utf-8") as f:
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

        # Add appropriate recommendations
        if risk_level == RiskLevel.SAFE:
            recommendations.append("✅ Safe to modify")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("⚠️ Proceed with caution, test changes")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("🚨 High risk - make backups, test thoroughly")
        else:  # CRITICAL
            recommendations.append("🛑 Critical risk - consider alternative approach")

        return risk_level, reasons, recommendations
