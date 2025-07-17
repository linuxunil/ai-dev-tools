#!/usr/bin/env python3
"""
Async Multi-Model Benchmark Suite

Concurrently tests multiple models across multiple Ollama containers
for maximum performance and comprehensive statistical analysis.
"""

import asyncio
import aiohttp
import json
import time
import statistics
from pathlib import Path
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging
import toml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_dev_tools.core.metrics_collector import measure_workflow, WorkflowType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration from pyproject.toml
def load_config():
    try:
        with open(Path(__file__).parent.parent / "pyproject.toml", "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        logger.error("pyproject.toml not found. Ensure you are running from the project root or script directory.")
        exit(1)

CONFIG = load_config()
BENCHMARK_CONFIG = CONFIG.get("tool", {}).get("ai-dev-tools", {}).get("benchmark", {})

class ModelInstance:
    def __init__(self, name: str, model: str, host: str, port: int):
        self.name = name
        self.model = model
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        self.ready = False

class BenchmarkTask:
    def __init__(self, name: str, baseline_prompt: str, tools_prompt: str, 
                 workflow_type: WorkflowType):
        self.name = name
        self.baseline_prompt = baseline_prompt
        self.tools_prompt = tools_prompt
        self.workflow_type = workflow_type

async def make_ollama_request_async(session: aiohttp.ClientSession, 
                                   url: str, prompt: str, model: str, 
                                   timeout: int = 30) -> dict:
    """Make async request to Ollama API"""
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 150
        }
    }
    
    start_time = time.time()
    
    try:
        async with session.post(f"{url}/api/generate", 
                               json=payload, 
                               timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            end_time = time.time()
            
            if response.status == 200:
                result = await response.json()
                
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "input_tokens": result.get("prompt_eval_count", 0),
                    "output_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                    "duration": end_time - start_time,
                    "model": model,
                    "timestamp": end_time,
                    "url": url
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status}: {error_text}",
                    "duration": end_time - start_time,
                    "timestamp": end_time,
                    "url": url
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "duration": time.time() - start_time,
            "timestamp": time.time(),
            "url": url
        }

