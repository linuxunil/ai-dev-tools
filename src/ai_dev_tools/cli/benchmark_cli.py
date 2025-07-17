"""
Unified CLI interface for AI Development Tools benchmarking.

Provides a comprehensive command-line interface for running benchmarks
with all the features of the new benchmarking system.
"""

import asyncio
import click
import json
import logging
from pathlib import Path
from typing import List, Optional

from ..benchmark import (
    BenchmarkRunner,
    BenchmarkConfig,
    HardwareProfile,
    OutputFormat,
    load_config
)
from ..benchmark.core import quick_benchmark, compare_profiles, batch_benchmark
from ..benchmark.config import WorkflowType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (pyproject.toml)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for results",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
@click.pass_context
def benchmark(ctx, config, output_dir, log_level):
    """AI Development Tools Benchmark Suite - Unified CLI Interface."""
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # Load configuration
    try:
        if config:
            benchmark_config = BenchmarkConfig.from_toml(config)
        else:
            benchmark_config = load_config()
        
        # Override output directory if specified
        if output_dir:
            benchmark_config.output_directory = output_dir
        
        # Create benchmark runner
        runner = BenchmarkRunner(benchmark_config)
        
        # Store in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj["runner"] = runner
        ctx.obj["config"] = benchmark_config
        
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        ctx.exit(1)


@benchmark.command()
@click.option(
    "--profile",
    "-p",
    type=click.Choice(["light", "medium", "heavy"]),
    required=True,
    help="Hardware profile to use",
)
@click.option(
    "--tasks",
    "-t",
    multiple=True,
    help="Specific tasks to run (run all if not specified)",
)
@click.option(
    "--samples",
    "-s",
    type=int,
    help="Number of samples per task (uses profile default if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "markdown", "csv", "console"]),
    help="Output format (uses config default if not specified)",
)
@click.option(
    "--filename",
    help="Output filename (auto-generated if not specified)",
)
@click.pass_context
def run(ctx, profile, tasks, samples, output_format, filename):
    """Run a single benchmark configuration."""
    
    runner = ctx.obj["runner"]
    
    # Convert string profile to enum
    profile_enum = HardwareProfile(profile)
    
    # Convert output format if specified
    format_enum = OutputFormat(output_format) if output_format else None
    
    # Convert tasks list
    task_list = list(tasks) if tasks else None
    
    async def run_benchmark():
        try:
            click.echo(f"🚀 Running benchmark with profile: {profile.upper()}")
            
            if task_list:
                click.echo(f"📋 Tasks: {', '.join(task_list)}")
            else:
                click.echo("📋 Running all available tasks")
            
            if samples:
                click.echo(f"🔢 Samples per task: {samples}")
            else:
                click.echo(f"🔢 Using profile default sample size")
            
            results = await runner.run_single_benchmark(
                profile=profile_enum,
                task_ids=task_list,
                sample_size=samples,
                output_format=format_enum,
                output_filename=filename
            )
            
            # Display summary
            benchmark_info = results.get("benchmark_info", {})
            comparison_metrics = results.get("comparison_metrics", {})
            
            click.echo("\n📊 Benchmark Complete!")
            click.echo(f"   Profile: {benchmark_info.get('profile', 'unknown').upper()}")
            click.echo(f"   Tasks: {benchmark_info.get('total_tasks', 0)}")
            click.echo(f"   Samples: {benchmark_info.get('sample_size', 0)}")
            click.echo(f"   Instances: {benchmark_info.get('instances', 0)}")
            
            if comparison_metrics:
                click.echo("\n🎯 Performance Improvements:")
                click.echo(f"   Token Reduction: {comparison_metrics.get('token_reduction_percent', 0):.1f}%")
                click.echo(f"   Time Reduction: {comparison_metrics.get('time_reduction_percent', 0):.1f}%")
                click.echo(f"   Efficiency Improvement: {comparison_metrics.get('efficiency_improvement_percent', 0):.1f}%")
            
        except Exception as e:
            click.echo(f"❌ Benchmark failed: {e}", err=True)
            return 1
    
    # Run the async function
    exit_code = asyncio.run(run_benchmark())
    if exit_code:
        ctx.exit(exit_code)


