#!/usr/bin/env python3
"""
Example script demonstrating the new AI Development Tools benchmark system.

This script shows how to use the simplified benchmarking API for common use cases.
"""

import asyncio
import json
from pathlib import Path

# Import the new simplified API
from ai_dev_tools.benchmark import (
    quick_benchmark,
    compare_profiles,
    batch_benchmark,
    BenchmarkRunner,
    BenchmarkConfig,
    load_config
)


async def basic_quick_benchmark():
    """Example 1: Run a quick benchmark with minimal configuration."""
    print("🚀 Running quick benchmark...")
    
    # Run a quick benchmark with default settings
    result = await quick_benchmark(
        profile="medium",
        sample_size=3
    )
    
    print(f"✅ Quick benchmark completed!")
    print(f"   Profile: {result.profile}")
    print(f"   Status: {result.status}")
    print(f"   Tasks executed: {result.tasks_executed}")
    print(f"   Success rate: {result.success_rate:.1%}")
    print(f"   Average duration: {result.avg_duration:.2f}s")
    print(f"   Total tokens: {result.total_tokens:,}")
    print(f"   Token reduction: {result.token_reduction_percent:.1f}%")
    print(f"   Time reduction: {result.time_reduction_percent:.1f}%")
    print()


async def profile_comparison():
    """Example 2: Compare performance across different hardware profiles."""
    print("📊 Comparing profiles...")
    
    # Compare light and medium profiles
    results = await compare_profiles(
        profiles=["light", "medium"],
        tasks=["safety_assessment", "pattern_detection"]
    )
    
    print(f"✅ Profile comparison completed!")
    for profile, result in results.items():
        print(f"   {profile.upper()}:")
        print(f"     Status: {result.status}")
        print(f"     Success rate: {result.success_rate:.1%}")
        print(f"     Token reduction: {result.token_reduction_percent:.1f}%")
        print(f"     Time reduction: {result.time_reduction_percent:.1f}%")
    print()


async def batch_benchmark_example():
    """Example 3: Run a predefined batch benchmark."""
    print("📦 Running batch benchmark...")
    
    # Run a standard batch benchmark
    results = await batch_benchmark(
        batch_name="standard",
        output_file="/tmp/batch_results.json"
    )
    
    print(f"✅ Batch benchmark completed!")
    print(f"   Batch: {results['batch_info']['batch_name']}")
    print(f"   Results saved to: /tmp/batch_results.json")
    
    # Show key metrics
    overall_metrics = results.get("overall_metrics", {})
    comparison_metrics = results.get("comparison_metrics", {})
    
    print(f"   Success rate: {overall_metrics.get('success_rate', 0):.1%}")
    print(f"   Token reduction: {comparison_metrics.get('token_reduction_percent', 0):.1f}%")
    print(f"   Time reduction: {comparison_metrics.get('time_reduction_percent', 0):.1f}%")
    print()


async def advanced_benchmark_runner():
    """Example 4: Use BenchmarkRunner for advanced scenarios."""
    print("🔧 Advanced benchmark runner...")
    
    # Load configuration (can be customized)
    config = load_config()
    
    # Create runner instance
    runner = BenchmarkRunner(config)
    
    # Get system information
    print("📋 System Info:")
    system_info = runner.get_system_info()
    print(f"   Profiles: {system_info['profiles']}")
    print(f"   Tasks: {system_info['tasks']}")
    print(f"   Batches: {system_info['batches']}")
    print(f"   Execution mode: {system_info['execution_mode']}")
    
    # List available tasks
    print("\n📝 Available Tasks:")
    tasks = runner.get_available_tasks()
    for task_id in tasks[:3]:  # Show first 3
        print(f"   - {task_id}")
    
    # Add a custom task
    print("\n➕ Adding custom task...")
    success = runner.add_custom_task(
        task_id="custom_example",
        name="Custom Example Task",
        description="A custom task for demonstration",
        baseline_prompt="Analyze this code: def hello(): return 'world'",
        tools_prompt="Use tools to analyze: def hello(): return 'world'",
        workflow_type="pattern_analysis"
    )
    
    if success:
        print("   ✅ Custom task added successfully!")
        
        # Run benchmark with custom task
        result = await runner.run_quick_benchmark(
            profile="light",
            tasks=["custom_example"],
            sample_size=2
        )
        
        print(f"   Custom task result: {result.status}")
        print(f"   Success rate: {result.success_rate:.1%}")
    else:
        print("   ❌ Failed to add custom task")
    
    print()


async def main():
    """Main function demonstrating all examples."""
    print("🎯 AI Development Tools Benchmark Examples")
    print("=" * 50)
    
    try:
        # Example 1: Quick benchmark
        await basic_quick_benchmark()
        
        # Example 2: Profile comparison
        await profile_comparison()
        
        # Example 3: Batch benchmark
        await batch_benchmark_example()
        
        # Example 4: Advanced runner
        await advanced_benchmark_runner()
        
        print("🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Note: This example requires Docker and Ollama to be running")
        print("For testing purposes, the execution engine can be mocked")


def run_examples():
    """Run all examples."""
    asyncio.run(main())


if __name__ == "__main__":
    run_examples()