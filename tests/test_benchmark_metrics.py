"""
Tests for benchmark metrics collection and analysis.
"""

import pytest
import asyncio
import statistics
from unittest.mock import Mock, AsyncMock

from ai_dev_tools.benchmark.metrics import (
    BenchmarkMetrics,
    ComparisonMetrics,
    MetricsCollector
)
from ai_dev_tools.benchmark.tasks import (
    TaskResult,
    TaskStatus,
    TaskApproach
)


class TestBenchmarkMetrics:
    """Test BenchmarkMetrics class."""
    
    def test_benchmark_metrics_creation(self):
        """Test basic benchmark metrics creation."""
        metrics = BenchmarkMetrics(
            total_tasks=100,
            completed_tasks=95,
            failed_tasks=5,
            success_rate=0.95,
            total_duration=120.5,
            total_tokens=5000
        )
        
        assert metrics.total_tasks == 100
        assert metrics.completed_tasks == 95
        assert metrics.failed_tasks == 5
        assert metrics.success_rate == 0.95
        assert metrics.total_duration == 120.5
        assert metrics.total_tokens == 5000
        assert metrics.timeout_count == 0
        assert metrics.retry_count == 0
        assert metrics.error_rate == 0.0
        assert metrics.concurrent_peak == 0
    
    def test_benchmark_metrics_to_dict(self):
        """Test converting benchmark metrics to dictionary."""
        metrics = BenchmarkMetrics(
            total_tasks=50,
            completed_tasks=45,
            failed_tasks=5,
            success_rate=0.9,
            total_duration=60.0,
            average_task_duration=1.2,
            total_tokens=2500,
            throughput=0.75,
            efficiency_score=0.85
        )
        
        metrics_dict = metrics.to_dict()
        
        assert metrics_dict["total_tasks"] == 50
        assert metrics_dict["completed_tasks"] == 45
        assert metrics_dict["failed_tasks"] == 5
        assert metrics_dict["success_rate"] == 0.9
        assert metrics_dict["total_duration"] == 60.0
        assert metrics_dict["average_task_duration"] == 1.2
        assert metrics_dict["total_tokens"] == 2500
        assert metrics_dict["throughput"] == 0.75
        assert metrics_dict["efficiency_score"] == 0.85


