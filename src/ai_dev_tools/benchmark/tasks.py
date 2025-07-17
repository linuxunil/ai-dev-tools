"""
Task management for AI Development Tools benchmarking.

Provides extensible task registry, task definitions, and task execution logic.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .config import WorkflowType


class TaskStatus(str, Enum):
    """Status of a benchmark task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskApproach(str, Enum):
    """Approach used for task execution."""

    BASELINE = "baseline"  # Manual/simulated baseline
    TOOLS = "tools"  # Using AI development tools


@dataclass
class TaskResult:
    """Result of a single task execution."""

    task_id: str
    approach: TaskApproach
    model_instance: str
    status: TaskStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None

    # Response data
    response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Error information
    error: Optional[str] = None

    # Metadata
    sample_num: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_completed(self, response: str = "", tokens_in: int = 0, tokens_out: int = 0) -> None:
        """Mark task as completed with results."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = TaskStatus.COMPLETED
        self.response = response
        self.input_tokens = tokens_in
        self.output_tokens = tokens_out
        self.total_tokens = tokens_in + tokens_out

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = TaskStatus.FAILED
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "approach": self.approach.value,
            "model_instance": self.model_instance,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "response": self.response,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "error": self.error,
            "sample_num": self.sample_num,
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkTask:
    """Definition of a benchmark task."""

    task_id: str
    name: str
    description: str
    workflow_type: WorkflowType

    # Prompts for different approaches
    baseline_prompt: str
    tools_prompt: str

    # Expected outputs for validation
    expected_outputs: Dict[str, Any] = field(default_factory=dict)

    # Task configuration
    timeout: int = 30
    max_retries: int = 3

    # File dependencies
    target_files: List[str] = field(default_factory=list)

    # Custom execution functions
    baseline_executor: Optional[Callable[..., Awaitable[TaskResult]]] = None
    tools_executor: Optional[Callable[..., Awaitable[TaskResult]]] = None

    def create_result(self, approach: TaskApproach, model_instance: str, sample_num: int = 0) -> TaskResult:
        """Create a new task result instance."""
        return TaskResult(
            task_id=self.task_id,
            approach=approach,
            model_instance=model_instance,
            status=TaskStatus.PENDING,
            start_time=time.time(),
            sample_num=sample_num,
        )


class TaskRegistry:
    """Registry for benchmark tasks with extensible task management."""

    def __init__(self):
        self._tasks: Dict[str, BenchmarkTask] = {}
        self._load_default_tasks()

    def _load_default_tasks(self) -> None:
        """Load default benchmark tasks."""
        default_tasks = [
            BenchmarkTask(
                task_id="safety_assessment",
                name="Safety Assessment",
                description="Analyze code for security vulnerabilities",
                workflow_type=WorkflowType.SAFETY_CHECK,
                baseline_prompt="Analyze this code for security issues: def process(data): return eval(data)",
                tools_prompt='Based on this safety analysis: {"risk_level": "HIGH", "issues": ["eval usage"]}, provide assessment.',
                expected_outputs={"risk_level": "HIGH", "issues": ["eval"], "safe_to_modify": False},
            ),
            BenchmarkTask(
                task_id="pattern_detection",
                name="Pattern Detection",
                description="Find similar code patterns for systematic fixes",
                workflow_type=WorkflowType.PATTERN_ANALYSIS,
                baseline_prompt="Find patterns in: def get_user(id): return db.fetch(id); def get_order(id): return db.fetch(id)",
                tools_prompt='Based on pattern analysis: {"pattern": "fetch_by_id", "matches": 2}, provide summary.',
                expected_outputs={"pattern": "fetch_by_id", "matches": 2, "confidence": 0.8},
            ),
            BenchmarkTask(
                task_id="context_analysis",
                name="Context Analysis",
                description="Analyze project structure and complexity",
                workflow_type=WorkflowType.CONTEXT_ANALYSIS,
                baseline_prompt="Analyze project with files: user.py, order.py, api.py, tests/. What's the architecture?",
                tools_prompt='Based on context: {"architecture": "microservices", "complexity": 6}, provide summary.',
                expected_outputs={"architecture": "microservices", "complexity": 6, "file_count": 4},
            ),
            BenchmarkTask(
                task_id="tensorflow_context",
                name="TensorFlow Math Ops Context",
                description="Analyze TensorFlow math operations module",
                workflow_type=WorkflowType.CONTEXT_ANALYSIS,
                baseline_prompt="Given the file `tensorflow/python/ops/math_ops.py`, describe its role in TensorFlow, its main functionalities, and its key internal and external dependencies. Focus on how it integrates with the broader TensorFlow ecosystem.",
                tools_prompt="Based on an analysis of `tensorflow/python/ops/math_ops.py`, provide a summary of its architectural role, core functionalities, and significant dependencies within TensorFlow.",
                expected_outputs={
                    "module_type": "math_operations",
                    "dependencies": ["tensorflow.python.framework"],
                    "complexity": 8,
                },
            ),
            BenchmarkTask(
                task_id="repo_analysis",
                name="Repository Analysis",
                description="Comprehensive repository structure analysis",
                workflow_type=WorkflowType.REPO_ANALYSIS,
                baseline_prompt="Analyze this repository structure and provide insights about code organization, patterns, and potential improvements.",
                tools_prompt="Based on repository analysis results, provide a comprehensive summary of the codebase structure and recommendations.",
                expected_outputs={
                    "structure_type": "modular",
                    "organization_score": 7,
                    "suggestions": ["improve_documentation", "refactor_duplicates"],
                },
            ),
            BenchmarkTask(
                task_id="systematic_fix",
                name="Systematic Fix Planning",
                description="Plan systematic fixes across similar code patterns",
                workflow_type=WorkflowType.SYSTEMATIC_FIX,
                baseline_prompt="Plan systematic fixes for similar patterns found in: function getUserById(id), function getOrderById(id), function getProductById(id)",
                tools_prompt="Based on systematic fix analysis, provide implementation plan for consistent pattern updates.",
                expected_outputs={"fix_type": "parameter_validation", "affected_functions": 3, "risk_level": "LOW"},
            ),
        ]

        for task in default_tasks:
            self._tasks[task.task_id] = task

    def register_task(self, task: BenchmarkTask) -> None:
        """Register a new benchmark task."""
        self._tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Optional[BenchmarkTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[BenchmarkTask]:
        """Get all registered tasks."""
        return list(self._tasks.values())

    def get_tasks_by_workflow(self, workflow_type: WorkflowType) -> List[BenchmarkTask]:
        """Get tasks by workflow type."""
        return [task for task in self._tasks.values() if task.workflow_type == workflow_type]

    def list_task_ids(self) -> List[str]:
        """Get list of all task IDs."""
        return list(self._tasks.keys())

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from registry."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def clear_tasks(self) -> None:
        """Clear all tasks from registry."""
        self._tasks.clear()

    def create_custom_task(
        self,
        task_id: str,
        name: str,
        description: str,
        workflow_type: WorkflowType,
        baseline_prompt: str,
        tools_prompt: str,
        expected_outputs: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        max_retries: int = 3,
        target_files: Optional[List[str]] = None,
    ) -> BenchmarkTask:
        """Create and register a custom task."""
        task = BenchmarkTask(
            task_id=task_id,
            name=name,
            description=description,
            workflow_type=workflow_type,
            baseline_prompt=baseline_prompt,
            tools_prompt=tools_prompt,
            expected_outputs=expected_outputs or {},
            timeout=timeout,
            max_retries=max_retries,
            target_files=target_files or [],
        )

        self.register_task(task)
        return task

    def validate_task(self, task: BenchmarkTask) -> List[str]:
        """Validate a task configuration."""
        issues = []

        if not task.task_id or not task.task_id.strip():
            issues.append("Task ID cannot be empty")

        if not task.name or not task.name.strip():
            issues.append("Task name cannot be empty")

        if not task.baseline_prompt or not task.baseline_prompt.strip():
            issues.append("Baseline prompt cannot be empty")

        if not task.tools_prompt or not task.tools_prompt.strip():
            issues.append("Tools prompt cannot be empty")

        if task.timeout <= 0:
            issues.append("Timeout must be positive")

        if task.max_retries < 0:
            issues.append("Max retries cannot be negative")

        # Check target files exist if specified
        for file_path in task.target_files:
            if not Path(file_path).exists():
                issues.append(f"Target file not found: {file_path}")

        return issues

    def get_task_stats(self) -> Dict[str, Any]:
        """Get statistics about registered tasks."""
        workflow_counts = {}
        total_tasks = len(self._tasks)

        for task in self._tasks.values():
            workflow_type = task.workflow_type.value
            workflow_counts[workflow_type] = workflow_counts.get(workflow_type, 0) + 1

        return {
            "total_tasks": total_tasks,
            "workflow_distribution": workflow_counts,
            "task_ids": list(self._tasks.keys()),
        }


# Global task registry instance
_task_registry = TaskRegistry()


def get_task_registry() -> TaskRegistry:
    """Get the global task registry instance."""
    return _task_registry
