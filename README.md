# AI Development Tools

Python libraries and CLI tools optimized for AI-assisted development workflows.

## Key Features

- **Pattern Detection**: Find similar code patterns using structural analysis
- **Safety Checking**: Assess risk before making code changes  
- **Repository Analysis**: Quick repository health and context
- **Agent Interface**: High-level API designed for AI agents

## Design Philosophy

**AI-First Design:**
- Exit codes encode information (0=success, N=count/risk level)
- JSON output for programmatic consumption
- Composable libraries for agent integration
- Self-documenting APIs

## Quick Start

### As a Library (for AI Agents)

```python
from ai_dev_tools.agents import AIAgent

# Initialize agent with repository context
agent = AIAgent(repo_path="/path/to/repo")

# Core AI workflow: Fix one error → find similar patterns → assess safety
result = agent.fix_and_propagate_workflow(
    fixed_file="modules/shell.nix",
    fixed_line=249,
    search_scope="modules/"
)

print(f"Found {result['similar_patterns']['count']} similar patterns")
print(f"Summary: {result['summary']}")

# Check repository health before making changes
context = agent.get_repository_context()
if context['ready_for_changes']:
    print("✅ Repository ready for changes")
else:
    print("⚠️ Issues found:", context['blocking_issues'])
```

### As CLI Tools

```bash
# Find similar patterns (exit code = count found)
ai-pattern-scan shell.nix:249 --search-dir modules/ --format json

# Check file safety (exit code = risk level: 0=safe, 1=medium, 2=high, 3=critical)  
ai-safety-check modules/shell.nix --format json

# Get repository status (exit code = syntax error count)
ai-repo-status --format json
```

## Core Libraries

### PatternScanner
Find structurally similar code patterns:

```python
from ai_dev_tools.core import PatternScanner

scanner = PatternScanner()
result = scanner.scan_for_similar_patterns(
    target_file="shell.nix",
    target_line=249,
    search_dir="modules/"
)

print(f"Found {result.count} similar patterns")
for match in result.matches:
    print(f"  {match.file}:{match.line} (confidence: {match.confidence})")
```

### SafetyChecker
Assess risk before making changes:

```python
from ai_dev_tools.core import SafetyChecker

checker = SafetyChecker()
result = checker.check_file_safety("configuration.nix")

print(f"Risk Level: {result.risk_level.name}")
print(f"Safe to Modify: {result.safe_to_modify}")
```

### RepoAnalyzer
Quick repository health assessment:

```python
from ai_dev_tools.core import RepoAnalyzer

analyzer = RepoAnalyzer()
health = analyzer.get_repo_health()

print(f"Repository Health: {health.summary}")
print(f"Syntax Errors: {health.syntax_errors}")
```

## AI Agent Workflows

### 1. Fix and Propagate Pattern
The core workflow for consistent fixes:

```python
# After fixing an error at shell.nix:249
result = agent.fix_and_propagate_workflow(
    fixed_file="shell.nix", 
    fixed_line=249
)

# Result includes:
# - Similar patterns found
# - Safety assessment for each
# - Recommendations for next steps
```

### 2. Safety Assessment
Before making changes to multiple files:

```python
files_to_modify = ["shell.nix", "core.nix", "development.nix"]
safety = agent.assess_change_safety(files_to_modify)

if safety['safe_to_proceed']:
    print("✅ Safe to proceed with changes")
else:
    print("⚠️ High risk detected")
```

### 3. Repository Context
Understanding project state:

```python
context = agent.get_repository_context()

if context['ready_for_changes']:
    # Proceed with modifications
    pass
else:
    # Address blocking issues first
    print("Blocking issues:", context['blocking_issues'])
```

## Exit Code Patterns

All tools use exit codes to encode information for AI consumption:

- **Pattern Scanner**: Exit code = number of patterns found (0-255)
- **Safety Checker**: Exit code = risk level (0=safe, 1=medium, 2=high, 3=critical)  
- **Repo Status**: Exit code = number of syntax errors (0=healthy)

## Installation

```bash
cd ai-dev-tools
pip install -e .
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/
```

## Use Cases

### For AI Agents
- **Systematic error fixing**: Fix one error, find and fix all similar patterns
- **Risk assessment**: Check safety before making changes
- **Context awareness**: Understand repository state for better decisions

### For Developers  
- **Code consistency**: Find and fix inconsistent patterns across codebase
- **Safety checks**: Assess risk of modifications before making them
- **Repository health**: Quick overview of project status

## Architecture

```
ai-dev-tools/
├── src/ai_dev_tools/
│   ├── core/              # Core libraries
│   │   ├── pattern_scanner.py
│   │   ├── safety_checker.py
│   │   └── repo_analyzer.py
│   ├── cli/               # Command-line interfaces
│   ├── agents/            # High-level agent APIs
│   └── patterns/          # Pattern definitions
```

## Contributing

This project is designed to be AI-maintainable:
- Clear, documented APIs
- Modular architecture  
- Comprehensive type hints
- JSON-based configuration
- Self-documenting code

AI agents can extend and modify these tools as needed for specific workflows.