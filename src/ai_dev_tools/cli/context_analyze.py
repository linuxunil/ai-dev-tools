"""
CLI for context analysis - AI-optimized interface

Provides command-line interface for project context analysis with AI-friendly output
"""

import click
import sys
from pathlib import Path

from ..core.context_analyzer import ContextAnalyzer


@click.command()
@click.argument("project_path", default=".")
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for maximum efficiency - exit code only)",
)
def main(project_path: str, format: str):
    """
    Analyze project context and structure

    PROJECT_PATH should be a directory containing the project to analyze

    Exit code: project complexity score (0-254)
    """
    try:
        # Initialize analyzer
        analyzer = ContextAnalyzer(Path(project_path))

        # Perform analysis
        context = analyzer.analyze()

        # Output based on format
        if format == "json":
            import json

            click.echo(json.dumps(context.to_dict(), indent=2))
        elif format == "compact":
            click.echo(f"Type: {context.project_type.value}")
            click.echo(f"Framework: {context.framework.value}")
            click.echo(f"Complexity: {context.complexity_score}")
            click.echo(f"Files: {context.total_files} ({context.code_files} code)")
            click.echo(f"Dependencies: {len(context.dependencies)}")
        elif format == "human":
            click.echo(f"Project Analysis for: {project_path}")
            click.echo(f"  Type: {context.project_type.value}")
            click.echo(f"  Framework: {context.framework.value}")
            click.echo(f"  Complexity Score: {context.complexity_score}/254")
            click.echo(f"  Total Files: {context.total_files}")
            click.echo(f"    Code Files: {context.code_files}")
            click.echo(f"    Config Files: {context.config_files}")
            click.echo(f"  Dependencies: {len(context.dependencies)}")
            if context.entry_points:
                click.echo(f"  Entry Points: {', '.join(context.entry_points)}")
            if context.build_tools:
                click.echo(f"  Build Tools: {', '.join(context.build_tools)}")
            if context.test_frameworks:
                click.echo(f"  Test Frameworks: {', '.join(context.test_frameworks)}")
            if context.key_directories:
                click.echo(f"  Key Directories: {', '.join(context.key_directories)}")
        # format == "silent" produces no output

        # Exit with complexity score
        sys.exit(context.complexity_score)

    except FileNotFoundError:
        if format != "silent":
            click.echo(f"Error: Project path does not exist: {project_path}", err=True)
        sys.exit(255)
    except NotADirectoryError:
        if format != "silent":
            click.echo(f"Error: Path is not a directory: {project_path}", err=True)
        sys.exit(255)
    except Exception as e:
        if format != "silent":
            click.echo(f"Error: {str(e)}", err=True)
        sys.exit(255)


if __name__ == "__main__":
    main()