@benchmark.command()
@click.argument("batch_name", type=click.Choice(["quick", "standard", "comprehensive", "scaling"]))
@click.option(
    "--tasks",
    "-t",
    multiple=True,
    help="Specific tasks to run (run all if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "markdown", "csv", "console"]),
    help="Output format (uses config default if not specified)",
)
@click.option(
    "--filename",
    help="Output filename (auto-generated if not specified)",
)
@click.pass_context
def batch(ctx, batch_name, tasks, output_format, filename):
    """Run a predefined batch benchmark configuration."""
    
    runner = ctx.obj["runner"]
    
    # Convert output format if specified
    format_enum = OutputFormat(output_format) if output_format else None
    
    # Convert tasks list
    task_list = list(tasks) if tasks else None
    
    async def run_batch():
        try:
            click.echo(f"🚀 Running batch benchmark: {batch_name.upper()}")
            
            if task_list:
                click.echo(f"📋 Tasks: {', '.join(task_list)}")
            else:
                click.echo("📋 Running all available tasks")
            
            results = await runner.run_batch_benchmark(
                batch_name=batch_name,
                task_ids=task_list,
                output_format=format_enum,
                output_filename=filename
            )
            
            # Display summary for each result
            click.echo("\n📊 Batch Complete!")
            
            for i, result in enumerate(results, 1):
                batch_info = result.get("batch_info", {})
                comparison_metrics = result.get("comparison_metrics", {})
                
                click.echo(f"\n   Run {i}:")
                click.echo(f"     Configuration: {batch_info.get('batch_name', 'unknown')}")
                
                if comparison_metrics:
                    click.echo(f"     Token Reduction: {comparison_metrics.get('token_reduction_percent', 0):.1f}%")
                    click.echo(f"     Time Reduction: {comparison_metrics.get('time_reduction_percent', 0):.1f}%")
                    click.echo(f"     Efficiency Improvement: {comparison_metrics.get('efficiency_improvement_percent', 0):.1f}%")
            
        except Exception as e:
            click.echo(f"❌ Batch benchmark failed: {e}", err=True)
            return 1
    
    # Run the async function
    exit_code = asyncio.run(run_batch())
    if exit_code:
        ctx.exit(exit_code)


