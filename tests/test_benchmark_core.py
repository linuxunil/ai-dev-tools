"""
Tests for the core benchmarking framework.

Tests the new simplified benchmarking API and core functionality.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from typing import Dict, Any

from ai_dev_tools.benchmark.core import (
    BenchmarkResult,
    BenchmarkRunner,
    quick_benchmark,
    compare_profiles,
    batch_benchmark
)
from ai_dev_tools.benchmark.config import BenchmarkConfig, HardwareProfile, ModelInstance
from ai_dev_tools.benchmark.tasks import BenchmarkTask, TaskRegistry


class TestBenchmarkResult:
    """Test the BenchmarkResult model."""
    
    def test_benchmark_result_creation(self):
        """Test creating a basic benchmark result."""
        result = BenchmarkResult(
            benchmark_id="test_123",
            profile="medium",
            tasks_executed=5,
            success_rate=0.85,
            avg_duration=2.5,
            total_tokens=1000,
            tokens_per_second=400.0,
            status="completed",
            start_time=1234567890.0,
            end_time=1234567900.0
        )
        
        assert result.benchmark_id == "test_123"
        assert result.profile == "medium"
        assert result.tasks_executed == 5
        assert result.success_rate == 0.85
        assert result.avg_duration == 2.5
        assert result.total_tokens == 1000
        assert result.tokens_per_second == 400.0
        assert result.status == "completed"
        assert result.error_message is None
        
    def test_benchmark_result_with_error(self):
        """Test creating a benchmark result with error."""
        result = BenchmarkResult(
            benchmark_id="test_failed",
            profile="light",
            tasks_executed=0,
            success_rate=0.0,
            avg_duration=0.0,
            total_tokens=0,
            tokens_per_second=0.0,
            status="failed",
            error_message="Connection timeout",
            start_time=1234567890.0,
            end_time=1234567895.0
        )
        
        assert result.status == "failed"
        assert result.error_message == "Connection timeout"
        assert result.success_rate == 0.0
        
    def test_benchmark_result_to_dict(self):
        """Test converting benchmark result to dictionary."""
        result = BenchmarkResult(
            benchmark_id="test_dict",
            profile="heavy",
            tasks_executed=3,
            success_rate=1.0,
            avg_duration=1.5,
            total_tokens=500,
            tokens_per_second=333.33,
            token_reduction_percent=25.0,
            time_reduction_percent=40.0,
            status="completed",
            start_time=1234567890.0,
            end_time=1234567895.0
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["benchmark_id"] == "test_dict"
        assert result_dict["profile"] == "heavy"
        assert result_dict["tasks_executed"] == 3
        assert result_dict["success_rate"] == 1.0
        assert result_dict["token_reduction_percent"] == 25.0
        assert result_dict["time_reduction_percent"] == 40.0
        assert result_dict["status"] == "completed"


class TestBenchmarkRunner:
    """Test the BenchmarkRunner class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock benchmark configuration."""
        config = Mock(spec=BenchmarkConfig)
        config.output_directory = Path("/tmp/benchmark_results")
        config.get_sample_size.return_value = 3
        config.validate_runtime.return_value = []
        config.batch_configurations = {
            "quick": Mock(
                name="quick",
                profile=HardwareProfile.LIGHT,
                sample_size=2,
                timeout=300
            )
        }
        config.profiles = {
            HardwareProfile.LIGHT: [
                ModelInstance(name="small", model="llama3.2:1b", port=11434)
            ],
            HardwareProfile.MEDIUM: [
                ModelInstance(name="small", model="llama3.2:1b", port=11434),
                ModelInstance(name="medium", model="llama3.2:3b", port=11435)
            ]
        }
        return config
    
    @pytest.fixture
    def mock_task_registry(self):
        """Create a mock task registry."""
        registry = Mock(spec=TaskRegistry)
        registry.get_all_tasks.return_value = [
            Mock(task_id="task1", name="Task 1", workflow_type=Mock(value="safety_check")),
            Mock(task_id="task2", name="Task 2", workflow_type=Mock(value="pattern_analysis")),
            Mock(task_id="task3", name="Task 3", workflow_type=Mock(value="context_analysis"))
        ]
        registry.get_task.return_value = Mock(task_id="task1", name="Task 1")
        registry.list_task_ids.return_value = ["task1", "task2", "task3"]
        return registry
    
    @pytest.fixture
    def benchmark_runner(self, mock_config, mock_task_registry):
        """Create a benchmark runner with mocked dependencies."""
        with patch('ai_dev_tools.benchmark.core.get_task_registry', return_value=mock_task_registry):
            with patch('ai_dev_tools.benchmark.core.ReportGenerator'):
                runner = BenchmarkRunner(mock_config)
                return runner
    
    def test_benchmark_runner_initialization(self, benchmark_runner, mock_config):
        """Test benchmark runner initialization."""
        assert benchmark_runner.config == mock_config
        assert benchmark_runner.task_registry is not None
        assert benchmark_runner.report_generator is not None
    
    @pytest.mark.asyncio
    async def test_run_quick_benchmark_success(self, benchmark_runner):
        """Test successful quick benchmark run."""
        # Mock the execution engine
        mock_engine = AsyncMock()
        mock_results = {
            "overall_metrics": {
                "total_tasks": 3,
                "success_rate": 0.9,
                "average_task_duration": 2.0,
                "total_tokens": 1000,
                "tokens_per_second": 500.0
            },
            "comparison_metrics": {
                "token_reduction_percent": 20.0,
                "time_reduction_percent": 30.0
            }
        }
        mock_engine.execute_benchmark.return_value = mock_results
        
        with patch('ai_dev_tools.benchmark.core.ExecutionEngine') as mock_engine_class:
            mock_engine_class.return_value.__aenter__.return_value = mock_engine
            
            result = await benchmark_runner.run_quick_benchmark(
                profile="medium",
                tasks=["task1", "task2"],
                sample_size=5
            )
            
            assert result.profile == "medium"
            assert result.tasks_executed == 3
            assert result.success_rate == 0.9
            assert result.avg_duration == 2.0
            assert result.total_tokens == 1000
            assert result.tokens_per_second == 500.0
            assert result.token_reduction_percent == 20.0
            assert result.time_reduction_percent == 30.0
            assert result.status == "completed"
            assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_run_quick_benchmark_failure(self, benchmark_runner):
        """Test quick benchmark run with failure."""
        with patch('ai_dev_tools.benchmark.core.ExecutionEngine') as mock_engine_class:
            mock_engine_class.return_value.__aenter__.side_effect = Exception("Connection failed")
            
            result = await benchmark_runner.run_quick_benchmark(
                profile="light",
                tasks=["task1"],
                sample_size=3
            )
            
            assert result.status == "failed"
            assert result.error_message == "Connection failed"
            assert result.success_rate == 0.0
            assert result.total_tokens == 0
    
    @pytest.mark.asyncio
    async def test_run_quick_benchmark_no_tasks(self, benchmark_runner):
        """Test quick benchmark run with no valid tasks."""
        benchmark_runner.task_registry.get_task.return_value = None
        
        result = await benchmark_runner.run_quick_benchmark(
            profile="medium",
            tasks=["invalid_task"],
            sample_size=3
        )
        
        assert result.status == "failed"
        assert result.error_message == "No valid tasks found"
        assert result.tasks_executed == 0
    
    @pytest.mark.asyncio
    async def test_run_comparison_benchmark(self, benchmark_runner):
        """Test comparison benchmark across profiles."""
        # Mock the execution for each profile
        mock_results = {
            "overall_metrics": {
                "total_tasks": 2,
                "success_rate": 0.8,
                "average_task_duration": 1.5,
                "total_tokens": 800,
                "tokens_per_second": 533.33
            },
            "comparison_metrics": {
                "token_reduction_percent": 15.0,
                "time_reduction_percent": 25.0
            }
        }
        
        with patch.object(benchmark_runner, 'run_quick_benchmark') as mock_quick:
            mock_quick.return_value = BenchmarkResult(
                benchmark_id="comp_test",
                profile="medium",
                tasks_executed=2,
                success_rate=0.8,
                avg_duration=1.5,
                total_tokens=800,
                tokens_per_second=533.33,
                token_reduction_percent=15.0,
                time_reduction_percent=25.0,
                status="completed",
                start_time=1234567890.0,
                end_time=1234567895.0
            )
            
            results = await benchmark_runner.run_comparison_benchmark(
                profiles=["light", "medium"],
                tasks=["task1", "task2"],
                sample_size=3
            )
            
            assert "light" in results
            assert "medium" in results
            assert results["light"].profile == "medium"  # Mock returns same result
            assert results["medium"].profile == "medium"
            assert mock_quick.call_count == 2
    
    @pytest.mark.asyncio
    async def test_run_batch_benchmark(self, benchmark_runner):
        """Test batch benchmark execution."""
        mock_engine = AsyncMock()
        mock_results = {
            "overall_metrics": {
                "total_tasks": 3,
                "success_rate": 0.95,
                "average_task_duration": 1.8,
                "total_tokens": 1200,
                "tokens_per_second": 666.67
            },
            "comparison_metrics": {
                "token_reduction_percent": 30.0,
                "time_reduction_percent": 35.0
            }
        }
        mock_engine.execute_benchmark.return_value = mock_results
        
        with patch('ai_dev_tools.benchmark.core.ExecutionEngine') as mock_engine_class:
            mock_engine_class.return_value.__aenter__.return_value = mock_engine
            
            results = await benchmark_runner.run_batch_benchmark(
                batch_name="quick",
                output_file=None
            )
            
            assert "batch_info" in results
            assert results["batch_info"]["batch_name"] == "quick"
            assert "overall_metrics" in results
            assert results["overall_metrics"]["success_rate"] == 0.95
    
    def test_get_available_profiles(self, benchmark_runner):
        """Test getting available profiles."""
        profiles = benchmark_runner.get_available_profiles()
        assert "light" in profiles
        assert "medium" in profiles
        assert "heavy" in profiles
    
    def test_get_available_tasks(self, benchmark_runner):
        """Test getting available tasks."""
        tasks = benchmark_runner.get_available_tasks()
        assert tasks == ["task1", "task2", "task3"]
    
    def test_get_available_batches(self, benchmark_runner):
        """Test getting available batch configurations."""
        batches = benchmark_runner.get_available_batches()
        assert "quick" in batches
    
    def test_add_custom_task_success(self, benchmark_runner):
        """Test adding a custom task successfully."""
        benchmark_runner.task_registry.create_custom_task.return_value = Mock()
        benchmark_runner.task_registry.validate_task.return_value = []
        
        success = benchmark_runner.add_custom_task(
            task_id="custom_task",
            name="Custom Task",
            description="A custom benchmark task",
            baseline_prompt="Baseline prompt",
            tools_prompt="Tools prompt",
            workflow_type="pattern_analysis"
        )
        
        assert success is True
        benchmark_runner.task_registry.create_custom_task.assert_called_once()
    
    def test_add_custom_task_validation_failure(self, benchmark_runner):
        """Test adding a custom task with validation failure."""
        benchmark_runner.task_registry.create_custom_task.return_value = Mock()
        benchmark_runner.task_registry.validate_task.return_value = ["Invalid task"]
        
        success = benchmark_runner.add_custom_task(
            task_id="invalid_task",
            name="Invalid Task",
            description="An invalid task",
            baseline_prompt="Baseline prompt",
            tools_prompt="Tools prompt",
            workflow_type="pattern_analysis"
        )
        
        assert success is False
    
    def test_add_custom_task_exception(self, benchmark_runner):
        """Test adding a custom task with exception."""
        benchmark_runner.task_registry.create_custom_task.side_effect = Exception("Creation failed")
        
        success = benchmark_runner.add_custom_task(
            task_id="error_task",
            name="Error Task",
            description="A task that causes error",
            baseline_prompt="Baseline prompt",
            tools_prompt="Tools prompt",
            workflow_type="pattern_analysis"
        )
        
        assert success is False
    
    def test_get_system_info(self, benchmark_runner):
        """Test getting system information."""
        info = benchmark_runner.get_system_info()
        
        assert "profiles" in info
        assert "tasks" in info
        assert "batches" in info
        assert "execution_mode" in info
        assert "output_directory" in info
        assert "container_timeout" in info
        assert "task_timeout" in info


class TestConvenienceFunctions:
    """Test the convenience functions for common operations."""
    
    @pytest.mark.asyncio
    async def test_quick_benchmark_function(self):
        """Test the quick_benchmark convenience function."""
        mock_config = Mock()
        mock_result = BenchmarkResult(
            benchmark_id="quick_test",
            profile="medium",
            tasks_executed=2,
            success_rate=0.9,
            avg_duration=1.5,
            total_tokens=600,
            tokens_per_second=400.0,
            status="completed",
            start_time=1234567890.0,
            end_time=1234567895.0
        )
        
        with patch('ai_dev_tools.benchmark.core.BenchmarkRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run_quick_benchmark.return_value = mock_result
            mock_runner_class.return_value = mock_runner
            
            result = await quick_benchmark(
                profile="medium",
                tasks=["task1", "task2"],
                sample_size=3,
                config=mock_config
            )
            
            assert result.benchmark_id == "quick_test"
            assert result.profile == "medium"
            assert result.status == "completed"
            mock_runner.run_quick_benchmark.assert_called_once_with("medium", ["task1", "task2"], 3)
    
    @pytest.mark.asyncio
    async def test_compare_profiles_function(self):
        """Test the compare_profiles convenience function."""
        mock_config = Mock()
        mock_results = {
            "light": BenchmarkResult(
                benchmark_id="comp_light",
                profile="light",
                tasks_executed=3,
                success_rate=0.85,
                avg_duration=2.0,
                total_tokens=800,
                tokens_per_second=400.0,
                status="completed",
                start_time=1234567890.0,
                end_time=1234567895.0
            ),
            "medium": BenchmarkResult(
                benchmark_id="comp_medium",
                profile="medium",
                tasks_executed=3,
                success_rate=0.9,
                avg_duration=1.5,
                total_tokens=600,
                tokens_per_second=400.0,
                status="completed",
                start_time=1234567890.0,
                end_time=1234567895.0
            )
        }
        
        with patch('ai_dev_tools.benchmark.core.BenchmarkRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run_comparison_benchmark.return_value = mock_results
            mock_runner_class.return_value = mock_runner
            
            results = await compare_profiles(
                profiles=["light", "medium"],
                tasks=["task1"],
                config=mock_config
            )
            
            assert "light" in results
            assert "medium" in results
            assert results["light"].profile == "light"
            assert results["medium"].profile == "medium"
            mock_runner.run_comparison_benchmark.assert_called_once_with(["light", "medium"], ["task1"])
    
    @pytest.mark.asyncio
    async def test_batch_benchmark_function(self):
        """Test the batch_benchmark convenience function."""
        mock_config = Mock()
        mock_results = {
            "batch_info": {"batch_name": "standard"},
            "overall_metrics": {"success_rate": 0.95}
        }
        
        with patch('ai_dev_tools.benchmark.core.BenchmarkRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run_batch_benchmark.return_value = mock_results
            mock_runner_class.return_value = mock_runner
            
            results = await batch_benchmark(
                batch_name="standard",
                output_file="/tmp/output.json",
                config=mock_config
            )
            
            assert results["batch_info"]["batch_name"] == "standard"
            assert results["overall_metrics"]["success_rate"] == 0.95
            mock_runner.run_batch_benchmark.assert_called_once_with("standard", "/tmp/output.json")


class TestIntegration:
    """Integration tests for the benchmarking system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_quick_benchmark(self):
        """Test a complete end-to-end quick benchmark flow."""
        # This would require actual configuration and mocked execution
        # For now, we'll test the key integration points
        
        # Mock configuration
        mock_config = Mock()
        mock_config.output_directory = Path("/tmp/test_output")
        mock_config.get_sample_size.return_value = 3
        mock_config.validate_runtime.return_value = []
        
        # Mock task registry
        mock_task = Mock()
        mock_task.task_id = "integration_task"
        mock_task.name = "Integration Task"
        mock_task.workflow_type = Mock(value="safety_check")
        
        # Mock execution results
        mock_execution_results = {
            "overall_metrics": {
                "total_tasks": 1,
                "success_rate": 1.0,
                "average_task_duration": 1.0,
                "total_tokens": 500,
                "tokens_per_second": 500.0
            },
            "comparison_metrics": {
                "token_reduction_percent": 10.0,
                "time_reduction_percent": 20.0
            }
        }
        
        with patch('ai_dev_tools.benchmark.core.get_task_registry') as mock_registry:
            mock_registry.return_value.get_all_tasks.return_value = [mock_task]
            mock_registry.return_value.get_task.return_value = mock_task
            
            with patch('ai_dev_tools.benchmark.core.ExecutionEngine') as mock_engine_class:
                mock_engine = AsyncMock()
                mock_engine.execute_benchmark.return_value = mock_execution_results
                mock_engine_class.return_value.__aenter__.return_value = mock_engine
                
                with patch('ai_dev_tools.benchmark.core.ReportGenerator'):
                    result = await quick_benchmark(
                        profile="medium",
                        tasks=["integration_task"],
                        sample_size=3,
                        config=mock_config
                    )
                    
                    assert result.status == "completed"
                    assert result.profile == "medium"
                    assert result.tasks_executed == 1
                    assert result.success_rate == 1.0
                    assert result.token_reduction_percent == 10.0
                    assert result.time_reduction_percent == 20.0