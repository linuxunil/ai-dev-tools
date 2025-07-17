"""
Metrics Collector - Token usage and execution time measurement system

Designed to measure the efficiency gains of AI development tools by comparing:
- Baseline (no tools): Manual AI workflows without our tools
- Current iteration: Using our AI-first tools with exit codes
- Future changes: Performance improvements and optimizations

Key metrics:
- Token usage: Input/output tokens for AI decision making
- Execution time: Wall clock time for completing workflows
- Success rate: Percentage of successful operations
- Efficiency ratio: Token savings and time improvements
"""

import json
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, ContextManager, Dict, List, Optional

# import psutil  # Optional dependency for memory monitoring


class WorkflowType(Enum):
    """Types of AI workflows we measure"""

    BASELINE_MANUAL = "baseline_manual"  # Manual AI workflow without tools
    PATTERN_ANALYSIS = "pattern_analysis"  # Using pattern scanner
    SAFETY_CHECK = "safety_check"  # Using safety checker
    CONTEXT_ANALYSIS = "context_analysis"  # Using context analyzer
    SYSTEMATIC_FIX = "systematic_fix"  # Using systematic fix workflow
    PROJECT_ANALYSIS = "project_analysis"  # Using AI Helper analyze
    CHANGE_PLANNING = "change_planning"  # Using AI Helper plan
    UNIFIED_WORKFLOW = "unified_workflow"  # Using AI Helper orchestration


class MetricType(Enum):
    """Types of metrics we collect"""

    TOKEN_INPUT = "token_input"  # Tokens sent to AI
    TOKEN_OUTPUT = "token_output"  # Tokens received from AI
    EXECUTION_TIME = "execution_time"  # Wall clock time in seconds
    MEMORY_PEAK = "memory_peak"  # Peak memory usage in MB
    FILES_PROCESSED = "files_processed"  # Number of files analyzed
    SUCCESS_RATE = "success_rate"  # Percentage of successful operations


