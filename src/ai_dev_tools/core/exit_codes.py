"""
Exit Code Patterns - AI-optimized communication via exit codes

Defines standardized exit codes that encode information for maximum efficiency.
Exit codes are the most token-efficient way to communicate results to AI agents.
"""

from enum import Enum
from typing import Any, Dict, Optional


class ExitCodePattern(Enum):
    """Standard exit code patterns for AI tools"""

    # Success patterns
    SUCCESS = 0  # Operation successful, no items found

    # Count patterns (1-254)
    COUNT_RANGE = (1, 254)  # Exit code = count of items found

    # Error patterns (255)
    ERROR_INVALID_INPUT = 255  # Invalid arguments or file not found

    # Risk level patterns (0-3)
    RISK_SAFE = 0  # Safe to proceed
    RISK_MEDIUM = 1  # Medium risk
    RISK_HIGH = 2  # High risk
    RISK_CRITICAL = 3  # Critical risk

    # Boolean patterns (0-1)
    BOOLEAN_FALSE = 0  # False/No/Disabled
    BOOLEAN_TRUE = 1  # True/Yes/Enabled


class ExitCodeEncoder:
    """
    Encodes information into exit codes for maximum AI efficiency

    Exit codes eliminate the need for output parsing and provide
    instant, token-free communication of results.
    """

    @staticmethod
    def encode_count(count: int) -> int:
        """
        Encode count as exit code

        Args:
            count: Number of items found (0-254)

        Returns:
            Exit code representing count (0-254, or 254 if count > 254)
        """
        if count < 0:
            return 0
        elif count > 254:
            return 254  # Max representable count
        else:
            return count

    @staticmethod
    def encode_risk_level(risk_level: int) -> int:
        """
        Encode risk level as exit code

        Args:
            risk_level: Risk level (0=safe, 1=medium, 2=high, 3=critical)

        Returns:
            Exit code representing risk level (0-3)
        """
        return max(0, min(3, risk_level))

    @staticmethod
    def encode_boolean(value: bool) -> int:
        """
        Encode boolean as exit code

        Args:
            value: Boolean value

        Returns:
            Exit code (0=False, 1=True)
        """
        return 1 if value else 0

    @staticmethod
    def encode_error() -> int:
        """
        Encode error condition

        Returns:
            Exit code 255 for errors
        """
        return 255


class ExitCodeDecoder:
    """
    Decodes exit codes back to information for testing/validation
    """

    @staticmethod
    def decode_count(exit_code: int) -> Optional[int]:
        """Decode count from exit code"""
        if 0 <= exit_code <= 254:
            return exit_code
        return None

    @staticmethod
    def decode_risk_level(exit_code: int) -> Optional[str]:
        """Decode risk level from exit code"""
        risk_map = {0: "SAFE", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}
        return risk_map.get(exit_code)

    @staticmethod
    def decode_boolean(exit_code: int) -> Optional[bool]:
        """Decode boolean from exit code"""
        if exit_code == 0:
            return False
        elif exit_code == 1:
            return True
        return None

    @staticmethod
    def is_error(exit_code: int) -> bool:
        """Check if exit code represents an error"""
        return exit_code == 255


def create_exit_code_result(
    primary_value: int,
    pattern: ExitCodePattern,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create result optimized for exit code communication

    Args:
        primary_value: The main value to encode in exit code
        pattern: The exit code pattern being used
        metadata: Optional metadata (only included if output is requested)

    Returns:
        Result dict with exit code and minimal metadata
    """
    result = {"exit_code": primary_value, "pattern": pattern.name}

    # Only include metadata if it's essential
    if metadata:
        essential_meta = {
            k: v for k, v in metadata.items() if v is not None and v != "" and v != []
        }
        if essential_meta:
            result["meta"] = essential_meta

    return result


# AI Agent Usage Examples:
"""
# Pattern Scanner - Count-based exit codes
ai-pattern-scan shell.nix:10 --format silent
# Exit code 3 = found 3 patterns (no output needed)

# Safety Checker - Risk-based exit codes
ai-safety-check configuration.nix --format silent
# Exit code 2 = HIGH risk (no output needed)

# Repository Analyzer - Error count exit codes
ai-repo-status --format silent
# Exit code 0 = no syntax errors (no output needed)

# Boolean checks
ai-repo-ready --format silent
# Exit code 1 = ready for changes (no output needed)

# AI can make decisions purely from exit codes:
if subprocess.run(["ai-pattern-scan", "file.nix:10"]).returncode > 0:
    # Found patterns, apply fix to similar locations
    pattern_count = result.returncode

if subprocess.run(["ai-safety-check", "file.nix"]).returncode <= 1:
    # Safe or medium risk, proceed with changes

if subprocess.run(["ai-repo-status"]).returncode == 0:
    # No syntax errors, repository is clean
"""