@benchmark.command()
@click.option(
    "--profiles",
    "-p",
    multiple=True,
    type=click.Choice(["light", "medium", "heavy"]),
    required=True,
    help="Hardware profiles to compare",
)
@click.option(
    "--tasks",
    "-t",
    multiple=True,
    help="Specific tasks to run (run all if not specified)",
)
@click.option(
    "--samples",
    "-s",
    type=int,
    help="Number of samples per task (uses profile defaults if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "markdown", "csv", "console"]),
    help="Output format (uses config default if not specified)",
)
@click.option(
    "--filename",
    help="Output filename (auto-generated if not specified)",
)
@click.pass_context
def compare(ctx, profiles, tasks, samples, output_format, filename):
    """Compare performance across multiple hardware profiles."""
    
    runner = ctx.obj["runner"]
    
    # Convert string profiles to enums
    profile_enums = [HardwareProfile(p) for p in profiles]
    
    # Convert output format if specified
    format_enum = OutputFormat(output_format) if output_format else None
    
    # Convert tasks list
    task_list = list(tasks) if tasks else None
    
    async def run_comparison():
        try:
            click.echo(f"🚀 Running comparison across profiles: {', '.join(profiles).upper()}")
            
            if task_list:
                click.echo(f"📋 Tasks: {', '.join(task_list)}")
            else:
                click.echo("📋 Running all available tasks")
            
            if samples:
                click.echo(f"🔢 Samples per task: {samples}")
            else:
                click.echo("🔢 Using profile default sample sizes")
            
            results = await runner.run_comparison_benchmark(
                profiles=profile_enums,
                task_ids=task_list,
                sample_size=samples,
                output_format=format_enum,
                output_filename=filename
            )
            
            # Display comparison summary
            comparison_info = results.get("comparison_info", {})
            profile_comparison = results.get("profile_comparison", {})
            
            click.echo("\n📊 Comparison Complete!")
            click.echo(f"   Profiles: {comparison_info.get('profiles', [])}")
            click.echo(f"   Tasks: {comparison_info.get('tasks', 0)}")
            
            if profile_comparison:
                click.echo("\n🎯 Performance by Profile:")
                for profile_name, metrics in profile_comparison.items():
                    click.echo(f"   {profile_name.upper()}:")
                    click.echo(f"     Token Reduction: {metrics.get('token_reduction', 0):.1f}%")
                    click.echo(f"     Time Reduction: {metrics.get('time_reduction', 0):.1f}%")
                    click.echo(f"     Efficiency Improvement: {metrics.get('efficiency_improvement', 0):.1f}%")
            
        except Exception as e:
            click.echo(f"❌ Comparison failed: {e}", err=True)
            return 1
    
    # Run the async function
    exit_code = asyncio.run(run_comparison())
    if exit_code:
        ctx.exit(exit_code)


@benchmark.command()
@click.option(
    "--profile",
    "-p",
    type=click.Choice(["light", "medium", "heavy"]),
    default="medium",
    help="Hardware profile to use",
)
@click.option(
    "--tasks",
    "-t",
    multiple=True,
    help="Specific tasks to run (run 3 default tasks if not specified)",
)
@click.option(
    "--samples",
    "-s",
    type=int,
    default=3,
    help="Number of samples per task",
)
@click.pass_context
def quick(ctx, profile, tasks, samples):
    """Run a quick benchmark with minimal configuration."""
    
    config = ctx.obj["config"]
    task_list = list(tasks) if tasks else None
    
    async def run_quick():
        try:
            click.echo(f"⚡ Running quick benchmark with profile: {profile.upper()}")
            
            if task_list:
                click.echo(f"📋 Tasks: {', '.join(task_list)}")
            else:
                click.echo("📋 Running default tasks (up to 3)")
            
            click.echo(f"🔢 Samples per task: {samples}")
            
            result = await quick_benchmark(
                profile=profile,
                tasks=task_list,
                sample_size=samples,
                config=config
            )
            
            # Display results
            click.echo(f"\n📊 Quick Benchmark Results:")
            click.echo(f"   Profile: {result.profile.upper()}")
            click.echo(f"   Status: {result.status}")
            click.echo(f"   Tasks Executed: {result.tasks_executed}")
            click.echo(f"   Success Rate: {result.success_rate:.1%}")
            
            if result.status == "completed":
                click.echo(f"   Average Duration: {result.avg_duration:.2f}s")
                click.echo(f"   Total Tokens: {result.total_tokens:,}")
                click.echo(f"   Tokens/Second: {result.tokens_per_second:.2f}")
                
                if result.token_reduction_percent or result.time_reduction_percent:
                    click.echo(f"\n🎯 Improvements:")
                    click.echo(f"   Token Reduction: {result.token_reduction_percent:.1f}%")
                    click.echo(f"   Time Reduction: {result.time_reduction_percent:.1f}%")
            else:
                click.echo(f"   Error: {result.error_message}")
                return 1
            
        except Exception as e:
            click.echo(f"❌ Quick benchmark failed: {e}", err=True)
            return 1
    
    # Run the async function
    exit_code = asyncio.run(run_quick())
    if exit_code:
        ctx.exit(exit_code)


