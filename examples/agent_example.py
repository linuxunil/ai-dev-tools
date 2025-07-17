#!/usr/bin/env python3
"""
Example: AI Agent using development tools

Demonstrates how an AI agent would use the libraries for systematic
code analysis and modification workflows.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_dev_tools.agents import AIAgent
from ai_dev_tools.core import PatternScanner, RepoAnalyzer, SafetyChecker


def demonstrate_agent_workflow():
    """Demonstrate the complete AI agent workflow"""

    print("🤖 AI Development Tools - Agent Example")
    print("=" * 50)

    # Initialize agent
    agent = AIAgent(repo_path=".")

    # 1. Check repository health first
    print("\n1. Repository Health Check")
    print("-" * 30)
    context = agent.get_repository_context()
    print(f"Repository Health: {context['repository_health']['summary']}")
    print(f"Ready for Changes: {context['ready_for_changes']}")

    if context["blocking_issues"]:
        print("Blocking Issues:")
        for issue in context["blocking_issues"]:
            print(f"  - {issue}")

    # 2. Demonstrate pattern finding (simulated)
    print("\n2. Pattern Detection Example")
    print("-" * 30)

    # This would be used after fixing an error
    # For demo, we'll use a hypothetical file
    demo_file = "demo_file.nix"
    demo_line = 42

    print(f"Simulating: After fixing error in {demo_file}:{demo_line}")
    print("Searching for similar patterns...")

    # In real usage, this would find actual patterns
    # For demo, we'll show the workflow structure

    # 3. Safety assessment workflow
    print("\n3. Safety Assessment Example")
    print("-" * 30)

    # Check safety of modifying multiple files
    demo_files = ["shell.nix", "core.nix", "development.nix"]
    print(f"Assessing safety for files: {demo_files}")

    # This would check actual files if they exist
    # For demo, we'll show the workflow

    # 4. Complete fix and propagate workflow
    print("\n4. Fix and Propagate Workflow")
    print("-" * 30)

    print("This workflow would:")
    print("  1. Find patterns similar to your fix")
    print("  2. Assess safety of modifying each file")
    print("  3. Generate recommendations")
    print("  4. Provide structured results for AI decision-making")

    print("\n✅ Agent workflow demonstration complete!")


def demonstrate_individual_libraries():
    """Demonstrate using individual libraries directly"""

    print("\n🔧 Individual Library Examples")
    print("=" * 50)

    # Pattern Scanner
    print("\n1. Pattern Scanner")
    print("-" * 20)
    PatternScanner()
    print("PatternScanner initialized")
    print("Usage: scanner.scan_for_similar_patterns(file, line, search_dir)")

    # Safety Checker
    print("\n2. Safety Checker")
    print("-" * 20)
    SafetyChecker()
    print("SafetyChecker initialized")
    print("Usage: checker.check_file_safety(file_path)")

    # Repository Analyzer
    print("\n3. Repository Analyzer")
    print("-" * 20)
    analyzer = RepoAnalyzer()
    health = analyzer.get_repo_health()
    print(f"Repository Health: {health.summary}")
    print(f"Total Files: {health.total_files}")
    print(f"Syntax Errors: {health.syntax_errors}")


def demonstrate_ai_decision_making():
    """Show how AI would use these tools for decision making"""

    print("\n🧠 AI Decision Making Example")
    print("=" * 50)

    agent = AIAgent()

    # Scenario: AI just fixed an error and wants to find similar issues
    print("\nScenario: AI fixed mkIf + list concatenation error")
    print("Decision process:")

    # Step 1: Check if repository is ready
    context = agent.get_repository_context()
    if not context["ready_for_changes"]:
        print("❌ Repository not ready - address blocking issues first")
        return

    print("✅ Repository ready for changes")

    # Step 2: Find similar patterns (simulated)
    print("🔍 Scanning for similar patterns...")
    # result = agent.fix_and_propagate_workflow("shell.nix", 249)

    # Step 3: AI decision logic
    print("🤖 AI Decision Logic:")
    print("  - If 0 patterns found: Fix is isolated, proceed with next task")
    print("  - If 1-5 patterns found: Apply same fix to each")
    print("  - If >5 patterns found: Consider batch fix approach")
    print("  - If high-risk files found: Proceed with extra caution")

    print("\n✅ AI decision making demonstration complete!")


if __name__ == "__main__":
    try:
        demonstrate_agent_workflow()
        demonstrate_individual_libraries()
        demonstrate_ai_decision_making()

    except ImportError as e:
        print(f"Import error: {e}")
        print("\nNote: This example requires the ai-dev-tools package to be installed.")
        print("Run: pip install -e . from the project root")

    except Exception as e:
        print(f"Error: {e}")
        print("This is a demonstration - some features may not work without actual files.")
