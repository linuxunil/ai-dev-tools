#!/bin/bash
# Benchmark Setup Script - Sets up Ollama containers for metrics collection

set -e

echo "🚀 Setting up AI Development Tools Benchmark Environment"
echo "========================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start Ollama container
echo "🐳 Starting Ollama container..."
docker compose up -d ollama

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
timeout=60
count=0
while ! curl -s http://localhost:11434/api/version > /dev/null; do
    sleep 2
    count=$((count + 2))
    if [ $count -ge $timeout ]; then
        echo "❌ Timeout waiting for Ollama to start"
        exit 1
    fi
done

echo "✅ Ollama is ready!"

# Install default models for benchmarking
echo "📦 Installing benchmark models..."
uv run ai-benchmark setup-models --models "llama3.2:1b,llama3.2:3b"

echo "🎯 Running quick verification test..."
uv run ai-benchmark standardized --models "small" --output-file "benchmark_test.json"

echo ""
echo "✅ Setup complete! You can now run benchmarks:"
echo ""
echo "# Run standardized benchmark suite"
echo "uv run ai-benchmark standardized --models 'small,medium'"
echo ""
echo "# Test multiple Ollama instances" 
echo "docker compose --profile multi-instance up -d"
echo "uv run ai-benchmark standardized --ollama-hosts 'localhost:11434,localhost:11435'"
echo ""
echo "# View results"
echo "cat benchmark_test.json | jq '.comparisons'"