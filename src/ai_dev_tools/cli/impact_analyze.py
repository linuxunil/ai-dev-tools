"""
CLI for impact analysis - AI-optimized interface

Provides command-line interface for change impact analysis with AI-friendly output
"""

import sys
from pathlib import Path

import click

from ..core.impact_analyzer import ImpactAnalyzer


@click.command()
@click.argument("target_file")
@click.option(
    "--project-path",
    default=".",
    help="Path to project root (default: current directory)",
)
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for maximum efficiency - exit code only)",
)
@click.option(
    "--max-files",
    default=50,
    type=int,
    help="Maximum number of impacted files to analyze (default: 50)",
)
def main(target_file: str, project_path: str, format: str, max_files: int):
    """
    Analyze the impact of changes to a specific file

    TARGET_FILE should be the file to analyze for impact

    Exit code: impact severity score (0-254)
    """
    try:
        # Initialize analyzer
        analyzer = ImpactAnalyzer(Path(project_path))

        # Convert target file to Path object
        target_path = Path(target_file)

        # Perform impact analysis
        analysis = analyzer.analyze_file_impact(target_path)

        # Limit output if requested
        if len(analysis.impacted_files) > max_files:
            analysis.impacted_files = analysis.impacted_files[:max_files]
            analysis.summary += f" (showing first {max_files} files)"

        # Output based on format
        if format == "json":
            import json

            click.echo(json.dumps(analysis.to_dict(), indent=2))
        elif format == "compact":
            click.echo(f"Impact: {analysis.severity_score}")
            click.echo(f"Files: {analysis.total_impacted_files}")
            click.echo(f"Max Severity: {analysis.max_severity.value}")
            if analysis.total_impacted_files > 0:
                click.echo(
                    f"Types: {', '.join(set(f.impact_type.value for f in analysis.impacted_files))} "
                    "(showing first {max_files} files)"
                )
        elif format == "human":
            click.echo(f"Impact Analysis for: {analysis.target_file}")
            click.echo(f"  Summary: {analysis.summary}")
            click.echo(f"  Impact Score: {analysis.severity_score}/254")
            click.echo(f"  Max Severity: {analysis.max_severity.value}")
            click.echo(f"  Total Impacted Files: {analysis.total_impacted_files}")

            if analysis.impacted_files:
                click.echo("  Impacted Files:")
                for impact_file in analysis.impacted_files[:10]:  # Show first 10
                    severity_marker = {
                        "none": "○",
                        "low": "●",
                        "medium": "◐",
                        "high": "◑",
                        "critical": "◉",
                    }.get(impact_file.severity.value, "?")

                    click.echo(f"    {severity_marker} {impact_file.path}")
                    click.echo(f"      {impact_file.impact_type.value}: {impact_file.reason}")

                if len(analysis.impacted_files) > 10:
                    remaining = len(analysis.impacted_files) - 10
                    click.echo(f"    ... and {remaining} more files")

            if analysis.recommendations:
                click.echo("  Recommendations:")
                for rec in analysis.recommendations:
                    click.echo(f"    • {rec}")
        # format == "silent" produces no output

        # Exit with severity score (capped at 254)
        sys.exit(min(254, analysis.severity_score))

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
