#!/bin/bash
# AI Development Tools Batch Benchmark Runner
# Automated batch testing across multiple configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

show_help() {
    cat << EOF
AI Development Tools Batch Benchmark Suite

USAGE:
    ./scripts/run_batch.sh [BATCH] [OPTIONS]

BATCH TYPES:
    quick         - Fast validation (light + medium profiles, small samples)
    standard      - Production testing (all profiles, standard samples)
    comprehensive - Exhaustive analysis (all profiles, large samples)
    scaling       - Model scaling comparison (same samples across profiles)
    sample_size   - Sample size impact analysis (medium profile, varying samples)

EXECUTION MODES:
    --sequential  - Run configurations one after another [DEFAULT]
    --parallel    - Run configurations concurrently (faster, more resource intensive)

OPTIONS:
    --max-concurrent N  - Max parallel runs (default: 2, only for --parallel)
    --output-dir DIR    - Output directory (default: batch_results)
    --no-build         - Skip Docker rebuild
    --dry-run          - Show what would be run without executing
    --help             - Show this help

EXAMPLES:
    ./scripts/run_batch.sh quick
    ./scripts/run_batch.sh standard --parallel --max-concurrent 3
    ./scripts/run_batch.sh comprehensive --output-dir results/comprehensive
    ./scripts/run_batch.sh scaling --dry-run

BATCH DESCRIPTIONS:
    quick:         2 configurations, 2-3 samples each (~5-10 min)
    standard:      3 configurations, 8 samples, 10 repetitions each (80 total samples/config, ~30-60 min)
    comprehensive: 3 configurations, 10-20 samples each (~45-90 min)
    scaling:       3 configurations, 5 samples each (~15-20 min)
    sample_size:   4 configurations, 3-20 samples each (~20-40 min)

RESOURCE REQUIREMENTS:
    Light batches:  8GB+ RAM, 2+ cores
    Medium batches: 16GB+ RAM, 4+ cores
    Heavy batches:  32GB+ RAM, 8+ cores (for comprehensive/parallel)
EOF
}

show_configurations() {
    cat << EOF
📋 AVAILABLE BATCH CONFIGURATIONS:

QUICK (Fast validation):
  • light_quick:   1 model, 2 samples  (laptop test)
  • medium_quick:  2 models, 3 samples (desktop test)

STANDARD (Production testing):
  • light_standard:   1 model, 8 samples, 10 repetitions (80 total samples)
  • medium_standard:  2 models, 8 samples, 10 repetitions (80 total samples)  
  • heavy_standard:   4 models, 8 samples, 10 repetitions (80 total samples)

COMPREHENSIVE (Exhaustive analysis):
  • light_comprehensive:   1 model, 10 samples  (deep laptop analysis)
  • medium_comprehensive:  2 models, 15 samples (deep desktop analysis)
  • heavy_comprehensive:   4 models, 20 samples (deep server analysis)

SCALING (Model scaling comparison):
  • scaling_small:   1 model, 5 samples  (small model baseline)
  • scaling_medium:  2 models, 5 samples (medium model comparison)
  • scaling_large:   4 models, 5 samples (large model comparison)

SAMPLE_SIZE (Sample size impact):
  • samples_3:   2 models, 3 samples   (low sample count)
  • samples_6:   2 models, 6 samples   (medium sample count)
  • samples_12:  2 models, 12 samples  (high sample count)
  • samples_20:  2 models, 20 samples  (very high sample count)
EOF
}

# Parse arguments
BATCH_TYPE=""
MODE="--sequential"
BUILD_FLAG="--build"
EXTRA_ARGS=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        quick|standard|comprehensive|scaling|sample_size)
            BATCH_TYPE="$1"
            shift
            ;;
        --sequential)
            MODE="sequential"
            shift
            ;;
        --parallel)
            MODE="--mode parallel"
            shift
            ;;
        --max-concurrent)
            EXTRA_ARGS="$EXTRA_ARGS --max-concurrent $2"
            shift 2
            ;;
        --output-dir)
            EXTRA_ARGS="$EXTRA_ARGS --output-dir $2"
            shift 2
            ;;
        --no-build)
            BUILD_FLAG=""
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --configurations)
            show_configurations
            exit 0
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

if [[ -z "$BATCH_TYPE" ]]; then
    echo "❌ Error: Batch type required"
    echo "Available: quick, standard, comprehensive, scaling, sample_size"
    echo "Run --help for detailed information"
    exit 1
fi

echo "🚀 AI Development Tools Batch Benchmark Suite"
echo "📊 Batch: $(echo $BATCH_TYPE | tr '[:lower:]' '[:upper:]') | Mode: $(echo $MODE | sed 's/--mode //')"
echo "======================================================================"

if [[ "$DRY_RUN" == true ]]; then
    echo "🔍 DRY RUN - Showing configuration without execution"
    echo ""
    uv run python scripts/batch_benchmark.py "$BATCH_TYPE" "$MODE" $EXTRA_ARGS --help
    echo ""
    show_configurations | grep -A 10 "$(echo $BATCH_TYPE | tr '[:lower:]' '[:upper:]')"
    exit 0
fi

# Determine required containers based on batch type
case $BATCH_TYPE in
    quick)
        echo "🪶 Starting containers for quick batch (light + medium profiles)"
        CONTAINERS="ollama-small ollama-medium"
        ;;
    standard|scaling|sample_size)
        echo "⚖️  Starting containers for standard batch (all main profiles)"
        CONTAINERS="ollama-small ollama-medium ollama-large"
        ;;
    comprehensive)
        echo "🏋️  Starting containers for comprehensive batch (all profiles including code)"
        CONTAINERS=""  # Start all with extended profile
        ;;
esac

# Start appropriate containers
if [[ -n "$CONTAINERS" ]]; then
    echo "🐳 Starting containers: $CONTAINERS"
    podman compose up -d $BUILD_FLAG $CONTAINERS
else
    echo "🐳 Starting all containers (extended profile)"
    podman compose --profile extended up -d $BUILD_FLAG
fi

echo "⏳ Waiting for containers to be ready..."
sleep 10

# Check container health
echo "🏥 Checking container health..."
podman ps

echo ""
echo "🔥 Running batch benchmark: $BATCH_TYPE"
echo "⚡ Command: uv run python scripts/batch_benchmark.py $BATCH_TYPE "$MODE" $EXTRA_ARGS"
echo ""

# Run the batch benchmark
uv run python scripts/batch_benchmark.py "$BATCH_TYPE" --mode "$MODE" $EXTRA_ARGSecho ""
echo "✅ Batch benchmark complete!"
echo "📊 Results saved in batch_results/ directory"
echo "🐳 Containers still running - use 'docker compose down' to stop"