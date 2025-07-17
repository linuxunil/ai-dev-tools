# AI Development Tools - Enhanced Benchmarking System

A comprehensive and user-friendly benchmarking system for measuring AI tool performance across different models, hardware profiles, and execution scenarios.

## 🚀 Quick Start

### Simple Benchmark
```python
from ai_dev_tools.benchmark import quick_benchmark

# Run a quick benchmark
result = await quick_benchmark(
    profile="medium",
    sample_size=3
)

print(f"Token reduction: {result.token_reduction_percent:.1f}%")
print(f"Time reduction: {result.time_reduction_percent:.1f}%")
```

### Profile Comparison
```python
from ai_dev_tools.benchmark import compare_profiles

# Compare performance across profiles
results = await compare_profiles(
    profiles=["light", "medium", "heavy"],
    tasks=["safety_assessment", "pattern_detection"]
)

for profile, result in results.items():
    print(f"{profile}: {result.success_rate:.1%} success")
```

### Batch Benchmarking
```python
from ai_dev_tools.benchmark import batch_benchmark

# Run predefined batch
results = await batch_benchmark(
    batch_name="standard",
    output_file="results.json"
)
```

## 📊 Features

### Simplified API
- **`quick_benchmark()`** - Run benchmarks with minimal configuration
- **`compare_profiles()`** - Compare performance across hardware profiles
- **`batch_benchmark()`** - Execute predefined benchmark suites

### Advanced Features
- **Hardware-optimized profiles** (light/medium/heavy)
- **Comprehensive metrics** with statistical analysis
- **Multiple output formats** (JSON, Markdown, CSV, Console)
- **ASCII visualization** with progress bars and charts
- **Trend analysis** for historical data
- **Custom task support** with validation
- **Container orchestration** with Docker Compose
- **Async execution** with configurable concurrency

### Enhanced Reporting
- **Performance dashboards** with ASCII visualization
- **Comparison charts** showing baseline vs tools
- **Trend analysis** for performance tracking
- **Batch aggregation** with statistical summaries
- **Export capabilities** for further analysis

## 🛠️ Installation

```bash
# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## 📋 Hardware Profiles

### Light Profile (Laptop/Minimal)
- **Target**: 8GB+ RAM, 2+ cores
- **Models**: 1 model (llama3.2:1b)
- **Sample size**: 3 per task
- **Use case**: Quick validation, development

### Medium Profile (Desktop/Development)
- **Target**: 16GB+ RAM, 4+ cores
- **Models**: 2 models (llama3.2:1b, llama3.2:3b)
- **Sample size**: 6 per task
- **Use case**: Standard benchmarking, CI/CD

### Heavy Profile (Server/Comprehensive)
- **Target**: 32GB+ RAM, 8+ cores
- **Models**: 4 models (llama3.2:1b, llama3.2:3b, llama3.1:8b, codellama:7b)
- **Sample size**: 12 per task
- **Use case**: Production validation, research

## 🔧 CLI Usage

### Quick Benchmark
```bash
# Run quick benchmark
uv run python -m ai_dev_tools.cli.benchmark_cli quick --profile medium --samples 5

# Run with specific tasks
uv run python -m ai_dev_tools.cli.benchmark_cli quick --tasks safety_assessment pattern_detection

# Run comparison
uv run python -m ai_dev_tools.cli.benchmark_cli compare --profiles light medium --samples 3
```

### Full Benchmark
```bash
# Run full benchmark
uv run python -m ai_dev_tools.cli.benchmark_cli run --profile heavy --format markdown

# Run batch benchmark
uv run python -m ai_dev_tools.cli.benchmark_cli batch standard --format json

# List available options
uv run python -m ai_dev_tools.cli.benchmark_cli list-tasks
uv run python -m ai_dev_tools.cli.benchmark_cli list-profiles
uv run python -m ai_dev_tools.cli.benchmark_cli list-batches
```

### Configuration Management
```bash
# Show system info
uv run python -m ai_dev_tools.cli.benchmark_cli info

# Validate setup
uv run python -m ai_dev_tools.cli.benchmark_cli validate

