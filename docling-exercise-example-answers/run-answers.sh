#!/usr/bin/env bash
# Run all three workshop answer scripts in sequence.
# Execute from the repo root:  bash workshop--example-answers/run-answers.sh

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "══════════════════════════════════════════════════════════"
echo " Part 1 — Docling: parse PDF, extract images/tables, chunk"
echo "══════════════════════════════════════════════════════════"
uv run --no-project --with docling --with transformers --with typing-extensions \
    workshop--example-answers/docling-starter-script.py \
    -i workshop/attention.pdf

echo ""
echo "══════════════════════════════════════════════════════════"
echo " Part 2 — DuckDB: persist chunks and query"
echo "══════════════════════════════════════════════════════════"
uv run --no-project --with duckdb \
    workshop--example-answers/docling-part2-answer.py \
    -i workshop/output/20260212_125354/chunks/chunks.json \
    --search "transformer"

echo ""
echo "══════════════════════════════════════════════════════════"
echo " Part 3 — Hybrid search (BM25 + vector) + RAG"
echo "══════════════════════════════════════════════════════════"
uv run --no-project --with duckdb --with ollama \
    workshop--example-answers/docling-part3-answer.py \
    --query "How does the transformer handle long-range dependencies?"

