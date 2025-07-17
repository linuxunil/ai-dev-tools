"""
Reporting and visualization for AI Development Tools benchmarking.

Provides flexible report generation, data visualization, and export capabilities.
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import OutputFormat


class ReportGenerator:
    """Generates comprehensive benchmark reports in multiple formats."""

    def __init__(self, output_dir: Union[str, Path] = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        benchmark_data: Dict[str, Any],
        format_type: OutputFormat = OutputFormat.JSON,
        filename: Optional[str] = None,
    ) -> str:
        """Generate a report in the specified format."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            profile = benchmark_data.get("benchmark_info", {}).get("profile", "unknown")
            filename = f"benchmark_{profile}_{timestamp}"

        filepath = self.output_dir / f"{filename}.{format_type.value}"

        if format_type == OutputFormat.JSON:
            content = self._generate_json_report(benchmark_data)
        elif format_type == OutputFormat.MARKDOWN:
            content = self._generate_markdown_report(benchmark_data)
        elif format_type == OutputFormat.CSV:
            content = self._generate_csv_report(benchmark_data)
        elif format_type == OutputFormat.CONSOLE:
            content = self._generate_console_report(benchmark_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Write to file (except for console format)
        if format_type != OutputFormat.CONSOLE:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return str(filepath)
        else:
            return content

    def _generate_json_report(self, data: Dict[str, Any]) -> str:
        """Generate JSON format report."""
        return json.dumps(data, indent=2, default=str)

    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate Markdown format report."""
        lines = []

        # Title and metadata
        benchmark_info = data.get("benchmark_info", {})
        profile = benchmark_info.get("profile", "unknown")

        lines.append("# AI Development Tools Benchmark Report")
        lines.append("")
        lines.append(f"**Profile:** {profile.upper()}")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Tasks:** {benchmark_info.get('total_tasks', 0)}")
        lines.append(f"**Sample Size:** {benchmark_info.get('sample_size', 0)}")
        lines.append(f"**Execution Mode:** {benchmark_info.get('execution_mode', 'unknown')}")
        lines.append("")

        # Overall metrics
        overall_metrics = data.get("overall_metrics", {})
        if overall_metrics:
            lines.append("## Overall Performance")
            lines.append("")
            lines.append(f"- **Success Rate:** {overall_metrics.get('success_rate', 0):.1%}")
            lines.append(f"- **Total Tasks:** {overall_metrics.get('total_tasks', 0)}")
            lines.append(f"- **Completed Tasks:** {overall_metrics.get('completed_tasks', 0)}")
            lines.append(f"- **Failed Tasks:** {overall_metrics.get('failed_tasks', 0)}")
            lines.append(f"- **Average Duration:** {overall_metrics.get('average_task_duration', 0):.2f}s")
            lines.append(f"- **Total Tokens:** {overall_metrics.get('total_tokens', 0):,}")
            lines.append(f"- **Throughput:** {overall_metrics.get('throughput', 0):.2f} tasks/sec")
            lines.append(f"- **Efficiency Score:** {overall_metrics.get('efficiency_score', 0):.2f}")
            lines.append("")

        # Comparison metrics
        comparison_metrics = data.get("comparison_metrics", {})
        if comparison_metrics:
            lines.append("## Baseline vs Tools Comparison")
            lines.append("")
            lines.append(f"- **Token Reduction:** {comparison_metrics.get('token_reduction_percent', 0):.1f}%")
            lines.append(f"- **Time Reduction:** {comparison_metrics.get('time_reduction_percent', 0):.1f}%")
            lines.append(
                f"- **Efficiency Improvement:** {comparison_metrics.get('efficiency_improvement_percent', 0):.1f}%"
            )
            lines.append(f"- **Sample Size:** {comparison_metrics.get('sample_size', 0)}")
            lines.append("")

            # Detailed comparison
            baseline_metrics = comparison_metrics.get("baseline_metrics", {})
            tools_metrics = comparison_metrics.get("tools_metrics", {})

            lines.append("### Detailed Comparison")
            lines.append("")
            lines.append("| Metric | Baseline | Tools | Improvement |")
            lines.append("|--------|----------|-------|-------------|")

            metrics_to_compare = [
                ("Average Duration", "average_task_duration", "s"),
                ("Total Tokens", "total_tokens", ""),
                ("Success Rate", "success_rate", "%"),
                ("Throughput", "throughput", "tasks/s"),
                ("Efficiency Score", "efficiency_score", ""),
            ]

            for metric_name, key, unit in metrics_to_compare:
                baseline_val = baseline_metrics.get(key, 0)
                tools_val = tools_metrics.get(key, 0)

                if key == "success_rate":
                    baseline_val *= 100
                    tools_val *= 100

                if baseline_val > 0:
                    if key in ["average_task_duration"]:
                        # Lower is better
                        improvement = ((baseline_val - tools_val) / baseline_val) * 100
                    else:
                        # Higher is better
                        improvement = ((tools_val - baseline_val) / baseline_val) * 100
                else:
                    improvement = 0

                lines.append(
                    f"| {metric_name} | {baseline_val:.2f}{unit} | {tools_val:.2f}{unit} | {improvement:+.1f}% |"
                )

            lines.append("")

        # Task breakdown
        metrics_by_task = data.get("metrics_by_task", {})
        if metrics_by_task:
            lines.append("## Performance by Task")
            lines.append("")

            for task_id, task_metrics in metrics_by_task.items():
                lines.append(f"### {task_id}")
                lines.append("")
                lines.append(f"- **Success Rate:** {task_metrics.get('success_rate', 0):.1%}")
                lines.append(f"- **Average Duration:** {task_metrics.get('average_task_duration', 0):.2f}s")
                lines.append(f"- **Total Tokens:** {task_metrics.get('total_tokens', 0):,}")
                lines.append(f"- **Efficiency Score:** {task_metrics.get('efficiency_score', 0):.2f}")
                lines.append("")

        # Model breakdown
        metrics_by_model = data.get("metrics_by_model", {})
        if metrics_by_model:
            lines.append("## Performance by Model")
            lines.append("")

            for model_name, model_metrics in metrics_by_model.items():
                lines.append(f"### {model_name}")
                lines.append("")
                lines.append(f"- **Success Rate:** {model_metrics.get('success_rate', 0):.1%}")
                lines.append(f"- **Average Duration:** {model_metrics.get('average_task_duration', 0):.2f}s")
                lines.append(f"- **Total Tokens:** {model_metrics.get('total_tokens', 0):,}")
                lines.append(f"- **Efficiency Score:** {model_metrics.get('efficiency_score', 0):.2f}")
                lines.append("")

        # Error analysis
        overall_metrics = data.get("overall_metrics", {})
        error_types = overall_metrics.get("error_types", {})
        if error_types:
            lines.append("## Error Analysis")
            lines.append("")

            for error_type, count in error_types.items():
                lines.append(f"- **{error_type}:** {count}")

            lines.append("")

        return "\n".join(lines)

    def _generate_csv_report(self, data: Dict[str, Any]) -> str:
        """Generate CSV format report."""
        output = []

        # Get results
        results = data.get("results", [])
        if not results:
            return "No results found"

        # CSV header
        fieldnames = [
            "task_id",
            "approach",
            "model_instance",
            "status",
            "duration",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "sample_num",
            "start_time",
            "end_time",
            "error",
        ]

        # Write header
        output.append(",".join(fieldnames))

        # Write data rows
        for result in results:
            row = []
            for field in fieldnames:
                value = result.get(field, "")
                if value is None:
                    value = ""
                row.append(str(value))
            output.append(",".join(row))

        return "\n".join(output)

    def _generate_console_report(self, data: Dict[str, Any]) -> str:
        """Generate console-friendly report."""
        lines = []

        # Title
        benchmark_info = data.get("benchmark_info", {})
        profile = benchmark_info.get("profile", "unknown")

        lines.append("🚀 AI Development Tools Benchmark Report")
        lines.append("=" * 60)
        lines.append(f"Profile: {profile.upper()}")
        lines.append(f"Tasks: {benchmark_info.get('total_tasks', 0)}")
        lines.append(f"Sample Size: {benchmark_info.get('sample_size', 0)}")
        lines.append("")

        # Overall metrics
        overall_metrics = data.get("overall_metrics", {})
        if overall_metrics:
            lines.append("📊 Overall Performance:")
            lines.append("-" * 30)
            lines.append(f"Success Rate: {overall_metrics.get('success_rate', 0):.1%}")
            lines.append(f"Total Tasks: {overall_metrics.get('total_tasks', 0)}")
            lines.append(f"Average Duration: {overall_metrics.get('average_task_duration', 0):.2f}s")
            lines.append(f"Total Tokens: {overall_metrics.get('total_tokens', 0):,}")
            lines.append(f"Throughput: {overall_metrics.get('throughput', 0):.2f} tasks/sec")
            lines.append(f"Efficiency Score: {overall_metrics.get('efficiency_score', 0):.2f}")
            lines.append("")

        # Comparison metrics
        comparison_metrics = data.get("comparison_metrics", {})
        if comparison_metrics:
            lines.append("🎯 Baseline vs Tools:")
            lines.append("-" * 20)
            lines.append(f"Token Reduction: {comparison_metrics.get('token_reduction_percent', 0):.1f}%")
            lines.append(f"Time Reduction: {comparison_metrics.get('time_reduction_percent', 0):.1f}%")
            lines.append(f"Efficiency Improvement: {comparison_metrics.get('efficiency_improvement_percent', 0):.1f}%")
            lines.append("")

        # Task performance
        metrics_by_task = data.get("metrics_by_task", {})
        if metrics_by_task:
            lines.append("📋 Task Performance:")
            lines.append("-" * 20)

            for task_id, task_metrics in metrics_by_task.items():
                lines.append(f"{task_id}:")
                lines.append(f"  Success: {task_metrics.get('success_rate', 0):.1%}")
                lines.append(f"  Duration: {task_metrics.get('average_task_duration', 0):.2f}s")
                lines.append(f"  Tokens: {task_metrics.get('total_tokens', 0):,}")

            lines.append("")

        # Model performance
        metrics_by_model = data.get("metrics_by_model", {})
        if metrics_by_model:
            lines.append("🤖 Model Performance:")
            lines.append("-" * 20)

            for model_name, model_metrics in metrics_by_model.items():
                lines.append(f"{model_name}:")
                lines.append(f"  Success: {model_metrics.get('success_rate', 0):.1%}")
                lines.append(f"  Duration: {model_metrics.get('average_task_duration', 0):.2f}s")
                lines.append(f"  Tokens: {model_metrics.get('total_tokens', 0):,}")

            lines.append("")

        return "\n".join(lines)

    def generate_batch_report(
        self,
        batch_results: List[Dict[str, Any]],
        format_type: OutputFormat = OutputFormat.JSON,
        filename: Optional[str] = None,
    ) -> str:
        """Generate a report for batch benchmark results."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_report_{timestamp}"

        filepath = self.output_dir / f"{filename}.{format_type.value}"

        # Aggregate batch data
        batch_data = self._aggregate_batch_data(batch_results)

        if format_type == OutputFormat.JSON:
            content = self._generate_json_report(batch_data)
        elif format_type == OutputFormat.MARKDOWN:
            content = self._generate_batch_markdown_report(batch_data)
        elif format_type == OutputFormat.CONSOLE:
            content = self._generate_batch_console_report(batch_data)
        else:
            raise ValueError(f"Unsupported format for batch report: {format_type}")

        # Write to file (except for console format)
        if format_type != OutputFormat.CONSOLE:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return str(filepath)
        else:
            return content

    def _aggregate_batch_data(self, batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate data from multiple batch results."""
        successful_results = [r for r in batch_results if r.get("overall_metrics")]

        if not successful_results:
            return {"batch_results": batch_results, "aggregated_stats": {}}

        # Aggregate overall metrics
        all_token_reductions = []
        all_time_reductions = []
        all_efficiency_improvements = []

        for result in successful_results:
            comparison = result.get("comparison_metrics", {})
            if comparison:
                all_token_reductions.append(comparison.get("token_reduction_percent", 0))
                all_time_reductions.append(comparison.get("time_reduction_percent", 0))
                all_efficiency_improvements.append(comparison.get("efficiency_improvement_percent", 0))

        aggregated_stats = {}
        if all_token_reductions:
            aggregated_stats = {
                "token_reduction": {
                    "mean": statistics.mean(all_token_reductions),
                    "median": statistics.median(all_token_reductions),
                    "std": statistics.stdev(all_token_reductions) if len(all_token_reductions) > 1 else 0,
                    "min": min(all_token_reductions),
                    "max": max(all_token_reductions),
                },
                "time_reduction": {
                    "mean": statistics.mean(all_time_reductions),
                    "median": statistics.median(all_time_reductions),
                    "std": statistics.stdev(all_time_reductions) if len(all_time_reductions) > 1 else 0,
                    "min": min(all_time_reductions),
                    "max": max(all_time_reductions),
                },
                "efficiency_improvement": {
                    "mean": statistics.mean(all_efficiency_improvements),
                    "median": statistics.median(all_efficiency_improvements),
                    "std": statistics.stdev(all_efficiency_improvements) if len(all_efficiency_improvements) > 1 else 0,
                    "min": min(all_efficiency_improvements),
                    "max": max(all_efficiency_improvements),
                },
                "total_configurations": len(batch_results),
                "successful_configurations": len(successful_results),
                "success_rate": len(successful_results) / len(batch_results) if batch_results else 0,
            }

        return {
            "batch_results": batch_results,
            "aggregated_stats": aggregated_stats,
            "summary": {
                "total_runs": len(batch_results),
                "successful_runs": len(successful_results),
                "timestamp": time.time(),
            },
        }

    def _generate_batch_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report for batch results."""
        lines = []

        lines.append("# Batch Benchmark Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        summary = data.get("summary", {})
        lines.append(f"**Total Runs:** {summary.get('total_runs', 0)}")
        lines.append(f"**Successful Runs:** {summary.get('successful_runs', 0)}")
        lines.append("")

        # Aggregated statistics
        aggregated_stats = data.get("aggregated_stats", {})
        if aggregated_stats:
            lines.append("## Aggregated Statistics")
            lines.append("")

            for metric_name, stats in aggregated_stats.items():
                if isinstance(stats, dict) and "mean" in stats:
                    lines.append(f"### {metric_name.replace('_', ' ').title()}")
                    lines.append("")
                    lines.append(f"- **Mean:** {stats['mean']:.2f}")
                    lines.append(f"- **Median:** {stats['median']:.2f}")
                    lines.append(f"- **Std Dev:** {stats['std']:.2f}")
                    lines.append(f"- **Min:** {stats['min']:.2f}")
                    lines.append(f"- **Max:** {stats['max']:.2f}")
                    lines.append("")

        # Individual results
        batch_results = data.get("batch_results", [])
        if batch_results:
            lines.append("## Individual Results")
            lines.append("")

            for i, result in enumerate(batch_results, 1):
                benchmark_info = result.get("benchmark_info", {})
                profile = benchmark_info.get("profile", "unknown")

                lines.append(f"### Run {i}: {profile.upper()}")
                lines.append("")

                if "error" in result:
                    lines.append("**Status:** Failed")
                    lines.append(f"**Error:** {result['error']}")
                else:
                    lines.append("**Status:** Success")
                    comparison = result.get("comparison_metrics", {})
                    if comparison:
                        lines.append(f"**Token Reduction:** {comparison.get('token_reduction_percent', 0):.1f}%")
                        lines.append(f"**Time Reduction:** {comparison.get('time_reduction_percent', 0):.1f}%")
                        lines.append(
                            f"**Efficiency Improvement:** {comparison.get('efficiency_improvement_percent', 0):.1f}%"
                        )

                lines.append("")

        return "\n".join(lines)

    def _generate_batch_console_report(self, data: Dict[str, Any]) -> str:
        """Generate console report for batch results."""
        lines = []

        lines.append("🚀 Batch Benchmark Report")
        lines.append("=" * 40)

        summary = data.get("summary", {})
        lines.append(f"Total Runs: {summary.get('total_runs', 0)}")
        lines.append(f"Successful: {summary.get('successful_runs', 0)}")
        lines.append("")

        # Aggregated statistics
        aggregated_stats = data.get("aggregated_stats", {})
        if aggregated_stats:
            lines.append("📊 Aggregated Performance:")
            lines.append("-" * 30)

            for metric_name, stats in aggregated_stats.items():
                if isinstance(stats, dict) and "mean" in stats:
                    lines.append(f"{metric_name.replace('_', ' ').title()}:")
                    lines.append(f"  Mean: {stats['mean']:.2f}")
                    lines.append(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")

            lines.append("")

        return "\n".join(lines)

    def export_raw_data(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Export raw benchmark data for further analysis."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_data_{timestamp}"

        filepath = self.output_dir / f"{filename}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return str(filepath)

    def create_summary_table(self, batch_results: List[Dict[str, Any]]) -> str:
        """Create a summary table of batch results."""
        lines = []

        # Header
        lines.append("| Configuration | Profile | Status | Token Reduction | Time Reduction | Efficiency |")
        lines.append("|---------------|---------|--------|-----------------|----------------|------------|")

        # Data rows
        for result in batch_results:
            batch_info = result.get("batch_info", {})
            config_name = batch_info.get("name", "unknown")
            profile = batch_info.get("profile", "unknown")

            if "error" in result:
                status = "Failed"
                token_reduction = "N/A"
                time_reduction = "N/A"
                efficiency = "N/A"
            else:
                status = "Success"
                comparison = result.get("comparison_metrics", {})
                token_reduction = f"{comparison.get('token_reduction_percent', 0):.1f}%"
                time_reduction = f"{comparison.get('time_reduction_percent', 0):.1f}%"
                efficiency = f"{comparison.get('efficiency_improvement_percent', 0):.1f}%"

            lines.append(
                f"| {config_name} | {profile} | {status} | {token_reduction} | {time_reduction} | {efficiency} |"
            )

        return "\n".join(lines)

    def generate_performance_dashboard(self, data: Dict[str, Any]) -> str:
        """Generate a simple ASCII dashboard for performance metrics."""
        lines = []

        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                 Performance Dashboard                       │")
        lines.append("├─────────────────────────────────────────────────────────────┤")

        # Overall metrics
        overall_metrics = data.get("overall_metrics", {})
        comparison_metrics = data.get("comparison_metrics", {})

        if overall_metrics:
            success_rate = overall_metrics.get("success_rate", 0)
            avg_duration = overall_metrics.get("average_task_duration", 0)
            throughput = overall_metrics.get("throughput", 0)

            lines.append(f"│ Success Rate:     {success_rate:.1%} {self._create_bar(success_rate, 0.8)} │")
            lines.append(f"│ Avg Duration:     {avg_duration:.2f}s                               │")
            lines.append(f"│ Throughput:       {throughput:.2f} tasks/sec                       │")

        if comparison_metrics:
            token_reduction = comparison_metrics.get("token_reduction_percent", 0) / 100
            time_reduction = comparison_metrics.get("time_reduction_percent", 0) / 100

            lines.append("├─────────────────────────────────────────────────────────────┤")
            lines.append("│                   Improvements                              │")
            lines.append("├─────────────────────────────────────────────────────────────┤")
            lines.append(f"│ Token Reduction:  {token_reduction:.1%} {self._create_bar(token_reduction, 0.3)} │")
            lines.append(f"│ Time Reduction:   {time_reduction:.1%} {self._create_bar(time_reduction, 0.3)} │")

        lines.append("└─────────────────────────────────────────────────────────────┘")

        return "\n".join(lines)

    def _create_bar(self, value: float, threshold: float = 0.5) -> str:
        """Create a simple ASCII progress bar."""
        bar_length = 20
        filled_length = int(bar_length * min(value, 1.0))

        if value >= threshold:
            bar_char = "█"
        else:
            bar_char = "▓"

        bar = bar_char * filled_length + "░" * (bar_length - filled_length)
        return f"[{bar}]"

    def generate_comparison_chart(self, comparison_data: Dict[str, Any]) -> str:
        """Generate a simple ASCII chart comparing baseline vs tools."""
        lines = []

        lines.append("┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                 Baseline vs Tools                           │")
        lines.append("├─────────────────────────────────────────────────────────────┤")

        baseline_metrics = comparison_data.get("baseline_metrics", {})
        tools_metrics = comparison_data.get("tools_metrics", {})

        # Compare key metrics
        metrics_to_compare = [
            ("Duration", "average_task_duration", "s", True),  # Lower is better
            ("Tokens", "total_tokens", "", True),  # Lower is better
            ("Success Rate", "success_rate", "%", False),  # Higher is better
            ("Throughput", "throughput", "tasks/s", False),  # Higher is better
        ]

        for metric_name, key, unit, lower_is_better in metrics_to_compare:
            baseline_val = baseline_metrics.get(key, 0)
            tools_val = tools_metrics.get(key, 0)

            if key == "success_rate":
                baseline_val *= 100
                tools_val *= 100

            # Create comparison visualization
            if baseline_val > 0:
                if lower_is_better:
                    ratio = tools_val / baseline_val
                    improvement = (1 - ratio) * 100
                    winner = "Tools" if tools_val < baseline_val else "Baseline"
                else:
                    ratio = tools_val / baseline_val
                    improvement = (ratio - 1) * 100
                    winner = "Tools" if tools_val > baseline_val else "Baseline"
            else:
                improvement = 0
                winner = "Tie"

            lines.append(f"│ {metric_name:<12} │ Baseline: {baseline_val:8.2f}{unit:<6} │ Tools: {tools_val:8.2f}{unit:<6} │")
            lines.append(f"│              │ Winner: {winner:<8} │ Improvement: {improvement:+6.1f}% │")
            lines.append("├─────────────────────────────────────────────────────────────┤")

        lines.append("└─────────────────────────────────────────────────────────────┘")

        return "\n".join(lines)

    def generate_trend_analysis(self, historical_data: List[Dict[str, Any]]) -> str:
        """Generate trend analysis from historical benchmark data."""
        if len(historical_data) < 2:
            return "Insufficient data for trend analysis (need at least 2 data points)"

        lines = []
        lines.append("📈 Trend Analysis")
        lines.append("=" * 20)

        # Extract key metrics over time
        timestamps = []
        token_reductions = []
        time_reductions = []
        success_rates = []

        for data in historical_data:
            comparison = data.get("comparison_metrics", {})
            overall = data.get("overall_metrics", {})

            if comparison and overall:
                timestamps.append(data.get("benchmark_info", {}).get("timestamp", 0))
                token_reductions.append(comparison.get("token_reduction_percent", 0))
                time_reductions.append(comparison.get("time_reduction_percent", 0))
                success_rates.append(overall.get("success_rate", 0) * 100)

        if len(timestamps) >= 2:
            # Calculate trends
            token_trend = self._calculate_trend(token_reductions)
            time_trend = self._calculate_trend(time_reductions)
            success_trend = self._calculate_trend(success_rates)

            lines.append(f"Token Reduction Trend: {token_trend}")
            lines.append(f"Time Reduction Trend: {time_trend}")
            lines.append(f"Success Rate Trend: {success_trend}")
            lines.append("")

            # Show latest vs first comparison
            if len(historical_data) >= 2:
                first_data = historical_data[0]
                latest_data = historical_data[-1]

                first_comparison = first_data.get("comparison_metrics", {})
                latest_comparison = latest_data.get("comparison_metrics", {})

                if first_comparison and latest_comparison:
                    token_change = latest_comparison.get("token_reduction_percent", 0) - first_comparison.get("token_reduction_percent", 0)
                    time_change = latest_comparison.get("time_reduction_percent", 0) - first_comparison.get("time_reduction_percent", 0)

                    lines.append("📊 Change Since First Run:")
                    lines.append(f"  Token Reduction: {token_change:+.1f}% change")
                    lines.append(f"  Time Reduction: {time_change:+.1f}% change")

        return "\n".join(lines)

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "No trend data"

        # Simple trend calculation
        start_value = values[0]
        end_value = values[-1]

        if abs(end_value - start_value) < 0.1:
            return "Stable"
        elif end_value > start_value:
            return "Improving ↗"
        else:
            return "Declining ↘"
