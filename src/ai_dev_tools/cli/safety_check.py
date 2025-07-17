"""
CLI for safety checking - AI-optimized interface

Provides command-line interface for safety analysis with AI-friendly output
"""

import json
import sys

import click

from ..core.safety_checker import SafetyChecker


@click.command()
@click.argument("file_path")
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for maximum efficiency - exit code only)",
)
def main(file_path: str, format: str):
    """
    Check if a file is safe to modify
    
    Args:
        file_path: File to check for safety

    Exit code: risk level (0=SAFE, 1=MEDIUM, 2=HIGH, 3=CRITICAL)
    """
    # Validate input - let safety checker handle file existence
    # This allows us to return proper risk assessment for non-existent files

    # Run safety check
    checker = SafetyChecker()
    result = checker.check_file_safety(file_path)

    # Output results using exit-code-first strategy
    if format == "silent":
        # No output - exit code only (maximum efficiency)
        pass
    elif format == "compact":
        # AI-optimized compact JSON
        click.echo(json.dumps(result.to_ai_format(), separators=(",", ":")))
    elif format == "json":
        # Pretty JSON for debugging
        click.echo(json.dumps(result.to_dict(), indent=2))
    elif format == "human":
        # Human-readable output
        click.echo(f"Risk Level: {result.risk_level.name}")
        click.echo(f"Safe to Modify: {result.safe_to_modify}")
        if result.reasons:
            click.echo("Reasons:")
            for reason in result.reasons:
                click.echo(f"  - {reason}")
        if result.recommendations:
            click.echo("Recommendations:")
            for rec in result.recommendations:
                click.echo(f"  - {rec}")

    # Exit with risk level (most efficient communication)
    sys.exit(result.risk_level.value)


if __name__ == "__main__":
    main()
