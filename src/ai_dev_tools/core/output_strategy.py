"""
Output Strategy Pattern - AI-first design with machine-readable defaults

Provides efficient, token-optimized output for AI consumption with optional
human-readable formats via flags.
"""

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class OutputFormat(Enum):
    """Available output formats"""

    COMPACT = "compact"  # Default: minimal JSON for AI
    JSON = "json"  # Pretty JSON for debugging
    HUMAN = "human"  # Human-readable text
    SILENT = "silent"  # No output (exit code only)


class OutputStrategy(ABC):
    """Abstract base class for output strategies"""

    @abstractmethod
    def format_result(self, data: Dict[str, Any]) -> str:
        """Format the result data according to strategy"""
        pass

    @abstractmethod
    def format_error(self, error: str, code: int = 1) -> str:
        """Format error messages according to strategy"""
        pass


class CompactStrategy(OutputStrategy):
    """Compact JSON output optimized for AI token efficiency"""

    def format_result(self, data: Dict[str, Any]) -> str:
        """Minimal JSON without whitespace"""
        # Remove null/empty values to save tokens
        cleaned = self._clean_data(data)
        return json.dumps(cleaned, separators=(",", ":"))

    def format_error(self, error: str, code: int = 1) -> str:
        """Compact error format"""
        return json.dumps({"error": error, "code": code}, separators=(",", ":"))

    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove empty/null values to minimize tokens"""
        cleaned = {}
        for key, value in data.items():
            if value is not None and value != [] and value != {}:
                if isinstance(value, dict):
                    cleaned_nested = self._clean_data(value)
                    if cleaned_nested:
                        cleaned[key] = cleaned_nested
                elif isinstance(value, list):
                    cleaned_list = [item for item in value if item is not None]
                    if cleaned_list:
                        cleaned[key] = cleaned_list
                else:
                    cleaned[key] = value
        return cleaned


class JsonStrategy(OutputStrategy):
    """Pretty JSON output for debugging"""

    def format_result(self, data: Dict[str, Any]) -> str:
        """Pretty formatted JSON"""
        return json.dumps(data, indent=2)

    def format_error(self, error: str, code: int = 1) -> str:
        """Pretty formatted error"""
        return json.dumps({"error": error, "code": code}, indent=2)


class HumanStrategy(OutputStrategy):
    """Human-readable text output"""

    def format_result(self, data: Dict[str, Any]) -> str:
        """Human-friendly text format"""
        if "count" in data:
            return f"Found {data['count']} results"
        elif "risk_level" in data:
            return f"Risk Level: {data['risk_level']} - {data.get('message', '')}"
        elif "health" in data:
            health = data["health"]
            return f"Repository Health: {health.get('status', 'unknown')}"
        else:
            return str(data)

    def format_error(self, error: str, code: int = 1) -> str:
        """Human-friendly error format"""
        return f"Error: {error}"


class SilentStrategy(OutputStrategy):
    """No output - exit code only"""

    def format_result(self, data: Dict[str, Any]) -> str:
        """No output"""
        return ""

    def format_error(self, error: str, code: int = 1) -> str:
        """No output for errors either"""
        return ""


class OutputFormatter:
    """Factory for output strategies with AI-first defaults"""

    _strategies = {
        OutputFormat.COMPACT: CompactStrategy(),
        OutputFormat.JSON: JsonStrategy(),
        OutputFormat.HUMAN: HumanStrategy(),
        OutputFormat.SILENT: SilentStrategy(),
    }

    @classmethod
    def get_strategy(cls, format_type: OutputFormat = OutputFormat.SILENT) -> OutputStrategy:
        """Get output strategy (defaults to silent for maximum efficiency)"""
        return cls._strategies[format_type]

    @classmethod
    def format_output(cls, data: Dict[str, Any], format_type: OutputFormat = OutputFormat.SILENT) -> str:
        """Format output using specified strategy (defaults to silent)"""
        strategy = cls.get_strategy(format_type)
        return strategy.format_result(data)

    @classmethod
    def format_error(cls, error: str, code: int = 1, format_type: OutputFormat = OutputFormat.SILENT) -> str:
        """Format error using specified strategy (defaults to silent)"""
        strategy = cls.get_strategy(format_type)
        return strategy.format_error(error, code)


def create_ai_optimized_result(
    count: int,
    items: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create AI-optimized result structure

    Prioritizes essential information first for token efficiency:
    1. Count (for exit code)
    2. Essential items only
    3. Metadata only if needed
    """
    result = {"c": count}  # Short key to save tokens

    if items:
        # Only include essential fields from items
        essential_items = []
        for item in items:
            essential = {}
            # Map to shorter keys for token efficiency
            if "file" in item:
                essential["f"] = item["file"]
            if "line" in item:
                essential["l"] = item["line"]
            if "confidence" in item and item["confidence"] < 1.0:
                essential["conf"] = round(item["confidence"], 2)
            if "risk_level" in item:
                essential["risk"] = item["risk_level"]
            essential_items.append(essential)

        if essential_items:
            result["items"] = essential_items

    if metadata:
        # Only include non-default metadata
        filtered_meta = {k: v for k, v in metadata.items() if v is not None and v != "" and v != []}
        if filtered_meta:
            result["meta"] = filtered_meta

    return result
