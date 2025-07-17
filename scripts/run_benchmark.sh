#!/bin/bash
# AI Development Tools Benchmark Runner
# Hardware-optimized benchmark profiles for different environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

show_help() {
    cat << EOF
AI Development Tools Benchmark Suite

USAGE:
    ./scripts/run_benchmark.sh [PROFILE] [OPTIONS]

PROFILES:
    light   - Laptop/Low-resource (1 model: llama3.2:1b)
    medium  - Desktop/Standard (2 models: llama3.2:1b, 3b) [DEFAULT]
    heavy   - Server/High-resource (4 models: llama3.2:1b, 3b, llama3.1:8b, codellama:7b)

OPTIONS:
    --samples N    - Override sample size (default: light=3, medium=6, heavy=12)
    --no-build     - Skip Docker rebuild
    --help         - Show this help

EXAMPLES:
    ./scripts/run_benchmark.sh light
    ./scripts/run_benchmark.sh medium --samples 10
    ./scripts/run_benchmark.sh heavy --no-build

HARDWARE RECOMMENDATIONS:
    Light:  8GB+ RAM, 2+ cores (laptop/minimal testing)
    Medium: 16GB+ RAM, 4+ cores (desktop/development)
    Heavy:  32GB+ RAM, 8+ cores (server/comprehensive testing)
EOF
}

# Parse arguments
PROFILE="medium"
BUILD_FLAG="--build"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        light|medium|heavy)
            PROFILE="$1"
            shift
            ;;
        --samples)
            EXTRA_ARGS="$EXTRA_ARGS --samples $2"
            shift 2
            ;;
        --no-build)
            BUILD_FLAG=""
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 AI Development Tools Benchmark Suite"
echo "📊 Profile: ${PROFILE^^} hardware target"
echo "=" * 50

# Start appropriate containers based on profile
case $PROFILE in
    light)
        echo "🪶 Starting light profile (laptop): 1 model"
        podman compose up -d $BUILD_FLAG ollama-small
        ;;
    medium)
        echo "⚖️  Starting medium profile (desktop): 2 models"
        podman compose --profile medium up -d $BUILD_FLAG
        ;;
    heavy)
        echo "🏋️  Starting heavy profile (server): 4 models"
        podman compose --profile extended up -d $BUILD_FLAG
        ;;
esac

echo "⏳ Waiting for containers to be ready..."
sleep 5

echo "🔥 Running async benchmark with profile: $PROFILE"
uv run python scripts/async_benchmark.py --profile "$PROFILE" $EXTRA_ARGS

echo "✅ Benchmark complete!"
echo "📊 Results saved with profile prefix: benchmark_${PROFILE}_*.json"