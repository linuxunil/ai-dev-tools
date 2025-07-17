"""
Pattern Scanner - Exit-code-first pattern detection for AI workflows

Finds similar code patterns and returns count via exit codes (0-254).
Designed for zero-token AI decision making with optional verbose output.

Exit Codes:
- 0-254: Number of patterns found
- 255: Error (file not found, invalid input, etc.)
"""

import json
import sys
from dataclasses import asdict, dataclass
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
    context: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["pattern_type"] = self.pattern_type.value
        return result


@dataclass
class PatternScanResult:
    """Results from a pattern scan operation"""

    target_file: str
    target_line: int
    pattern_type: PatternType
    matches: List[PatternMatch]
    count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "target": {
                "file": self.target_file,
                "line": self.target_line,
                "pattern_type": self.pattern_type.value,
            },
            "patterns": [match.to_dict() for match in self.matches],
            "count": self.count,
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def to_ai_format(self) -> Dict[str, Any]:
        """Convert to AI-optimized compact format"""
        try:
            from .output_strategy import create_ai_optimized_result

            items = []
            for match in self.matches:
                items.append(
                    {
                        "file": match.file,
                        "line": match.line,
                        "confidence": match.confidence,
                        "pattern_type": match.pattern_type.value,
                    }
                )

            metadata = {
                "target_file": self.target_file,
                "target_line": self.target_line,
                "pattern_type": self.pattern_type.value,
            }

            return create_ai_optimized_result(count=self.count, items=items, metadata=metadata)
        except ImportError:
            # Fallback if output_strategy not available
            return {
                "count": self.count,
                "matches": [match.to_dict() for match in self.matches],
                "target": {
                    "file": self.target_file,
                    "line": self.target_line,
                    "pattern_type": self.pattern_type.value,
                },
            }


