#!/usr/bin/env python3
"""
Standalone Pattern Scanner - Exit-code-first design

Finds similar code patterns and returns count via exit codes (0-254).
Designed for zero-token AI decision making.

Exit Codes:
- 0-254: Number of patterns found
- 255: Error (file not found, invalid input, etc.)
"""

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PatternType(Enum):
    """Known pattern types for specialized matching"""

    MKIF_HOME_PACKAGES = "mkIf_home_packages"
    MKIF_LIST_CONCAT = "mkIf_list_concat"
    HOMEBREW_LIST = "homebrew_list"
    SHELL_SCRIPT_BIN = "shell_script_bin"
    HOME_FILE_CONFIG = "home_file_config"
    GENERIC = "generic"


@dataclass
class PatternMatch:
    """Represents a found pattern match"""

    file: str
    line: int
    confidence: float
    pattern_type: PatternType
    content: str


class PatternScanner:
    """AI-optimized pattern scanner for finding similar code structures"""

    def __init__(self, file_extensions: Optional[List[str]] = None):
        self.file_extensions = file_extensions or [".nix", ".py", ".js", ".ts"]

    def scan_for_similar_patterns(
        self,
        target_file: str,
        target_line: int,
        search_dir: str = ".",
        pattern_type: Optional[PatternType] = None,
        max_results: int = 254,
    ) -> List[PatternMatch]:
        """Find patterns similar to the one at target_file:target_line"""

        # Extract target pattern
        target_pattern = self._extract_pattern(target_file, target_line)
        if not target_pattern:
            return []

        # Override pattern type if specified
        if pattern_type:
            target_pattern["pattern_type"] = pattern_type

        # Find similar patterns
        matches = self._find_similar_patterns(target_pattern, search_dir)

        # Filter out the original location
        matches = [
            match
            for match in matches
            if not (Path(match.file).samefile(Path(target_file)) and match.line == target_line)
        ]

        # Limit results
        return matches[:max_results]

    def _extract_pattern(self, file_path: str, line_number: int) -> Optional[Dict[str, Any]]:
        """Extract pattern information from target location"""
        try:
            with open(file_path) as f:
                lines = f.readlines()

            if line_number > len(lines) or line_number < 1:
                return None

            target_line = lines[line_number - 1].strip()

            return {
                "line_content": target_line,
                "pattern_type": self._detect_pattern_type(target_line, lines, line_number - 1),
                "context_lines": self._get_context(lines, line_number - 1, 3),
            }
        except Exception:
            return None

    def _detect_pattern_type(self, line: str, all_lines: List[str], line_idx: int) -> PatternType:
        """Detect the type of pattern this line represents"""
        if "home.packages" in line and "mkIf" in line:
            return PatternType.MKIF_HOME_PACKAGES
        elif "mkIf" in line and "++" in line:
            return PatternType.MKIF_LIST_CONCAT
        elif "casks = [" in line or "brews = [" in line:
            return PatternType.HOMEBREW_LIST
        elif "writeShellScriptBin" in line:
            return PatternType.SHELL_SCRIPT_BIN
        elif "home.file." in line:
            return PatternType.HOME_FILE_CONFIG
        elif "def " in line or "function " in line:
            return PatternType.GENERIC
        elif "import " in line or "from " in line:
            return PatternType.GENERIC
        else:
            return PatternType.GENERIC

    def _get_context(self, lines: List[str], line_idx: int, context_size: int) -> List[str]:
        """Get surrounding lines for context matching"""
        start = max(0, line_idx - context_size)
        end = min(len(lines), line_idx + context_size + 1)
        return [line.strip() for line in lines[start:end]]

    def _find_similar_patterns(self, target_pattern: Dict[str, Any], search_dir: str) -> List[PatternMatch]:
        """Find similar patterns in the search directory"""
        matches = []
        search_path = Path(search_dir)

        # Find all files with matching extensions
        for ext in self.file_extensions:
            for file_path in search_path.rglob(f"*{ext}"):
                if file_path.is_file():
                    matches.extend(self._scan_file_for_patterns(file_path, target_pattern))

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def _scan_file_for_patterns(self, file_path: Path, target_pattern: Dict[str, Any]) -> List[PatternMatch]:
        """Scan a single file for patterns similar to target"""
        matches = []

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Skip empty lines and comments
                if not line_stripped or line_stripped.startswith("#") or line_stripped.startswith("//"):
                    continue

                # Calculate similarity
                similarity = self._calculate_similarity(target_pattern, line_stripped, lines, i)

                # Use different thresholds based on pattern type
                threshold = (
                    0.7
                    if target_pattern["pattern_type"] in [PatternType.MKIF_LIST_CONCAT, PatternType.HOMEBREW_LIST]
                    else 0.3
                )  # Lower threshold for generic patterns

                if similarity > threshold:
                    matches.append(
                        PatternMatch(
                            file=str(file_path),
                            line=i + 1,
                            confidence=round(similarity, 2),
                            pattern_type=PatternType(target_pattern["pattern_type"]),
                            content=line_stripped,
                        )
                    )

        except Exception:
            pass  # Skip files we can't read

        return matches

    def _calculate_similarity(
        self,
        target_pattern: Dict[str, Any],
        line: str,
        all_lines: List[str],
        line_idx: int,
    ) -> float:
        """Calculate similarity between target pattern and current line"""
        # Pattern type must match
        current_pattern_type = self._detect_pattern_type(line, all_lines, line_idx)
        if current_pattern_type != PatternType(target_pattern["pattern_type"]):
            return 0.0

        # Use specialized matching for known patterns
        pattern_type = PatternType(target_pattern["pattern_type"])

        if pattern_type == PatternType.MKIF_LIST_CONCAT:
            return self._match_mkif_list_concat(target_pattern, line)
        elif pattern_type == PatternType.HOMEBREW_LIST:
            return self._match_homebrew_list(target_pattern, line)
        else:
            return self._generic_similarity(target_pattern["line_content"], line)

    def _match_mkif_list_concat(self, target_pattern: Dict[str, Any], line: str) -> float:
        """Specialized matching for mkIf + list concatenation patterns"""
        target_line = target_pattern["line_content"]

        if "mkIf" in target_line and "mkIf" in line and "++" in target_line and "++" in line:
            return 0.9
        return 0.0

    def _match_homebrew_list(self, target_pattern: Dict[str, Any], line: str) -> float:
        """Specialized matching for Homebrew list patterns"""
        target_line = target_pattern["line_content"]

        if ("casks" in target_line or "brews" in target_line) and ("casks" in line or "brews" in line):
            return 0.85
        return 0.0

    def _generic_similarity(self, target_line: str, current_line: str) -> float:
        """Generic similarity calculation based on common keywords"""
        target_words = set(target_line.split())
        current_words = set(current_line.split())

        if not target_words or not current_words:
            return 0.0

        intersection = target_words.intersection(current_words)
        union = target_words.union(current_words)

        return len(intersection) / len(union) if union else 0.0


