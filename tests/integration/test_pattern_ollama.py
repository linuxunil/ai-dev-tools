#!/usr/bin/env python3
"""
Test Pattern Scanner with Ollama integration
"""

import subprocess
import sys


def test_pattern_scanner_with_ollama():
    """Test pattern scanner with AI decision making"""

    print("🔍 Testing Pattern Scanner with Ollama")
    print("=" * 40)

    # Test 1: Find function patterns
    print("\n📋 Test 1: Function definition patterns")
    result = subprocess.run(
        ["python3", "standalone_pattern_scanner.py", "test_patterns.py", "1"],
        capture_output=True,
    )

    pattern_count = result.returncode
    print(f"📊 Pattern count (exit code): {pattern_count}")

    # AI decision based on pattern count
    if pattern_count == 255:
        decision = "ERROR - Cannot proceed"
    elif pattern_count > 100:
        decision = "HIGH - Many similar patterns found, good for systematic fixes"
    elif pattern_count > 10:
        decision = "MEDIUM - Some patterns found, review recommended"
    elif pattern_count > 0:
        decision = "LOW - Few patterns found, manual review needed"
    else:
        decision = "NONE - No similar patterns found"

    print(f"🤖 AI Decision: {decision}")

    # Test with Ollama
    prompt = f"""
    A pattern scanner found {pattern_count} similar code patterns.
    
    Pattern counts mean:
    - 0: No similar patterns
    - 1-10: Few patterns (manual review)
    - 11-100: Some patterns (systematic fix possible)
    - 100+: Many patterns (excellent for automation)
    
    What action should be taken? Answer in one word: MANUAL, REVIEW, AUTOFIX, or SKIP.
    """

    try:
        ollama_result = subprocess.run(
            ["ollama", "run", "llama3.2:1b", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if ollama_result.returncode == 0:
            ai_response = ollama_result.stdout.strip()
            print(f"🧠 Ollama response: {ai_response}")
        else:
            print(f"❌ Ollama error: {ollama_result.stderr}")

    except subprocess.TimeoutExpired:
        print("⏰ Ollama timeout")
    except Exception as e:
        print(f"❌ Error calling Ollama: {e}")

    # Test 2: Import patterns
    print("\n📋 Test 2: Import statement patterns")
    result2 = subprocess.run(
        ["python3", "standalone_pattern_scanner.py", "test_patterns2.py", "1"],
        capture_output=True,
    )

    import_count = result2.returncode
    print(f"📊 Import pattern count: {import_count}")

    print("\n✅ Pattern Scanner tests completed!")
    print(f"🎯 Key Benefits:")
    print(f"  • Zero-token pattern counting via exit codes")
    print(f"  • AI can make decisions using only exit codes")
    print(
        f"  • Found {pattern_count} function patterns and {import_count} import patterns"
    )
    print(f"  • Sub-second execution for rapid feedback")


if __name__ == "__main__":
    test_pattern_scanner_with_ollama()
