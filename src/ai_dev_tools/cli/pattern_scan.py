"""
CLI for pattern scanning - AI-optimized interface

Provides command-line interface for pattern detection with AI-friendly output
"""

import sys
from pathlib import Path

import click

from ..core.pattern_scanner import PatternScanner, PatternType


@click.command()
@click.argument("target", required=True, help="Target location as file:line")
@click.option("--search-dir", default=".", help="Directory to search for patterns")
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for maximum efficiency - exit code only)",
)
@click.option(
    "--pattern-type",
    type=click.Choice([pt.value for pt in PatternType]),
    help="Override pattern type",
)
@click.option("--max-results", default=255, help="Maximum number of results")
def main(
    target: str, search_dir: str, format: str, pattern_type: str, max_results: int
):
    """
    Find similar code patterns using structural analysis

    TARGET should be in format file:line (e.g., shell.nix:249)

    Exit code: number of similar patterns found (0-255)
    """
    # Parse target
    if ":" not in target:
        click.echo("Error: Target must be in format file:line", err=True)
        sys.exit(255)

    file_path, line_str = target.rsplit(":", 1)
    try:
        line_number = int(line_str)
    except ValueError:
        click.echo("Error: Line number must be an integer", err=True)
        sys.exit(255)

    # Validate inputs
    if not Path(file_path).exists():
        click.echo(f"Error: File '{file_path}' not found", err=True)
        sys.exit(255)

    if not Path(search_dir).is_dir():
        click.echo(f"Error: Search directory '{search_dir}' not found", err=True)
        sys.exit(255)

    # Convert pattern type
    pattern_type_enum = None
    if pattern_type:
        pattern_type_enum = PatternType(pattern_type)

    # Run pattern scan
    scanner = PatternScanner()
    result = scanner.scan_for_similar_patterns(
        target_file=file_path,
        target_line=line_number,
        search_dir=search_dir,
        pattern_type=pattern_type_enum,
        max_results=max_results,
    )

    # Output results using strategy pattern - prefer exit codes
    from ..core.exit_codes import ExitCodeEncoder
    from ..core.output_strategy import OutputFormat, OutputFormatter

    format_map = {
        "silent": OutputFormat.SILENT,
        "compact": OutputFormat.COMPACT,
        "json": OutputFormat.JSON,
        "human": OutputFormat.HUMAN,
    }

    output_format = format_map[format]

    # Only produce output if explicitly requested (not silent)
    output = None
    if output_format != OutputFormat.SILENT:
        if output_format == OutputFormat.COMPACT:
            # AI-optimized output
            output = OutputFormatter.format_output(result.to_ai_format(), output_format)
        elif output_format == OutputFormat.JSON:
            # Pretty JSON for debugging
            output = OutputFormatter.format_output(result.to_dict(), output_format)
        elif output_format == OutputFormat.HUMAN:
            # Human-readable summary
            data = {
                "count": result.count,
                "patterns": result.matches[:5],
            }  # Top 5 for humans
            output = OutputFormatter.format_output(data, output_format)

        if output:
            click.echo(output)

    # Exit with pattern count (most efficient communication)
    exit_code = ExitCodeEncoder.encode_count(result.count)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
