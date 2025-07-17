"""
Metrics collection and analysis for AI Development Tools benchmarking.

Provides comprehensive metrics collection, statistical analysis, and performance tracking.
"""

import asyncio
import statistics
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .tasks import TaskApproach, TaskResult


@dataclass
class BenchmarkMetrics:
    """Comprehensive metrics for a benchmark run."""

    # Basic execution metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0

    # Timing metrics
    total_duration: float = 0.0
    average_task_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    duration_std: float = 0.0

    # Token metrics
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    average_tokens_per_task: float = 0.0
    tokens_per_second: float = 0.0

    # Performance metrics
    throughput: float = 0.0  # tasks per second
    efficiency_score: float = 0.0  # composite efficiency metric

    # Error metrics
    timeout_count: int = 0
    retry_count: int = 0
    error_rate: float = 0.0

    # Resource utilization
    concurrent_peak: int = 0
    resource_utilization: float = 0.0

    # Additional statistics
    percentiles: Dict[str, float] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "average_task_duration": self.average_task_duration,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "duration_std": self.duration_std,
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "average_tokens_per_task": self.average_tokens_per_task,
            "tokens_per_second": self.tokens_per_second,
            "throughput": self.throughput,
            "efficiency_score": self.efficiency_score,
            "timeout_count": self.timeout_count,
            "retry_count": self.retry_count,
            "error_rate": self.error_rate,
            "concurrent_peak": self.concurrent_peak,
            "resource_utilization": self.resource_utilization,
            "percentiles": self.percentiles,
            "error_types": self.error_types,
        }


