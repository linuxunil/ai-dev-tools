"""
AI Helper CLI - Unified AI assistant with tool orchestration

Provides high-level workflows that orchestrate all AI development tools
for comprehensive project analysis, change planning, and systematic fixes.
"""

import json
import sys
from typing import List, Optional

import click

from ..core.ai_helper import AIHelper, HelperWorkflowResult


def format_output(result: HelperWorkflowResult, format_type: str) -> str:
    """Format workflow result for output"""
    if format_type == "json":
        return json.dumps(result.to_dict(), indent=2)
    elif format_type == "compact":
        return json.dumps(result.to_dict())
    else:  # human-readable
        output = []
        output.append(f"Workflow: {result.workflow_type}")
        output.append(f"Status: {'✅ Success' if result.success else '❌ Failed'}")
        output.append(f"Summary: {result.summary}")

        if result.recommendations:
            output.append("\nRecommendations:")
            for i, rec in enumerate(result.recommendations, 1):
                output.append(f"  {i}. {rec}")

        if result.context:
            output.append(f"\nContext: {result.context}")

        return "\n".join(output)


@click.group()
@click.option(
    "--repo-path",
    default=".",
    help="Path to repository root (default: current directory)",
)
@click.pass_context
def ai_helper(ctx, repo_path: str):
    """
    AI Helper - Unified AI assistant with tool orchestration

    Provides high-level workflows for project analysis, change planning,
    and systematic code improvements using all AI development tools.

    Exit codes encode workflow results for AI consumption:
    - 0-254: Workflow-specific metrics (patterns found, health score, etc.)
    - 255: Error occurred
    """
    ctx.ensure_object(dict)
    ctx.obj["repo_path"] = repo_path
    ctx.obj["helper"] = AIHelper(repo_path)


@ai_helper.command()
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default=None,
    help="Output format (default: silent for AI consumption)",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip validation checks for faster analysis",
)
@click.option(
    "--skip-context",
    is_flag=True,
    help="Skip context analysis for faster analysis",
)
@click.pass_context
def analyze(ctx, format: Optional[str], skip_validation: bool, skip_context: bool):
    """
    Comprehensive project analysis workflow

    Combines repository health, context analysis, and validation
    to provide complete project understanding for AI decision making.

    Exit code: Overall health score (0-100)
    """
    helper: AIHelper = ctx.obj["helper"]

    result = helper.analyze_project(include_validation=not skip_validation, include_context=not skip_context)

    if format:
        click.echo(format_output(result, format))

    sys.exit(result.exit_code)


@ai_helper.command()
@click.argument("files", nargs=-1, required=True)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default=None,
    help="Output format (default: silent for AI consumption)",
)
@click.option(
    "--description",
    default="",
    help="Description of planned changes",
)
@click.option(
    "--skip-impact",
    is_flag=True,
    help="Skip impact analysis for faster planning",
)
@click.pass_context
def plan(ctx, files: List[str], format: Optional[str], description: str, skip_impact: bool):
    """
    Change planning workflow with impact analysis and safety assessment

    Analyzes safety and impact of modifying the specified files
    to help plan changes and identify potential risks.

    Exit code: Maximum risk level (0=safe, 1=medium, 2=high, 3=critical)
    """
    helper: AIHelper = ctx.obj["helper"]

    result = helper.plan_changes(
        target_files=list(files),
        change_description=description,
        assess_impact=not skip_impact,
    )

    if format:
        click.echo(format_output(result, format))

    sys.exit(result.exit_code)


@ai_helper.command()
@click.argument("fixed_file", required=True)
@click.argument("fixed_line", type=int, required=True)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default=None,
    help="Output format (default: silent for AI consumption)",
)
@click.option(
    "--scope",
    default=".",
    help="Directory scope for pattern search (default: current directory)",
)
@click.option(
    "--max-patterns",
    type=int,
    default=50,
    help="Maximum patterns to find (default: 50)",
)
@click.pass_context
def fix(
    ctx,
    fixed_file: str,
    fixed_line: int,
    format: Optional[str],
    scope: str,
    max_patterns: int,
):
    """
    Systematic fix workflow: find similar patterns and assess safety

    After fixing an issue at a specific location, finds all similar patterns
    in the codebase and assesses the safety of applying the same fix.

    This is the core AI workflow for systematic code improvements.

    Exit code: Number of similar patterns found (0-254)
    """
    helper: AIHelper = ctx.obj["helper"]

    result = helper.systematic_fix_workflow(
        fixed_file=fixed_file,
        fixed_line=fixed_line,
        search_scope=scope,
        max_patterns=max_patterns,
    )

    if format:
        click.echo(format_output(result, format))

    sys.exit(result.exit_code)


@ai_helper.command()
@click.argument("file1", required=True)
@click.argument("file2", required=True)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default=None,
    help="Output format (default: silent for AI consumption)",
)
@click.option(
    "--context-lines",
    type=int,
    default=3,
    help="Lines of context around differences (default: 3)",
)
@click.pass_context
def compare(ctx, file1: str, file2: str, format: Optional[str], context_lines: int):
    """
    Configuration comparison workflow with semantic analysis

    Compares two files and provides semantic analysis of differences,
    helping understand the impact of configuration changes.

    Exit code: Number of differences found (0-254)
    """
    helper: AIHelper = ctx.obj["helper"]

    result = helper.compare_configurations(file1=file1, file2=file2, context_lines=context_lines)

    if format:
        click.echo(format_output(result, format))

    sys.exit(result.exit_code)


@ai_helper.command()
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default="human",
    help="Output format (default: human-readable)",
)
@click.pass_context
def workflows(ctx, format: str):
    """
    List available AI Helper workflows and their descriptions

    Shows all available workflows with their purposes and exit codes
    for AI agents to understand available capabilities.
    """
    workflows_info = {
        "analyze": {
            "description": "Comprehensive project analysis with health, context, and validation",
            "exit_code": "Overall health score (0-100)",
            "usage": "ai-helper analyze [--skip-validation] [--skip-context]",
        },
        "plan": {
            "description": "Change planning with impact analysis and safety assessment",
            "exit_code": "Maximum risk level (0=safe, 1=medium, 2=high, 3=critical)",
            "usage": "ai-helper plan <files...> [--description TEXT] [--skip-impact]",
        },
        "fix": {
            "description": "Systematic fix workflow: find similar patterns and assess safety",
            "exit_code": "Number of similar patterns found (0-254)",
            "usage": "ai-helper fix <file> <line> [--scope DIR] [--max-patterns N]",
        },
        "compare": {
            "description": "Configuration comparison with semantic analysis",
            "exit_code": "Number of differences found (0-254)",
            "usage": "ai-helper compare <file1> <file2> [--context-lines N]",
        },
    }

    if format == "json":
        click.echo(json.dumps(workflows_info, indent=2))
    elif format == "compact":
        click.echo(json.dumps(workflows_info))
    else:  # human
        click.echo("AI Helper Workflows:")
        click.echo("===================")
        for name, info in workflows_info.items():
            click.echo(f"\n{name}:")
            click.echo(f"  Description: {info['description']}")
            click.echo(f"  Exit Code: {info['exit_code']}")
            click.echo(f"  Usage: {info['usage']}")

    sys.exit(0)


if __name__ == "__main__":
    ai_helper()
