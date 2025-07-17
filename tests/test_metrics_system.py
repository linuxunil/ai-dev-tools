"""
Tests for the metrics collection system

Tests the core metrics collection, baseline simulation, and benchmarking
functionality for measuring token usage and execution time improvements.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from ai_dev_tools.core.baseline_simulator import BaselineSimulator
from ai_dev_tools.core.metrics_collector import (
    MetricsCollector,
    MetricType,
    WorkflowMetrics,
    WorkflowType,
)


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.collector = MetricsCollector(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test MetricsCollector initialization"""
        assert self.collector.output_dir == Path(self.temp_dir)
        assert len(self.collector._metrics) == 0
        assert len(self.collector._workflows) == 0

    def test_record_metric(self):
        """Test recording individual metrics"""
        self.collector.record_metric(
            WorkflowType.PATTERN_ANALYSIS,
            MetricType.TOKEN_INPUT,
            100.0,
            {"test": "data"},
        )

        assert len(self.collector._metrics) == 1
        metric = self.collector._metrics[0]
        assert metric.workflow_type == WorkflowType.PATTERN_ANALYSIS
        assert metric.metric_type == MetricType.TOKEN_INPUT
        assert metric.value == 100.0
        assert metric.metadata["test"] == "data"

    def test_measure_workflow_success(self):
        """Test successful workflow measurement"""
        with self.collector.measure_workflow(WorkflowType.PATTERN_ANALYSIS, {"test": "metadata"}) as context:
            context.record_tokens(50, 25)
            context.record_files_processed(5)
            context.add_metadata("result", "success")

        assert len(self.collector._workflows) == 1
        workflow = self.collector._workflows[0]
        assert workflow.workflow_type == WorkflowType.PATTERN_ANALYSIS
        assert workflow.token_input == 50
        assert workflow.token_output == 25
        assert workflow.total_tokens == 75
        assert workflow.files_processed == 5
        assert workflow.success is True
        assert workflow.metadata["test"] == "metadata"
        assert workflow.metadata["result"] == "success"

    def test_measure_workflow_failure(self):
        """Test workflow measurement with exception"""
        with pytest.raises(ValueError):
            with self.collector.measure_workflow(WorkflowType.PATTERN_ANALYSIS) as context:
                context.record_tokens(50, 25)
                raise ValueError("Test error")

        assert len(self.collector._workflows) == 1
        workflow = self.collector._workflows[0]
        assert workflow.success is False

    def test_get_metrics_summary(self):
        """Test metrics summary generation"""
        # Add some test workflows
        with self.collector.measure_workflow(WorkflowType.PATTERN_ANALYSIS) as context:
            context.record_tokens(100, 50)
            context.record_files_processed(10)

        with self.collector.measure_workflow(WorkflowType.SAFETY_CHECK) as context:
            context.record_tokens(200, 100)
            context.record_files_processed(5)

        summary = self.collector.get_metrics_summary()

        assert summary["total_workflows"] == 2
        assert summary["successful_workflows"] == 2
        assert summary["success_rate"] == 100.0
        assert summary["tokens"]["total_avg"] == 225.0  # (150 + 300) / 2

    def test_compare_workflows(self):
        """Test workflow comparison"""
        # Add baseline workflow
        with self.collector.measure_workflow(WorkflowType.BASELINE_MANUAL) as context:
            context.record_tokens(1000, 500)  # High token usage
            context.record_files_processed(20)

        # Add current workflow
        with self.collector.measure_workflow(WorkflowType.PATTERN_ANALYSIS) as context:
            context.record_tokens(100, 50)  # Low token usage
            context.record_files_processed(5)

        comparison = self.collector.compare_workflows(WorkflowType.BASELINE_MANUAL, WorkflowType.PATTERN_ANALYSIS)

        assert "improvements" in comparison
        assert comparison["verdict"]["more_token_efficient"] is True

    def test_export_metrics(self):
        """Test metrics export"""
        # Add some test data
        self.collector.record_metric(WorkflowType.PATTERN_ANALYSIS, MetricType.TOKEN_INPUT, 100.0)

        export_path = self.collector.export_metrics("test_export.json")

        assert export_path.exists()
        assert export_path.name == "test_export.json"

        # Verify export content
        import json

        with open(export_path) as f:
            data = json.load(f)

        assert "export_timestamp" in data
        assert data["total_metrics"] == 1
        assert len(data["metrics"]) == 1

    def test_clear_metrics(self):
        """Test clearing metrics"""
        # Add some data
        self.collector.record_metric(WorkflowType.PATTERN_ANALYSIS, MetricType.TOKEN_INPUT, 100.0)

        assert len(self.collector._metrics) == 1

        self.collector.clear_metrics()

        assert len(self.collector._metrics) == 0
        assert len(self.collector._workflows) == 0


