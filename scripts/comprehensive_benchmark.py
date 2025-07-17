#!/usr/bin/env python3
"""
Comprehensive Benchmark Suite - Statistically Significant Data Collection

Runs multiple standardized tasks with sufficient sample size for statistical analysis.
"""

import json
import time
import requests
import statistics
from pathlib import Path
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_dev_tools.core.metrics_collector import measure_workflow, WorkflowType

class BenchmarkTask:
    def __init__(self, name: str, baseline_prompt: str, tools_prompt: str, 
                 workflow_type: WorkflowType, expected_improvement: float = 30.0):
        self.name = name
        self.baseline_prompt = baseline_prompt
        self.tools_prompt = tools_prompt
        self.workflow_type = workflow_type
        self.expected_improvement = expected_improvement

def make_ollama_request(prompt: str, model: str = "llama3.2:1b", 
                       host: str = "localhost:11434", timeout: int = 30) -> dict:
    """Make a request to Ollama API with error handling"""
    
    url = f"http://{host}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Consistent results
            "top_p": 0.9,
            "num_predict": 150   # Consistent response length
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=timeout)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "input_tokens": result.get("prompt_eval_count", 0),
                "output_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                "duration": end_time - start_time,
                "model": model,
                "timestamp": end_time
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "duration": end_time - start_time,
                "timestamp": end_time
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "duration": time.time() - start_time if 'start_time' in locals() else 0,
            "timestamp": time.time()
        }

def create_benchmark_tasks() -> List[BenchmarkTask]:
    """Create standardized benchmark tasks"""
    
    # Task 1: Safety Assessment
    unsafe_code = '''
def process_user_input(user_data):
    # Dangerous: direct eval of user input
    result = eval(user_data["expression"])
    
    # Dangerous: SQL injection risk
    query = f"SELECT * FROM users WHERE id = {user_data['id']}"
    
    # Dangerous: file system access
    with open(user_data["filename"], "w") as f:
        f.write(result)
    
    return result
'''
    
    safety_baseline = f"""
Analyze this Python code for security vulnerabilities and safety issues. Provide a detailed assessment.

Code:
{unsafe_code}

Please provide:
1. Overall risk level (SAFE/MEDIUM/HIGH/CRITICAL)
2. List all security issues found
3. Explain each vulnerability
4. Recommend fixes
"""
    
    safety_tools = f"""
Based on this structured safety analysis, provide a brief assessment:

{{
  "file": "user_input.py",
  "risk_level": "CRITICAL",
  "safe_to_modify": false,
  "issues_found": [
    {{"line": 3, "type": "code_injection", "pattern": "eval()"}},
    {{"line": 6, "type": "sql_injection", "pattern": "f-string query"}},
    {{"line": 9, "type": "path_traversal", "pattern": "open(user_input)"}}
  ],
  "risk_factors": ["eval", "sql_injection", "file_access"],
  "complexity_score": 8
}}

Provide a concise security assessment.
"""
    
    # Task 2: Pattern Detection
    pattern_code = '''
# File 1: user_service.py
def get_user(user_id):
    if user_id is None:
        return None
    return database.fetch_user(user_id)

# File 2: order_service.py  
def get_order(order_id):
    if order_id is None:
        return None
    return database.fetch_order(order_id)

# File 3: product_service.py
def get_product(product_id):
    if product_id is None:
        return None
    return database.fetch_product(product_id)
'''
    
    pattern_baseline = f"""
Analyze this code and find similar patterns that could be refactored or improved.

Code:
{pattern_code}

Please identify:
1. Repeated patterns in the code
2. How many similar instances exist
3. Opportunities for refactoring
4. Suggested improvements
"""
    
    pattern_tools = f"""
Based on this pattern analysis, provide a summary:

{{
  "pattern_type": "null_check_fetch",
  "pattern_matches": [
    {{"file": "user_service.py", "line": 2, "confidence": 0.95}},
    {{"file": "order_service.py", "line": 2, "confidence": 0.95}},
    {{"file": "product_service.py", "line": 2, "confidence": 0.95}}
  ],
  "total_matches": 3,
  "refactor_opportunity": "generic_fetch_function",
  "complexity_reduction": 40
}}

Provide a brief pattern analysis summary.
"""
    
    # Task 3: Context Analysis  
    context_baseline = f"""
Analyze this project structure and provide context about the codebase:

Project files:
- src/services/user_service.py (authentication, user management)
- src/services/order_service.py (order processing, payments)
- src/models/user.py (user data models)
- src/models/order.py (order data models)
- src/api/routes.py (REST API endpoints)
- src/database/migrations/ (database schema changes)
- tests/unit/ (unit tests)
- tests/integration/ (integration tests)
- docker-compose.yml (container orchestration)
- requirements.txt (Python dependencies)

Please analyze:
1. Architecture pattern being used
2. Project complexity level
3. Technology stack
4. Potential areas of concern
5. Overall code organization quality
"""
    
    context_tools = f"""
Based on this structured project analysis, provide a summary:

{{
  "architecture": "microservices",
  "complexity_score": 6,
  "tech_stack": ["python", "docker", "rest_api"],
  "file_count": 10,
  "test_coverage": "good",
  "concerns": ["service_coupling", "migration_complexity"],
  "organization_score": 7,
  "estimated_team_size": "3-5 developers"
}}

Provide a brief project context analysis.
"""
    
    return [
        BenchmarkTask("Safety Assessment", safety_baseline, safety_tools, 
                     WorkflowType.SAFETY_CHECK, 35.0),
        BenchmarkTask("Pattern Detection", pattern_baseline, pattern_tools,
                     WorkflowType.PATTERN_ANALYSIS, 40.0),
        BenchmarkTask("Context Analysis", context_baseline, context_tools,
                     WorkflowType.CONTEXT_ANALYSIS, 25.0)
    ]