# Export configuration
uv run python -m ai_dev_tools.cli.benchmark_cli export-config config.json
```

## ⚙️ Configuration

Configuration is loaded from `pyproject.toml`:

```toml
[tool.ai-dev-tools.benchmark]
execution_mode = "async"
output_format = "json"
output_directory = "benchmark_results"
container_startup_timeout = 180
task_timeout = 30
retry_attempts = 3

[tool.ai-dev-tools.benchmark.sample_sizes]
light = 3
medium = 6
heavy = 12

[tool.ai-dev-tools.benchmark.ollama_profiles.light]
[[tool.ai-dev-tools.benchmark.ollama_profiles.light]]
name = "small"
model = "llama3.2:1b"
port = 11434
timeout = 30
max_concurrent = 3
```

## 📊 Metrics and Analysis

### Key Metrics
- **Success Rate**: Percentage of tasks completed successfully
- **Token Reduction**: Improvement in token efficiency vs baseline
- **Time Reduction**: Improvement in execution time vs baseline
- **Throughput**: Tasks completed per second
- **Efficiency Score**: Composite performance metric

### Statistical Analysis
- **Percentiles**: P25, P50, P75, P90, P95, P99
- **Confidence Intervals**: 95% confidence bounds
- **Trend Analysis**: Performance trends over time
- **Error Classification**: Categorized error analysis

## 🎯 Batch Configurations

### Predefined Batches
- **quick**: Fast validation (2-3 samples, ~5-10 min)
- **standard**: Production testing (8 samples, ~15-30 min)
- **comprehensive**: Exhaustive analysis (20 samples, ~45-90 min)
- **scaling**: Model scaling comparison (5 samples × 3 runs)

### Custom Batches
```python
from ai_dev_tools.benchmark import BenchmarkRunner

runner = BenchmarkRunner()
runner.add_custom_task(
    task_id="custom_security_scan",
    name="Custom Security Scan",
    description="Scan for security vulnerabilities",
    baseline_prompt="Manually analyze this code for security issues",
    tools_prompt="Use security tools to analyze this code",
    workflow_type="safety_check"
)
```

## 📈 Visualization

### ASCII Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│                 Performance Dashboard                       │
├─────────────────────────────────────────────────────────────┤
│ Success Rate:     95.0% [███████████████████░] │
│ Avg Duration:     2.50s                                     │
│ Throughput:       1.20 tasks/sec                           │
├─────────────────────────────────────────────────────────────┤
│                   Improvements                              │
├─────────────────────────────────────────────────────────────┤
│ Token Reduction:  25.0% [████████░░░░░░░░░░░░] │
│ Time Reduction:   30.0% [██████████░░░░░░░░░░] │
└─────────────────────────────────────────────────────────────┘
```

### Comparison Charts
```
┌─────────────────────────────────────────────────────────────┐
│                 Baseline vs Tools                           │
├─────────────────────────────────────────────────────────────┤
│ Duration     │ Baseline:     3.50s    │ Tools:     2.50s    │
│              │ Winner: Tools    │ Improvement: +28.6% │
├─────────────────────────────────────────────────────────────┤
│ Tokens       │ Baseline:     2000     │ Tools:     1500     │
│              │ Winner: Tools    │ Improvement: +25.0% │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Container Orchestration

### Docker Compose Integration
```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama-small:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_MODELS=llama3.2:1b
    profiles:
      - light
      - medium
      - heavy

  ollama-medium:
    image: ollama/ollama:latest
    ports:
      - "11435:11435"
    environment:
      - OLLAMA_MODELS=llama3.2:3b
    profiles:
      - medium
      - heavy
```

### Automatic Profile Management
- **Profile-based container startup**: Only starts containers needed for profile
- **Health checks**: Waits for containers to be ready before benchmarking
- **Resource management**: Manages concurrent requests per container
- **Automatic cleanup**: Stops containers after benchmarking

## 🧪 Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test modules
uv run pytest tests/test_benchmark_core.py
uv run pytest tests/test_benchmark_reporting.py
uv run pytest tests/test_benchmark_config_enhanced.py

# Run with coverage
uv run pytest --cov=ai_dev_tools.benchmark --cov-report=html
```

