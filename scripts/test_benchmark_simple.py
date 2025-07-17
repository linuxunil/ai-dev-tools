#!/usr/bin/env python3
"""Simple benchmark test to show actual output"""

import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_dev_tools.core.benchmark_suite import BenchmarkSuite, create_benchmark_report
from ai_dev_tools.core.ollama_client import ModelSize

def main():
    print("🚀 Testing AI Development Tools Benchmark")
    print("=" * 50)
    
    # Create a simple test suite
    suite = BenchmarkSuite("test_codebase")
    
    # Test just one task with small model
    task_id = "safety_1"  # Safety assessment task
    task = suite.tasks[task_id]
    model = ModelSize.SMALL
    
    print(f"Running task: {task.name}")
    print(f"Model: {model.value}")
    
    try:
        # Run baseline
        print("  Running baseline simulation...")
        baseline_result = suite.run_task_baseline(task, model)
        
        # Run with tools
        print("  Running with tools...")
        tools_result = suite.run_task_with_tools(task, model)
        
        # Create simple comparison
        results = {
            "suite_info": {
                "test_mode": "simple",
                "task": task_id,
                "model": model.value
            },
            "task_results": [baseline_result, tools_result],
            "comparisons": {}
        }
        
        # Show results
        print("\n📊 Results:")
        print("-" * 20)
        
        print(f"Baseline approach:")
        baseline_metrics = baseline_result.get("metrics", {})
        print(f"  Tokens: {baseline_metrics.get('total_tokens', 'N/A')}")
        print(f"  Time: {baseline_metrics.get('execution_time', 'N/A')}s")
        
        print(f"Tools approach:")  
        tools_metrics = tools_result.get("metrics", {})
        print(f"  Tokens: {tools_metrics.get('total_tokens', 'N/A')}")
        print(f"  Time: {tools_metrics.get('execution_time', 'N/A')}s")
        
        # JSON output
        print(f"\n📋 JSON Output (AI-friendly):")
        print(json.dumps(results, indent=2))
        
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()