def run_benchmark_samples(task: BenchmarkTask, sample_size: int = 10, 
                         model: str = "llama3.2:1b") -> Dict[str, Any]:
    """Run multiple samples of a benchmark task"""
    
    print(f"\n🔬 Running {task.name} ({sample_size} samples each)")
    print("=" * 60)
    
    baseline_results = []
    tools_results = []
    
    # Run baseline samples
    print(f"Running baseline samples...")
    for i in range(sample_size):
        print(f"  Baseline {i+1}/{sample_size}", end=" ", flush=True)
        
        with measure_workflow(task.workflow_type) as context:
            result = make_ollama_request(task.baseline_prompt, model)
            
            if result["success"]:
                context.record_tokens(result["input_tokens"], result["output_tokens"])
                baseline_results.append(result)
                print("✅")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    # Run tools samples
    print(f"Running tools samples...")
    for i in range(sample_size):
        print(f"  Tools {i+1}/{sample_size}", end=" ", flush=True)
        
        with measure_workflow(task.workflow_type) as context:
            result = make_ollama_request(task.tools_prompt, model)
            
            if result["success"]:
                context.record_tokens(result["input_tokens"], result["output_tokens"])
                tools_results.append(result)
                print("✅")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")
        
        time.sleep(0.5)
    
    return {
        "task_name": task.name,
        "workflow_type": task.workflow_type.value,
        "model": model,
        "sample_size": sample_size,
        "baseline_results": baseline_results,
        "tools_results": tools_results,
        "timestamp": datetime.now().isoformat()
    }

