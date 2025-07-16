"""
AI Workflow CLI - High-level interface for AI agent workflows

Provides command-line access to AI agent functionality
"""

import click
import sys
import json
from pathlib import Path

from ..agents.ai_agent import AIAgent


@click.group()
def cli():
    """AI Development Tools - Workflow Commands"""
    pass


@cli.command()
@click.argument("fixed_file", required=True)
@click.argument("fixed_line", type=int, required=True)
@click.option("--search-dir", default=".", help="Directory to search for patterns")
@click.option("--max-patterns", default=50, help="Maximum patterns to find")
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format (default: silent for AI efficiency)",
)
def fix_and_propagate(
    fixed_file: str, fixed_line: int, search_dir: str, max_patterns: int, format: str
):
    """
    Core AI workflow: find similar patterns after fixing one location

    Example: ai-workflow fix-and-propagate shell.nix 249 --search-dir modules/
    """
    try:
        agent = AIAgent()
        result = agent.fix_and_propagate_workflow(
            fixed_file=fixed_file,
            fixed_line=fixed_line,
            search_scope=search_dir,
            max_patterns=max_patterns,
        )

        # Output based on format
        output = ""
        if format == "silent":
            # Silent mode - exit code only
            pass
        elif format == "compact":
            output = f"{result.similar_patterns['count']}"
        elif format == "json":
            output = json.dumps(result.to_dict(), indent=2)
        elif format == "human":
            output = f"Workflow: {result.workflow_type}\n"
            output += f"Success: {result.success}\n"
            output += f"Summary: {result.summary}\n"
            output += f"Patterns found: {result.similar_patterns['count']}\n"
            output += f"Safe files: {result.safety_assessment['safe_files']}\n"
            output += (
                f"High-risk files: {result.safety_assessment['high_risk_files']}\n"
            )
            if result.recommendations:
                output += "Recommendations:\n"
                for i, rec in enumerate(result.recommendations, 1):
                    output += f"  {i}. {rec}\n"

        # Print output if not silent
        if format != "silent" and output:
            click.echo(output)

        # Exit with meaningful code for AI consumption
        sys.exit(result.exit_code)

    except Exception as e:
        if format == "json":
            error_result = {
                "workflow": "fix_and_propagate",
                "success": False,
                "error": str(e),
                "exit_code": 255,
            }
            click.echo(json.dumps(error_result))
        elif format != "silent":
            click.echo(f"Error: {e}", err=True)
        sys.exit(255)


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format",
)
def repo_context(format: str):
    """
    Get repository context for AI decision making

    Example: ai-workflow repo-context --format json
    """
    try:
        agent = AIAgent()
        context = agent.get_repository_context()

        # Output based on format
        output = ""
        if format == "silent":
            # Silent mode - exit code only
            pass
        elif format == "compact":
            output = f"{context['health_score']:.1f}"
        elif format == "json":
            output = json.dumps(context, indent=2)
        elif format == "human":
            output = f"Repository Health: {context['health_score']:.1f}\n"
            output += f"Ready for changes: {context['ready_for_changes']}\n"
            output += f"Summary: {context['summary']}\n"
            if context["blocking_issues"]:
                output += "Blocking issues:\n"
                for issue in context["blocking_issues"]:
                    output += f"  - {issue}\n"

        # Print output if not silent
        if format != "silent" and output:
            click.echo(output)

        # Exit with syntax error count for AI consumption
        sys.exit(context["exit_code"])

    except Exception as e:
        if format == "json":
            error_result = {
                "ready_for_changes": False,
                "error": str(e),
                "exit_code": 255,
            }
            click.echo(json.dumps(error_result))
        elif format != "silent":
            click.echo(f"Error: {e}", err=True)
        sys.exit(255)


@cli.command()
@click.argument("files", nargs=-1, required=True)
@click.option(
    "--format",
    type=click.Choice(["silent", "compact", "json", "human"]),
    default="silent",
    help="Output format",
)
def assess_safety(files, format: str):
    """
    Assess safety of modifying multiple files

    Example: ai-workflow assess-safety file1.nix file2.py --format json
    """
    try:
        agent = AIAgent()
        safety = agent.assess_change_safety(list(files))

        # Output based on format
        output = ""
        if format == "silent":
            # Silent mode - exit code only
            pass
        elif format == "compact":
            output = safety["risk_level"]
        elif format == "json":
            output = json.dumps(safety, indent=2)
        elif format == "human":
            output = f"Safety Assessment for {safety['total_files']} files\n"
            output += f"Safe to proceed: {safety['safe_to_proceed']}\n"
            output += f"Risk level: {safety['risk_level']}\n"
            if safety["critical_files"]:
                output += f"Critical files: {', '.join(safety['critical_files'])}\n"
            if safety["warnings"]:
                output += "Warnings:\n"
                for warning in safety["warnings"]:
                    output += f"  - {warning}\n"

        # Print output if not silent
        if format != "silent" and output:
            click.echo(output)

        # Exit with risk level for AI consumption
        sys.exit(safety["exit_code"])

    except Exception as e:
        if format == "json":
            error_result = {"safe_to_proceed": False, "error": str(e), "exit_code": 255}
            click.echo(json.dumps(error_result))
        elif format != "silent":
            click.echo(f"Error: {e}", err=True)
        sys.exit(255)


if __name__ == "__main__":
    cli()