class TestBaselineSimulator:
    """Test BaselineSimulator functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.collector = MetricsCollector(self.temp_dir)
        self.simulator = BaselineSimulator(self.collector)

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test BaselineSimulator initialization"""
        assert self.simulator.metrics_collector == self.collector
        assert WorkflowType.PATTERN_ANALYSIS in self.simulator.SCENARIOS

    def test_simulate_workflow(self):
        """Test workflow simulation"""
        result = self.simulator.simulate_workflow(
            WorkflowType.PATTERN_ANALYSIS,
            add_variance=False,  # Disable variance for predictable testing
        )

        assert result["workflow_type"] == WorkflowType.PATTERN_ANALYSIS.value
        assert "scenario" in result
        assert "metrics" in result
        assert "efficiency" in result

        metrics = result["metrics"]
        assert "total_tokens" in metrics
        assert "duration_seconds" in metrics
        assert "success" in metrics

    def test_simulate_workflow_with_variance(self):
        """Test workflow simulation with variance"""
        result1 = self.simulator.simulate_workflow(WorkflowType.PATTERN_ANALYSIS)
        result2 = self.simulator.simulate_workflow(WorkflowType.PATTERN_ANALYSIS)

        # Results should be different due to variance
        assert result1["metrics"]["total_tokens"] != result2["metrics"]["total_tokens"]

    def test_run_baseline_suite(self):
        """Test running complete baseline suite"""
        results = self.simulator.run_baseline_suite(iterations=2)

        assert "project_path" in results
        assert "iterations" in results
        assert "workflows" in results
        assert "summary" in results

        # Should have results for multiple workflow types
        assert len(results["workflows"]) > 0

        summary = results["summary"]
        assert "total_workflows" in summary
        assert "success_rate" in summary
        assert "total_tokens" in summary

    def test_compare_with_current(self):
        """Test comparison with current metrics"""
        # Run baseline simulation
        baseline_results = self.simulator.run_baseline_suite(iterations=1)

        # Mock current metrics (better performance)
        current_metrics = {
            "tokens": {"total_avg": 100},  # Much lower than baseline
            "execution_time": {"avg": 5.0},  # Much faster than baseline
            "efficiency": {"tokens_per_second": 20.0},
            "success_rate": 95.0,
        }

        comparison = self.simulator.compare_with_current(current_metrics, baseline_results)

        assert "baseline" in comparison
        assert "current" in comparison
        assert "improvements" in comparison
        assert "verdict" in comparison
        assert "roi_analysis" in comparison

        # Should show improvements
        verdict = comparison["verdict"]
        assert verdict["more_token_efficient"] is True
        assert verdict["faster"] is True


class TestWorkflowMetrics:
    """Test WorkflowMetrics data class"""

    def test_workflow_metrics_properties(self):
        """Test WorkflowMetrics calculated properties"""
        from datetime import datetime, timezone

        start_time = datetime.now(timezone.utc)
        end_time = start_time

        metrics = WorkflowMetrics(
            workflow_type=WorkflowType.PATTERN_ANALYSIS,
            start_time=start_time,
            end_time=end_time,
            execution_time=10.0,
            token_input=100,
            token_output=50,
            memory_peak=25.0,
            files_processed=5,
            success=True,
            metadata={"test": "data"},
        )

        assert metrics.total_tokens == 150
        assert metrics.tokens_per_second == 15.0

    def test_workflow_metrics_to_dict(self):
        """Test WorkflowMetrics serialization"""
        from datetime import datetime, timezone

        start_time = datetime.now(timezone.utc)
        end_time = start_time

        metrics = WorkflowMetrics(
            workflow_type=WorkflowType.PATTERN_ANALYSIS,
            start_time=start_time,
            end_time=end_time,
            execution_time=10.0,
            token_input=100,
            token_output=50,
            memory_peak=25.0,
            files_processed=5,
            success=True,
            metadata={"test": "data"},
        )

        result_dict = metrics.to_dict()

        assert result_dict["workflow_type"] == WorkflowType.PATTERN_ANALYSIS.value
        assert result_dict["execution_time"] == 10.0
        assert result_dict["token_input"] == 100
        assert result_dict["token_output"] == 50
        assert result_dict["total_tokens"] == 150
        assert result_dict["tokens_per_second"] == 15.0
        assert result_dict["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])
