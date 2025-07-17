"""
AI Development Tools - Efficient tools for AI-assisted development

This package provides libraries and CLI tools optimized for AI workflows:
- Pattern detection and analysis
- Repository safety checks
- Code structure analysis
- Agent-friendly interfaces
"""

__version__ = "0.1.0"

from .core.pattern_scanner import PatternScanner
from .core.repo_analyzer import RepoAnalyzer
from .core.safety_checker import SafetyChecker

__all__ = [
    "PatternScanner",
    "SafetyChecker",
    "RepoAnalyzer",
]