@dataclass
class MetricPoint:
    """Single metric measurement point"""

    timestamp: datetime
    workflow_type: WorkflowType
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "workflow_type": self.workflow_type.value,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowMetrics:
    """Complete metrics for a workflow execution"""

    workflow_type: WorkflowType
    start_time: datetime
    end_time: datetime
    execution_time: float
    token_input: int
    token_output: int
    memory_peak: float
    files_processed: int
    success: bool
    metadata: Dict[str, Any]

    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output)"""
        return self.token_input + self.token_output

    @property
    def tokens_per_second(self) -> float:
        """Token processing rate"""
        if self.execution_time > 0:
            return self.total_tokens / self.execution_time
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "workflow_type": self.workflow_type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "execution_time": self.execution_time,
            "token_input": self.token_input,
            "token_output": self.token_output,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "memory_peak": self.memory_peak,
            "files_processed": self.files_processed,
            "success": self.success,
            "metadata": self.metadata,
        }


class MetricsCollector:
    """
    Thread-safe metrics collection system for AI workflow performance

    Designed to measure token efficiency and execution time improvements
    across different workflow types and tool iterations.
    """

    def __init__(self, output_dir: str = ".ai_metrics"):
        """
        Initialize metrics collector

        Args:
            output_dir: Directory to store metrics data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self._metrics: List[MetricPoint] = []
        self._workflows: List[WorkflowMetrics] = []
        self._lock = threading.Lock()
        self._current_workflow: Optional[Dict[str, Any]] = None

        # Process monitoring (optional)
        try:
            import psutil

            self._process = psutil.Process()
            self._baseline_memory = self._process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            self._process = None
            self._baseline_memory = 0

    def record_metric(
        self,
        workflow_type: WorkflowType,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a single metric point

        Args:
            workflow_type: Type of workflow being measured
            metric_type: Type of metric being recorded
            value: Metric value
            metadata: Additional context information
        """
        with self._lock:
            metric = MetricPoint(
                timestamp=datetime.now(timezone.utc),
                workflow_type=workflow_type,
                metric_type=metric_type,
                value=value,
                metadata=metadata or {},
            )
            self._metrics.append(metric)

    @contextmanager
    def measure_workflow(
        self, workflow_type: WorkflowType, metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for measuring complete workflow execution

        Args:
            workflow_type: Type of workflow being measured
            metadata: Additional context information

        Yields:
            WorkflowContext for recording workflow-specific metrics
        """
        start_time = datetime.now(timezone.utc)
        start_memory = 0
        if self._process:
            start_memory = self._process.memory_info().rss / 1024 / 1024  # MB

        context = WorkflowContext(self, workflow_type, metadata or {})
        success = False

        try:
            yield context
            success = True
        except Exception:
            success = False
            raise
        finally:
            end_time = datetime.now(timezone.utc)
            end_memory = start_memory
            if self._process:
                end_memory = self._process.memory_info().rss / 1024 / 1024  # MB
            execution_time = (end_time - start_time).total_seconds()

            workflow_metrics = WorkflowMetrics(
                workflow_type=workflow_type,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                token_input=context.token_input,
                token_output=context.token_output,
                memory_peak=max(end_memory - self._baseline_memory, 0),
                files_processed=context.files_processed,
                success=success,
                metadata=context.metadata,
            )

            with self._lock:
                self._workflows.append(workflow_metrics)

    def get_metrics_summary(
        self, workflow_type: Optional[WorkflowType] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for collected metrics

        Args:
            workflow_type: Filter by specific workflow type

        Returns:
            Summary statistics dictionary
        """
        with self._lock:
            workflows = self._workflows
            if workflow_type:
                workflows = [w for w in workflows if w.workflow_type == workflow_type]

        if not workflows:
            return {"error": "No metrics collected"}

        # Calculate summary statistics
        total_workflows = len(workflows)
        successful_workflows = len([w for w in workflows if w.success])
        success_rate = (successful_workflows / total_workflows) * 100

        execution_times = [w.execution_time for w in workflows]
        token_inputs = [w.token_input for w in workflows]
        token_outputs = [w.token_output for w in workflows]
        total_tokens = [w.total_tokens for w in workflows]

        return {
            "workflow_type": workflow_type.value if workflow_type else "all",
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "success_rate": success_rate,
            "execution_time": {
                "min": min(execution_times),
                "max": max(execution_times),
                "avg": sum(execution_times) / len(execution_times),
                "total": sum(execution_times),
            },
            "tokens": {
                "input_avg": sum(token_inputs) / len(token_inputs),
                "output_avg": sum(token_outputs) / len(token_outputs),
                "total_avg": sum(total_tokens) / len(total_tokens),
                "total_consumed": sum(total_tokens),
            },
            "efficiency": {
                "tokens_per_second": sum(w.tokens_per_second for w in workflows)
                / len(workflows),
                "files_per_second": sum(
                    w.files_processed / w.execution_time
                    for w in workflows
                    if w.execution_time > 0
                )
                / len(workflows),
            },
        }

    def compare_workflows(
        self, baseline_type: WorkflowType, comparison_type: WorkflowType
    ) -> Dict[str, Any]:
        """
        Compare performance between two workflow types

        Args:
            baseline_type: Baseline workflow type
            comparison_type: Comparison workflow type

        Returns:
            Comparison analysis dictionary
        """
        baseline_summary = self.get_metrics_summary(baseline_type)
        comparison_summary = self.get_metrics_summary(comparison_type)

        if "error" in baseline_summary or "error" in comparison_summary:
            return {"error": "Insufficient data for comparison"}

        # Calculate improvements
        time_improvement = (
            (
                baseline_summary["execution_time"]["avg"]
                - comparison_summary["execution_time"]["avg"]
            )
            / baseline_summary["execution_time"]["avg"]
            * 100
        )

        token_improvement = (
            (
                baseline_summary["tokens"]["total_avg"]
                - comparison_summary["tokens"]["total_avg"]
            )
            / baseline_summary["tokens"]["total_avg"]
            * 100
        )

        efficiency_improvement = (
            (
                comparison_summary["efficiency"]["tokens_per_second"]
                - baseline_summary["efficiency"]["tokens_per_second"]
            )
            / baseline_summary["efficiency"]["tokens_per_second"]
            * 100
        )

        return {
            "baseline": baseline_summary,
            "comparison": comparison_summary,
            "improvements": {
                "execution_time_percent": time_improvement,
                "token_usage_percent": token_improvement,
                "efficiency_percent": efficiency_improvement,
                "success_rate_change": comparison_summary["success_rate"]
                - baseline_summary["success_rate"],
            },
            "verdict": {
                "faster": time_improvement > 0,
                "more_token_efficient": token_improvement > 0,
                "more_efficient_overall": efficiency_improvement > 0,
            },
        }

    def export_metrics(self, filename: Optional[str] = None) -> Path:
        """
        Export all collected metrics to JSON file

        Args:
            filename: Output filename (default: timestamp-based)

        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_metrics_{timestamp}.json"

        output_path = self.output_dir / filename

        with self._lock:
            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_metrics": len(self._metrics),
                "total_workflows": len(self._workflows),
                "metrics": [m.to_dict() for m in self._metrics],
                "workflows": [w.to_dict() for w in self._workflows],
                "summary": self.get_metrics_summary(),
            }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return output_path

    def clear_metrics(self) -> None:
        """Clear all collected metrics"""
        with self._lock:
            self._metrics.clear()
            self._workflows.clear()


class WorkflowContext:
    """Context object for recording workflow-specific metrics"""

    def __init__(
        self,
        collector: MetricsCollector,
        workflow_type: WorkflowType,
        metadata: Dict[str, Any],
    ):
        self.collector = collector
        self.workflow_type = workflow_type
        self.metadata = metadata
        self.token_input = 0
        self.token_output = 0
        self.files_processed = 0

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage for this workflow"""
        self.token_input += input_tokens
        self.token_output += output_tokens

    def record_files_processed(self, count: int) -> None:
        """Record number of files processed"""
        self.files_processed += count

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to this workflow"""
        self.metadata[key] = value


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def measure_workflow(
    workflow_type: WorkflowType, metadata: Optional[Dict[str, Any]] = None
) -> ContextManager[WorkflowContext]:
    """Convenience function for measuring workflows"""
    return get_metrics_collector().measure_workflow(workflow_type, metadata)


def record_metric(
    workflow_type: WorkflowType,
    metric_type: MetricType,
    value: float,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function for recording metrics"""
    get_metrics_collector().record_metric(workflow_type, metric_type, value, metadata)