async def check_instance_health(session: aiohttp.ClientSession, 
                               instance: ModelInstance) -> bool:
    """Check if an Ollama instance is ready"""
    
    try:
        async with session.get(f"{instance.url}/api/version", 
                              timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                # Check if model is loaded
                async with session.get(f"{instance.url}/api/tags",
                                     timeout=aiohttp.ClientTimeout(total=5)) as tags_response:
                    if tags_response.status == 200:
                        tags_data = await tags_response.json()
                        models = [m["name"] for m in tags_data.get("models", [])]
                        instance.ready = instance.model in models
                        return instance.ready
            return False
    except Exception as e:
        logger.debug(f"Health check failed for {instance.name}: {e}")
        return False

async def wait_for_instances(instances: List[ModelInstance], max_wait: int = 300) -> List[ModelInstance]:
    """Wait for all instances to be ready"""
    
    logger.info(f"Waiting for {len(instances)} Ollama instances to be ready...")
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        ready_instances = []
        
        while time.time() - start_time < max_wait:
            pending_instances = [inst for inst in instances if not inst.ready]
            
            if not pending_instances:
                break
            
            # Check health of pending instances
            health_tasks = [check_instance_health(session, inst) for inst in pending_instances]
            await asyncio.gather(*health_tasks, return_exceptions=True)
            
            # Update ready list
            ready_instances = [inst for inst in instances if inst.ready]
            
            if ready_instances:
                ready_names = [inst.name for inst in ready_instances]
                logger.info(f"Ready: {ready_names}")
            
            if len(ready_instances) < len(instances):
                await asyncio.sleep(10)
        
        final_ready = [inst for inst in instances if inst.ready]
        if len(final_ready) < len(instances):
            not_ready = [inst.name for inst in instances if not inst.ready]
            logger.warning(f"Instances not ready after {max_wait}s: {not_ready}")
        
        return final_ready

async def run_task_samples_async(session: aiohttp.ClientSession,
                                instance: ModelInstance,
                                task: BenchmarkTask,
                                approach: str,
                                prompt: str,
                                sample_size: int) -> List[Dict[str, Any]]:
    """Run multiple samples of a task on one instance"""
    
    logger.info(f"Running {task.name} {approach} on {instance.name} ({sample_size} samples)")
    
    # Create all tasks concurrently (but limit concurrency to avoid overwhelming)
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests per instance
    
    async def run_single_sample(sample_num: int) -> Dict[str, Any]:
        async with semaphore:
            result = await make_ollama_request_async(
                session, instance.url, prompt, instance.model
            )
            result["sample_num"] = sample_num
            result["approach"] = approach
            result["task"] = task.name
            result["instance"] = instance.name
            return result
    
    # Run all samples concurrently
    tasks = [run_single_sample(i) for i in range(sample_size)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successful results
    successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]
    
    logger.info(f"  {instance.name} {approach}: {len(successful_results)}/{sample_size} successful")
    
    return successful_results

async def run_comprehensive_benchmark_async(instances: List[ModelInstance],
                                           tasks: List[BenchmarkTask],
                                           sample_size: int = 8) -> Dict[str, Any]:
    """Run comprehensive benchmark across all instances and tasks"""
    
    logger.info(f"Starting comprehensive async benchmark")
    logger.info(f"Instances: {[i.name for i in instances]}")
    logger.info(f"Tasks: {[t.name for t in tasks]}")
    logger.info(f"Sample size: {sample_size} per approach per task")
    
    start_time = time.time()
    all_results = {
        "benchmark_info": {
            "timestamp": datetime.now().isoformat(),
            "sample_size_per_approach": sample_size,
            "total_tasks": len(tasks),
            "total_instances": len(instances),
            "concurrent": True
        },
        "task_results": []
    }
    
    async with aiohttp.ClientSession() as session:
        # Create all benchmark tasks
        benchmark_coroutines = []
        
        for task in tasks:
            for instance in instances:
                # Baseline approach
                baseline_coro = run_task_samples_async(
                    session, instance, task, "baseline", 
                    task.baseline_prompt, sample_size
                )
                benchmark_coroutines.append(("baseline", task, instance, baseline_coro))
                
                # Tools approach  
                tools_coro = run_task_samples_async(
                    session, instance, task, "tools",
                    task.tools_prompt, sample_size
                )
                benchmark_coroutines.append(("tools", task, instance, tools_coro))
        
        logger.info(f"Running {len(benchmark_coroutines)} concurrent benchmark tasks...")
        
        # Execute all benchmarks concurrently
        coroutines = [coro for _, _, _, coro in benchmark_coroutines]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Organize results
        for i, (approach, task, instance, _) in enumerate(benchmark_coroutines):
            if i < len(results) and isinstance(results[i], list):
                task_result = {
                    "task_name": task.name,
                    "workflow_type": task.workflow_type.value,
                    "instance_name": instance.name,
                    "model": instance.model,
                    "approach": approach,
                    "results": results[i],
                    "sample_size": len(results[i])
                }
                all_results["task_results"].append(task_result)
    
    total_time = time.time() - start_time
    all_results["benchmark_info"]["total_duration_seconds"] = total_time
    
    logger.info(f"Async benchmark completed in {total_time:.1f}s")
    
    return all_results

def create_benchmark_tasks() -> List[BenchmarkTask]:
    """Create standardized benchmark tasks"""
    
    # Simplified tasks for concurrent testing
    return [
        BenchmarkTask(
            name="Safety Assessment",
            baseline_prompt="Analyze this code for security issues: def process(data): return eval(data)",
            tools_prompt="Based on this safety analysis: {\"risk_level\": \"HIGH\", \"issues\": [\"eval usage\"]}, provide assessment.",
            workflow_type=WorkflowType.SAFETY_CHECK
        ),
        BenchmarkTask(
            name="Pattern Detection", 
            baseline_prompt="Find patterns in: def get_user(id): return db.fetch(id); def get_order(id): return db.fetch(id)",
            tools_prompt="Based on pattern analysis: {\"pattern\": \"fetch_by_id\", \"matches\": 2}, provide summary.",
            workflow_type=WorkflowType.PATTERN_ANALYSIS
        ),
        BenchmarkTask(
            name="Context Analysis",
            baseline_prompt="Analyze project with files: user.py, order.py, api.py, tests/. What's the architecture?",
            tools_prompt="Based on context: {\"architecture\": \"microservices\", \"complexity\": 6}, provide summary.",
            workflow_type=WorkflowType.CONTEXT_ANALYSIS
        )
    ]

def calculate_improvement_stats(all_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate statistical improvements across all results"""
    
    stats = {
        "by_model": {},
        "by_task": {},
        "overall": {}
    }
    
    # Group results by model and task
    for result in all_results["task_results"]:
        model = result["model"]
        task = result["task_name"]
        approach = result["approach"]
        
        if model not in stats["by_model"]:
            stats["by_model"][model] = {"baseline": [], "tools": []}
        if task not in stats["by_task"]:
            stats["by_task"][task] = {"baseline": [], "tools": []}
        
        # Extract metrics
        for sample in result["results"]:
            tokens = sample.get("total_tokens", 0)
            duration = sample.get("duration", 0)
            
            if tokens > 0:
                stats["by_model"][model][approach].append({"tokens": tokens, "duration": duration})
                stats["by_task"][task][approach].append({"tokens": tokens, "duration": duration})
    
    # Calculate improvements
    improvements = {}
    
    for model in stats["by_model"]:
        baseline_tokens = [r["tokens"] for r in stats["by_model"][model]["baseline"]]
        tools_tokens = [r["tokens"] for r in stats["by_model"][model]["tools"]]
        baseline_time = [r["duration"] for r in stats["by_model"][model]["baseline"]]
        tools_time = [r["duration"] for r in stats["by_model"][model]["tools"]]
        
        if baseline_tokens and tools_tokens:
            token_improvement = ((statistics.mean(baseline_tokens) - statistics.mean(tools_tokens)) / 
                               statistics.mean(baseline_tokens)) * 100
            time_improvement = ((statistics.mean(baseline_time) - statistics.mean(tools_time)) / 
                              statistics.mean(baseline_time)) * 100
            
            improvements[model] = {
                "token_reduction_percent": token_improvement,
                "time_reduction_percent": time_improvement,
                "sample_size": len(baseline_tokens)
            }
    
    return improvements

def get_benchmark_profile(profile: str) -> List[ModelInstance]:
    """Get model instances based on hardware profile from configuration"""
    profile_configs = BENCHMARK_CONFIG.get("ollama_profiles", {})
    selected_profile = profile_configs.get(profile, profile_configs.get("medium", []))
    return [ModelInstance(**p) for p in selected_profile]

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Development Tools Benchmark Suite")
    parser.add_argument("--profile", 
                       choices=["light", "medium", "heavy"],
                       default="medium",
                       help="Hardware profile: light (laptop), medium (desktop), heavy (server)")
    parser.add_argument("--samples",
                       type=int,
                       default=None,
                       help="Sample size per approach (auto-scaled by profile if not specified)")
    
    args = parser.parse_args()
    
    # Auto-scale sample sizes based on profile from configuration
    sample_sizes = BENCHMARK_CONFIG.get("sample_sizes", {"light": 3, "medium": 6, "heavy": 12})
    sample_size = args.samples or sample_sizes[args.profile]
    
    print("🚀 AI Development Tools Benchmark Suite")
    print(f"📊 Profile: {args.profile.upper()} ({['Laptop', 'Desktop', 'Server'][['light', 'medium', 'heavy'].index(args.profile)]})")
    print("=" * 70)
    
    # Get model instances for profile
    instances = get_benchmark_profile(args.profile)
    
    # Wait for instances to be ready
    ready_instances = await wait_for_instances(instances, max_wait=300)
    
    if not ready_instances:
        logger.error("No Ollama instances are ready!")
        logger.info("Run: docker compose up -d to start the containers")
        return
    
    logger.info(f"Using {len(ready_instances)} ready instances: {[i.name for i in ready_instances]}")
    
    # Create tasks
    tasks = create_benchmark_tasks()
    
    # Run benchmark with profile-specific sample size
    results = await run_comprehensive_benchmark_async(ready_instances, tasks, sample_size)
    
    # Add profile info to results
    results["benchmark_info"]["profile"] = args.profile
    results["benchmark_info"]["hardware_target"] = ["Laptop", "Desktop", "Server"][["light", "medium", "heavy"].index(args.profile)]
    
    # Calculate improvements
    improvements = calculate_improvement_stats(results)
    
    # Display results
    print(f"\n📊 CONCURRENT BENCHMARK RESULTS")
    print("=" * 50)
    
    for model, stats in improvements.items():
        print(f"\n{model.upper()} Model:")
        print(f"  Token reduction: {stats['token_reduction_percent']:.1f}%")
        print(f"  Time reduction: {stats['time_reduction_percent']:.1f}%")
        print(f"  Sample size: {stats['sample_size']}")
    
    # Overall summary
    if improvements:
        avg_token = statistics.mean([s["token_reduction_percent"] for s in improvements.values()])
        avg_time = statistics.mean([s["time_reduction_percent"] for s in improvements.values()])
        
        print(f"\n🎯 OVERALL IMPROVEMENTS:")
        print(f"   Average token reduction: {avg_token:.1f}%")
        print(f"   Average time reduction: {avg_time:.1f}%")
        print(f"   Total duration: {results['benchmark_info']['total_duration_seconds']:.1f}s")
        print(f"   Concurrent instances: {len(ready_instances)}")
    
    # Save results
    output_dir = Path("benchmark_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"benchmark_{args.profile}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    total_samples = len(ready_instances) * len(tasks) * 2 * sample_size
    print(f"📏 Total concurrent samples: {total_samples}")
    print(f"🖥️  Hardware profile: {args.profile} ({results['benchmark_info']['hardware_target']})")
    print(f"🔢 Sample size per approach: {sample_size}")

if __name__ == "__main__":
    asyncio.run(main())