@benchmark.command()
@click.pass_context
def list_tasks(ctx):
    """List all available benchmark tasks."""
    
    runner = ctx.obj["runner"]
    
    tasks = runner.list_available_tasks()
    
    click.echo("📋 Available Benchmark Tasks:")
    click.echo("=" * 50)
    
    for task in tasks:
        click.echo(f"\n🔸 {task['task_id']}")
        click.echo(f"   Name: {task['name']}")
        click.echo(f"   Type: {task['workflow_type']}")
        click.echo(f"   Description: {task['description']}")
        click.echo(f"   Timeout: {task['timeout']}s")
        
        if task['target_files']:
            click.echo(f"   Target Files: {', '.join(task['target_files'])}")


@benchmark.command()
@click.pass_context
def list_profiles(ctx):
    """List all available hardware profiles."""
    
    runner = ctx.obj["runner"]
    
    profiles = runner.list_available_profiles()
    
    click.echo("🖥️  Available Hardware Profiles:")
    click.echo("=" * 50)
    
    for profile in profiles:
        click.echo(f"\n🔸 {profile['profile']}")
        click.echo(f"   Description: {profile['description']}")
        click.echo(f"   Instances: {profile['instances']}")
        click.echo(f"   Models: {', '.join(profile['models'])}")
        click.echo(f"   Default Sample Size: {profile['default_sample_size']}")


@benchmark.command()
@click.pass_context
def list_batches(ctx):
    """List all available batch configurations."""
    
    runner = ctx.obj["runner"]
    
    batches = runner.list_available_batches()
    
    click.echo("📦 Available Batch Configurations:")
    click.echo("=" * 50)
    
    for batch in batches:
        click.echo(f"\n🔸 {batch['batch_name']}")
        click.echo(f"   Description: {batch['description']}")
        click.echo(f"   Profile: {batch['profile']}")
        click.echo(f"   Sample Size: {batch['sample_size']}")
        click.echo(f"   Repetitions: {batch['repetitions']}")
        click.echo(f"   Timeout: {batch['timeout']}s")


@benchmark.command()
@click.option(
    "--task-id",
    required=True,
    help="Unique identifier for the task",
)
@click.option(
    "--name",
    required=True,
    help="Human-readable name for the task",
)
@click.option(
    "--description",
    required=True,
    help="Description of what the task does",
)
@click.option(
    "--workflow-type",
    required=True,
    type=click.Choice(["pattern_analysis", "safety_check", "context_analysis", "systematic_fix", "repo_analysis"]),
    help="Type of workflow this task represents",
)
@click.option(
    "--baseline-prompt",
    required=True,
    help="Prompt for baseline approach",
)
@click.option(
    "--tools-prompt",
    required=True,
    help="Prompt for tools approach",
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Task timeout in seconds",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Maximum retry attempts",
)
@click.pass_context
def add_task(ctx, task_id, name, description, workflow_type, baseline_prompt, tools_prompt, timeout, max_retries):
    """Add a custom task to the benchmark suite."""
    
    runner = ctx.obj["runner"]
    
    try:
        success = runner.add_custom_task(
            task_id=task_id,
            name=name,
            description=description,
            workflow_type=workflow_type,
            baseline_prompt=baseline_prompt,
            tools_prompt=tools_prompt,
            timeout=timeout,
            max_retries=max_retries
        )
        
        if success:
            click.echo(f"✅ Successfully added task: {task_id}")
        else:
            click.echo(f"❌ Failed to add task: {task_id}")
            ctx.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error adding task: {e}", err=True)
        ctx.exit(1)


