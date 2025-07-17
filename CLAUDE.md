# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI Development Tools - Agent Guidelines

## Build/Test Commands
- **Environment**: `uv` (Python package manager with virtual environment)
- **Install**: `uv sync` (installs dependencies from pyproject.toml)
- **Install dev deps**: `uv add --dev pytest pytest-cov pytest-bdd mypy` (already included)
- **Test**: `uv run pytest` (with coverage: `uv run pytest --cov`)
- **Single test**: `uv run pytest path/to/test_file.py::test_function_name`
- **Lint**: `uv run ruff check src/`
- **Format**: `uv run ruff format src/`
- **Type check**: `uv run mypy src/` (requires python_version >= 3.9 in pyproject.toml)

## Code Style
- **Formatting**: Ruff (line length 88), replaces Black and isort
- **Types**: Full type hints required (`disallow_untyped_defs = true`)
- **Imports**: Absolute imports from `ai_dev_tools.*`, group stdlib/third-party/local
- **Docstrings**: Google style with Args/Returns sections
- **Error handling**: Use try/except with specific exceptions, return None/empty for failures
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Tools**: Use Astral tools (ruff, uv) over legacy alternatives
- **Dependencies**: Managed via `uv` with pyproject.toml, includes uv.lock for reproducible builds

## Architecture Patterns
- **Core libraries**: `src/ai_dev_tools/core/` (pattern_scanner, safety_checker, repo_analyzer, context_analyzer)
- **CLI tools**: `src/ai_dev_tools/cli/` with click framework
- **Agent interface**: `src/ai_dev_tools/agents/` high-level APIs
- **Data classes**: Use `@dataclass` with `to_dict()` methods for JSON serialization
- **Exit codes**: Encode information (0=success, N=count/risk level) for AI consumption

## AI-Specific Guidelines
- **Exit-code-first**: Prefer exit codes over output for maximum token efficiency
- **Silent by default**: No output unless explicitly requested with --format flag
- **Meaningful exit codes**: 0-254 for counts, 0-3 for risk levels, 255 for errors
- Pattern detection focus: Find similar code structures for systematic fixes
- Safety-first: Always assess risk before modifications
- **Tool Design Philosophy**: Tools should be developed with ai output as the default and human readable as flags. Prioritize exit codes with flags for more detailed output.

## Exit Code Patterns
- **Pattern Scanner**: Exit code = number of patterns found (0-254)
- **Safety Checker**: Exit code = risk level (0=safe, 1=medium, 2=high, 3=critical)
- **Repo Analyzer**: Exit code = syntax error count (0=clean, N=error count)
- **Context Analyzer**: Exit code = complexity score (0-254, higher = more complex)
- **Errors**: Exit code 255 for invalid input/file not found

## Benchmark & Metrics System

### **Hardware-Optimized Benchmark Profiles**
The system includes three benchmark profiles optimized for different hardware configurations:

#### **Light Profile (Laptop/Minimal)**
- **Target**: 8GB+ RAM, 2+ cores
- **Models**: 1 model (llama3.2:1b)
- **Samples**: 3 per approach
- **Usage**: `./scripts/run_benchmark.sh light`

#### **Medium Profile (Desktop/Development)**
- **Target**: 16GB+ RAM, 4+ cores  
- **Models**: 2 models (llama3.2:1b, llama3.2:3b)
- **Samples**: 6 per approach
- **Usage**: `./scripts/run_benchmark.sh medium` (default)

#### **Heavy Profile (Server/Comprehensive)**
- **Target**: 32GB+ RAM, 8+ cores
- **Models**: 4 models (llama3.2:1b, llama3.2:3b, llama3.1:8b, codellama:7b)
- **Samples**: 12 per approach  
- **Usage**: `./scripts/run_benchmark.sh heavy`

### **Benchmark Commands**
- **Quick test**: `./scripts/run_benchmark.sh light`
- **Development**: `./scripts/run_benchmark.sh medium --samples 10`
- **Production**: `./scripts/run_benchmark.sh heavy`
- **Manual**: `uv run python scripts/async_benchmark.py --profile medium --samples 8`

### **Batch Processing**
The system supports automated batch runs across multiple configurations:

#### **Batch Types**
- **quick**: Fast validation (2-3 configs, 2-3 samples, ~5-10 min)
- **standard**: Production testing (3 configs, 5-8 samples, ~15-30 min)
- **comprehensive**: Exhaustive analysis (3 configs, 10-20 samples, ~45-90 min)
- **scaling**: Model scaling comparison (3 configs, 5 samples, ~15-20 min)
- **sample_size**: Sample size impact analysis (4 configs, 3-20 samples, ~20-40 min)

#### **Batch Commands**
- **Quick validation**: `./scripts/run_batch.sh quick`
- **Production testing**: `./scripts/run_batch.sh standard --parallel`
- **Comprehensive analysis**: `./scripts/run_batch.sh comprehensive --output-dir results/full`
- **Manual batch**: `uv run python scripts/batch_benchmark.py standard --mode sequential`

#### **Execution Modes**
- **Sequential**: Runs one after another (safer, less resource intensive)
- **Parallel**: Runs concurrently (faster, requires more resources)

### **Docker Compose Profiles**
- **Basic**: `docker compose up -d` (medium profile containers)
- **Extended**: `docker compose --profile extended up -d` (all containers including codellama)
- **Single model**: `docker compose up -d ollama-small` (light profile)