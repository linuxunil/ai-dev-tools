#!/usr/bin/env python3
"""
Comprehensive Ollama Integration Test

Tests AI development tools with standardized Ollama models using:
- Standard system prompts for different task types
- Consistent test codebase for reproducible results
- Token tracking and metrics collection
- Exit-code-first decision making
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_dev_tools.core.metrics_collector import (
    WorkflowType,
    get_metrics_collector,
    measure_workflow,
)
from ai_dev_tools.core.ollama_client import (
    ModelSize,
    PromptType,
    get_ollama_client,
    quick_ai_decision,
)


def test_pattern_detection():
    """Test pattern detection with Ollama"""
    print("🔍 Testing Pattern Detection with Ollama")
    print("=" * 50)

    client = get_ollama_client()

    # Test with simple functions
    test_file = "test_codebase/simple/basic_functions.py"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file) as f:
        code_content = f.read()

    # Use metrics collection
    with measure_workflow(WorkflowType.PATTERN_ANALYSIS) as ctx:
        response = client.query(
            prompt_type=PromptType.PATTERN_DETECTION,
            user_prompt=f"Analyze this code for patterns:\n\n{code_content}",
            model=ModelSize.SMALL,
            workflow_type=WorkflowType.PATTERN_ANALYSIS,
        )

        ctx.record_files_processed(1)
        ctx.add_metadata("file_path", test_file)

    if response.success:
        print(f"✅ Pattern analysis completed in {response.execution_time:.2f}s")
        print(f"📊 Estimated tokens: {response.estimated_tokens}")
        print(f"🤖 AI Analysis:\n{response.content}")
    else:
        print(f"❌ Error: {response.error}")


def test_safety_assessment():
    """Test safety assessment with Ollama"""
    print("\n🛡️ Testing Safety Assessment with Ollama")
    print("=" * 50)

    client = get_ollama_client()

    # Test with problematic code
    test_file = "test_codebase/problematic/unsafe_code.py"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file) as f:
        code_content = f.read()

    with measure_workflow(WorkflowType.SAFETY_CHECK) as ctx:
        response = client.query(
            prompt_type=PromptType.SAFETY_ASSESSMENT,
            user_prompt=f"Assess the safety of this code:\n\n{code_content}",
            model=ModelSize.SMALL,
            workflow_type=WorkflowType.SAFETY_CHECK,
        )

        ctx.record_files_processed(1)
        ctx.add_metadata("file_path", test_file)

    if response.success:
        print(f"✅ Safety assessment completed in {response.execution_time:.2f}s")
        print(f"📊 Estimated tokens: {response.estimated_tokens}")
        print(f"🛡️ Safety Analysis:\n{response.content}")
    else:
        print(f"❌ Error: {response.error}")


def test_exit_code_decision():
    """Test exit-code-first decision making"""
    print("\n🎯 Testing Exit-Code Decision Making")
    print("=" * 50)

    # Simulate different exit codes from tools
    test_cases = [
        (0, "SAFE", "Pattern scanner found 0 similar patterns"),
        (5, "LOW", "Pattern scanner found 5 similar patterns"),
        (25, "MEDIUM", "Pattern scanner found 25 similar patterns"),
        (150, "HIGH", "Pattern scanner found 150 similar patterns"),
    ]

    for exit_code, expected_level, description in test_cases:
        decision = quick_ai_decision(
            prompt_type=PromptType.PATTERN_DETECTION,
            decision_prompt=f"{description}. Should we proceed with systematic fixes? Answer: SKIP, MANUAL, REVIEW, or AUTOFIX.",
            exit_code=exit_code,
            context={"tool": "pattern_scanner", "threshold": 10},
        )

        print(f"📊 Exit code {exit_code} ({expected_level}): {decision}")


def test_context_analysis():
    """Test context analysis with medium complexity code"""
    print("\n📋 Testing Context Analysis")
    print("=" * 50)

    client = get_ollama_client()

    test_file = "test_codebase/medium/data_processor.py"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file) as f:
        code_content = f.read()

    with measure_workflow(WorkflowType.CONTEXT_ANALYSIS) as ctx:
        response = client.query(
            prompt_type=PromptType.CONTEXT_ANALYSIS,
            user_prompt=f"Analyze the structure and complexity of this code:\n\n{code_content}",
            model=ModelSize.MEDIUM,  # Use larger model for complex analysis
            workflow_type=WorkflowType.CONTEXT_ANALYSIS,
        )

        ctx.record_files_processed(1)
        ctx.add_metadata("file_path", test_file)

    if response.success:
        print(f"✅ Context analysis completed in {response.execution_time:.2f}s")
        print(f"📊 Estimated tokens: {response.estimated_tokens}")
        print(f"📋 Context Analysis:\n{response.content}")
    else:
        print(f"❌ Error: {response.error}")


def test_model_availability():
    """Test Ollama model availability"""
    print("\n🔧 Testing Model Availability")
    print("=" * 50)

    client = get_ollama_client()

    if client.is_available():
        print("✅ Ollama is available")
        models = client.list_models()
        print(f"📋 Available models: {models}")

        # Test each model size if available
        for model_size in ModelSize:
            if model_size.value in models:
                print(f"✅ {model_size.name}: {model_size.value}")
            else:
                print(f"❌ {model_size.name}: {model_size.value} (not available)")
    else:
        print("❌ Ollama is not available")
        print("💡 Install Ollama and run: ollama pull llama3.2:1b")


def show_metrics_summary():
    """Show collected metrics summary"""
    print("\n📊 Metrics Summary")
    print("=" * 50)

    collector = get_metrics_collector()
    summary = collector.get_metrics_summary()

    if "error" in summary:
        print("❌ No metrics collected")
        return

    print(f"Total workflows: {summary['total_workflows']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"Average execution time: {summary['execution_time']['avg']:.2f}s")
    print(f"Average tokens per workflow: {summary['tokens']['total_avg']:.0f}")
    print(f"Token efficiency: {summary['efficiency']['tokens_per_second']:.0f} tokens/sec")

    # Export metrics
    export_path = collector.export_metrics()
    print(f"📁 Metrics exported to: {export_path}")


def main():
    """Main test function"""
    print("🚀 AI Development Tools - Comprehensive Ollama Integration Test")
    print("=" * 70)

    # Check Ollama availability first
    test_model_availability()

    client = get_ollama_client()
    if not client.is_available():
        print("\n❌ Ollama not available. Please install and run:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        print("   ollama pull llama3.2:1b")
        return 1

    # Run comprehensive tests
    test_pattern_detection()
    test_safety_assessment()
    test_exit_code_decision()
    test_context_analysis()

    # Show results
    show_metrics_summary()

    print("\n✅ Comprehensive Ollama integration test completed!")
    print("\n🎯 Key Benefits Demonstrated:")
    print("  • Standardized system prompts for consistent AI behavior")
    print("  • Token-efficient exit-code-first decision making")
    print("  • Automatic metrics collection and analysis")
    print("  • Reproducible testing with standard codebase")
    print("  • Local AI model integration for privacy and speed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