def scan_patterns_with_exit_code(
    target_file: str,
    target_line: int,
    search_dir: str = ".",
    pattern_type: Optional[str] = None,
    max_results: int = 254,
    format_output: str = "silent",
) -> int:
    """
    Scan for patterns and return count via exit code (AI-first design)

    Returns:
        Exit code: 0-254 = pattern count, 255 = error
    """
    try:
        # Validate inputs
        if not Path(target_file).exists():
            if format_output != "silent":
                print(f"Error: File not found: {target_file}", file=sys.stderr)
            return 255

        if target_line < 1:
            if format_output != "silent":
                print(f"Error: Invalid line number: {target_line}", file=sys.stderr)
            return 255

        # Convert pattern type string to enum
        pattern_enum = None
        if pattern_type:
            try:
                pattern_enum = PatternType(pattern_type)
            except ValueError:
                if format_output != "silent":
                    print(f"Error: Invalid pattern type: {pattern_type}", file=sys.stderr)
                return 255

        # Create scanner and run scan
        scanner = PatternScanner()
        matches = scanner.scan_for_similar_patterns(
            target_file=target_file,
            target_line=target_line,
            search_dir=search_dir,
            pattern_type=pattern_enum,
            max_results=max_results,
        )

        # Output results if requested
        if format_output != "silent":
            if format_output == "compact":
                result = {
                    "c": len(matches),
                    "items": [{"f": m.file, "l": m.line, "conf": m.confidence} for m in matches[:10]],
                }
                print(json.dumps(result, separators=(",", ":")))
            elif format_output == "json":
                result = {
                    "count": len(matches),
                    "matches": [
                        {
                            "file": m.file,
                            "line": m.line,
                            "confidence": m.confidence,
                            "pattern_type": m.pattern_type.value,
                            "content": m.content,
                        }
                        for m in matches
                    ],
                }
                print(json.dumps(result, indent=2))
            elif format_output == "human":
                print(f"Found {len(matches)} similar patterns")
                for match in matches[:5]:  # Show first 5
                    print(f"  {match.file}:{match.line} (confidence: {match.confidence})")
                if len(matches) > 5:
                    print(f"  ... and {len(matches) - 5} more")

        # Return count as exit code (capped at 254)
        return min(len(matches), 254)

    except Exception as e:
        if format_output != "silent":
            print(f"Error: {str(e)}", file=sys.stderr)
        return 255


def main():
    """CLI entry point for pattern scanner"""
    parser = argparse.ArgumentParser(
        description="Find similar code patterns (exit-code-first design)",
        epilog="Exit codes: 0-254 = pattern count, 255 = error",
    )
    parser.add_argument("target_file", help="File containing target pattern")
    parser.add_argument("target_line", type=int, help="Line number of target pattern")
    parser.add_argument("--search-dir", default=".", help="Directory to search (default: .)")
    parser.add_argument("--pattern-type", help="Override detected pattern type")
    parser.add_argument("--max-results", type=int, default=254, help="Maximum results (default: 254)")
    parser.add_argument(
        "--format",
        choices=["silent", "compact", "json", "human"],
        default="silent",
        help="Output format (default: silent for AI efficiency)",
    )

    args = parser.parse_args()

    exit_code = scan_patterns_with_exit_code(
        target_file=args.target_file,
        target_line=args.target_line,
        search_dir=args.search_dir,
        pattern_type=args.pattern_type,
        max_results=args.max_results,
        format_output=args.format,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
