"""
CLI for repository status - AI-optimized interface

Provides command-line interface for repository analysis with AI-friendly output
"""

import json
import sys

import click

from ..core.repo_analyzer import RepoAnalyzer


@click.command()
@click.option("--repo-path", default=".", help="Path to repository")
@click.option(
    "--format",
    type=click.Choice(["json", "summary"]),
    default="json",
    help="Output format",
)
def main(repo_path: str, format: str):
    """
    Get repository health status

    Exit code: number of syntax errors (0=healthy, N=errors)
    """
    # Run repository analysis
    analyzer = RepoAnalyzer(repo_path)
    health = analyzer.get_repo_health()

    # Output results
    if format == "json":
        click.echo(json.dumps(health.to_dict(), indent=2))
    else:
        click.echo(f"Repository Health: {health.summary}")
        click.echo(f"Clean: {health.is_clean}")
        click.echo(f"Syntax Errors: {health.syntax_errors}")
        click.echo(f"Total Files: {health.total_files}")

    # Exit with syntax error count
    sys.exit(health.syntax_errors)


if __name__ == "__main__":
    main()
