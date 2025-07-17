"""
Tests for benchmark task management system.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock

from ai_dev_tools.benchmark.tasks import (
    BenchmarkTask,
    TaskResult,
    TaskRegistry,
    TaskStatus,
    TaskApproach,
    get_task_registry
)
from ai_dev_tools.benchmark.config import WorkflowType


class TestTaskResult:
    """Test TaskResult class."""
    
    def test_task_result_creation(self):
        """Test basic task result creation."""
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.BASELINE,
            model_instance="test_model",
            status=TaskStatus.PENDING,
            start_time=time.time()
        )
        
        assert result.task_id == "test_task"
        assert result.approach == TaskApproach.BASELINE
        assert result.model_instance == "test_model"
        assert result.status == TaskStatus.PENDING
        assert result.end_time is None
        assert result.duration is None
        assert result.response == ""
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.total_tokens == 0
        assert result.error is None
        assert result.sample_num == 0
    
    def test_mark_completed(self):
        """Test marking task as completed."""
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.TOOLS,
            model_instance="test_model",
            status=TaskStatus.RUNNING,
            start_time=time.time()
        )
        
        result.mark_completed(
            response="Test response",
            tokens_in=100,
            tokens_out=200
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.end_time is not None
        assert result.duration is not None
        assert result.duration > 0
        assert result.response == "Test response"
        assert result.input_tokens == 100
        assert result.output_tokens == 200
        assert result.total_tokens == 300
        assert result.error is None
    
    def test_mark_failed(self):
        """Test marking task as failed."""
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.BASELINE,
            model_instance="test_model",
            status=TaskStatus.RUNNING,
            start_time=time.time()
        )
        
        result.mark_failed("Test error message")
        
        assert result.status == TaskStatus.FAILED
        assert result.end_time is not None
        assert result.duration is not None
        assert result.duration > 0
        assert result.error == "Test error message"
    
    def test_to_dict(self):
        """Test converting task result to dictionary."""
        result = TaskResult(
            task_id="test_task",
            approach=TaskApproach.TOOLS,
            model_instance="test_model",
            status=TaskStatus.COMPLETED,
            start_time=123456.0,
            sample_num=5
        )
        
        result.mark_completed("Test response", 50, 75)
        
        result_dict = result.to_dict()
        
        assert result_dict["task_id"] == "test_task"
        assert result_dict["approach"] == "tools"
        assert result_dict["model_instance"] == "test_model"
        assert result_dict["status"] == "completed"
        assert result_dict["start_time"] == 123456.0
        assert result_dict["response"] == "Test response"
        assert result_dict["input_tokens"] == 50
        assert result_dict["output_tokens"] == 75
        assert result_dict["total_tokens"] == 125
        assert result_dict["sample_num"] == 5


class TestBenchmarkTask:
    """Test BenchmarkTask class."""
    
    def test_benchmark_task_creation(self):
        """Test basic benchmark task creation."""
        task = BenchmarkTask(
            task_id="test_task",
            name="Test Task",
            description="A test task",
            workflow_type=WorkflowType.SAFETY_CHECK,
            baseline_prompt="Test baseline prompt",
            tools_prompt="Test tools prompt"
        )
        
        assert task.task_id == "test_task"
        assert task.name == "Test Task"
        assert task.description == "A test task"
        assert task.workflow_type == WorkflowType.SAFETY_CHECK
        assert task.baseline_prompt == "Test baseline prompt"
        assert task.tools_prompt == "Test tools prompt"
        assert task.timeout == 30
        assert task.max_retries == 3
        assert task.target_files == []
        assert task.expected_outputs == {}
        assert task.baseline_executor is None
        assert task.tools_executor is None
    
    def test_benchmark_task_with_options(self):
        """Test benchmark task with optional parameters."""
        expected_outputs = {"key": "value"}
        target_files = ["file1.py", "file2.py"]
        
        task = BenchmarkTask(
            task_id="complex_task",
            name="Complex Task",
            description="A complex test task",
            workflow_type=WorkflowType.PATTERN_ANALYSIS,
            baseline_prompt="Complex baseline prompt",
            tools_prompt="Complex tools prompt",
            expected_outputs=expected_outputs,
            timeout=60,
            max_retries=5,
            target_files=target_files
        )
        
        assert task.expected_outputs == expected_outputs
        assert task.timeout == 60
        assert task.max_retries == 5
        assert task.target_files == target_files
    
    def test_create_result(self):
        """Test creating task result from task."""
        task = BenchmarkTask(
            task_id="test_task",
            name="Test Task",
            description="A test task",
            workflow_type=WorkflowType.CONTEXT_ANALYSIS,
            baseline_prompt="Test baseline prompt",
            tools_prompt="Test tools prompt"
        )
        
        result = task.create_result(TaskApproach.BASELINE, "test_model", 3)
        
        assert result.task_id == "test_task"
        assert result.approach == TaskApproach.BASELINE
        assert result.model_instance == "test_model"
        assert result.status == TaskStatus.PENDING
        assert result.sample_num == 3
        assert result.start_time > 0


class TestTaskRegistry:
    """Test TaskRegistry class."""
    
    def test_task_registry_initialization(self):
        """Test task registry initialization with default tasks."""
        registry = TaskRegistry()
        
        tasks = registry.get_all_tasks()
        assert len(tasks) > 0
        
        # Should have default tasks
        task_ids = registry.list_task_ids()
        assert "safety_assessment" in task_ids
        assert "pattern_detection" in task_ids
        assert "context_analysis" in task_ids
        assert "tensorflow_context" in task_ids
        assert "repo_analysis" in task_ids
        assert "systematic_fix" in task_ids
    
    def test_register_task(self):
        """Test registering a new task."""
        registry = TaskRegistry()
        initial_count = len(registry.get_all_tasks())
        
        task = BenchmarkTask(
            task_id="custom_task",
            name="Custom Task",
            description="A custom test task",
            workflow_type=WorkflowType.SAFETY_CHECK,
            baseline_prompt="Custom baseline prompt",
            tools_prompt="Custom tools prompt"
        )
        
        registry.register_task(task)
        
        assert len(registry.get_all_tasks()) == initial_count + 1
        assert registry.get_task("custom_task") is not None
        assert registry.get_task("custom_task").name == "Custom Task"
    
    def test_get_task(self):
        """Test getting a task by ID."""
        registry = TaskRegistry()
        
        task = registry.get_task("safety_assessment")
        assert task is not None
        assert task.task_id == "safety_assessment"
        assert task.workflow_type == WorkflowType.SAFETY_CHECK
        
        # Non-existent task
        assert registry.get_task("nonexistent") is None
    
    def test_get_tasks_by_workflow(self):
        """Test getting tasks by workflow type."""
        registry = TaskRegistry()
        
        safety_tasks = registry.get_tasks_by_workflow(WorkflowType.SAFETY_CHECK)
        assert len(safety_tasks) > 0
        
        for task in safety_tasks:
            assert task.workflow_type == WorkflowType.SAFETY_CHECK
        
        context_tasks = registry.get_tasks_by_workflow(WorkflowType.CONTEXT_ANALYSIS)
        assert len(context_tasks) > 0
        
        for task in context_tasks:
            assert task.workflow_type == WorkflowType.CONTEXT_ANALYSIS
    
    def test_remove_task(self):
        """Test removing a task."""
        registry = TaskRegistry()
        
        # Add a task to remove
        task = BenchmarkTask(
            task_id="removable_task",
            name="Removable Task",
            description="A task to be removed",
            workflow_type=WorkflowType.PATTERN_ANALYSIS,
            baseline_prompt="Removable baseline prompt",
            tools_prompt="Removable tools prompt"
        )
        
        registry.register_task(task)
        assert registry.get_task("removable_task") is not None
        
        # Remove the task
        result = registry.remove_task("removable_task")
        assert result is True
        assert registry.get_task("removable_task") is None
        
        # Try to remove non-existent task
        result = registry.remove_task("nonexistent")
        assert result is False
    
    def test_clear_tasks(self):
        """Test clearing all tasks."""
        registry = TaskRegistry()
        
        assert len(registry.get_all_tasks()) > 0
        
        registry.clear_tasks()
        
        assert len(registry.get_all_tasks()) == 0
        assert len(registry.list_task_ids()) == 0
    
    def test_create_custom_task(self):
        """Test creating a custom task."""
        registry = TaskRegistry()
        
        task = registry.create_custom_task(
            task_id="my_custom_task",
            name="My Custom Task",
            description="A custom task created via registry",
            workflow_type=WorkflowType.SYSTEMATIC_FIX,
            baseline_prompt="Custom baseline",
            tools_prompt="Custom tools",
            expected_outputs={"result": "expected"},
            timeout=45,
            max_retries=2,
            target_files=["test.py"]
        )
        
        assert task.task_id == "my_custom_task"
        assert task.name == "My Custom Task"
        assert task.workflow_type == WorkflowType.SYSTEMATIC_FIX
        assert task.expected_outputs == {"result": "expected"}
        assert task.timeout == 45
        assert task.max_retries == 2
        assert task.target_files == ["test.py"]
        
        # Should be registered automatically
        assert registry.get_task("my_custom_task") is not None
    
    def test_validate_task(self):
        """Test task validation."""
        registry = TaskRegistry()
        
        # Valid task
        valid_task = BenchmarkTask(
            task_id="valid_task",
            name="Valid Task",
            description="A valid task",
            workflow_type=WorkflowType.SAFETY_CHECK,
            baseline_prompt="Valid baseline prompt",
            tools_prompt="Valid tools prompt"
        )
        
        issues = registry.validate_task(valid_task)
        assert len(issues) == 0
        
        # Invalid task - empty ID
        invalid_task = BenchmarkTask(
            task_id="",
            name="Invalid Task",
            description="An invalid task",
            workflow_type=WorkflowType.SAFETY_CHECK,
            baseline_prompt="Invalid baseline prompt",
            tools_prompt="Invalid tools prompt"
        )
        
        issues = registry.validate_task(invalid_task)
        assert len(issues) > 0
        assert any("Task ID cannot be empty" in issue for issue in issues)
        
        # Invalid task - negative timeout
        invalid_task2 = BenchmarkTask(
            task_id="invalid_task2",
            name="Invalid Task 2",
            description="Another invalid task",
            workflow_type=WorkflowType.SAFETY_CHECK,
            baseline_prompt="Invalid baseline prompt",
            tools_prompt="Invalid tools prompt",
            timeout=-5
        )
        
        issues = registry.validate_task(invalid_task2)
        assert len(issues) > 0
        assert any("Timeout must be positive" in issue for issue in issues)
    
    def test_get_task_stats(self):
        """Test getting task statistics."""
        registry = TaskRegistry()
        
        stats = registry.get_task_stats()
        
        assert "total_tasks" in stats
        assert "workflow_distribution" in stats
        assert "task_ids" in stats
        
        assert stats["total_tasks"] > 0
        assert isinstance(stats["workflow_distribution"], dict)
        assert isinstance(stats["task_ids"], list)
        
        # Check workflow distribution
        workflow_dist = stats["workflow_distribution"]
        assert "safety_check" in workflow_dist
        assert "pattern_analysis" in workflow_dist
        assert "context_analysis" in workflow_dist


class TestTaskRegistryGlobal:
    """Test global task registry functionality."""
    
    def test_get_task_registry(self):
        """Test getting global task registry."""
        registry1 = get_task_registry()
        registry2 = get_task_registry()
        
        # Should be the same instance
        assert registry1 is registry2
        
        # Should have default tasks
        assert len(registry1.get_all_tasks()) > 0


class TestTaskEnums:
    """Test task-related enums."""
    
    def test_task_status_enum(self):
        """Test TaskStatus enum."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.TIMEOUT.value == "timeout"
    
    def test_task_approach_enum(self):
        """Test TaskApproach enum."""
        assert TaskApproach.BASELINE.value == "baseline"
        assert TaskApproach.TOOLS.value == "tools"


if __name__ == "__main__":
    pytest.main([__file__])