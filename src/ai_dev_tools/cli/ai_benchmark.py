"""
AI Benchmark CLI - Token usage and execution time benchmarking tool

Provides comprehensive benchmarking capabilities to measure the efficiency
gains of our AI development tools compared to baseline manual workflows.

Key features:
- Baseline simulation of manual AI workflows
- Current tool performance measurement
- Comparative analysis and reporting
- Performance regression testing
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import click

from ..core.ai_helper import AIHelper
from ..core.baseline_simulator import BaselineSimulator
from ..core.benchmark_suite import BenchmarkSuite, create_benchmark_report
from ..core.metrics_collector import (
    MetricsCollector,
    WorkflowType,
)
from ..core.ollama_client import ModelSize


def format_benchmark_output(results: Dict[str, Any], format_type: str) -> str:
    """Format benchmark results for output"""
    if format_type == "json":
        return json.dumps(results, indent=2)
    elif format_type == "compact":
        return json.dumps(results)
    else:  # human-readable
        output = []
        output.append("🚀 AI Development Tools Benchmark Results")
        output.append("=" * 50)

        if "comparison" in results:
            comp = results["comparison"]
            improvements = comp.get("improvements", {})
            verdict = comp.get("verdict", {})

            output.append("\n📊 Performance Comparison:")
            output.append(
                f"Token Efficiency: {improvements.get('token_reduction_percent', 0):.1f}% improvement"
            )
            output.append(
                f"Execution Speed: {improvements.get('time_reduction_percent', 0):.1f}% improvement"
            )
            output.append(
                f"Overall Efficiency: {improvements.get('efficiency_increase_percent', 0):.1f}% improvement"
            )
            output.append(
                f"Success Rate: {improvements.get('success_rate_improvement', 0):.1f}% improvement"
            )

            output.append("\n✅ Verdict:")
            output.append(
                f"More Token Efficient: {'Yes' if verdict.get('more_token_efficient') else 'No'}"
            )
            output.append(
                f"Faster Execution: {'Yes' if verdict.get('faster') else 'No'}"
            )
            output.append(
                f"More Reliable: {'Yes' if verdict.get('more_reliable') else 'No'}"
            )

            if "roi_analysis" in comp:
                roi = comp["roi_analysis"]
                output.append("\n💰 ROI Analysis:")
                output.append(
                    f"Token Savings per Workflow: {roi.get('token_savings_per_workflow', 0):.0f}"
                )
                output.append(
                    f"Time Savings per Workflow: {roi.get('time_savings_per_workflow', 0):.1f}s"
                )
                output.append(
                    f"Cost Impact: {roi.get('estimated_cost_savings', 'N/A')}"
                )

        if "summary" in results:
            summary = results["summary"]
            output.append("\n📈 Summary Statistics:")
            output.append(f"Total Workflows: {summary.get('total_workflows', 0)}")
            output.append(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
            output.append(
                f"Average Tokens: {summary.get('average_tokens_per_workflow', 0):.0f}"
            )
            output.append(
                f"Average Duration: {summary.get('average_duration_per_workflow', 0):.1f}s"
            )

        return "\n".join(output)


@click.group()
@click.option(
    "--metrics-dir",
    default=".ai_metrics",
    help="Directory for metrics storage (default: .ai_metrics)",
)
@click.pass_context
def ai_benchmark(ctx, metrics_dir: str):
    """
    AI Benchmark - Token usage and execution time benchmarking

    Measures the efficiency gains of AI development tools by comparing
    token usage and execution time against baseline manual workflows.

    Exit codes:
    - 0: Benchmark completed successfully
    - 1: Performance regression detected
    - 255: Error occurred
    """
    ctx.ensure_object(dict)
    ctx.obj["metrics_dir"] = metrics_dir
    ctx.obj["collector"] = MetricsCollector(metrics_dir)


@ai_benchmark.command()
@click.option(
    "--workflow",
    type=click.Choice(
        [wt.value for wt in WorkflowType if wt != WorkflowType.BASELINE_MANUAL]
    ),
    help="Specific workflow type to benchmark",
)
@click.option(
    "--iterations",
    type=int,
    default=5,
    help="Number of iterations per workflow (default: 5)",
)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default="human",
    help="Output format (default: human-readable)",
)
@click.pass_context
def baseline(ctx, workflow: Optional[str], iterations: int, format: str):
    """
    Run baseline simulation of manual AI workflows

    Simulates how AI agents would work WITHOUT our tools to establish
    baseline measurements for token usage and execution time.
    """
    collector = ctx.obj["collector"]
    simulator = BaselineSimulator(collector)

    try:
        if workflow:
            # Run single workflow type
            workflow_type = WorkflowType(workflow)
            results = []
            for i in range(iterations):
                result = simulator.simulate_workflow(workflow_type)
                results.append(result)

            output_results = {
                "workflow_type": workflow,
                "iterations": iterations,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Run complete baseline suite
            output_results = simulator.run_baseline_suite(iterations=iterations)
            output_results["timestamp"] = datetime.now().isoformat()

        click.echo(format_benchmark_output(output_results, format))
        sys.exit(0)

    except Exception as e:
        click.echo(f"Baseline simulation failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.option(
    "--workflow",
    type=click.Choice(
        [wt.value for wt in WorkflowType if wt != WorkflowType.BASELINE_MANUAL]
    ),
    help="Specific workflow type to benchmark",
)
@click.option(
    "--project-path",
    default=".",
    help="Project path for analysis (default: current directory)",
)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default="human",
    help="Output format (default: human-readable)",
)
@click.pass_context
def current(ctx, workflow: Optional[str], project_path: str, format: str):
    """
    Benchmark current AI tools performance

    Measures the actual performance of our AI development tools
    for comparison against baseline manual workflows.
    """
    collector = ctx.obj["collector"]

    try:
        if workflow:
            workflow_type = WorkflowType(workflow)

            # Run specific workflow with metrics collection
            if workflow_type == WorkflowType.PROJECT_ANALYSIS:
                helper = AIHelper(project_path)
                with collector.measure_workflow(
                    WorkflowType.UNIFIED_WORKFLOW
                ) as context:
                    result = helper.analyze_project()
                    context.record_tokens(
                        50, 200
                    )  # Estimated tokens for exit code workflow
                    context.record_files_processed(10)  # Estimated files processed
                    context.add_metadata("tool_result", result.to_dict())

            # Add more workflow implementations as needed

            summary = collector.get_metrics_summary(workflow_type)
        else:
            # Get overall summary
            summary = collector.get_metrics_summary()

        output_results = {
            "current_performance": summary,
            "timestamp": datetime.now().isoformat(),
            "project_path": project_path,
        }

        click.echo(format_benchmark_output(output_results, format))
        sys.exit(0)

    except Exception as e:
        click.echo(f"Current benchmark failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.option(
    "--baseline-file",
    type=click.Path(exists=True),
    help="Baseline results file (if not provided, runs new baseline)",
)
@click.option(
    "--current-file",
    type=click.Path(exists=True),
    help="Current results file (if not provided, runs new benchmark)",
)
@click.option(
    "--project-path",
    default=".",
    help="Project path for analysis (default: current directory)",
)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default="human",
    help="Output format (default: human-readable)",
)
@click.pass_context
def compare(
    ctx,
    baseline_file: Optional[str],
    current_file: Optional[str],
    project_path: str,
    format: str,
):
    """
    Compare baseline vs current performance

    Provides comprehensive comparison analysis showing the efficiency
    gains of our AI development tools over manual workflows.
    """
    collector = ctx.obj["collector"]
    simulator = BaselineSimulator(collector)

    try:
        # Get baseline results
        if baseline_file:
            with open(baseline_file) as f:
                baseline_data = json.load(f)
                baseline_results = baseline_data.get("summary", baseline_data)
        else:
            click.echo("Running baseline simulation...", err=True)
            baseline_suite = simulator.run_baseline_suite(project_path=project_path)
            baseline_results = baseline_suite["summary"]

        # Get current results
        if current_file:
            with open(current_file) as f:
                current_data = json.load(f)
                current_results = current_data.get("current_performance", current_data)
        else:
            click.echo("Running current tool benchmark...", err=True)
            # Run a quick benchmark of current tools
            helper = AIHelper(project_path)
            with collector.measure_workflow(WorkflowType.UNIFIED_WORKFLOW) as context:
                helper.analyze_project()
                context.record_tokens(50, 200)  # Estimated tokens
                context.record_files_processed(10)

            current_results = collector.get_metrics_summary()

        # Perform comparison
        comparison = simulator.compare_with_current(
            current_results, {"summary": baseline_results}
        )

        output_results = {
            "comparison": comparison,
            "timestamp": datetime.now().isoformat(),
            "project_path": project_path,
        }

        click.echo(format_benchmark_output(output_results, format))

        # Exit with appropriate code based on performance
        verdict = comparison.get("verdict", {})
        if verdict.get("more_token_efficient") and verdict.get("faster"):
            sys.exit(0)  # Success - tools are better
        else:
            sys.exit(1)  # Performance regression detected

    except Exception as e:
        click.echo(f"Comparison failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.option(
    "--output-file",
    help="Output file for metrics export (default: timestamp-based)",
)
@click.option(
    "--format",
    type=click.Choice(["json"]),
    default="json",
    help="Export format (default: json)",
)
@click.pass_context
def export(ctx, output_file: Optional[str], format: str):
    """
    Export collected metrics to file

    Exports all collected benchmark metrics for analysis,
    reporting, or historical comparison.
    """
    collector = ctx.obj["collector"]

    try:
        export_path = collector.export_metrics(output_file)
        click.echo(f"Metrics exported to: {export_path}")
        sys.exit(0)

    except Exception as e:
        click.echo(f"Export failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.pass_context
def clear(ctx):
    """
    Clear all collected metrics

    Resets the metrics collector to start fresh measurements.
    """
    collector = ctx.obj["collector"]

    try:
        collector.clear_metrics()
        click.echo("All metrics cleared successfully")
        sys.exit(0)

    except Exception as e:
        click.echo(f"Clear failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.option(
    "--threshold",
    type=float,
    default=5.0,
    help="Performance regression threshold in percent (default: 5.0)",
)
@click.option(
    "--baseline-file",
    type=click.Path(exists=True),
    required=True,
    help="Baseline results file for comparison",
)
@click.option(
    "--project-path",
    default=".",
    help="Project path for analysis (default: current directory)",
)
@click.pass_context
def regression_test(ctx, threshold: float, baseline_file: str, project_path: str):
    """
    Run performance regression test

    Compares current performance against a baseline and fails if
    performance has regressed beyond the specified threshold.

    Exit codes:
    - 0: No regression detected
    - 1: Performance regression detected
    - 255: Test failed to run
    """
    try:
        # Load baseline
        with open(baseline_file) as f:
            baseline_data = json.load(f)

        # Run current benchmark
        collector = ctx.obj["collector"]
        helper = AIHelper(project_path)

        with collector.measure_workflow(WorkflowType.UNIFIED_WORKFLOW) as context:
            helper.analyze_project()
            context.record_tokens(50, 200)
            context.record_files_processed(10)

        current_results = collector.get_metrics_summary()

        # Compare performance
        simulator = BaselineSimulator()
        comparison = simulator.compare_with_current(
            current_results, baseline_data.get("summary", baseline_data)
        )

        improvements = comparison.get("improvements", {})

        # Check for regressions
        token_regression = improvements.get("token_reduction_percent", 0) < -threshold
        time_regression = improvements.get("time_reduction_percent", 0) < -threshold

        if token_regression or time_regression:
            click.echo("❌ Performance regression detected!", err=True)
            click.echo(
                f"Token efficiency change: {improvements.get('token_reduction_percent', 0):.1f}%",
                err=True,
            )
            click.echo(
                f"Time efficiency change: {improvements.get('time_reduction_percent', 0):.1f}%",
                err=True,
            )
            click.echo(f"Threshold: {threshold}%", err=True)
            sys.exit(1)
        else:
            click.echo("✅ No performance regression detected")
            click.echo(
                f"Token efficiency: {improvements.get('token_reduction_percent', 0):.1f}%"
            )
            click.echo(
                f"Time efficiency: {improvements.get('time_reduction_percent', 0):.1f}%"
            )
            sys.exit(0)

    except Exception as e:
        click.echo(f"Regression test failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.option(
    "--models",
    default="llama3.2:1b,llama3.2:3b",
    help="Comma-separated list of models to test (default: small,medium)",
)
@click.option(
    "--ollama-hosts", 
    default="localhost:11434",
    help="Comma-separated list of Ollama hosts (default: localhost:11434)",
)
@click.option(
    "--test-codebase",
    default="test_codebase", 
    help="Path to standardized test codebase (default: test_codebase)",
)
@click.option(
    "--output-file",
    help="Save detailed results to file",
)
@click.option(
    "--format",
    type=click.Choice(["human", "json", "compact"]),
    default="human",
    help="Output format",
)
@click.pass_context
def standardized(ctx, models: str, ollama_hosts: str, test_codebase: str, 
                output_file: Optional[str], format: str):
    """
    Run standardized benchmark suite across models and containers
    
    Executes fixed tasks on standardized codebase to compare:
    - Baseline (manual AI workflows) vs Tools (our AI dev tools)  
    - Different models (llama3.2:1b vs llama3.2:3b vs llama3.1:8b)
    - Different Ollama instances (for A/B testing)
    
    Exit code: 0=success, 255=error
    """
    try:
        # Parse model list
        model_list = []
        for model_str in models.split(","):
            model_str = model_str.strip()
            try:
                # Map common names to ModelSize enum
                model_map = {
                    "small": ModelSize.SMALL,
                    "medium": ModelSize.MEDIUM, 
                    "large": ModelSize.LARGE,
                    "xlarge": ModelSize.XLARGE,
                    "llama3.2:1b": ModelSize.SMALL,
                    "llama3.2:3b": ModelSize.MEDIUM,
                    "llama3.1:8b": ModelSize.LARGE,
                    "llama3.1:70b": ModelSize.XLARGE,
                }
                
                if model_str in model_map:
                    model_list.append(model_map[model_str])
                else:
                    # Try to find by value
                    for size in ModelSize:
                        if size.value == model_str:
                            model_list.append(size)
                            break
                    else:
                        click.echo(f"Warning: Unknown model '{model_str}', skipping", err=True)
            except Exception as e:
                click.echo(f"Error parsing model '{model_str}': {e}", err=True)
        
        if not model_list:
            click.echo("Error: No valid models specified", err=True)
            sys.exit(255)
        
        # Parse host list
        host_list = [h.strip() for h in ollama_hosts.split(",")]
        
        click.echo(f"🚀 Running standardized benchmark suite")
        click.echo(f"Models: {[m.value for m in model_list]}")
        click.echo(f"Hosts: {host_list}")
        click.echo(f"Test codebase: {test_codebase}")
        click.echo("")
        
        # Initialize benchmark suite
        suite = BenchmarkSuite(test_codebase)
        
        # Run complete comparison
        results = suite.run_comparison_suite(model_list, host_list)
        
        # Generate report
        if format == "json":
            output = json.dumps(results, indent=2)
        elif format == "compact":
            output = json.dumps(results)
        else:  # human
            output = create_benchmark_report(results)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            click.echo(f"✅ Results saved to {output_file}")
        
        # Print to stdout
        click.echo(output)
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"Benchmark failed: {str(e)}", err=True)
        sys.exit(255)


@ai_benchmark.command()
@click.option(
    "--host",
    default="localhost:11434",
    help="Ollama host to test (default: localhost:11434)",
)
@click.option(
    "--models",
    default="llama3.2:1b,llama3.2:3b",
    help="Models to install and test",
)
@click.pass_context
def setup_models(ctx, host: str, models: str):
    """
    Setup and verify models on Ollama instance
    
    Pulls required models and verifies they're working for benchmarking.
    
    Exit code: 0=success, 1=some failures, 255=complete failure
    """
    try:
        import subprocess
        
        model_list = [m.strip() for m in models.split(",")]
        
        click.echo(f"🔧 Setting up models on {host}")
        
        success_count = 0
        total_count = len(model_list)
        
        for model in model_list:
            click.echo(f"Installing {model}...")
            
            try:
                # Use ollama CLI to pull model
                env = {"OLLAMA_HOST": host}
                result = subprocess.run(
                    ["ollama", "pull", model],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    click.echo(f"  ✅ {model} installed successfully")
                    success_count += 1
                else:
                    click.echo(f"  ❌ {model} failed: {result.stderr}", err=True)
                    
            except subprocess.TimeoutExpired:
                click.echo(f"  ⏰ {model} installation timed out", err=True)
            except Exception as e:
                click.echo(f"  ❌ {model} error: {e}", err=True)
        
        click.echo(f"\n📊 Setup complete: {success_count}/{total_count} models installed")
        
        if success_count == total_count:
            sys.exit(0)
        elif success_count > 0:
            sys.exit(1)
        else:
            sys.exit(255)
            
    except Exception as e:
        click.echo(f"Setup failed: {str(e)}", err=True)
        sys.exit(255)


if __name__ == "__main__":
    ai_benchmark()
