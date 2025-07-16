# AI Development Tools - Agent Guidelines

## Build/Test Commands
- **Environment**: `nix develop` (activates development shell with uv and Python)
- **Install**: `nix develop --command uv pip install -e .`
- **Install dev deps**: `nix develop --command uv pip install pytest pytest-bdd pytest-cov ruff mypy`
- **Test**: `nix develop --command pytest` (with coverage: `pytest --cov`)
- **Single test**: `nix develop --command pytest path/to/test_file.py::test_function_name`
- **Lint**: `nix develop --command ruff check src/`
- **Format**: `nix develop --command ruff format src/`
- **Type check**: `nix develop --command mypy src/`

## Code Style
- **Formatting**: Ruff (line length 88), replaces Black and isort
- **Types**: Full type hints required (`disallow_untyped_defs = true`)
- **Imports**: Absolute imports from `ai_dev_tools.*`, group stdlib/third-party/local
- **Docstrings**: Google style with Args/Returns sections
- **Error handling**: Use try/except with specific exceptions, return None/empty for failures
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Tools**: Use Astral tools (ruff, uv) over legacy alternatives

## Architecture Patterns
- **Core libraries**: `src/ai_dev_tools/core/` (pattern_scanner, safety_checker, repo_analyzer)
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

## Exit Code Patterns
- **Pattern Scanner**: Exit code = number of patterns found (0-254)
- **Safety Checker**: Exit code = risk level (0=safe, 1=medium, 2=high, 3=critical)
- **Repo Analyzer**: Exit code = syntax error count (0=clean, N=error count)
- **Errors**: Exit code 255 for invalid input/file not found

## Development Plan

### Current Status
✅ Core architecture - Complete with pattern scanner, safety checker, repo analyzer  
✅ AI-first design - Exit codes, JSON output, token efficiency  
✅ AI Agent interface - High-level workflows for systematic code improvements
✅ CLI tools - Complete command-line interface with ai-workflow commands
⚠️ Testing gaps - Need comprehensive test coverage and validation  

### Phase 1: Core Implementation ✅ COMPLETED
1. ✅ Complete Pattern Scanner - Structural pattern matching with Nix-specific detection
2. ✅ Implement Safety Checker - Risk assessment algorithms for code changes  
3. ✅ Build Repository Analyzer - Syntax error detection and health metrics
4. ✅ Fix CLI Tools - All command-line interfaces working properly

### Phase 2: AI Agent Interface ✅ COMPLETED  
1. ✅ Complete AIAgent class - High-level API for AI workflows
2. ✅ Implement fix_and_propagate_workflow - Core systematic fix workflow
3. ✅ Add repository context methods - Health assessment for AI decision making
4. ✅ AI Workflow CLI - Command-line interface for AI agent operations

### Phase 3: Testing & Validation (Medium Priority)
1. Exit code validation - Ensure deterministic, reliable exit codes
2. Integration tests - End-to-end workflow testing
3. Performance benchmarks - Speed and memory optimization
4. Token efficiency tests - Measure AI token savings

### Phase 4: Polish & Documentation (Low Priority)
1. Error handling - Robust edge case management
2. Performance optimization - Large repository scalability  
3. Documentation - Usage examples and API docs

### Next Priority
**Phase 3: Testing & Validation** - Comprehensive test coverage and performance validation

### Current Release
**v0.3.0-alpha** - Complete AI Agent interface with systematic workflow capabilities