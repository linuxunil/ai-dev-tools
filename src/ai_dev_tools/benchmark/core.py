"""Core benchmarking framework - Simplified and enhanced version.

Provides a streamlined API for benchmarking AI development tools with
improved error handling, performance, and ease of use.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
from pydantic import BaseModel, Field

from .config import BenchmarkConfig, HardwareProfile, ModelInstance, load_config
from .execution import ExecutionEngine
from .metrics import MetricsCollector
from .reporting import ReportGenerator
from .tasks import BenchmarkTask, TaskRegistry, get_task_registry

logger = logging.getLogger(__name__)


class BenchmarkResult(BaseModel):
    """Simplified benchmark result container."""
    
    benchmark_id: str = Field(..., description="Unique identifier for this benchmark run")
    profile: str = Field(..., description="Hardware profile used")
    tasks_executed: int = Field(..., description="Number of tasks executed")
    success_rate: float = Field(..., description="Overall success rate (0.0-1.0)")
    
    # Performance metrics
    avg_duration: float = Field(..., description="Average task duration in seconds")
    total_tokens: int = Field(..., description="Total tokens processed")
    tokens_per_second: float = Field(..., description="Token processing rate")
    
    # Comparison metrics
    token_reduction_percent: float = Field(default=0.0, description="Token reduction vs baseline")
    time_reduction_percent: float = Field(default=0.0, description="Time reduction vs baseline")
    
    # Status
    status: str = Field(..., description="Overall benchmark status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Timestamps
    start_time: float = Field(..., description="Start timestamp")
    end_time: float = Field(..., description="End timestamp")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()


class BenchmarkRunner:
    """Simplified benchmark runner with enhanced usability."""
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or load_config()
        self.task_registry = get_task_registry()
        self.report_generator = ReportGenerator(self.config.output_directory)
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Validate configuration and log any issues."""
        issues = self.config.validate_runtime()
        if issues:
            logger.warning(f"Configuration issues found: {', '.join(issues)}")
    
    async def run_quick_benchmark(
        self, 
        profile: Union[str, HardwareProfile] = "medium",
        tasks: Optional[List[str]] = None,
        sample_size: int = 3
    ) -> BenchmarkResult:
        """Run a quick benchmark with minimal configuration.
        
        Args:
            profile: Hardware profile to use ("light", "medium", "heavy")
            tasks: List of task IDs to run (defaults to all tasks)
            sample_size: Number of samples per task
            
        Returns:
            BenchmarkResult with key metrics
        """
        benchmark_id = f"quick_{int(time.time())}"
        
        # Convert profile to enum if needed
        if isinstance(profile, str):
            profile = HardwareProfile(profile)
            
        # Get tasks to run
        if tasks:
            task_objects = [self.task_registry.get_task(task_id) for task_id in tasks]
            task_objects = [t for t in task_objects if t is not None]
        else:
            task_objects = self.task_registry.get_all_tasks()[:3]  # Limit to 3 for quick run
            
        if not task_objects:
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                profile=profile.value,
                tasks_executed=0,
                success_rate=0.0,
                avg_duration=0.0,
                total_tokens=0,
                tokens_per_second=0.0,
                status="failed",
                error_message="No valid tasks found",
                start_time=time.time(),
                end_time=time.time()
            )
            
        start_time = time.time()
        
        try:
            # Execute benchmark
            async with ExecutionEngine(self.config) as engine:
                results = await engine.execute_benchmark(
                    tasks=task_objects,
                    profile=profile,
                    sample_size=sample_size
                )
                
            end_time = time.time()
            
            # Extract key metrics
            overall_metrics = results.get("overall_metrics", {})
            comparison_metrics = results.get("comparison_metrics", {})
            
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                profile=profile.value,
                tasks_executed=overall_metrics.get("total_tasks", 0),
                success_rate=overall_metrics.get("success_rate", 0.0),
                avg_duration=overall_metrics.get("average_task_duration", 0.0),
                total_tokens=overall_metrics.get("total_tokens", 0),
                tokens_per_second=overall_metrics.get("tokens_per_second", 0.0),
                token_reduction_percent=comparison_metrics.get("token_reduction_percent", 0.0),
                time_reduction_percent=comparison_metrics.get("time_reduction_percent", 0.0),
                status="completed",
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            logger.error(f"Quick benchmark failed: {e}")
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                profile=profile.value,
                tasks_executed=0,
                success_rate=0.0,
                avg_duration=0.0,
                total_tokens=0,
                tokens_per_second=0.0,
                status="failed",
                error_message=str(e),
                start_time=start_time,
                end_time=time.time()
            )
    
    async def run_comparison_benchmark(
        self,
        profiles: List[Union[str, HardwareProfile]] = ["light", "medium", "heavy"],
        tasks: Optional[List[str]] = None,
        sample_size: Optional[int] = None
    ) -> Dict[str, BenchmarkResult]:
        """Run comparison benchmark across multiple profiles.
        
        Args:
            profiles: List of hardware profiles to compare
            tasks: List of task IDs to run (defaults to all tasks)
            sample_size: Number of samples per task (uses profile defaults if None)
            
        Returns:
            Dictionary mapping profile names to BenchmarkResult
        """
        results = {}
        
        for profile in profiles:
            if isinstance(profile, str):
                profile = HardwareProfile(profile)
                
            profile_sample_size = sample_size or self.config.get_sample_size(profile)
            
            result = await self.run_quick_benchmark(
                profile=profile,
                tasks=tasks,
                sample_size=profile_sample_size
            )
            
            results[profile.value] = result
            
        return results
    
    async def run_batch_benchmark(
        self,
        batch_name: str = "standard",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a predefined batch benchmark.
        
        Args:
            batch_name: Name of batch configuration ("quick", "standard", "comprehensive")
            output_file: Optional output file path
            
        Returns:
            Full benchmark results dictionary
        """
        batch_config = self.config.get_batch_config(batch_name)
        if not batch_config:
            raise ValueError(f"Batch configuration '{batch_name}' not found")
            
        # Get all tasks for batch run
        tasks = self.task_registry.get_all_tasks()
        
        async with ExecutionEngine(self.config) as engine:
            results = await engine.execute_benchmark(
                tasks=tasks,
                profile=batch_config.profile,
                sample_size=batch_config.sample_size
            )
            
        # Add batch info
        results["batch_info"] = {
            "batch_name": batch_name,
            "config": batch_config.model_dump() if hasattr(batch_config, "model_dump") else str(batch_config)
        }
        
        # Save results if output file specified
        if output_file:
            await self._save_results(results, output_file)
            
        return results
    
    async def _save_results(self, results: Dict[str, Any], output_file: str) -> None:
        """Save results to file asynchronously."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(output_path, 'w') as f:
            await f.write(json.dumps(results, indent=2, default=str))
            
        logger.info(f"Results saved to: {output_path}")
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available hardware profiles."""
        return [profile.value for profile in HardwareProfile]
    
    def get_available_tasks(self) -> List[str]:
        """Get list of available task IDs."""
        return self.task_registry.list_task_ids()
    
    def get_available_batches(self) -> List[str]:
        """Get list of available batch configurations."""
        return list(self.config.batch_configurations.keys())
    
    def add_custom_task(
        self,
        task_id: str,
        name: str,
        description: str,
        baseline_prompt: str,
        tools_prompt: str,
        workflow_type: str = "pattern_analysis"
    ) -> bool:
        """Add a custom task to the registry.
        
        Args:
            task_id: Unique identifier for the task
            name: Human-readable name
            description: Task description
            baseline_prompt: Prompt for baseline execution
            tools_prompt: Prompt for tools execution
            workflow_type: Type of workflow ("pattern_analysis", "safety_check", etc.)
            
        Returns:
            True if task was added successfully
        """
        try:
            from .config import WorkflowType
            
            workflow_enum = WorkflowType(workflow_type)
            
            task = self.task_registry.create_custom_task(
                task_id=task_id,
                name=name,
                description=description,
                workflow_type=workflow_enum,
                baseline_prompt=baseline_prompt,
                tools_prompt=tools_prompt
            )
            
            # Validate task
            issues = self.task_registry.validate_task(task)
            if issues:
                logger.warning(f"Task validation issues: {', '.join(issues)}")
                return False
                
            logger.info(f"Successfully added custom task: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom task: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system configuration information."""
        return {
            "profiles": len(self.config.profiles),
            "tasks": len(self.task_registry.get_all_tasks()),
            "batches": len(self.config.batch_configurations),
            "execution_mode": self.config.execution_mode.value,
            "output_directory": str(self.config.output_directory),
            "container_timeout": self.config.container_startup_timeout,
            "task_timeout": self.config.task_timeout
        }


# Convenience functions for common operations

async def quick_benchmark(
    profile: str = "medium",
    tasks: Optional[List[str]] = None,
    sample_size: int = 3,
    config: Optional[BenchmarkConfig] = None
) -> BenchmarkResult:
    """Run a quick benchmark with minimal setup.
    
    Args:
        profile: Hardware profile ("light", "medium", "heavy")
        tasks: List of task IDs to run
        sample_size: Number of samples per task
        config: Optional configuration (loads default if None)
        
    Returns:
        BenchmarkResult with key metrics
    """
    runner = BenchmarkRunner(config)
    return await runner.run_quick_benchmark(profile, tasks, sample_size)


async def compare_profiles(
    profiles: List[str] = ["light", "medium", "heavy"],
    tasks: Optional[List[str]] = None,
    config: Optional[BenchmarkConfig] = None
) -> Dict[str, BenchmarkResult]:
    """Compare performance across multiple hardware profiles.
    
    Args:
        profiles: List of hardware profiles to compare
        tasks: List of task IDs to run
        config: Optional configuration (loads default if None)
        
    Returns:
        Dictionary mapping profile names to BenchmarkResult
    """
    runner = BenchmarkRunner(config)
    return await runner.run_comparison_benchmark(profiles, tasks)


async def batch_benchmark(
    batch_name: str = "standard",
    output_file: Optional[str] = None,
    config: Optional[BenchmarkConfig] = None
) -> Dict[str, Any]:
    """Run a predefined batch benchmark.
    
    Args:
        batch_name: Name of batch configuration
        output_file: Optional output file path
        config: Optional configuration (loads default if None)
        
    Returns:
        Full benchmark results dictionary
    """
    runner = BenchmarkRunner(config)
    return await runner.run_batch_benchmark(batch_name, output_file)
