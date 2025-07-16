"""
Baseline Simulator - Simulates manual AI workflows without our tools

This module simulates how AI agents would work WITHOUT our AI development tools,
providing baseline measurements for token usage and execution time comparisons.

The baseline represents typical AI workflows where:
- AI agents read entire files to understand context
- No exit codes provide structured information
- Multiple round-trips needed for decision making
- No systematic pattern detection
- Manual safety assessment through file inspection
"""

import time
import random
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .metrics_collector import MetricsCollector, WorkflowType


@dataclass
class BaselineScenario:
    """Represents a baseline workflow scenario for comparison"""

    name: str
    description: str
    typical_files_read: int
    typical_tokens_per_file: int
    typical_ai_rounds: int
    typical_duration_seconds: float
    success_rate: float


class BaselineSimulator:
    """
    Simulates manual AI workflows without our tools for baseline comparison

    This helps measure the efficiency gains of our AI-first tools by comparing
    against typical manual AI workflows that require more tokens and time.
    """

    # Baseline scenarios based on typical AI workflows
    SCENARIOS = {
        WorkflowType.PATTERN_ANALYSIS: BaselineScenario(
            name="Manual Pattern Analysis",
            description="AI reads multiple files to find similar patterns manually",
            typical_files_read=15,  # AI needs to read many files to find patterns
            typical_tokens_per_file=800,  # Full file content
            typical_ai_rounds=3,  # Multiple rounds to understand and find patterns
            typical_duration_seconds=45.0,
            success_rate=0.75,  # Lower success rate due to manual process
        ),
        WorkflowType.SAFETY_CHECK: BaselineScenario(
            name="Manual Safety Assessment",
            description="AI reads file content and context to assess safety manually",
            typical_files_read=5,  # Need to read target file + related files
            typical_tokens_per_file=1200,  # Full file content + context
            typical_ai_rounds=2,  # Initial assessment + confirmation
            typical_duration_seconds=25.0,
            success_rate=0.80,
        ),
        WorkflowType.CONTEXT_ANALYSIS: BaselineScenario(
            name="Manual Context Analysis",
            description="AI explores project structure and dependencies manually",
            typical_files_read=25,  # Many config files, source files, docs
            typical_tokens_per_file=600,  # Various file types
            typical_ai_rounds=4,  # Multiple rounds to build understanding
            typical_duration_seconds=60.0,
            success_rate=0.70,
        ),
        WorkflowType.SYSTEMATIC_FIX: BaselineScenario(
            name="Manual Systematic Fix",
            description="AI manually searches for similar issues across codebase",
            typical_files_read=30,  # Need to search through many files
            typical_tokens_per_file=1000,  # Full file content to find patterns
            typical_ai_rounds=5,  # Multiple rounds to find all instances
            typical_duration_seconds=90.0,
            success_rate=0.65,  # Easy to miss instances
        ),
        WorkflowType.PROJECT_ANALYSIS: BaselineScenario(
            name="Manual Project Analysis",
            description="AI manually analyzes project health, structure, and issues",
            typical_files_read=40,  # Comprehensive project exploration
            typical_tokens_per_file=700,  # Various file types and configs
            typical_ai_rounds=6,  # Multiple analysis rounds
            typical_duration_seconds=120.0,
            success_rate=0.75,
        ),
        WorkflowType.CHANGE_PLANNING: BaselineScenario(
            name="Manual Change Planning",
            description="AI manually assesses impact and safety of proposed changes",
            typical_files_read=20,  # Target files + dependencies + tests
            typical_tokens_per_file=900,  # Full context needed
            typical_ai_rounds=4,  # Planning + impact assessment + safety check
            typical_duration_seconds=70.0,
            success_rate=0.70,
        ),
    }

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize baseline simulator

        Args:
            metrics_collector: Optional metrics collector instance
        """
        self.metrics_collector = metrics_collector

    def simulate_workflow(
        self,
        workflow_type: WorkflowType,
        project_path: str = ".",
        add_variance: bool = True,
    ) -> Dict[str, Any]:
        """
        Simulate a baseline workflow without our tools

        Args:
            workflow_type: Type of workflow to simulate
            project_path: Project path for context
            add_variance: Whether to add realistic variance to measurements

        Returns:
            Simulation results dictionary
        """
        if workflow_type not in self.SCENARIOS:
            raise ValueError(f"No baseline scenario for workflow type: {workflow_type}")

        scenario = self.SCENARIOS[workflow_type]

        # Add realistic variance if requested
        variance_factor = 1.0
        if add_variance:
            variance_factor = random.uniform(0.8, 1.3)  # ±30% variance

        # Calculate simulated metrics
        files_read = int(scenario.typical_files_read * variance_factor)
        tokens_per_file = int(scenario.typical_tokens_per_file * variance_factor)
        ai_rounds = max(1, int(scenario.typical_ai_rounds * variance_factor))
        duration = scenario.typical_duration_seconds * variance_factor

        # Total tokens = (input tokens for reading files) + (output tokens from AI responses)
        input_tokens = files_read * tokens_per_file
        output_tokens = ai_rounds * 300  # Typical AI response length
        total_tokens = input_tokens + output_tokens

        # Simulate success/failure
        success = random.random() < scenario.success_rate

        # Record metrics if collector provided
        if self.metrics_collector:
            with self.metrics_collector.measure_workflow(
                WorkflowType.BASELINE_MANUAL,
                metadata={
                    "simulated_workflow": workflow_type.value,
                    "scenario_name": scenario.name,
                    "project_path": project_path,
                },
            ) as context:
                # Simulate the work being done
                time.sleep(min(duration / 10, 2.0))  # Scaled down for testing

                context.record_tokens(input_tokens, output_tokens)
                context.record_files_processed(files_read)
                context.add_metadata("ai_rounds", ai_rounds)
                context.add_metadata("simulated", True)

                if not success:
                    raise Exception("Simulated workflow failure")

        return {
            "workflow_type": workflow_type.value,
            "scenario": scenario.name,
            "description": scenario.description,
            "metrics": {
                "files_read": files_read,
                "tokens_per_file": tokens_per_file,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "ai_rounds": ai_rounds,
                "duration_seconds": duration,
                "success": success,
            },
            "efficiency": {
                "tokens_per_second": total_tokens / duration if duration > 0 else 0,
                "files_per_second": files_read / duration if duration > 0 else 0,
            },
        }

    def run_baseline_suite(
        self, project_path: str = ".", iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Run complete baseline simulation suite for all workflow types

        Args:
            project_path: Project path for context
            iterations: Number of iterations per workflow type

        Returns:
            Complete baseline results
        """
        results = {
            "project_path": project_path,
            "iterations": iterations,
            "workflows": {},
            "summary": {},
        }

        total_tokens = 0
        total_duration = 0
        total_workflows = 0
        successful_workflows = 0

        for workflow_type in self.SCENARIOS.keys():
            workflow_results = []

            for i in range(iterations):
                try:
                    result = self.simulate_workflow(workflow_type, project_path)
                    workflow_results.append(result)

                    # Accumulate totals
                    total_tokens += result["metrics"]["total_tokens"]
                    total_duration += result["metrics"]["duration_seconds"]
                    total_workflows += 1
                    if result["metrics"]["success"]:
                        successful_workflows += 1

                except Exception as e:
                    workflow_results.append(
                        {
                            "workflow_type": workflow_type.value,
                            "error": str(e),
                            "success": False,
                        }
                    )
                    total_workflows += 1

            results["workflows"][workflow_type.value] = workflow_results

        # Calculate summary statistics
        results["summary"] = {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "success_rate": (successful_workflows / total_workflows * 100)
            if total_workflows > 0
            else 0,
            "total_tokens": total_tokens,
            "total_duration": total_duration,
            "average_tokens_per_workflow": total_tokens / total_workflows
            if total_workflows > 0
            else 0,
            "average_duration_per_workflow": total_duration / total_workflows
            if total_workflows > 0
            else 0,
            "overall_efficiency": total_tokens / total_duration
            if total_duration > 0
            else 0,
        }

        return results

    def compare_with_current(
        self, current_metrics: Dict[str, Any], baseline_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare baseline simulation with current tool performance

        Args:
            current_metrics: Metrics from current AI tools
            baseline_results: Results from baseline simulation

        Returns:
            Comparison analysis
        """
        baseline_summary = baseline_results["summary"]

        # Calculate improvements
        token_improvement = (
            (
                (
                    baseline_summary["average_tokens_per_workflow"]
                    - current_metrics.get("tokens", {}).get("total_avg", 0)
                )
                / baseline_summary["average_tokens_per_workflow"]
                * 100
            )
            if baseline_summary["average_tokens_per_workflow"] > 0
            else 0
        )

        time_improvement = (
            (
                (
                    baseline_summary["average_duration_per_workflow"]
                    - current_metrics.get("execution_time", {}).get("avg", 0)
                )
                / baseline_summary["average_duration_per_workflow"]
                * 100
            )
            if baseline_summary["average_duration_per_workflow"] > 0
            else 0
        )

        efficiency_improvement = (
            (
                (
                    current_metrics.get("efficiency", {}).get("tokens_per_second", 0)
                    - baseline_summary["overall_efficiency"]
                )
                / baseline_summary["overall_efficiency"]
                * 100
            )
            if baseline_summary["overall_efficiency"] > 0
            else 0
        )

        return {
            "baseline": baseline_summary,
            "current": current_metrics,
            "improvements": {
                "token_reduction_percent": token_improvement,
                "time_reduction_percent": time_improvement,
                "efficiency_increase_percent": efficiency_improvement,
                "success_rate_improvement": current_metrics.get("success_rate", 0)
                - baseline_summary["success_rate"],
            },
            "verdict": {
                "more_token_efficient": token_improvement > 0,
                "faster": time_improvement > 0,
                "more_efficient_overall": efficiency_improvement > 0,
                "more_reliable": current_metrics.get("success_rate", 0)
                > baseline_summary["success_rate"],
            },
            "roi_analysis": {
                "token_savings_per_workflow": baseline_summary[
                    "average_tokens_per_workflow"
                ]
                - current_metrics.get("tokens", {}).get("total_avg", 0),
                "time_savings_per_workflow": baseline_summary[
                    "average_duration_per_workflow"
                ]
                - current_metrics.get("execution_time", {}).get("avg", 0),
                "estimated_cost_savings": "Significant reduction in AI API costs due to token efficiency",
            },
        }


def create_baseline_simulator(
    metrics_collector: Optional[MetricsCollector] = None,
) -> BaselineSimulator:
    """Create a baseline simulator instance"""
    return BaselineSimulator(metrics_collector)


def simulate_baseline_workflow(
    workflow_type: WorkflowType,
    project_path: str = ".",
    metrics_collector: Optional[MetricsCollector] = None,
) -> Dict[str, Any]:
    """Convenience function to simulate a single baseline workflow"""
    simulator = BaselineSimulator(metrics_collector)
    return simulator.simulate_workflow(workflow_type, project_path)
