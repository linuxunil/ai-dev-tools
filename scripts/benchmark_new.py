#!/usr/bin/env python3
"""
New Benchmark Runner Script

Modern replacement for the old benchmark scripts using the new unified
benchmarking system. Provides a simple command-line interface for running
benchmarks without the full CLI complexity.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_dev_tools.benchmark import BenchmarkRunner, HardwareProfile, OutputFormat, load_config


async def main():
    """Main function to run benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Development Tools Benchmark Runner")
    parser.add_argument(
        "--profile",
        choices=["light", "medium", "heavy"],
        default="medium",
        help="Hardware profile to use (default: medium)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        help="Number of samples per task (uses profile default if not specified)"
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Specific tasks to run (runs all if not specified)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "csv", "console"],
        default="console",
        help="Output format (default: console)"
    )
    parser.add_argument(
        "--output",
        help="Output filename (auto-generated if not specified)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (uses default if not specified)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate setup before running"
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List available tasks and exit"
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        if args.config:
            from ai_dev_tools.benchmark.config import BenchmarkConfig
            config = BenchmarkConfig.from_toml(args.config)
        else:
            config = load_config()
        
        # Create runner
        runner = BenchmarkRunner(config)
        
        # Handle list commands
        if args.list_tasks:
            print("📋 Available Tasks:")
            print("=" * 50)
            tasks = runner.list_available_tasks()
            for task in tasks:
                print(f"  {task['task_id']}: {task['name']}")
                print(f"    Type: {task['workflow_type']}")
                print(f"    Description: {task['description']}")
                print()
            return
        
        if args.list_profiles:
            print("🖥️  Available Profiles:")
            print("=" * 50)
            profiles = runner.list_available_profiles()
            for profile in profiles:
                print(f"  {profile['profile']}: {profile['description']}")
                print(f"    Instances: {profile['instances']}")
                print(f"    Models: {', '.join(profile['models'])}")
                print(f"    Default samples: {profile['default_sample_size']}")
                print()
            return
        
        # Validate setup if requested
        if args.validate:
            print("🔍 Validating setup...")
            validation = runner.validate_setup()
            
            if validation["valid"]:
                print("✅ Setup is valid!")
            else:
                print("❌ Setup issues found:")
                for issue in validation["issues"]:
                    print(f"  • {issue}")
                return 1
            
            if validation["warnings"]:
                print("\n⚠️  Warnings:")
                for warning in validation["warnings"]:
                    print(f"  • {warning}")
            
            print(f"\n📊 Available: {validation['profiles_available']} profiles, "
                  f"{validation['tasks_available']} tasks, {validation['batches_available']} batches")
            return
        
        # Run benchmark
        profile_enum = HardwareProfile(args.profile)
        format_enum = OutputFormat(args.format)
        
        print(f"🚀 Running benchmark with profile: {args.profile.upper()}")
        if args.tasks:
            print(f"📋 Tasks: {', '.join(args.tasks)}")
        else:
            print("📋 Running all available tasks")
        
        if args.samples:
            print(f"🔢 Samples per task: {args.samples}")
        else:
            print("🔢 Using profile default sample size")
        
        print("⏳ Starting benchmark execution...")
        
        results = await runner.run_single_benchmark(
            profile=profile_enum,
            task_ids=args.tasks,
            sample_size=args.samples,
            output_format=format_enum,
            output_filename=args.output
        )
        
        # Display results summary
        benchmark_info = results.get("benchmark_info", {})
        comparison_metrics = results.get("comparison_metrics", {})
        
        print("\n📊 Benchmark Complete!")
        print(f"   Profile: {benchmark_info.get('profile', 'unknown').upper()}")
        print(f"   Tasks: {benchmark_info.get('total_tasks', 0)}")
        print(f"   Samples: {benchmark_info.get('sample_size', 0)}")
        print(f"   Instances: {benchmark_info.get('instances', 0)}")
        print(f"   Execution mode: {benchmark_info.get('execution_mode', 'unknown')}")
        
        if comparison_metrics:
            print("\n🎯 Performance Improvements:")
            print(f"   Token Reduction: {comparison_metrics.get('token_reduction_percent', 0):.1f}%")
            print(f"   Time Reduction: {comparison_metrics.get('time_reduction_percent', 0):.1f}%")
            print(f"   Efficiency Improvement: {comparison_metrics.get('efficiency_improvement_percent', 0):.1f}%")
            print(f"   Sample Size: {comparison_metrics.get('sample_size', 0)}")
        
        # Show overall metrics
        overall_metrics = results.get("overall_metrics", {})
        if overall_metrics:
            print("\n📈 Overall Metrics:")
            print(f"   Success Rate: {overall_metrics.get('success_rate', 0):.1%}")
            print(f"   Total Tasks: {overall_metrics.get('total_tasks', 0)}")
            print(f"   Completed: {overall_metrics.get('completed_tasks', 0)}")
            print(f"   Failed: {overall_metrics.get('failed_tasks', 0)}")
            print(f"   Average Duration: {overall_metrics.get('average_task_duration', 0):.2f}s")
            print(f"   Total Tokens: {overall_metrics.get('total_tokens', 0):,}")
            print(f"   Throughput: {overall_metrics.get('throughput', 0):.2f} tasks/sec")
            print(f"   Efficiency Score: {overall_metrics.get('efficiency_score', 0):.2f}")
        
        # Show errors if any
        if overall_metrics.get('failed_tasks', 0) > 0:
            error_types = overall_metrics.get('error_types', {})
            if error_types:
                print("\n❌ Error Summary:")
                for error_type, count in error_types.items():
                    print(f"   {error_type}: {count}")
        
        print("\n✅ Benchmark completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code or 0)