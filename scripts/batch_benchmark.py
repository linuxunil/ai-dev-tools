#!/usr/bin/env python3
"""
Batch Benchmark Runner

Executes multiple benchmark configurations in sequence or parallel
for comprehensive performance analysis across different scenarios.
"""

import asyncio
import json
import time
import statistics
from pathlib import Path
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from async_benchmark import (
    get_benchmark_profile, 
    run_comprehensive_benchmark_async,
    create_benchmark_tasks,
    calculate_improvement_stats,
    wait_for_instances
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchConfiguration:
    def __init__(self, name: str, profile: str, sample_size: int, repetitions: int = 1, description: str = ""):
        self.name = name
        self.profile = profile
        self.sample_size = sample_size
        self.description = description

class BatchRunner:
    def __init__(self, output_dir: str = "batch_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.batch_results = []
        
    def get_predefined_batches(self) -> Dict[str, List[BatchConfiguration]]:
        """Get predefined batch configurations"""
        
        return {
            "quick": [
                BatchConfiguration("light_quick", "light", 2, 1, "Quick laptop test (2 samples)"),
                BatchConfiguration("medium_quick", "medium", 3, 1, "Quick desktop test (3 samples)")
            ],
            
            "standard": [
                BatchConfiguration("light_standard", "light", 8, 10, "Standard laptop benchmark (80 total samples)"),
                BatchConfiguration("medium_standard", "medium", 8, 10, "Standard desktop benchmark (80 total samples)"),
                BatchConfiguration("heavy_standard", "heavy", 8, 10, "Standard server benchmark (80 total samples)")
            ],
            
            "comprehensive": [
                BatchConfiguration("light_comprehensive", "light", 10, 1, "Comprehensive laptop analysis (10 samples)"),
                BatchConfiguration("medium_comprehensive", "medium", 15, 1, "Comprehensive desktop analysis (15 samples)"),
                BatchConfiguration("heavy_comprehensive", "heavy", 20, 1, "Comprehensive server analysis (20 samples)")
            ],
            
            "scaling": [
                BatchConfiguration("scaling_small", "light", 5, 1, "Small model scaling test (5 samples)"),
                BatchConfiguration("scaling_medium", "medium", 5, 1, "Medium model scaling test (5 samples)"),
                BatchConfiguration("scaling_large", "heavy", 5, 1, "Large model scaling test (5 samples)")
            ],
            
            "sample_size": [
                BatchConfiguration("samples_3", "medium", 3, 1, "Low sample count (3 samples)"),
                BatchConfiguration("samples_6", "medium", 6, 1, "Medium sample count (6 samples)"),
                BatchConfiguration("samples_12", "medium", 12, 1, "High sample count (12 samples)"),
                BatchConfiguration("samples_20", "medium", 20, 1, "Very high sample count (20 samples)")
            ]
        }
    
    async def run_single_configuration(self, config: BatchConfiguration) -> Dict[str, Any]:
        """Run a single benchmark configuration"""
        
        logger.info(f"🔄 Running batch: {config.name} ({config.description})")
        logger.info(f"   Profile: {config.profile}, Samples per run: {config.sample_size}, Repetitions: {config.repetitions}")
        
        start_time = time.time()
        all_run_results = []
        
        try:
            # Get instances for this profile
            instances = get_benchmark_profile(config.profile)
            
            # Wait for instances to be ready
            ready_instances = await wait_for_instances(instances, max_wait=180)
            
            if not ready_instances:
                logger.error(f"❌ No instances ready for {config.name}")
                return {
                    "config": config.__dict__,
                    "success": False,
                    "error": "No instances ready",
                    "duration": time.time() - start_time
                }
            
            # Create tasks once
            tasks = create_benchmark_tasks()
            
            for i in range(config.repetitions):
                logger.info(f"   Running repetition {i+1}/{config.repetitions} for {config.name}")
                
                # Run benchmark
                results = await run_comprehensive_benchmark_async(
                    ready_instances, tasks, config.sample_size
                )
                all_run_results.append(results)
            
            # Aggregate results from all repetitions
            aggregated_results = self._aggregate_repetition_results(all_run_results)
            
            # Add batch info
            aggregated_results["batch_info"] = {
                "config_name": config.name,
                "profile": config.profile,
                "sample_size_per_run": config.sample_size,
                "repetitions": config.repetitions,
                "total_samples": config.sample_size * config.repetitions,
                "description": config.description,
                "instances_used": len(ready_instances),
                "batch_duration": time.time() - start_time
            }
            
            # Calculate improvements
            improvements = calculate_improvement_stats(aggregated_results)
            aggregated_results["improvements"] = improvements
            
            logger.info(f"✅ Completed {config.name} in {time.time() - start_time:.1f}s")
            
            return {
                "config": config.__dict__,
                "success": True,
                "results": aggregated_results,
                "duration": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"❌ Failed {config.name}: {e}")
            return {
                "config": config.__dict__,
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def run_batch_sequential(self, configs: List[BatchConfiguration]) -> List[Dict[str, Any]]:
        """Run batch configurations sequentially"""
        
        logger.info(f"🔄 Running {len(configs)} configurations sequentially")
        results = []
        
        for i, config in enumerate(configs, 1):
            logger.info(f"📊 Batch {i}/{len(configs)}: {config.name}")
            
            result = await self.run_single_configuration(config)
            results.append(result)
            
            # Brief pause between runs
            if i < len(configs):
                logger.info("⏳ Pausing 10s between batches...")
                await asyncio.sleep(10)
        
        return results
    
    async def run_batch_parallel(self, configs: List[BatchConfiguration], 
                                max_concurrent: int = 2) -> List[Dict[str, Any]]:
        """Run batch configurations in parallel with concurrency limit"""
        
        logger.info(f"🔄 Running {len(configs)} configurations in parallel (max {max_concurrent})")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(config):
            async with semaphore:
                return await self.run_single_configuration(config)
        
        tasks = [run_with_semaphore(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "config": configs[i].__dict__,
                    "success": False,
                    "error": str(result),
                    "duration": 0
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def save_batch_results(self, batch_name: str, results: List[Dict[str, Any]], 
                          execution_mode: str) -> str:
        """Save batch results to file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"batch_{batch_name}_{execution_mode}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Calculate batch summary
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        total_duration = sum(r.get("duration", 0) for r in results)
        
        batch_summary = {
            "batch_info": {
                "batch_name": batch_name,
                "execution_mode": execution_mode,
                "timestamp": datetime.now().isoformat(),
                "total_configurations": len(results),
                "successful_runs": len(successful),
                "failed_runs": len(failed),
                "total_duration_seconds": total_duration
            },
            "configurations": results
        }
        
        # Add aggregated statistics if we have successful runs
        if successful:
            batch_summary["aggregated_stats"] = self.calculate_batch_statistics(successful)
        
        with open(filepath, 'w') as f:
            json.dump(batch_summary, f, indent=2)
        
        logger.info(f"💾 Batch results saved to: {filepath}")
        return str(filepath)
    
    def calculate_batch_statistics(self, successful_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregated statistics across batch runs"""
        
        all_improvements = []
        profile_stats = {}
        
        for result in successful_results:
            if "results" in result and "improvements" in result["results"]:
                improvements = result["results"]["improvements"]
                config = result["config"]
                
                # Collect all improvement percentages
                for model, stats in improvements.items():
                    all_improvements.append({
                        "profile": config["profile"],
                        "model": model,
                        "token_reduction": stats["token_reduction_percent"],
                        "time_reduction": stats["time_reduction_percent"]
                    })
                
                # Group by profile
                profile = config["profile"]
                if profile not in profile_stats:
                    profile_stats[profile] = []
                profile_stats[profile].extend(improvements.values())
        
        # Calculate overall statistics
        if all_improvements:
            token_reductions = [imp["token_reduction"] for imp in all_improvements]
            time_reductions = [imp["time_reduction"] for imp in all_improvements]
            
            return {
                "overall": {
                    "avg_token_reduction": statistics.mean(token_reductions),
                    "median_token_reduction": statistics.median(token_reductions),
                    "std_token_reduction": statistics.stdev(token_reductions) if len(token_reductions) > 1 else 0,
                    "avg_time_reduction": statistics.mean(time_reductions),
                    "median_time_reduction": statistics.median(time_reductions),
                    "std_time_reduction": statistics.stdev(time_reductions) if len(time_reductions) > 1 else 0,
                    "total_samples": len(all_improvements)
                },
                "by_profile": profile_stats
            }
        
        return {}

    def _aggregate_repetition_results(self, all_run_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates results from multiple benchmark repetitions."""
        if not all_run_results:
            return {}

        aggregated_data: Dict[str, Dict[str, List[float]]] = {}
        aggregated_metrics: Dict[str, Dict[str, List[float]]] = {}

        for run_result in all_run_results:
            if "data" in run_result:
                for model_name, model_data in run_result["data"].items():
                    if model_name not in aggregated_data:
                        aggregated_data[model_name] = {"total_tokens": [], "total_time": []}
                    aggregated_data[model_name]["total_tokens"].append(model_data.get("total_tokens", 0))
                    aggregated_data[model_name]["total_time"].append(model_data.get("total_time", 0))
            
            if "metrics" in run_result:
                for model_name, model_metrics in run_result["metrics"].items():
                    if model_name not in aggregated_metrics:
                        aggregated_metrics[model_name] = {
                            "avg_tokens_per_task": [],
                            "avg_time_per_task": [],
                            "success_rate": [],
                            "avg_token_efficiency": [],
                            "avg_time_efficiency": []
                        }
                    aggregated_metrics[model_name]["avg_tokens_per_task"].append(model_metrics.get("avg_tokens_per_task", 0))
                    aggregated_metrics[model_name]["avg_time_per_task"].append(model_metrics.get("avg_time_per_task", 0))
                    aggregated_metrics[model_name]["success_rate"].append(model_metrics.get("success_rate", 0))
                    aggregated_metrics[model_name]["avg_token_efficiency"].append(model_metrics.get("avg_token_efficiency", 0))
                    aggregated_metrics[model_name]["avg_time_efficiency"].append(model_metrics.get("avg_time_efficiency", 0))

        final_aggregated_results: Dict[str, Any] = {"data": {}, "metrics": {}}

        for model_name, data_values in aggregated_data.items():
            final_aggregated_results["data"][model_name] = {
                "total_tokens": statistics.mean(data_values["total_tokens"]) if data_values["total_tokens"] else 0,
                "total_time": statistics.mean(data_values["total_time"]) if data_values["total_time"] else 0,
            }
        
        for model_name, metric_values in aggregated_metrics.items():
            final_aggregated_results["metrics"][model_name] = {
                "avg_tokens_per_task": statistics.mean(metric_values["avg_tokens_per_task"]) if metric_values["avg_tokens_per_task"] else 0,
                "avg_time_per_task": statistics.mean(metric_values["avg_time_per_task"]) if metric_values["avg_time_per_task"] else 0,
                "success_rate": statistics.mean(metric_values["success_rate"]) if metric_values["success_rate"] else 0,
                "avg_token_efficiency": statistics.mean(metric_values["avg_token_efficiency"]) if metric_values["avg_token_efficiency"] else 0,
                "avg_time_efficiency": statistics.mean(metric_values["avg_time_efficiency"]) if metric_values["avg_time_efficiency"] else 0,
            }
        
        # Preserve other top-level keys if they exist and are consistent (e.g., 'baseline_metrics')
        # For simplicity, we'll assume 'baseline_metrics' is consistent across runs or take from the first run
        if "baseline_metrics" in all_run_results[0]:
            final_aggregated_results["baseline_metrics"] = all_run_results[0]["baseline_metrics"]

        return final_aggregated_results

async def main():
    parser = argparse.ArgumentParser(description="AI Development Tools Batch Benchmark Suite")
    parser.add_argument("batch_name", 
                       choices=["quick", "standard", "comprehensive", "scaling", "sample_size"],
                       help="Predefined batch configuration to run")
    parser.add_argument("--mode",
                       choices=["sequential", "parallel"],
                       default="sequential",
                       help="Execution mode (default: sequential)")
    parser.add_argument("--max-concurrent",
                       type=int,
                       default=2,
                       help="Max concurrent runs in parallel mode (default: 2)")
    parser.add_argument("--output-dir",
                       default="batch_results",
                       help="Output directory for results (default: batch_results)")
    
    args = parser.parse_args()
    
    print("🚀 AI Development Tools Batch Benchmark Suite")
    print(f"📊 Batch: {args.batch_name.upper()} | Mode: {args.mode.upper()}")
    print("=" * 70)
    
    # Initialize batch runner
    runner = BatchRunner(args.output_dir)
    
    # Get configurations
    predefined_batches = runner.get_predefined_batches()
    configs = predefined_batches[args.batch_name]
    
    print(f"📋 Running {len(configs)} configurations:")
    for i, config in enumerate(configs, 1):
        print(f"   {i}. {config.name}: {config.description}")
    print()
    
    start_time = time.time()
    
    # Run batch
    if args.mode == "sequential":
        results = await runner.run_batch_sequential(configs)
    else:
        results = await runner.run_batch_parallel(configs, args.max_concurrent)
    
    total_time = time.time() - start_time
    
    # Save results
    output_file = runner.save_batch_results(args.batch_name, results, args.mode)
    
    # Display summary
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    print(f"\n📊 BATCH RESULTS SUMMARY")
    print("=" * 50)
    print(f"✅ Successful runs: {len(successful)}/{len(results)}")
    print(f"❌ Failed runs: {len(failed)}")
    print(f"⏱️  Total duration: {total_time:.1f}s")
    print(f"💾 Results saved to: {output_file}")
    
    if failed:
        print(f"\n❌ FAILED CONFIGURATIONS:")
        for fail in failed:
            print(f"   • {fail['config']['name']}: {fail.get('error', 'Unknown error')}")
    
    if successful:
        print(f"\n🎯 PERFORMANCE OVERVIEW:")
        batch_stats = runner.calculate_batch_statistics(successful)
        if "overall" in batch_stats:
            overall = batch_stats["overall"]
            print(f"   Average token reduction: {overall['avg_token_reduction']:.1f}%")
            print(f"   Average time reduction: {overall['avg_time_reduction']:.1f}%")
            print(f"   Total data points: {overall['total_samples']}")

if __name__ == "__main__":
    asyncio.run(main())