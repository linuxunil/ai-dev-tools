"""
AI Development Tools Benchmark Package

A comprehensive benchmarking system for measuring AI tool performance
across different models, hardware profiles, and execution scenarios.
"""

from .config import BenchmarkConfig, HardwareProfile, ModelInstance, OutputFormat, load_config
from .core import BenchmarkRunner, BenchmarkResult, quick_benchmark, compare_profiles, batch_benchmark
from .execution import ExecutionEngine
from .metrics import BenchmarkMetrics, MetricsCollector
from .reporting import ReportGenerator
from .runner import BenchmarkRunner as LegacyBenchmarkRunner
from .tasks import BenchmarkTask, TaskRegistry

__all__ = [
    # Core API (New)
    "BenchmarkRunner",
    "BenchmarkResult", 
    "quick_benchmark",
    "compare_profiles",
    "batch_benchmark",
    
    # Configuration
    "BenchmarkConfig",
    "HardwareProfile",
    "ModelInstance",
    "OutputFormat",
    "load_config",
    
    # Components
    "ExecutionEngine",
    "MetricsCollector",
    "BenchmarkMetrics",
    "ReportGenerator",
    "TaskRegistry",
    "BenchmarkTask",
    
    # Legacy (Deprecated)
    "LegacyBenchmarkRunner",
]
