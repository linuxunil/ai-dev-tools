"""
AI Validate CLI - Project validation command-line interface

Provides command-line access to project validation functionality
"""

import click
import sys
import json
from pathlib import Path

from ..core.validator import ProjectValidator


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for AI efficiency)",
)
@click.option(
    "--no-syntax",
    is_flag=True,
    help="Skip syntax validation",
)
@click.option(
    "--no-structure",
    is_flag=True,
    help="Skip structure validation",
)
@click.option(
    "--no-dependencies",
    is_flag=True,
    help="Skip dependency validation",
)
@click.option(
    "--no-security",
    is_flag=True,
    help="Skip security validation",
)
def validate(
    path: str,
    format: str,
    no_syntax: bool,
    no_structure: bool,
    no_dependencies: bool,
    no_security: bool,
):
    """
    Validate project structure, syntax, dependencies, and security

    Exit codes:
    0 = Valid project (no errors/critical issues)
    1 = Warnings found
    2 = Errors found
    3 = Critical issues found
    255 = Tool error

    Examples:
        ai-validate                    # Validate current directory
        ai-validate /path/to/project   # Validate specific project
        ai-validate --format json      # Get detailed JSON output
        ai-validate --no-security      # Skip security checks
    """
    try:
        validator = ProjectValidator(path)

        result = validator.validate_project(
            check_syntax=not no_syntax,
            check_structure=not no_structure,
            check_dependencies=not no_dependencies,
            check_security=not no_security,
        )

        # Output based on format
        output = ""
        if format == "json":
            output = json.dumps(result.to_dict(), indent=2)
        elif format == "compact":
            output = json.dumps(result.to_dict())
        elif format == "human":
            output = _format_human_output(result)
        # Silent mode: no output

        if output:
            click.echo(output)

        # Exit with appropriate code
        sys.exit(result.get_exit_code())

    except Exception as e:
        if format in ["json", "compact"]:
            error_result = {
                "error": str(e),
                "is_valid": False,
                "total_issues": 1,
            }
            output = json.dumps(error_result, indent=2 if format == "json" else None)
            click.echo(output)
        elif format == "human":
            click.echo(f"Error: {e}", err=True)

        sys.exit(255)


def _format_human_output(result) -> str:
    """Format validation result for human reading"""
    lines = []

    # Summary
    lines.append(f"Project Validation: {'PASSED' if result.is_valid else 'FAILED'}")
    lines.append(f"Files checked: {result.total_files_checked}")
    lines.append(f"Issues found: {len(result.issues)}")
    lines.append("")

    if result.issues:
        # Group issues by category
        by_category = {}
        for issue in result.issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        for category, issues in by_category.items():
            lines.append(f"{category.upper()} ISSUES:")
            for issue in issues:
                level_symbol = {
                    "PASS": "✓",
                    "WARNING": "⚠",
                    "ERROR": "✗",
                    "CRITICAL": "🚨",
                }[issue.level.name]

                location = ""
                if issue.file_path:
                    location = f" ({issue.file_path}"
                    if issue.line_number:
                        location += f":{issue.line_number}"
                    location += ")"

                lines.append(f"  {level_symbol} {issue.message}{location}")

                if issue.suggestion:
                    lines.append(f"    → {issue.suggestion}")
            lines.append("")

    lines.append(result.summary)

    return "\n".join(lines)


if __name__ == "__main__":
    validate()