class PatternScanner:
    """
    AI-optimized pattern scanner for finding similar code structures

    Designed for AI agents to:
    1. Fix one error
    2. Find similar patterns
    3. Apply the same fix everywhere
    """

    def __init__(self, file_extensions: Optional[List[str]] = None):
        """
        Initialize pattern scanner

        Args:
            file_extensions: File extensions to scan (default: ['.nix'])
        """
        self.file_extensions = file_extensions or [".nix"]
        self._pattern_cache: Dict[str, Any] = {}

    def scan_for_similar_patterns(
        self,
        target_file: str,
        target_line: int,
        search_dir: str = ".",
        pattern_type: Optional[PatternType] = None,
        max_results: int = 255,
    ) -> PatternScanResult:
        """
        Find patterns similar to the one at target_file:target_line

        Args:
            target_file: File containing the target pattern
            target_line: Line number of the target pattern
            search_dir: Directory to search for similar patterns
            pattern_type: Override detected pattern type
            max_results: Maximum number of results (for exit code compatibility)

        Returns:
            PatternScanResult with found matches
        """
        # Extract target pattern
        target_pattern = self._extract_pattern(target_file, target_line)
        if not target_pattern:
            return PatternScanResult(
                target_file=target_file,
                target_line=target_line,
                pattern_type=PatternType.GENERIC,
                matches=[],
                count=0,
            )

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
        matches = matches[:max_results]

        return PatternScanResult(
            target_file=target_file,
            target_line=target_line,
            pattern_type=PatternType(target_pattern["pattern_type"]),
            matches=matches,
            count=len(matches),
        )

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
                matches.extend(self._scan_file_for_patterns(file_path, target_pattern))

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def _scan_file_for_patterns(self, file_path: Path, target_pattern: Dict[str, Any]) -> List[PatternMatch]:
        """Scan a single file for patterns similar to target"""
        matches = []

        try:
            with open(file_path) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Skip empty lines and comments
                if not line_stripped or line_stripped.startswith("#"):
                    continue

                # Calculate similarity
                similarity = self._calculate_similarity(target_pattern, line_stripped, lines, i)

                if similarity > 0.7:  # Threshold for "similar"
                    matches.append(
                        PatternMatch(
                            file=str(file_path),
                            line=i + 1,
                            confidence=round(similarity, 2),
                            pattern_type=PatternType(target_pattern["pattern_type"]),
                            content=line_stripped,
                            context=self._get_context(lines, i, 2),
                        )
                    )

        except Exception:
            pass  # Skip files we can't read

        return matches

    def _calculate_similarity(
        self,
        target_pattern: Dict[str, Any],
        line: str,
        context_lines: List[str],
        line_num: int,
    ) -> float:
        """
        Calculate similarity between target pattern and a candidate line

        Args:
            target_pattern: The target pattern to match against
            line: Candidate line content
            context_lines: All lines in the file for context
            line_num: Line number of the candidate

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not line.strip():
            return 0.0

        target_content = target_pattern["content"]

        # Exact match gets highest score
        if line == target_content:
            return 1.0

        # Pattern type specific matching
        pattern_type = target_pattern["pattern_type"]

        if pattern_type == PatternType.MKIF_HOME_PACKAGES:
            if "mkIf" in line and "home.packages" in line:
                return 0.9
        elif pattern_type == PatternType.MKIF_LIST_CONCAT:
            if "mkIf" in line and "++" in line:
                return 0.9
        elif pattern_type == PatternType.HOMEBREW_LIST:
            if "homebrew" in line.lower():
                return 0.8
        elif pattern_type == PatternType.HOME_FILE_CONFIG:
            if "home.file" in line:
                return 0.8
        elif pattern_type == PatternType.SHELL_SCRIPT_BIN:
            if "writeShellScriptBin" in line:
                return 0.9

        # Structural similarity for generic patterns
        target_tokens = self._tokenize_line(target_content)
        candidate_tokens = self._tokenize_line(line)

        if not target_tokens or not candidate_tokens:
            return 0.0

        # Calculate token overlap
        common_tokens = set(target_tokens) & set(candidate_tokens)
        total_tokens = set(target_tokens) | set(candidate_tokens)

        if not total_tokens:
            return 0.0

        token_similarity = len(common_tokens) / len(total_tokens)

        # Boost score if structure is similar
        if self._has_similar_structure(target_content, line):
            token_similarity *= 1.2

        return min(token_similarity, 1.0)

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

    def _tokenize_line(self, line: str) -> List[str]:
        """Tokenize a line into meaningful tokens"""
        import re

        # Split on whitespace and common delimiters, filter empty strings
        tokens = re.split(r"[\s\[\]{}(),;=]+", line.strip())
        return [token for token in tokens if token]

    def _has_similar_structure(self, line1: str, line2: str) -> bool:
        """Check if two lines have similar structural patterns"""

        # Remove content but keep structure indicators
        def get_structure(line):
            import re

            # Replace strings and numbers with placeholders
            line = re.sub(r'"[^"]*"', '"STR"', line)
            line = re.sub(r"'[^']*'", "'STR'", line)
            line = re.sub(r"\b\d+\b", "NUM", line)
            line = re.sub(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", "ID", line)
            return line

        struct1 = get_structure(line1)
        struct2 = get_structure(line2)

        # Check if structures are similar (allowing some variation)
        return struct1 == struct2 or len(set(struct1) & set(struct2)) / max(len(struct1), len(struct2), 1) > 0.7


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

    Args:
        target_file: File containing the target pattern
        target_line: Line number of the target pattern
        search_dir: Directory to search for similar patterns
        pattern_type: Override detected pattern type
        max_results: Maximum number of results (0-254)
        format_output: Output format (silent, compact, json, human)

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
        result = scanner.scan_for_similar_patterns(
            target_file=target_file,
            target_line=target_line,
            search_dir=search_dir,
            pattern_type=pattern_enum,
            max_results=max_results,
        )

        # Output results if requested
        if format_output != "silent":
            if format_output == "compact":
                print(json.dumps(result.to_ai_format(), separators=(",", ":")))
            elif format_output == "json":
                print(result.to_json())
            elif format_output == "human":
                print(f"Found {result.count} similar patterns")
                for match in result.matches[:5]:  # Show first 5
                    print(f"  {match.file}:{match.line} (confidence: {match.confidence})")
                if result.count > 5:
                    print(f"  ... and {result.count - 5} more")

        # Return count as exit code (capped at 254)
        return min(result.count, 254)

    except Exception as e:
        if format_output != "silent":
            print(f"Error: {str(e)}", file=sys.stderr)
        return 255


def main():
    """CLI entry point for pattern scanner"""
    import argparse

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