@benchmark.command()
@click.pass_context
def info(ctx):
    """Display configuration and system information."""
    
    runner = ctx.obj["runner"]
    config = ctx.obj["config"]
    
    click.echo("ℹ️  Benchmark Configuration Info:")
    click.echo("=" * 50)
    
    # Configuration summary
    config_summary = runner.get_config_summary()
    
    click.echo(f"\n🔧 Configuration:")
    click.echo(f"   Profiles: {config_summary['profiles']}")
    click.echo(f"   Tasks: {config_summary['tasks']}")
    click.echo(f"   Batch Configs: {config_summary['batches']}")
    click.echo(f"   Execution Mode: {config_summary['execution_mode']}")
    click.echo(f"   Output Format: {config_summary['output_format']}")
    click.echo(f"   Output Directory: {config_summary['output_directory']}")
    click.echo(f"   Docker Compose: {config_summary['docker_compose_file']}")
    click.echo(f"   Container Timeout: {config_summary['container_startup_timeout']}s")
    click.echo(f"   Task Timeout: {config_summary['task_timeout']}s")
    click.echo(f"   Retry Attempts: {config_summary['retry_attempts']}")
    
    # Task registry stats
    task_stats = runner.get_task_registry_stats()
    
    click.echo(f"\n📋 Task Registry:")
    click.echo(f"   Total Tasks: {task_stats['total_tasks']}")
    click.echo(f"   Workflow Distribution:")
    
    for workflow_type, count in task_stats['workflow_distribution'].items():
        click.echo(f"     {workflow_type}: {count}")


@benchmark.command()
@click.pass_context
def validate(ctx):
    """Validate the benchmark setup and configuration."""
    
    runner = ctx.obj["runner"]
    
    click.echo("🔍 Validating Benchmark Setup...")
    
    validation_result = runner.validate_setup()
    
    if validation_result["valid"]:
        click.echo("✅ All validation checks passed!")
    else:
        click.echo("❌ Validation issues found:")
        for issue in validation_result["issues"]:
            click.echo(f"   • {issue}")
    
    if validation_result["warnings"]:
        click.echo("\n⚠️  Warnings:")
        for warning in validation_result["warnings"]:
            click.echo(f"   • {warning}")
    
    click.echo(f"\n📊 Setup Summary:")
    click.echo(f"   Available Profiles: {validation_result['profiles_available']}")
    click.echo(f"   Available Tasks: {validation_result['tasks_available']}")
    click.echo(f"   Available Batches: {validation_result['batches_available']}")
    
    if not validation_result["valid"]:
        ctx.exit(1)


@benchmark.command()
@click.argument("output_file", type=click.Path(path_type=Path))
@click.pass_context
def export_config(ctx, output_file):
    """Export current configuration to a file."""
    
    config = ctx.obj["config"]
    
    try:
        # Convert config to dictionary for export
        config_dict = {
            "profiles": {
                profile.value: [
                    {
                        "name": instance.name,
                        "model": instance.model,
                        "host": instance.host,
                        "port": instance.port,
                        "timeout": instance.timeout,
                        "max_concurrent": instance.max_concurrent
                    }
                    for instance in instances
                ]
                for profile, instances in config.profiles.items()
            },
            "sample_sizes": {
                profile.value: size
                for profile, size in config.sample_sizes.items()
            },
            "execution_mode": config.execution_mode.value,
            "output_format": config.output_format.value,
            "output_directory": str(config.output_directory),
            "docker_compose_file": str(config.docker_compose_file),
            "container_startup_timeout": config.container_startup_timeout,
            "task_timeout": config.task_timeout,
            "retry_attempts": config.retry_attempts,
            "max_concurrent_batches": config.max_concurrent_batches,
            "batch_configurations": {
                name: {
                    "name": batch.name,
                    "profile": batch.profile.value,
                    "sample_size": batch.sample_size,
                    "repetitions": batch.repetitions,
                    "description": batch.description,
                    "timeout": batch.timeout
                }
                for name, batch in config.batch_configurations.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        click.echo(f"✅ Configuration exported to: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Failed to export configuration: {e}", err=True)
        ctx.exit(1)


if __name__ == "__main__":
    benchmark()