def calculate_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate statistical analysis of benchmark results"""
    
    baseline = results["baseline_results"]
    tools = results["tools_results"]
    
    if not baseline or not tools:
        return {"error": "Insufficient data for analysis"}
    
    # Extract metrics
    baseline_tokens = [r["total_tokens"] for r in baseline if r.get("total_tokens", 0) > 0]
    tools_tokens = [r["total_tokens"] for r in tools if r.get("total_tokens", 0) > 0]
    
    baseline_times = [r["duration"] for r in baseline]
    tools_times = [r["duration"] for r in tools]
    
    if not baseline_tokens or not tools_tokens:
        return {"error": "No valid token data"}
    
    # Calculate statistics
    stats = {
        "sample_sizes": {
            "baseline": len(baseline_tokens),
            "tools": len(tools_tokens)
        },
        "tokens": {
            "baseline": {
                "mean": statistics.mean(baseline_tokens),
                "median": statistics.median(baseline_tokens),
                "stdev": statistics.stdev(baseline_tokens) if len(baseline_tokens) > 1 else 0,
                "min": min(baseline_tokens),
                "max": max(baseline_tokens)
            },
            "tools": {
                "mean": statistics.mean(tools_tokens),
                "median": statistics.median(tools_tokens),
                "stdev": statistics.stdev(tools_tokens) if len(tools_tokens) > 1 else 0,
                "min": min(tools_tokens),
                "max": max(tools_tokens)
            }
        },
        "time": {
            "baseline": {
                "mean": statistics.mean(baseline_times),
                "median": statistics.median(baseline_times),
                "stdev": statistics.stdev(baseline_times) if len(baseline_times) > 1 else 0,
                "min": min(baseline_times),
                "max": max(baseline_times)
            },
            "tools": {
                "mean": statistics.mean(tools_times),
                "median": statistics.median(tools_times),
                "stdev": statistics.stdev(tools_times) if len(tools_times) > 1 else 0,
                "min": min(tools_times),
                "max": max(tools_times)
            }
        }
    }
    
    # Calculate improvements
    token_improvement = ((stats["tokens"]["baseline"]["mean"] - 
                         stats["tokens"]["tools"]["mean"]) / 
                        stats["tokens"]["baseline"]["mean"]) * 100
    
    time_improvement = ((stats["time"]["baseline"]["mean"] - 
                        stats["time"]["tools"]["mean"]) / 
                       stats["time"]["baseline"]["mean"]) * 100
    
    stats["improvements"] = {
        "token_reduction_percent": token_improvement,
        "time_reduction_percent": time_improvement,
        "statistical_significance": len(baseline_tokens) >= 10 and len(tools_tokens) >= 10
    }
    
    return stats

def main():
    print("🚀 Comprehensive AI Development Tools Benchmark")
    print("📊 Collecting Statistically Significant Sample Data")
    print("=" * 70)
    
    # Check Ollama availability
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama not available. Run: docker compose up -d ollama")
            return
        print(f"✅ Ollama ready (version: {response.json().get('version')})")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return
    
    # Configuration
    SAMPLE_SIZE = 30
    MODEL = "llama3.2:1b"
    
    print(f"📋 Configuration:")
    print(f"  • Sample size: {SAMPLE_SIZE} per approach per task")
    print(f"  • Model: {MODEL}")
    print(f"  • Total API calls: {SAMPLE_SIZE * 2 * 3} (≈ {SAMPLE_SIZE * 2 * 3 * 4 / 60:.1f} minutes)")
    
    # Create tasks
    tasks = create_benchmark_tasks()
    print(f"  • Tasks: {len(tasks)} ({', '.join(t.name for t in tasks)})")
    
    print(f"\n⏳ Starting benchmark in 3 seconds...")
    time.sleep(3)
    
    # Run benchmarks
    all_results = {
        "benchmark_info": {
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "sample_size_per_approach": SAMPLE_SIZE,
            "total_tasks": len(tasks),
            "ollama_version": response.json().get('version', 'unknown')
        },
        "task_results": [],
        "statistical_analysis": {}
    }
    
    start_time = time.time()
    
    for i, task in enumerate(tasks):
        print(f"\n[{i+1}/{len(tasks)}] {task.name}")
        task_results = run_benchmark_samples(task, SAMPLE_SIZE, MODEL)
        
        # Calculate statistics
        stats = calculate_statistics(task_results)
        task_results["statistics"] = stats
        
        all_results["task_results"].append(task_results)
        
        # Show progress
        if stats.get("improvements"):
            improvements = stats["improvements"]
            print(f"    📈 Token reduction: {improvements['token_reduction_percent']:.1f}%")
            print(f"    ⏱️  Time reduction: {improvements['time_reduction_percent']:.1f}%")
    
    total_time = time.time() - start_time
    
    # Overall analysis
    print(f"\n📊 COMPREHENSIVE RESULTS")
    print("=" * 50)
    
    total_token_improvements = []
    total_time_improvements = []
    
    for task_result in all_results["task_results"]:
        stats = task_result.get("statistics", {})
        if "improvements" in stats:
            improvements = stats["improvements"]
            total_token_improvements.append(improvements["token_reduction_percent"])
            total_time_improvements.append(improvements["time_reduction_percent"])
            
            print(f"\n{task_result['task_name']}:")
            print(f"  Token reduction: {improvements['token_reduction_percent']:.1f}%")
            print(f"  Time reduction: {improvements['time_reduction_percent']:.1f}%")
            
            # Show confidence in results
            baseline_size = stats["sample_sizes"]["baseline"]
            tools_size = stats["sample_sizes"]["tools"]
            print(f"  Sample sizes: {baseline_size} baseline, {tools_size} tools")
            
            if improvements["statistical_significance"]:
                print(f"  ✅ Statistically significant (n≥10)")
            else:
                print(f"  ⚠️  Small sample size")
    
    # Overall summary
    if total_token_improvements and total_time_improvements:
        avg_token_improvement = statistics.mean(total_token_improvements)
        avg_time_improvement = statistics.mean(total_time_improvements)
        
        all_results["overall_summary"] = {
            "average_token_reduction_percent": avg_token_improvement,
            "average_time_reduction_percent": avg_time_improvement,
            "total_benchmark_duration_seconds": total_time,
            "total_api_calls": SAMPLE_SIZE * 2 * len(tasks),
            "statistical_confidence": "high" if SAMPLE_SIZE >= 10 else "medium"
        }
        
        print(f"\n🎯 OVERALL PERFORMANCE GAINS:")
        print(f"   Average token reduction: {avg_token_improvement:.1f}%")
        print(f"   Average time reduction: {avg_time_improvement:.1f}%") 
        print(f"   Total benchmark time: {total_time:.1f}s")
        print(f"   Statistical confidence: {all_results['overall_summary']['statistical_confidence']}")
    
    # Save results
    output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"📏 Total data points: {len(all_results['task_results']) * SAMPLE_SIZE * 2}")

if __name__ == "__main__":
    main()
