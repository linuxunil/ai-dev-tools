"""
AI Ollama CLI - Local AI model integration for development tools

Provides command-line interface for using Ollama models with
standardized prompts and metrics collection.
"""

import sys
from typing import Optional

import click

from ai_dev_tools.core.metrics_collector import WorkflowType, measure_workflow
from ai_dev_tools.core.ollama_client import (
    ModelSize,
    PromptType,
    get_ollama_client,
)


@click.group()
@click.pass_context
def cli(ctx):
    """AI Ollama - Local AI model integration for development tools"""
    ctx.ensure_object(dict)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--model",
    type=click.Choice([m.name.lower() for m in ModelSize]),
    default="small",
    help="Model size to use",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def analyze_patterns(file_path: str, model: str, format: str):
    """Analyze code patterns using Ollama"""
    client = get_ollama_client()

    if not client.is_available():
        click.echo(
            "❌ Ollama not available. Install with: curl -fsSL https://ollama.ai/install.sh | sh",
            err=True,
        )
        sys.exit(1)

    model_size = ModelSize[model.upper()]

    try:
        with open(file_path) as f:
            code_content = f.read()
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}", err=True)
        sys.exit(1)

    with measure_workflow(WorkflowType.PATTERN_ANALYSIS) as ctx:
        response = client.query(
            prompt_type=PromptType.PATTERN_DETECTION,
            user_prompt=f"Analyze this code for patterns and suggest improvements:\n\n{code_content}",
            model=model_size,
            workflow_type=WorkflowType.PATTERN_ANALYSIS,
        )

        ctx.record_files_processed(1)
        ctx.add_metadata("file_path", file_path)

    if response.success:
        if format == "json":
            import json

            result = {
                "success": True,
                "analysis": response.content,
                "model": response.model,
                "execution_time": response.execution_time,
                "estimated_tokens": response.estimated_tokens,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(response.content)
        sys.exit(0)
    else:
        if format == "json":
            import json

            result = {
                "success": False,
                "error": response.error,
                "model": response.model,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"❌ Error: {response.error}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--model",
    type=click.Choice([m.name.lower() for m in ModelSize]),
    default="small",
    help="Model size to use",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def check_safety(file_path: str, model: str, format: str):
    """Check code safety using Ollama"""
    client = get_ollama_client()

    if not client.is_available():
        click.echo(
            "❌ Ollama not available. Install with: curl -fsSL https://ollama.ai/install.sh | sh",
            err=True,
        )
        sys.exit(1)

    model_size = ModelSize[model.upper()]

    try:
        with open(file_path) as f:
            code_content = f.read()
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}", err=True)
        sys.exit(1)

    with measure_workflow(WorkflowType.SAFETY_CHECK) as ctx:
        response = client.query(
            prompt_type=PromptType.SAFETY_ASSESSMENT,
            user_prompt=f"Assess the safety and security of this code:\n\n{code_content}",
            model=model_size,
            workflow_type=WorkflowType.SAFETY_CHECK,
        )

        ctx.record_files_processed(1)
        ctx.add_metadata("file_path", file_path)

    # Determine exit code based on safety assessment
    exit_code = 0  # Default: safe
    if response.success:
        content_lower = response.content.lower()
        if "critical" in content_lower:
            exit_code = 3
        elif "high" in content_lower:
            exit_code = 2
        elif "medium" in content_lower:
            exit_code = 1
    else:
        exit_code = 255  # Error

    if response.success:
        if format == "json":
            import json

            result = {
                "success": True,
                "assessment": response.content,
                "risk_level": exit_code,
                "model": response.model,
                "execution_time": response.execution_time,
                "estimated_tokens": response.estimated_tokens,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(response.content)
        sys.exit(exit_code)
    else:
        if format == "json":
            import json

            result = {
                "success": False,
                "error": response.error,
                "model": response.model,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"❌ Error: {response.error}", err=True)
        sys.exit(255)


@cli.command()
@click.argument("prompt")
@click.option(
    "--type",
    "prompt_type",
    type=click.Choice([t.value for t in PromptType]),
    default="code_analysis",
    help="Type of AI task",
)
@click.option(
    "--model",
    type=click.Choice([m.name.lower() for m in ModelSize]),
    default="small",
    help="Model size to use",
)
@click.option("--exit-code", type=int, help="Exit code from previous tool")
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def query(prompt: str, prompt_type: str, model: str, exit_code: Optional[int], format: str):
    """Query Ollama with custom prompt"""
    client = get_ollama_client()

    if not client.is_available():
        click.echo(
            "❌ Ollama not available. Install with: curl -fsSL https://ollama.ai/install.sh | sh",
            err=True,
        )
        sys.exit(1)

    model_size = ModelSize[model.upper()]
    prompt_enum = PromptType(prompt_type)

    context = {}
    if exit_code is not None:
        context["exit_code"] = exit_code

    response = client.query(
        prompt_type=prompt_enum,
        user_prompt=prompt,
        model=model_size,
        context=context if context else None,
    )

    if response.success:
        if format == "json":
            import json

            result = {
                "success": True,
                "response": response.content,
                "model": response.model,
                "execution_time": response.execution_time,
                "estimated_tokens": response.estimated_tokens,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(response.content)
        sys.exit(0)
    else:
        if format == "json":
            import json

            result = {
                "success": False,
                "error": response.error,
                "model": response.model,
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"❌ Error: {response.error}", err=True)
        sys.exit(1)


@cli.command()
def models():
    """List available Ollama models"""
    client = get_ollama_client()

    if not client.is_available():
        click.echo(
            "❌ Ollama not available. Install with: curl -fsSL https://ollama.ai/install.sh | sh",
            err=True,
        )
        sys.exit(1)

    available_models = client.list_models()

    click.echo("Available Ollama models:")
    for model in available_models:
        click.echo(f"  • {model}")

    click.echo("\nRecommended models for AI development tools:")
    for model_size in ModelSize:
        status = "✅" if model_size.value in available_models else "❌"
        click.echo(f"  {status} {model_size.name}: {model_size.value}")


@cli.command()
def metrics():
    """Show metrics summary"""
    from ai_dev_tools.core.metrics_collector import get_metrics_collector

    collector = get_metrics_collector()
    summary = collector.get_metrics_summary()

    if "error" in summary:
        click.echo("❌ No metrics collected yet")
        sys.exit(1)

    click.echo("📊 Ollama Usage Metrics:")
    click.echo(f"  Total workflows: {summary['total_workflows']}")
    click.echo(f"  Success rate: {summary['success_rate']:.1f}%")
    click.echo(f"  Average execution time: {summary['execution_time']['avg']:.2f}s")
    click.echo(f"  Average tokens per workflow: {summary['tokens']['total_avg']:.0f}")
    click.echo(f"  Token efficiency: {summary['efficiency']['tokens_per_second']:.0f} tokens/sec")

    # Export metrics
    export_path = collector.export_metrics()
    click.echo(f"📁 Detailed metrics exported to: {export_path}")


if __name__ == "__main__":
    cli()
