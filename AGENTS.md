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

## Exit Code Patterns
- **Pattern Scanner**: Exit code = number of patterns found (0-254)
- **Safety Checker**: Exit code = risk level (0=safe, 1=medium, 2=high, 3=critical)
- **Repo Analyzer**: Exit code = syntax error count (0=clean, N=error count)
- **Context Analyzer**: Exit code = complexity score (0-254, higher = more complex)
- **Errors**: Exit code 255 for invalid input/file not found

## Development Plan

### Project Goals
**Primary**: Build AI-optimized development tools with exit-code-first design for systematic code improvements
**Secondary**: Recreate functionality from ~/.nix/tools in a project-generic, AI-first manner

### Current Status
✅ Core architecture - Complete with pattern scanner, safety checker, repo analyzer, context analyzer
✅ AI-first design - Exit codes, JSON output, token efficiency  
✅ AI Agent interface - High-level workflows for systematic code improvements
✅ CLI tools - Complete command-line interface with ai-workflow and ai-context commands
✅ Testing & validation - Comprehensive test coverage with exit code validation
✅ Phase 4 Started - Context analyzer (ai-context) implemented and working

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

### Phase 3: Testing & Validation ✅ COMPLETED
1. ✅ Exit code validation - Ensure deterministic, reliable exit codes
2. ✅ Integration tests - End-to-end workflow testing
3. ✅ Core functionality tests - Pattern scanner, safety checker, AI agent
4. ✅ Token efficiency validation - Silent mode and AI-first design verification

### Phase 4: Extended Tools & Polish (In Progress)
1. ✅ **Context Analysis Tool** - Project-generic context analysis with complexity scoring
2. ✅ **Configuration Differ** - ai-diff tool for generic config and code comparison
3. ✅ **Impact Analyzer** - ai-impact tool for change impact assessment
4. ✅ **Validation Framework** - ai-validate tool for comprehensive project validation
5. ✅ **AI Helper Integration** - Enhanced AI assistant with unified workflows and tool orchestration
6. **Performance optimization** - Large repository scalability  
7. **Documentation** - Usage examples and API docs

### Phase 5: Advanced AI Features (Future)
1. **Multi-language support** - Extend beyond Nix to Python, JavaScript, etc.
2. **Advanced pattern learning** - ML-based pattern detection
3. **Automated fix suggestions** - AI-generated fix recommendations
4. **Integration ecosystem** - VS Code extensions, GitHub Actions, etc.

### Original Tools Analysis
**~/.nix/tools functionality to recreate:**
- `nix-context` → `ai-context` - Project context analysis (any language/framework)
- `nix-diff` → `ai-diff` - Configuration and code difference analysis  
- `nix-impact` → `ai-impact` - Change impact assessment across project
- `nix-validate` → `ai-validate` - Project validation and health checking
- `ai-helper` → Enhanced AI assistant with our new tools integration

### Next Priority
**Phase 4: Extended Tools** - AI Helper Integration and performance optimization

### Current Release
**v0.9.0** - AI Helper Integration complete, unified AI assistant with tool orchestration ready

## Workflow & Requirements Documentation

### **Established Development Workflow**
1. **Feature Branch Pattern**: Always create `feature/tool-name` branches for new tools
2. **Professional Git Workflow**: 
   - Atomic commits with descriptive messages
   - Pre-commit hooks for quality (ruff, mypy)
   - GitHub Actions CI/CD pipeline
   - Proper semantic versioning with git tags
3. **BDD Red-Green-Refactor**: Write failing tests first, implement to pass, refactor
4. **AI-Maintainable Design**: Simple, focused, well-documented code that AI can easily understand and modify

### **Core Design Principles**
1. **Exit-Code-First Architecture**: Tools communicate via exit codes (0-254 for data, 255 for errors)
2. **Silent by Default**: No output unless `--format` flag explicitly requests it
3. **Project-Generic Approach**: Tools work across languages/frameworks, not just Nix
4. **Token Efficiency**: Designed for AI agent consumption with minimal token usage
5. **Safety-First**: Always assess risk before making changes

### **Tool Implementation Pattern**
**Every new tool follows this exact structure:**
1. **Core Module**: `src/ai_dev_tools/core/tool_name.py` with main logic class
2. **CLI Interface**: `src/ai_dev_tools/cli/tool_name.py` with click command
3. **Entry Point**: Add command to `pyproject.toml` console_scripts
4. **Comprehensive Tests**: Both unit tests and BDD feature tests
5. **Exit Code Design**: Meaningful exit codes that encode information for AI consumption

### **Testing Requirements**
- **Unit Tests**: `tests/test_tool_name_basic.py` for core functionality
- **BDD Tests**: `tests/features/tool_name.feature` for behavior scenarios
- **Exit Code Validation**: Every tool must have deterministic, testable exit codes
- **Coverage**: Aim for comprehensive test coverage of all code paths
- **Integration**: Test CLI commands and core classes separately

### **Quality Standards**
- **Type Safety**: Full type hints required (`mypy --strict`)
- **Code Quality**: Ruff formatting and linting (line length 88)
- **Documentation**: Google-style docstrings with Args/Returns
- **Error Handling**: Specific exceptions, graceful failures
- **Security**: No secrets in code, safe file operations

### **AI Agent Integration**
- **High-Level API**: `src/ai_dev_tools/agents/ai_agent.py` provides workflow methods
- **Systematic Fixes**: `fix_and_propagate_workflow` for applying changes across codebase
- **Context Awareness**: Tools provide repository health and complexity metrics
- **Batch Operations**: Support for processing multiple files/patterns efficiently

### **Session Continuity Requirements**
**For future AI sessions, always:**
1. **Check Current Status**: Read `AGENTS.md` and run `git status` to understand state
2. **Follow Established Patterns**: Use existing tool structure and workflow
3. **Maintain Quality**: Run linting/testing before commits
4. **Update Documentation**: Keep `AGENTS.md` current with progress
5. **Professional Git**: Feature branches, atomic commits, proper tags

### **Key Success Factors**
- **Consistency**: Every tool follows the same patterns and quality standards
- **AI-Friendly**: Code is simple, well-documented, and easily maintainable by AI
- **Professional**: Git workflow, CI/CD, testing, and documentation meet industry standards
- **Focused**: Each tool has a single, clear responsibility with meaningful exit codes