"""
Execution engine for AI Development Tools benchmarking.

Handles model orchestration, container management, and task execution
with proper error handling and resource management.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set

import aiohttp

from ..core.container_orchestrator import ContainerOrchestrator
from .config import BenchmarkConfig, ExecutionMode, HardwareProfile, ModelInstance
from .metrics import MetricsCollector
from .tasks import BenchmarkTask, TaskApproach, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Handles execution of benchmark tasks across multiple models and containers."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.orchestrator = ContainerOrchestrator(str(config.docker_compose_file))
        self.metrics = MetricsCollector()
        self._active_profiles: Set[HardwareProfile] = set()
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphores: Dict[str, asyncio.Semaphore] = {}

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

        # Clean up any active profiles
        for profile in self._active_profiles.copy():
            await self.stop_profile(profile)

    async def start_profile(self, profile: HardwareProfile) -> List[ModelInstance]:
        """Start containers for a hardware profile and return ready instances."""
        logger.info(f"Starting containers for profile: {profile.value}")

        try:
            # Start containers
            self.orchestrator.up(profile=profile.value, build=False)

            # Get instances for this profile
            instances = self.config.get_profile_instances(profile)
            if not instances:
                raise ValueError(f"No instances configured for profile: {profile}")

            # Wait for instances to be ready
            ready_instances = await self.orchestrator.wait_for_instances(
                instances, max_wait=self.config.container_startup_timeout
            )

            if not ready_instances:
                raise RuntimeError(f"No instances became ready for profile: {profile}")

            # Create semaphores for concurrent request limiting
            for instance in ready_instances:
                self._semaphores[instance.name] = asyncio.Semaphore(instance.max_concurrent)

            self._active_profiles.add(profile)
            logger.info(f"Started {len(ready_instances)} instances for profile {profile.value}")

            return ready_instances

        except Exception as e:
            logger.error(f"Failed to start profile {profile.value}: {e}")
            raise

    async def stop_profile(self, profile: HardwareProfile) -> None:
        """Stop containers for a hardware profile."""
        logger.info(f"Stopping containers for profile: {profile.value}")

        try:
            self.orchestrator.down(profile=profile.value)
            self._active_profiles.discard(profile)

            # Clean up semaphores
            instances = self.config.get_profile_instances(profile)
            for instance in instances:
                self._semaphores.pop(instance.name, None)

        except Exception as e:
            logger.error(f"Failed to stop profile {profile.value}: {e}")
            raise

    async def execute_task_baseline(
        self, task: BenchmarkTask, model_instance: ModelInstance, sample_num: int = 0
    ) -> TaskResult:
        """Execute a task using baseline approach (simulated)."""
        result = task.create_result(TaskApproach.BASELINE, model_instance.name, sample_num)
        result.status = TaskStatus.RUNNING

        try:
            # Simulate baseline execution with realistic timing
            await asyncio.sleep(0.1)  # Simulate processing time

            # Simulate baseline metrics based on workflow type
            if task.workflow_type.value == "safety_check":
                tokens_in, tokens_out = 200, 150
                duration = 2.0
            elif task.workflow_type.value == "pattern_analysis":
                tokens_in, tokens_out = 250, 300
                duration = 3.0
            elif task.workflow_type.value == "context_analysis":
                tokens_in, tokens_out = 400, 600
                duration = 8.0
            else:
                tokens_in, tokens_out = 300, 400
                duration = 5.0

            # Add some realistic variation
            duration += (sample_num % 3) * 0.2  # Slight variation per sample

            # Simulate additional processing time
            await asyncio.sleep(min(duration / 20, 0.5))

            result.mark_completed(
                response=f"Baseline result for {task.name}", tokens_in=tokens_in, tokens_out=tokens_out
            )

        except Exception as e:
            result.mark_failed(str(e))

        return result

    async def execute_task_tools(
        self, task: BenchmarkTask, model_instance: ModelInstance, sample_num: int = 0
    ) -> TaskResult:
        """Execute a task using AI development tools approach."""
        result = task.create_result(TaskApproach.TOOLS, model_instance.name, sample_num)
        result.status = TaskStatus.RUNNING

        if not self._session:
            result.mark_failed("No HTTP session available")
            return result

        # Use semaphore to limit concurrent requests per instance
        semaphore = self._semaphores.get(model_instance.name)
        if not semaphore:
            result.mark_failed(f"No semaphore available for instance: {model_instance.name}")
            return result

        async with semaphore:
            try:
                # Make request to Ollama API
                api_result = await self._make_ollama_request(model_instance, task.tools_prompt, task.timeout)

                if api_result["success"]:
                    result.mark_completed(
                        response=api_result["response"],
                        tokens_in=api_result["input_tokens"],
                        tokens_out=api_result["output_tokens"],
                    )
                else:
                    result.mark_failed(api_result["error"])

            except Exception as e:
                result.mark_failed(str(e))

        return result

    async def _make_ollama_request(self, instance: ModelInstance, prompt: str, timeout: int) -> Dict[str, Any]:
        """Make a request to Ollama API."""
        payload = {
            "model": instance.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "top_p": 0.9, "num_predict": 150},
        }

        start_time = time.time()

        try:
            async with self._session.post(
                f"{instance.url}/api/generate", json=payload, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                end_time = time.time()

                if response.status == 200:
                    result = await response.json()

                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "input_tokens": result.get("prompt_eval_count", 0),
                        "output_tokens": result.get("eval_count", 0),
                        "duration": end_time - start_time,
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "duration": end_time - start_time,
                    }

        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout", "duration": time.time() - start_time}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time() - start_time}

    async def execute_task_samples(
        self,
        task: BenchmarkTask,
        instances: List[ModelInstance],
        sample_size: int,
        approaches: List[TaskApproach] = None,
    ) -> List[TaskResult]:
        """Execute multiple samples of a task across instances."""
        if approaches is None:
            approaches = [TaskApproach.BASELINE, TaskApproach.TOOLS]

        results = []

        # Create all task executions
        task_coroutines = []

        for approach in approaches:
            for instance in instances:
                for sample_num in range(sample_size):
                    if approach == TaskApproach.BASELINE:
                        coro = self.execute_task_baseline(task, instance, sample_num)
                    else:
                        coro = self.execute_task_tools(task, instance, sample_num)

                    task_coroutines.append(coro)

        # Execute based on execution mode
        if self.config.execution_mode == ExecutionMode.SEQUENTIAL:
            # Run tasks sequentially
            for coro in task_coroutines:
                result = await coro
                results.append(result)
                await self.metrics.add_task_result(result)

        elif self.config.execution_mode == ExecutionMode.PARALLEL:
            # Run tasks in parallel with limited concurrency
            semaphore = asyncio.Semaphore(self.config.max_concurrent_batches * 2)

            async def run_with_semaphore(coro):
                async with semaphore:
                    return await coro

            limited_coroutines = [run_with_semaphore(coro) for coro in task_coroutines]
            task_results = await asyncio.gather(*limited_coroutines, return_exceptions=True)

            for result in task_results:
                if isinstance(result, Exception):
                    # Create failed result for exception
                    failed_result = TaskResult(
                        task_id=task.task_id,
                        approach=TaskApproach.TOOLS,  # Default
                        model_instance="unknown",
                        status=TaskStatus.FAILED,
                        start_time=time.time(),
                        error=str(result),
                    )
                    results.append(failed_result)
                else:
                    results.append(result)

                await self.metrics.add_task_result(results[-1])

        else:  # ASYNC mode
            # Run all tasks fully async
            task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

            for result in task_results:
                if isinstance(result, Exception):
                    # Create failed result for exception
                    failed_result = TaskResult(
                        task_id=task.task_id,
                        approach=TaskApproach.TOOLS,  # Default
                        model_instance="unknown",
                        status=TaskStatus.FAILED,
                        start_time=time.time(),
                        error=str(result),
                    )
                    results.append(failed_result)
                else:
                    results.append(result)

                await self.metrics.add_task_result(results[-1])

        return results

    async def execute_benchmark(
        self,
        tasks: List[BenchmarkTask],
        profile: HardwareProfile,
        sample_size: Optional[int] = None,
        approaches: List[TaskApproach] = None,
    ) -> Dict[str, Any]:
        """Execute a full benchmark across tasks and instances."""
        if sample_size is None:
            sample_size = self.config.get_sample_size(profile)

        if approaches is None:
            approaches = [TaskApproach.BASELINE, TaskApproach.TOOLS]

        logger.info(f"Starting benchmark execution for profile: {profile.value}")
        logger.info(f"Tasks: {len(tasks)}, Sample size: {sample_size}")

        # Start metrics collection
        await self.metrics.start_collection()

        try:
            # Start profile containers
            instances = await self.start_profile(profile)

            # Execute all tasks
            all_results = []

            for task in tasks:
                logger.info(f"Executing task: {task.name}")

                task_results = await self.execute_task_samples(task, instances, sample_size, approaches)

                all_results.extend(task_results)

            # Stop metrics collection
            await self.metrics.stop_collection()

            # Calculate metrics
            overall_metrics = self.metrics.calculate_metrics()
            comparison_metrics = self.metrics.calculate_comparison_metrics()
            metrics_by_task = self.metrics.get_metrics_by_task()
            metrics_by_model = self.metrics.get_metrics_by_model()

            return {
                "benchmark_info": {
                    "profile": profile.value,
                    "total_tasks": len(tasks),
                    "sample_size": sample_size,
                    "approaches": [a.value for a in approaches],
                    "instances": len(instances),
                    "execution_mode": self.config.execution_mode.value,
                    "timestamp": time.time(),
                },
                "results": [result.to_dict() for result in all_results],
                "overall_metrics": overall_metrics.to_dict(),
                "comparison_metrics": comparison_metrics.to_dict(),
                "metrics_by_task": {k: v.to_dict() for k, v in metrics_by_task.items()},
                "metrics_by_model": {k: v.to_dict() for k, v in metrics_by_model.items()},
            }

        except Exception as e:
            logger.error(f"Benchmark execution failed: {e}")
            raise
        finally:
            # Always stop the profile
            if profile in self._active_profiles:
                await self.stop_profile(profile)

    async def execute_batch(
        self, batch_configs: List[Dict[str, Any]], tasks: List[BenchmarkTask]
    ) -> List[Dict[str, Any]]:
        """Execute multiple benchmark configurations in batch."""
        logger.info(f"Starting batch execution with {len(batch_configs)} configurations")

        results = []

        for i, config in enumerate(batch_configs):
            logger.info(f"Executing batch {i + 1}/{len(batch_configs)}: {config.get('name', 'unknown')}")

            try:
                profile = HardwareProfile(config["profile"])
                sample_size = config.get("sample_size", self.config.get_sample_size(profile))

                result = await self.execute_benchmark(tasks, profile, sample_size)

                result["batch_info"] = config
                results.append(result)

            except Exception as e:
                logger.error(f"Batch configuration failed: {e}")
                results.append({"batch_info": config, "error": str(e), "success": False})

        return results

    def get_active_profiles(self) -> Set[HardwareProfile]:
        """Get currently active profiles."""
        return self._active_profiles.copy()

    def get_metrics_collector(self) -> MetricsCollector:
        """Get the metrics collector for this execution."""
        return self.metrics
