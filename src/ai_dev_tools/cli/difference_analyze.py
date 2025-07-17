"""
CLI for difference analysis - AI-optimized interface

Provides command-line interface for file and directory difference analysis with AI-friendly output
"""

import sys
from pathlib import Path

import click

from ..core.difference_analyzer import DifferenceAnalyzer


@click.command()
@click.argument("path1")
@click.argument("path2")
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for maximum efficiency - exit code only)",
)
@click.option(
    "--ignore-whitespace/--no-ignore-whitespace",
    default=True,
    help="Ignore whitespace differences (default: True)",
)
@click.option(
    "--ignore-comments/--no-ignore-comments",
    default=False,
    help="Ignore comment-only changes (default: False)",
)
def main(path1: str, path2: str, format: str, ignore_whitespace: bool, ignore_comments: bool):
    """
    Analyze differences between files or directories

    PATH1 and PATH2 should be files or directories to compare

    Exit code: number of significant differences found (0-254)
    """
    try:
        # Initialize analyzer
        analyzer = DifferenceAnalyzer(ignore_whitespace=ignore_whitespace, ignore_comments=ignore_comments)

        # Convert to Path objects
        path1_obj = Path(path1)
        path2_obj = Path(path2)

        # Determine comparison type and perform analysis
        if path1_obj.is_file() and path2_obj.is_file():
            analysis = analyzer.compare_files(path1_obj, path2_obj)
        elif path1_obj.is_dir() and path2_obj.is_dir():
            analysis = analyzer.compare_directories(path1_obj, path2_obj)
        else:
            if format != "silent":
                click.echo(
                    "Error: Both paths must be files or both must be directories",
                    err=True,
                )
            sys.exit(255)

        # Output based on format
        if format == "json":
            import json

            click.echo(json.dumps(analysis.to_dict(), indent=2))
        elif format == "compact":
            click.echo(f"Differences: {analysis.significant_differences}")
            click.echo(f"Files: {analysis.files_compared}")
            if analysis.files_added:
                click.echo(f"Added: {analysis.files_added}")
            if analysis.files_removed:
                click.echo(f"Removed: {analysis.files_removed}")
            if analysis.files_modified:
                click.echo(f"Modified: {analysis.files_modified}")
        elif format == "human":
            click.echo(f"Difference Analysis: {path1} vs {path2}")
            click.echo(f"  Summary: {analysis.summary}")
            click.echo(f"  Total Differences: {analysis.total_differences}")
            click.echo(f"  Significant Differences: {analysis.significant_differences}")
            click.echo(f"  Files Compared: {analysis.files_compared}")

            if analysis.files_added:
                click.echo(f"  Files Added: {analysis.files_added}")
            if analysis.files_removed:
                click.echo(f"  Files Removed: {analysis.files_removed}")
            if analysis.files_modified:
                click.echo(f"  Files Modified: {analysis.files_modified}")

            if analysis.differences and len(analysis.differences) <= 10:
                click.echo("  Details:")
                for diff in analysis.differences:
                    significance_marker = {
                        "trivial": "~",
                        "minor": "-",
                        "major": "!",
                        "critical": "!!!",
                    }.get(diff.significance.value, "?")

                    click.echo(f"    {significance_marker} {diff.path}: {diff.difference_type.value}")
                    if diff.details:
                        click.echo(f"      {diff.details}")
            elif analysis.differences:
                click.echo(f"  ({len(analysis.differences)} differences - use --format=json for full details)")
        # format == "silent" produces no output

        # Exit with significant differences count (capped at 254)
        sys.exit(min(254, analysis.significant_differences))

    except FileNotFoundError as e:
        if format != "silent":
            click.echo(f"Error: {str(e)}", err=True)
        sys.exit(255)
    except NotADirectoryError as e:
        if format != "silent":
            click.echo(f"Error: {str(e)}", err=True)
        sys.exit(255)
    except Exception as e:
        if format != "silent":
            click.echo(f"Error: {str(e)}", err=True)
        sys.exit(255)


if __name__ == "__main__":
    main()
