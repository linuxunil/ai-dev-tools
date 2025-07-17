"""
Main benchmark runner for AI Development Tools.

Provides the primary interface for executing benchmarks with full
configuration management, error handling, and reporting.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .config import BenchmarkConfig, HardwareProfile, OutputFormat, load_config
from .execution import ExecutionEngine
from .reporting import ReportGenerator
from .tasks import get_task_registry

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Main benchmark runner with comprehensive configuration and execution management."""

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or load_config()
        self.task_registry = get_task_registry()
        self.report_generator = ReportGenerator(self.config.output_directory)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration and report any issues."""
        issues = self.config.validate_runtime()
        if issues:
            logger.warning("Configuration issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")

    async def run_single_benchmark(
        self,
        profile: HardwareProfile,
        task_ids: Optional[List[str]] = None,
        sample_size: Optional[int] = None,
        output_format: Optional[OutputFormat] = None,
        output_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run a single benchmark configuration.

        Args:
            profile: Hardware profile to use
            task_ids: List of task IDs to run (all if None)
            sample_size: Number of samples per task (config default if None)
            output_format: Output format (config default if None)
            output_filename: Output filename (auto-generated if None)

        Returns:
            Dictionary containing benchmark results
        """
        logger.info(f"Starting single benchmark for profile: {profile.value}")

        # Get tasks to run
        if task_ids:
            tasks = []
            for task_id in task_ids:
                task = self.task_registry.get_task(task_id)
                if task:
                    tasks.append(task)
                else:
                    logger.warning(f"Task not found: {task_id}")
        else:
            tasks = self.task_registry.get_all_tasks()

        if not tasks:
            raise ValueError("No tasks to run")

        # Use config defaults if not specified
        if sample_size is None:
            sample_size = self.config.get_sample_size(profile)

        if output_format is None:
            output_format = self.config.output_format

        logger.info(f"Running {len(tasks)} tasks with {sample_size} samples each")

        # Execute benchmark
        async with ExecutionEngine(self.config) as engine:
            results = await engine.execute_benchmark(tasks=tasks, profile=profile, sample_size=sample_size)

        # Generate report
        if output_filename or output_format != OutputFormat.CONSOLE:
            report_file = self.report_generator.generate_report(results, output_format, output_filename)
            logger.info(f"Report saved to: {report_file}")

        return results

    async def run_batch_benchmark(
        self,
        batch_name: str,
        task_ids: Optional[List[str]] = None,
        output_format: Optional[OutputFormat] = None,
        output_filename: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run a predefined batch benchmark configuration.

        Args:
            batch_name: Name of batch configuration
            task_ids: List of task IDs to run (all if None)
            output_format: Output format (config default if None)
            output_filename: Output filename (auto-generated if None)

        Returns:
            List of benchmark results for each configuration
        """
        logger.info(f"Starting batch benchmark: {batch_name}")

        # Get batch configuration
        batch_config = self.config.get_batch_config(batch_name)
        if not batch_config:
            raise ValueError(f"Batch configuration not found: {batch_name}")

        # Get tasks to run
        if task_ids:
            tasks = []
            for task_id in task_ids:
                task = self.task_registry.get_task(task_id)
                if task:
                    tasks.append(task)
                else:
                    logger.warning(f"Task not found: {task_id}")
        else:
            tasks = self.task_registry.get_all_tasks()

        if not tasks:
            raise ValueError("No tasks to run")

        # Use config defaults if not specified
        if output_format is None:
            output_format = self.config.output_format

        logger.info(f"Running {len(tasks)} tasks for batch: {batch_name}")

        # Execute batch benchmark
        async with ExecutionEngine(self.config) as engine:
            results = await engine.execute_benchmark(
                tasks=tasks, profile=batch_config.profile, sample_size=batch_config.sample_size
            )

        # Add batch info to results
        results["batch_info"] = {
            "batch_name": batch_name,
            "config": batch_config.dict() if hasattr(batch_config, "dict") else str(batch_config),
        }

        batch_results = [results]

        # Generate batch report
        if output_filename or output_format != OutputFormat.CONSOLE:
            report_file = self.report_generator.generate_batch_report(batch_results, output_format, output_filename)
            logger.info(f"Batch report saved to: {report_file}")

        return batch_results

    async def run_custom_batch(
        self,
        configurations: List[Dict[str, Any]],
        task_ids: Optional[List[str]] = None,
        output_format: Optional[OutputFormat] = None,
        output_filename: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run a custom batch of benchmark configurations.

        Args:
            configurations: List of configuration dictionaries
            task_ids: List of task IDs to run (all if None)
            output_format: Output format (config default if None)
            output_filename: Output filename (auto-generated if None)

        Returns:
            List of benchmark results for each configuration
        """
        logger.info(f"Starting custom batch with {len(configurations)} configurations")

        # Get tasks to run
        if task_ids:
            tasks = []
            for task_id in task_ids:
                task = self.task_registry.get_task(task_id)
                if task:
                    tasks.append(task)
                else:
                    logger.warning(f"Task not found: {task_id}")
        else:
            tasks = self.task_registry.get_all_tasks()

        if not tasks:
            raise ValueError("No tasks to run")

        # Use config defaults if not specified
        if output_format is None:
            output_format = self.config.output_format

        # Execute batch benchmarks
        async with ExecutionEngine(self.config) as engine:
            results = await engine.execute_batch(configurations, tasks)

        # Generate batch report
        if output_filename or output_format != OutputFormat.CONSOLE:
            report_file = self.report_generator.generate_batch_report(results, output_format, output_filename)
            logger.info(f"Custom batch report saved to: {report_file}")

        return results

    async def run_comparison_benchmark(
        self,
        profiles: List[HardwareProfile],
        task_ids: Optional[List[str]] = None,
        sample_size: Optional[int] = None,
        output_format: Optional[OutputFormat] = None,
        output_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run a comparison benchmark across multiple profiles.

        Args:
            profiles: List of hardware profiles to compare
            task_ids: List of task IDs to run (all if None)
            sample_size: Number of samples per task (uses profile defaults if None)
            output_format: Output format (config default if None)
            output_filename: Output filename (auto-generated if None)

        Returns:
            Dictionary containing comparison results
        """
        logger.info(f"Starting comparison benchmark across {len(profiles)} profiles")

        # Get tasks to run
        if task_ids:
            tasks = []
            for task_id in task_ids:
                task = self.task_registry.get_task(task_id)
                if task:
                    tasks.append(task)
                else:
                    logger.warning(f"Task not found: {task_id}")
        else:
            tasks = self.task_registry.get_all_tasks()

        if not tasks:
            raise ValueError("No tasks to run")

        # Use config defaults if not specified
        if output_format is None:
            output_format = self.config.output_format

        # Execute benchmarks for each profile
        results_by_profile = {}

        async with ExecutionEngine(self.config) as engine:
            for profile in profiles:
                logger.info(f"Running benchmark for profile: {profile.value}")

                profile_sample_size = sample_size or self.config.get_sample_size(profile)

                profile_results = await engine.execute_benchmark(
                    tasks=tasks, profile=profile, sample_size=profile_sample_size
                )

                results_by_profile[profile.value] = profile_results

        # Create comparison report
        comparison_data = {
            "comparison_info": {"profiles": [p.value for p in profiles], "tasks": len(tasks), "timestamp": time.time()},
            "results_by_profile": results_by_profile,
            "profile_comparison": self._generate_profile_comparison(results_by_profile),
        }

        # Generate comparison report
        if output_filename or output_format != OutputFormat.CONSOLE:
            report_file = self.report_generator.generate_report(comparison_data, output_format, output_filename)
            logger.info(f"Comparison report saved to: {report_file}")

        return comparison_data

    def _generate_profile_comparison(self, results_by_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison analysis between profiles."""
        comparison = {}

        for profile_name, profile_results in results_by_profile.items():
            comparison_metrics = profile_results.get("comparison_metrics", {})

            comparison[profile_name] = {
                "token_reduction": comparison_metrics.get("token_reduction_percent", 0),
                "time_reduction": comparison_metrics.get("time_reduction_percent", 0),
                "efficiency_improvement": comparison_metrics.get("efficiency_improvement_percent", 0),
                "sample_size": comparison_metrics.get("sample_size", 0),
            }

        return comparison

    def list_available_tasks(self) -> List[Dict[str, Any]]:
        """List all available tasks in the registry."""
        tasks = self.task_registry.get_all_tasks()
        return [
            {
                "task_id": task.task_id,
                "name": task.name,
                "description": task.description,
                "workflow_type": task.workflow_type.value,
                "timeout": task.timeout,
                "target_files": task.target_files,
            }
            for task in tasks
        ]

    def list_available_profiles(self) -> List[Dict[str, Any]]:
        """List all available hardware profiles."""
        profiles = []
        for profile in HardwareProfile:
            instances = self.config.get_profile_instances(profile)
            profiles.append(
                {
                    "profile": profile.value,
                    "description": self._get_profile_description(profile),
                    "instances": len(instances),
                    "models": [instance.model for instance in instances],
                    "default_sample_size": self.config.get_sample_size(profile),
                }
            )
        return profiles

    def _get_profile_description(self, profile: HardwareProfile) -> str:
        """Get human-readable description for a profile."""
        descriptions = {
            HardwareProfile.LIGHT: "Laptop/minimal (8GB+ RAM, 2+ cores)",
            HardwareProfile.MEDIUM: "Desktop/development (16GB+ RAM, 4+ cores)",
            HardwareProfile.HEAVY: "Server/comprehensive (32GB+ RAM, 8+ cores)",
        }
        return descriptions.get(profile, "Unknown profile")

    def list_available_batches(self) -> List[Dict[str, Any]]:
        """List all available batch configurations."""
        batches = []
        for batch_name, batch_config in self.config.batch_configurations.items():
            batches.append(
                {
                    "batch_name": batch_name,
                    "description": batch_config.description,
                    "profile": batch_config.profile.value,
                    "sample_size": batch_config.sample_size,
                    "repetitions": batch_config.repetitions,
                    "timeout": batch_config.timeout,
                }
            )
        return batches

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "profiles": len(self.config.profiles),
            "tasks": len(self.task_registry.get_all_tasks()),
            "batches": len(self.config.batch_configurations),
            "output_directory": str(self.config.output_directory),
            "execution_mode": self.config.execution_mode.value,
            "output_format": self.config.output_format.value,
            "docker_compose_file": str(self.config.docker_compose_file),
            "container_startup_timeout": self.config.container_startup_timeout,
            "task_timeout": self.config.task_timeout,
            "retry_attempts": self.config.retry_attempts,
        }

    def add_custom_task(
        self,
        task_id: str,
        name: str,
        description: str,
        workflow_type: str,
        baseline_prompt: str,
        tools_prompt: str,
        **kwargs,
    ) -> bool:
        """Add a custom task to the registry."""
        try:
            from .config import WorkflowType

            workflow_enum = WorkflowType(workflow_type)

            task = self.task_registry.create_custom_task(
                task_id=task_id,
                name=name,
                description=description,
                workflow_type=workflow_enum,
                baseline_prompt=baseline_prompt,
                tools_prompt=tools_prompt,
                **kwargs,
            )

            # Validate the task
            issues = self.task_registry.validate_task(task)
            if issues:
                logger.warning(f"Task validation issues: {issues}")
                return False

            logger.info(f"Added custom task: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add custom task: {e}")
            return False

    def get_task_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the task registry."""
        return self.task_registry.get_task_stats()

    def validate_setup(self) -> Dict[str, Any]:
        """Validate the entire benchmark setup."""
        issues = []
        warnings = []

        # Configuration validation
        config_issues = self.config.validate_runtime()
        issues.extend(config_issues)

        # Task validation
        for task in self.task_registry.get_all_tasks():
            task_issues = self.task_registry.validate_task(task)
            if task_issues:
                issues.extend([f"Task {task.task_id}: {issue}" for issue in task_issues])

        # Profile validation
        for profile in HardwareProfile:
            instances = self.config.get_profile_instances(profile)
            if not instances:
                warnings.append(f"No instances configured for profile: {profile.value}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "profiles_available": len(self.config.profiles),
            "tasks_available": len(self.task_registry.get_all_tasks()),
            "batches_available": len(self.config.batch_configurations),
        }