### Test Coverage
- **Core functionality**: 95%+ coverage
- **Configuration system**: 90%+ coverage
- **Reporting system**: 85%+ coverage
- **Integration tests**: End-to-end scenarios

## 🚀 Advanced Usage

### Custom Execution Engine
```python
from ai_dev_tools.benchmark import BenchmarkRunner, BenchmarkConfig

# Custom configuration
config = BenchmarkConfig(
    execution_mode="parallel",
    max_concurrent_batches=4,
    task_timeout=60
)

runner = BenchmarkRunner(config)

# Advanced benchmark with custom parameters
result = await runner.run_comparison_benchmark(
    profiles=["medium", "heavy"],
    tasks=["custom_task_1", "custom_task_2"],
    sample_size=10
)
```

### Historical Analysis
```python
from ai_dev_tools.benchmark.reporting import ReportGenerator

generator = ReportGenerator("/path/to/results")

# Load historical data
historical_data = [
    # ... load previous benchmark results
]

# Generate trend analysis
trend_report = generator.generate_trend_analysis(historical_data)
print(trend_report)
```

## 🔧 Development

### Adding New Tasks
```python
from ai_dev_tools.benchmark.tasks import TaskRegistry, BenchmarkTask
from ai_dev_tools.benchmark.config import WorkflowType

# Register new task
registry = TaskRegistry()
registry.register_task(BenchmarkTask(
    task_id="new_task",
    name="New Task",
    description="A new benchmark task",
    workflow_type=WorkflowType.PATTERN_ANALYSIS,
    baseline_prompt="Baseline approach",
    tools_prompt="Tools approach",
    timeout=45
))
```

### Custom Metrics
```python
from ai_dev_tools.benchmark.metrics import MetricsCollector

collector = MetricsCollector()
await collector.start_collection()

# ... run benchmarks

metrics = collector.calculate_metrics()
comparison = collector.calculate_comparison_metrics()
```

## 🐛 Troubleshooting

### Common Issues

1. **Container startup timeout**
   ```bash
   # Increase timeout in configuration
   [tool.ai-dev-tools.benchmark]
   container_startup_timeout = 300
   ```

2. **Memory issues with heavy profile**
   ```bash
   # Use lighter profile or reduce sample size
   uv run python -m ai_dev_tools.cli.benchmark_cli quick --profile medium --samples 3
   ```

3. **Port conflicts**
   ```bash
   # Check for conflicting services
   lsof -i :11434
   
   # Stop conflicting services
   docker stop $(docker ps -q)
   ```

### Debug Mode
```bash
# Enable debug logging
uv run python -m ai_dev_tools.cli.benchmark_cli --log-level DEBUG quick
```

## 📚 API Reference

### Core Functions
- **`quick_benchmark(profile, tasks, sample_size, config)`**
- **`compare_profiles(profiles, tasks, config)`**
- **`batch_benchmark(batch_name, output_file, config)`**

### Classes
- **`BenchmarkRunner`**: Main benchmark orchestrator
- **`BenchmarkResult`**: Simplified result container
- **`BenchmarkConfig`**: Configuration management
- **`ReportGenerator`**: Enhanced reporting with visualization

### Configuration
- **`load_config(path)`**: Load configuration from file
- **`HardwareProfile`**: Hardware profile enumeration
- **`ModelInstance`**: Model instance configuration
- **`OutputFormat`**: Output format options

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Add tests**: Ensure 90%+ test coverage
4. **Run tests**: `uv run pytest`
5. **Run linting**: `uv run ruff check src/`
6. **Submit PR**: With detailed description

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Changelog

### v2.0.0 (Current)
- **New simplified API** with `quick_benchmark()`, `compare_profiles()`, `batch_benchmark()`
- **Enhanced reporting** with ASCII visualization and trend analysis
- **Improved configuration** with better defaults and validation
- **Comprehensive testing** with 90%+ coverage
- **Better error handling** and retry mechanisms
- **Performance optimizations** for large-scale benchmarking

### v1.0.0 (Legacy)
- Initial benchmarking system
- Basic metrics collection
- Docker integration
- Command-line interface