@dataclass
class ComparisonMetrics:
    """Metrics comparing baseline vs tools performance."""

    # Improvement percentages
    token_reduction_percent: float = 0.0
    time_reduction_percent: float = 0.0
    efficiency_improvement_percent: float = 0.0

    # Baseline metrics
    baseline_metrics: BenchmarkMetrics = field(default_factory=BenchmarkMetrics)

    # Tools metrics
    tools_metrics: BenchmarkMetrics = field(default_factory=BenchmarkMetrics)

    # Statistical significance
    statistical_significance: float = 0.0
    confidence_interval: Dict[str, float] = field(default_factory=dict)

    # Sample information
    sample_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison metrics to dictionary."""
        return {
            "token_reduction_percent": self.token_reduction_percent,
            "time_reduction_percent": self.time_reduction_percent,
            "efficiency_improvement_percent": self.efficiency_improvement_percent,
            "baseline_metrics": self.baseline_metrics.to_dict(),
            "tools_metrics": self.tools_metrics.to_dict(),
            "statistical_significance": self.statistical_significance,
            "confidence_interval": self.confidence_interval,
            "sample_size": self.sample_size,
        }


class MetricsCollector:
    """Comprehensive metrics collection and analysis."""

    def __init__(self):
        self.task_results: List[TaskResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.concurrent_tasks: int = 0
        self.max_concurrent: int = 0
        self.retry_counts: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def start_collection(self) -> None:
        """Start metrics collection."""
        async with self._lock:
            self.start_time = time.time()
            self.task_results.clear()
            self.concurrent_tasks = 0
            self.max_concurrent = 0
            self.retry_counts.clear()

    async def stop_collection(self) -> None:
        """Stop metrics collection."""
        async with self._lock:
            self.end_time = time.time()

    @contextmanager
    def track_concurrent_task(self):
        """Context manager to track concurrent task execution."""
        self.concurrent_tasks += 1
        self.max_concurrent = max(self.max_concurrent, self.concurrent_tasks)
        try:
            yield
        finally:
            self.concurrent_tasks -= 1

    async def add_task_result(self, result: TaskResult) -> None:
        """Add a task result to the collection."""
        async with self._lock:
            self.task_results.append(result)

    async def record_retry(self, task_id: str) -> None:
        """Record a retry attempt for a task."""
        async with self._lock:
            self.retry_counts[task_id] += 1

    def calculate_metrics(self, filter_approach: Optional[TaskApproach] = None) -> BenchmarkMetrics:
        """Calculate comprehensive metrics from collected results."""
        if filter_approach:
            results = [r for r in self.task_results if r.approach == filter_approach]
        else:
            results = self.task_results

        if not results:
            return BenchmarkMetrics()

        # Basic counts
        total_tasks = len(results)
        completed_tasks = len([r for r in results if r.status.value == "completed"])
        failed_tasks = len([r for r in results if r.status.value == "failed"])
        timeout_tasks = len([r for r in results if r.status.value == "timeout"])

        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0.0

        # Duration metrics
        completed_results = [r for r in results if r.duration is not None]
        if completed_results:
            durations = [r.duration for r in completed_results]
            total_duration = sum(durations)
            average_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            duration_std = statistics.stdev(durations) if len(durations) > 1 else 0.0

            # Calculate percentiles
            percentiles = {}
            if len(durations) >= 2:
                percentiles = {
                    "p25": statistics.quantiles(durations, n=4)[0],
                    "p50": statistics.median(durations),
                    "p75": statistics.quantiles(durations, n=4)[2],
                    "p90": statistics.quantiles(durations, n=10)[8],
                    "p95": statistics.quantiles(durations, n=20)[18],
                    "p99": statistics.quantiles(durations, n=100)[98],
                }
        else:
            total_duration = 0.0
            average_duration = 0.0
            min_duration = 0.0
            max_duration = 0.0
            duration_std = 0.0
            percentiles = {}

        # Token metrics
        total_tokens = sum(r.total_tokens for r in results)
        total_input_tokens = sum(r.input_tokens for r in results)
        total_output_tokens = sum(r.output_tokens for r in results)
        average_tokens_per_task = total_tokens / completed_tasks if completed_tasks > 0 else 0.0

        # Performance metrics
        overall_duration = (self.end_time or time.time()) - (self.start_time or time.time())
        throughput = completed_tasks / overall_duration if overall_duration > 0 else 0.0
        tokens_per_second = total_tokens / overall_duration if overall_duration > 0 else 0.0

        # Efficiency score (composite metric)
        efficiency_score = self._calculate_efficiency_score(
            success_rate, throughput, tokens_per_second, average_duration
        )

        # Error analysis
        error_types = defaultdict(int)
        for result in results:
            if result.error:
                error_type = self._classify_error(result.error)
                error_types[error_type] += 1

        # Resource utilization
        resource_utilization = self.max_concurrent / 10.0  # Assuming max 10 concurrent tasks

        return BenchmarkMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            success_rate=success_rate,
            total_duration=total_duration,
            average_task_duration=average_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            duration_std=duration_std,
            total_tokens=total_tokens,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            average_tokens_per_task=average_tokens_per_task,
            tokens_per_second=tokens_per_second,
            throughput=throughput,
            efficiency_score=efficiency_score,
            timeout_count=timeout_tasks,
            retry_count=sum(self.retry_counts.values()),
            error_rate=error_rate,
            concurrent_peak=self.max_concurrent,
            resource_utilization=resource_utilization,
            percentiles=percentiles,
            error_types=dict(error_types),
        )

    def calculate_comparison_metrics(self) -> ComparisonMetrics:
        """Calculate comparison metrics between baseline and tools."""
        baseline_metrics = self.calculate_metrics(TaskApproach.BASELINE)
        tools_metrics = self.calculate_metrics(TaskApproach.TOOLS)

        # Calculate improvement percentages
        token_reduction = self._calculate_reduction_percent(baseline_metrics.total_tokens, tools_metrics.total_tokens)
        time_reduction = self._calculate_reduction_percent(
            baseline_metrics.total_duration, tools_metrics.total_duration
        )
        efficiency_improvement = self._calculate_improvement_percent(
            baseline_metrics.efficiency_score, tools_metrics.efficiency_score
        )

        # Calculate statistical significance (simplified)
        baseline_durations = [
            r.duration for r in self.task_results if r.approach == TaskApproach.BASELINE and r.duration is not None
        ]
        tools_durations = [
            r.duration for r in self.task_results if r.approach == TaskApproach.TOOLS and r.duration is not None
        ]

        statistical_significance = self._calculate_statistical_significance(baseline_durations, tools_durations)

        # Calculate confidence intervals
        confidence_interval = self._calculate_confidence_intervals(baseline_durations, tools_durations)

        sample_size = min(len(baseline_durations), len(tools_durations))

        return ComparisonMetrics(
            token_reduction_percent=token_reduction,
            time_reduction_percent=time_reduction,
            efficiency_improvement_percent=efficiency_improvement,
            baseline_metrics=baseline_metrics,
            tools_metrics=tools_metrics,
            statistical_significance=statistical_significance,
            confidence_interval=confidence_interval,
            sample_size=sample_size,
        )

    def get_metrics_by_task(self) -> Dict[str, BenchmarkMetrics]:
        """Get metrics broken down by task ID."""
        metrics_by_task = {}

        # Group results by task_id
        task_groups = defaultdict(list)
        for result in self.task_results:
            task_groups[result.task_id].append(result)

        # Calculate metrics for each task
        for task_id, results in task_groups.items():
            # Create a temporary collector for this task
            temp_collector = MetricsCollector()
            temp_collector.task_results = results
            temp_collector.start_time = min(r.start_time for r in results)
            temp_collector.end_time = max(r.end_time for r in results if r.end_time is not None)

            metrics_by_task[task_id] = temp_collector.calculate_metrics()

        return metrics_by_task

    def get_metrics_by_model(self) -> Dict[str, BenchmarkMetrics]:
        """Get metrics broken down by model instance."""
        metrics_by_model = {}

        # Group results by model_instance
        model_groups = defaultdict(list)
        for result in self.task_results:
            model_groups[result.model_instance].append(result)

        # Calculate metrics for each model
        for model_instance, results in model_groups.items():
            # Create a temporary collector for this model
            temp_collector = MetricsCollector()
            temp_collector.task_results = results
            temp_collector.start_time = min(r.start_time for r in results)
            temp_collector.end_time = max(r.end_time for r in results if r.end_time is not None)

            metrics_by_model[model_instance] = temp_collector.calculate_metrics()

        return metrics_by_model

    def _calculate_efficiency_score(
        self, success_rate: float, throughput: float, tokens_per_second: float, avg_duration: float
    ) -> float:
        """Calculate composite efficiency score."""
        if avg_duration == 0:
            return 0.0

        # Normalize metrics to 0-1 scale and weight them
        success_weight = 0.4
        throughput_weight = 0.3
        token_efficiency_weight = 0.2
        speed_weight = 0.1

        # Normalize throughput (assume max reasonable throughput is 10 tasks/second)
        normalized_throughput = min(throughput / 10.0, 1.0)

        # Normalize token efficiency (assume max reasonable is 1000 tokens/second)
        normalized_token_efficiency = min(tokens_per_second / 1000.0, 1.0)

        # Speed score (lower duration is better, assume max reasonable is 60 seconds)
        speed_score = max(0.0, 1.0 - (avg_duration / 60.0))

        efficiency_score = (
            success_rate * success_weight
            + normalized_throughput * throughput_weight
            + normalized_token_efficiency * token_efficiency_weight
            + speed_score * speed_weight
        )

        return efficiency_score

    def _calculate_reduction_percent(self, baseline: float, tools: float) -> float:
        """Calculate percentage reduction (positive = improvement)."""
        if baseline == 0:
            return 0.0
        return ((baseline - tools) / baseline) * 100.0

    def _calculate_improvement_percent(self, baseline: float, tools: float) -> float:
        """Calculate percentage improvement (positive = better)."""
        if baseline == 0:
            return 0.0
        return ((tools - baseline) / baseline) * 100.0

    def _classify_error(self, error: str) -> str:
        """Classify error type for statistics."""
        error_lower = error.lower()

        if "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower:
            return "connection"
        elif "http" in error_lower:
            return "http"
        elif "json" in error_lower:
            return "json"
        elif "model" in error_lower:
            return "model"
        else:
            return "unknown"

    def _calculate_statistical_significance(self, baseline_values: List[float], tools_values: List[float]) -> float:
        """Calculate statistical significance (simplified t-test approximation)."""
        if len(baseline_values) < 2 or len(tools_values) < 2:
            return 0.0

        try:
            baseline_mean = statistics.mean(baseline_values)
            tools_mean = statistics.mean(tools_values)
            baseline_std = statistics.stdev(baseline_values)
            tools_std = statistics.stdev(tools_values)

            # Simplified t-test approximation
            pooled_std = ((baseline_std**2) + (tools_std**2)) ** 0.5
            if pooled_std == 0:
                return 0.0

            t_stat = abs(baseline_mean - tools_mean) / pooled_std

            # Convert to approximate p-value (very simplified)
            # This is not a proper statistical test but gives an indication
            return max(0.0, 1.0 - (t_stat / 5.0))
        except:
            return 0.0

    def _calculate_confidence_intervals(
        self, baseline_values: List[float], tools_values: List[float]
    ) -> Dict[str, float]:
        """Calculate confidence intervals for the difference."""
        if len(baseline_values) < 2 or len(tools_values) < 2:
            return {}

        try:
            baseline_mean = statistics.mean(baseline_values)
            tools_mean = statistics.mean(tools_values)
            baseline_std = statistics.stdev(baseline_values)
            tools_std = statistics.stdev(tools_values)

            # 95% confidence interval approximation
            margin_of_error = (
                1.96 * ((baseline_std**2 / len(baseline_values)) + (tools_std**2 / len(tools_values))) ** 0.5
            )

            difference = baseline_mean - tools_mean

            return {
                "lower_bound": difference - margin_of_error,
                "upper_bound": difference + margin_of_error,
                "difference": difference,
            }
        except:
            return {}

    def reset(self) -> None:
        """Reset the metrics collector."""
        self.task_results.clear()
        self.start_time = None
        self.end_time = None
        self.concurrent_tasks = 0
        self.max_concurrent = 0
        self.retry_counts.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics state."""
        return {
            "total_results": len(self.task_results),
            "collection_active": self.start_time is not None and self.end_time is None,
            "concurrent_tasks": self.concurrent_tasks,
            "max_concurrent": self.max_concurrent,
            "total_retries": sum(self.retry_counts.values()),
            "collection_duration": (self.end_time or time.time()) - (self.start_time or time.time())
            if self.start_time
            else 0,
        }