class TestComparisonMetrics:
    """Test ComparisonMetrics class."""
    
    def test_comparison_metrics_creation(self):
        """Test basic comparison metrics creation."""
        baseline_metrics = BenchmarkMetrics(
            total_tasks=20,
            completed_tasks=20,
            total_duration=100.0,
            total_tokens=4000
        )
        
        tools_metrics = BenchmarkMetrics(
            total_tasks=20,
            completed_tasks=20,
            total_duration=80.0,
            total_tokens=3000
        )
        
        comparison = ComparisonMetrics(
            token_reduction_percent=25.0,
            time_reduction_percent=20.0,
            efficiency_improvement_percent=15.0,
            baseline_metrics=baseline_metrics,
            tools_metrics=tools_metrics,
            sample_size=20
        )
        
        assert comparison.token_reduction_percent == 25.0
        assert comparison.time_reduction_percent == 20.0
        assert comparison.efficiency_improvement_percent == 15.0
        assert comparison.sample_size == 20
        assert comparison.baseline_metrics == baseline_metrics
        assert comparison.tools_metrics == tools_metrics
    
    def test_comparison_metrics_to_dict(self):
        """Test converting comparison metrics to dictionary."""
        baseline_metrics = BenchmarkMetrics(total_tasks=10, total_tokens=1000)
        tools_metrics = BenchmarkMetrics(total_tasks=10, total_tokens=800)
        
        comparison = ComparisonMetrics(
            token_reduction_percent=20.0,
            time_reduction_percent=15.0,
            baseline_metrics=baseline_metrics,
            tools_metrics=tools_metrics,
            sample_size=10
        )
        
        comparison_dict = comparison.to_dict()
        
        assert comparison_dict["token_reduction_percent"] == 20.0
        assert comparison_dict["time_reduction_percent"] == 15.0
        assert comparison_dict["sample_size"] == 10
        assert "baseline_metrics" in comparison_dict
        assert "tools_metrics" in comparison_dict
        assert isinstance(comparison_dict["baseline_metrics"], dict)
        assert isinstance(comparison_dict["tools_metrics"], dict)


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        
        assert len(collector.task_results) == 0
        assert collector.start_time is None
        assert collector.end_time is None
        assert collector.concurrent_tasks == 0
        assert collector.max_concurrent == 0
        assert len(collector.retry_counts) == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_collection(self):
        """Test starting and stopping metrics collection."""
        collector = MetricsCollector()
        
        assert collector.start_time is None
        assert collector.end_time is None
        
        await collector.start_collection()
        
        assert collector.start_time is not None
        assert collector.end_time is None
        
        await collector.stop_collection()
        
        assert collector.start_time is not None
        assert collector.end_time is not None
        assert collector.end_time >= collector.start_time
    
    @pytest.mark.asyncio
    async def test_add_task_result(self):
        """Test adding task results."""
        collector = MetricsCollector()
        
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.BASELINE,
            model_instance="test_model",
            status=TaskStatus.COMPLETED,
            start_time=1000.0
        )
        
        result.mark_completed("Test response", 100, 200)
        
        await collector.add_task_result(result)
        
        assert len(collector.task_results) == 1
        assert collector.task_results[0] == result
    
    @pytest.mark.asyncio
    async def test_record_retry(self):
        """Test recording retry attempts."""
        collector = MetricsCollector()
        
        await collector.record_retry("task_1")
        await collector.record_retry("task_1")
        await collector.record_retry("task_2")
        
        assert collector.retry_counts["task_1"] == 2
        assert collector.retry_counts["task_2"] == 1
    
    def test_track_concurrent_task(self):
        """Test tracking concurrent task execution."""
        collector = MetricsCollector()
        
        assert collector.concurrent_tasks == 0
        assert collector.max_concurrent == 0
        
        with collector.track_concurrent_task():
            assert collector.concurrent_tasks == 1
            assert collector.max_concurrent == 1
            
            with collector.track_concurrent_task():
                assert collector.concurrent_tasks == 2
                assert collector.max_concurrent == 2
            
            assert collector.concurrent_tasks == 1
            assert collector.max_concurrent == 2
        
        assert collector.concurrent_tasks == 0
        assert collector.max_concurrent == 2
    
    def test_calculate_metrics_empty(self):
        """Test calculating metrics with no results."""
        collector = MetricsCollector()
        
        metrics = collector.calculate_metrics()
        
        assert metrics.total_tasks == 0
        assert metrics.completed_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.success_rate == 0.0
        assert metrics.total_duration == 0.0
        assert metrics.total_tokens == 0
    
    def test_calculate_metrics_with_results(self):
        """Test calculating metrics with task results."""
        collector = MetricsCollector()
        
        # Create some completed results
        for i in range(10):
            result = TaskResult(
                task_id=f"task_{i}",
                approach=TaskApproach.BASELINE,
                model_instance="test_model",
                status=TaskStatus.COMPLETED,
                start_time=1000.0 + i
            )
            result.mark_completed(f"Response {i}", 100, 150)
            collector.task_results.append(result)
        
        # Create some failed results
        for i in range(2):
            result = TaskResult(
                task_id=f"failed_task_{i}",
                approach=TaskApproach.TOOLS,
                model_instance="test_model",
                status=TaskStatus.FAILED,
                start_time=1000.0 + i
            )
            result.mark_failed(f"Error {i}")
            collector.task_results.append(result)
        
        collector.start_time = 1000.0
        collector.end_time = 1100.0
        
        metrics = collector.calculate_metrics()
        
        assert metrics.total_tasks == 12
        assert metrics.completed_tasks == 10
        assert metrics.failed_tasks == 2
        assert metrics.success_rate == 10/12
        assert metrics.error_rate == 2/12
        assert metrics.total_tokens == 10 * 250  # 10 completed * 250 tokens each
        assert metrics.total_input_tokens == 10 * 100
        assert metrics.total_output_tokens == 10 * 150
        assert metrics.average_tokens_per_task == 250.0
    
    def test_calculate_metrics_with_filter(self):
        """Test calculating metrics with approach filter."""
        collector = MetricsCollector()
        
        # Add baseline results
        for i in range(5):
            result = TaskResult(
                task_id=f"baseline_task_{i}",
                approach=TaskApproach.BASELINE,
                model_instance="test_model",
                status=TaskStatus.COMPLETED,
                start_time=1000.0 + i
            )
            result.mark_completed(f"Baseline response {i}", 200, 300)
            collector.task_results.append(result)
        
        # Add tools results
        for i in range(3):
            result = TaskResult(
                task_id=f"tools_task_{i}",
                approach=TaskApproach.TOOLS,
                model_instance="test_model",
                status=TaskStatus.COMPLETED,
                start_time=1000.0 + i
            )
            result.mark_completed(f"Tools response {i}", 150, 200)
            collector.task_results.append(result)
        
        collector.start_time = 1000.0
        collector.end_time = 1100.0
        
        # Test baseline filter
        baseline_metrics = collector.calculate_metrics(TaskApproach.BASELINE)
        assert baseline_metrics.total_tasks == 5
        assert baseline_metrics.completed_tasks == 5
        assert baseline_metrics.total_tokens == 5 * 500  # 5 * (200 + 300)
        
        # Test tools filter
        tools_metrics = collector.calculate_metrics(TaskApproach.TOOLS)
        assert tools_metrics.total_tasks == 3
        assert tools_metrics.completed_tasks == 3
        assert tools_metrics.total_tokens == 3 * 350  # 3 * (150 + 200)
    
    def test_calculate_comparison_metrics(self):
        """Test calculating comparison metrics."""
        collector = MetricsCollector()
        
        # Add baseline results (slower, more tokens)
        for i in range(5):
            result = TaskResult(
                task_id=f"baseline_task_{i}",
                approach=TaskApproach.BASELINE,
                model_instance="test_model",
                status=TaskStatus.COMPLETED,
                start_time=1000.0 + i
            )
            result.duration = 10.0  # Slower
            result.mark_completed(f"Baseline response {i}", 200, 400)  # More tokens
            collector.task_results.append(result)
        
        # Add tools results (faster, fewer tokens)
        for i in range(5):
            result = TaskResult(
                task_id=f"tools_task_{i}",
                approach=TaskApproach.TOOLS,
                model_instance="test_model",
                status=TaskStatus.COMPLETED,
                start_time=1000.0 + i
            )
            result.duration = 6.0  # Faster
            result.mark_completed(f"Tools response {i}", 150, 250)  # Fewer tokens
            collector.task_results.append(result)
        
        collector.start_time = 1000.0
        collector.end_time = 1100.0
        
        comparison = collector.calculate_comparison_metrics()
        
        assert comparison.sample_size == 5
        assert comparison.token_reduction_percent > 0  # Tools should use fewer tokens
        assert comparison.time_reduction_percent > 0   # Tools should be faster
        assert comparison.baseline_metrics.total_tasks == 5
        assert comparison.tools_metrics.total_tasks == 5
        assert comparison.baseline_metrics.total_tokens > comparison.tools_metrics.total_tokens
    
    def test_get_metrics_by_task(self):
        """Test getting metrics broken down by task."""
        collector = MetricsCollector()
        
        # Add results for multiple tasks
        for task_id in ["task_a", "task_b", "task_c"]:
            for i in range(3):
                result = TaskResult(
                    task_id=task_id,
                    approach=TaskApproach.BASELINE,
                    model_instance="test_model",
                    status=TaskStatus.COMPLETED,
                    start_time=1000.0 + i
                )
                result.mark_completed(f"Response {i}", 100, 150)
                collector.task_results.append(result)
        
        metrics_by_task = collector.get_metrics_by_task()
        
        assert len(metrics_by_task) == 3
        assert "task_a" in metrics_by_task
        assert "task_b" in metrics_by_task
        assert "task_c" in metrics_by_task
        
        for task_id, metrics in metrics_by_task.items():
            assert metrics.total_tasks == 3
            assert metrics.completed_tasks == 3
            assert metrics.total_tokens == 3 * 250
    
    def test_get_metrics_by_model(self):
        """Test getting metrics broken down by model."""
        collector = MetricsCollector()
        
        # Add results for multiple models
        for model_name in ["model_a", "model_b"]:
            for i in range(4):
                result = TaskResult(
                    task_id=f"task_{i}",
                    approach=TaskApproach.TOOLS,
                    model_instance=model_name,
                    status=TaskStatus.COMPLETED,
                    start_time=1000.0 + i
                )
                result.mark_completed(f"Response {i}", 120, 180)
                collector.task_results.append(result)
        
        metrics_by_model = collector.get_metrics_by_model()
        
        assert len(metrics_by_model) == 2
        assert "model_a" in metrics_by_model
        assert "model_b" in metrics_by_model
        
        for model_name, metrics in metrics_by_model.items():
            assert metrics.total_tasks == 4
            assert metrics.completed_tasks == 4
            assert metrics.total_tokens == 4 * 300
    
    def test_reset(self):
        """Test resetting the metrics collector."""
        collector = MetricsCollector()
        
        # Add some data
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.BASELINE,
            model_instance="test_model",
            status=TaskStatus.COMPLETED,
            start_time=1000.0
        )
        collector.task_results.append(result)
        collector.start_time = 1000.0
        collector.end_time = 1100.0
        collector.concurrent_tasks = 2
        collector.max_concurrent = 5
        collector.retry_counts["task_1"] = 3
        
        # Reset
        collector.reset()
        
        assert len(collector.task_results) == 0
        assert collector.start_time is None
        assert collector.end_time is None
        assert collector.concurrent_tasks == 0
        assert collector.max_concurrent == 0
        assert len(collector.retry_counts) == 0
    
    def test_get_summary(self):
        """Test getting collector summary."""
        collector = MetricsCollector()
        
        # Add some data
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.BASELINE,
            model_instance="test_model",
            status=TaskStatus.COMPLETED,
            start_time=1000.0
        )
        collector.task_results.append(result)
        collector.start_time = 1000.0
        collector.concurrent_tasks = 2
        collector.max_concurrent = 3
        collector.retry_counts["task_1"] = 2
        
        summary = collector.get_summary()
        
        assert summary["total_results"] == 1
        assert summary["collection_active"] is True  # No end_time set
        assert summary["concurrent_tasks"] == 2
        assert summary["max_concurrent"] == 3
        assert summary["total_retries"] == 2
        assert summary["collection_duration"] > 0


if __name__ == "__main__":
    pytest.main([__file__])