#!/usr/bin/env python3
"""🟢 Path D: Robust RAG — Easiest · ~60 new lines

Build HyDE + Multi-Query + Reranking into a polished, production-quality pipeline.

You will:
  1. Build hyde_search()       — generate a fake answer, embed it, search with its vector
  2. Build multi_query_search() — generate 3 query variants, search all, fuse with RRF
  3. Build robust_search()     — strategy wrapper with optional reranking + timing
  4. Wire up CLI               — --strategy and --rerank flags

═══════════════════════════════════════════════════════════════════════════════
REUSING YOUR PART 1-3 CODE
═══════════════════════════════════════════════════════════════════════════════
This file imports functions YOU built in Parts 1-3:
  • _search_vector(conn, query_vec, limit)  — cosine similarity search (Part 3, TODO 14)
  • _hybrid_search(conn, query, top_k)      — RRF fusion of BM25+Vector (Part 3, TODO 16)
  • _generate_answer(query, chunks)         — LLM generation (Part 3, TODO 17)
  • ollama.embed(model, input)              — local embeddings (Part 3, TODO 12)
  • RRF_K                                   — RRF constant k=60 (Part 3)

NEW TODAY (Remote GPU):
  • chat_client.chat.completions.create()   — remote 8B LLM for generation/rewriting
  • _rerank(query, documents, top_k)        — remote reranker for scoring/filtering

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_exercise/path_d_robust_rag.py \
        --query "How does attention work in transformers?" \
        --strategy hyde --rerank

Prerequisites:
  • workshop/docling_part3.py must exist (cp your Part 3 exercise)
  • workshop/output/rag_chunks.duckdb from Part 2
  • Ollama running with qwen3-embedding:0.6b
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# ── Make Part 3 importable ──────────────────────────────────────────────────
# The Part 3 answer key lives in workshop/workshop--example-answers/.
# We add that directory to Python's path so the import works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "workshop--example-answers"))

from docling_part3_answer import (   # Part 3 functions (local search)
    _connect_db, _search_vector, _search_bm25,
    _hybrid_search, _generate_answer,
    _add_embeddings, _create_indexes,
    EMBED_MODEL, RRF_K,
)
import ollama                         # Local embeddings
from openai import OpenAI             # Remote GPU chat
import requests                       # Remote GPU reranker

# ── Remote GPU Models (provided — no changes needed) ────────────────────────
# These point to Modal GPU endpoints. No API key required.
chat_client = OpenAI(
    base_url="https://dev-8--vllm-qwen3-vl-8b-serve.modal.run/v1",
    api_key="not-needed",
)
CHAT_MODEL = "qwen3-vl-8b"

RERANK_URL = "https://dev-8--qwen3-vl-reranker-2b-serve.modal.run/v1/rerank"
RERANK_MODEL = "qwen3-vl-reranker-2b"

def _rerank(query: str, documents: list[str], top_k: int = 3) -> list[tuple[str, float]]:
    """Rerank documents using remote GPU reranker. Returns [(text, score), ...]."""
    resp = requests.post(RERANK_URL, json={
        "model": RERANK_MODEL, "query": query,
        "documents": documents, "top_n": top_k,
    })
    results = resp.json()["results"]
    return [(r["document"], r["relevance_score"]) for r in results]

# ── Constants ───────────────────────────────────────────────────────────────
DEFAULT_DB = Path(__file__).resolve().parent.parent / "output" / "rag_chunks.duckdb"


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 (★★): Build hyde_search()  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# HyDE = Hypothetical Document Embeddings.
# Insight: A short query ("attention mechanism?") produces a vague embedding.
#          A fake 200-word answer produces a SPECIFIC embedding that's closer
#          to real documents in vector space.
#
# You REUSE from Part 3:
#   • ollama.embed(model=EMBED_MODEL, input=text) → {"embeddings": [[...]]}
#   • _search_vector(conn, query_vec, limit)       → [(chunk_id, score), ...]
#
# You USE NEW today:
#   • chat_client.chat.completions.create(model=CHAT_MODEL, messages=[...])
#     → resp.choices[0].message.content
# ───────────────────────────────────────────────────────────────────────────

def hyde_search(conn, query: str, top_k: int = 5) -> list[dict]:
    """Search using HyDE: generate fake answer → embed it → vector search."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 1: Implement HyDE search.                              │
    # │                                                              │
    # │  Step A: Generate a hypothetical answer using the remote LLM │
    # │    - Use chat_client.chat.completions.create()               │
    # │    - Prompt: "Write a short passage that answers: {query}"   │
    # │    - Extract: resp.choices[0].message.content                │
    # │                                                              │
    # │  Step B: Embed the FAKE ANSWER (not the query!)              │
    # │    - ollama.embed(model=EMBED_MODEL, input=fake_answer)      │
    # │    - Get vector: resp["embeddings"][0]                       │
    # │                                                              │
    # │  Step C: Search with the fake answer's embedding             │
    # │    - _search_vector(conn, hyde_vec, limit=top_k)             │
    # │                                                              │
    # │  Step D: Fetch text for each result                          │
    # │    - conn.execute("SELECT chunk_id, text FROM rag_chunks     │
    # │      WHERE chunk_id = ?", [chunk_id]).fetchone()             │
    # │    - Return list of {"chunk_id": ..., "text": ..., "score":} │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 1: implement hyde_search()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 (★★★): Build multi_query_search()  — ~25 lines
# ═══════════════════════════════════════════════════════════════════════════
# Multi-Query = cast a wider net. One query might miss documents due to
# vocabulary mismatch. Generate 3 variants, search with ALL of them,
# and fuse results using RRF — the SAME algorithm you built in Part 3!
#
# You REUSE from Part 3:
#   • _hybrid_search(conn, query, top_k)  → [{"chunk_id", "text", "rrf_score"}]
#   • RRF_K constant (k=60)
# ───────────────────────────────────────────────────────────────────────────

def multi_query_search(conn, query: str, top_k: int = 5) -> list[dict]:
    """Search using Multi-Query: generate variants → search all → RRF merge."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 2: Implement Multi-Query search.                       │
    # │                                                              │
    # │  Step A: Generate 3 query variants using the remote LLM      │
    # │    - Prompt: "Generate 3 different search queries for:       │
    # │      {query}\nReturn one query per line. No numbering."      │
    # │    - Split response by newlines, take first 3                │
    # │    - Combine: all_queries = [query] + variants               │
    # │                                                              │
    # │  Step B: Search with each variant                            │
    # │    - For each q in all_queries:                               │
    # │      results = _hybrid_search(conn, q, top_k=top_k)         │
    # │    - Accumulate RRF scores across all searches:              │
    # │      fused_scores[cid] += 1.0 / (RRF_K + rank + 1)         │
    # │      (same RRF formula from Part 3!)                         │
    # │                                                              │
    # │  Step C: Sort by fused score, return top_k                   │
    # │    - Return [{"chunk_id": ..., "text": ..., "rrf_score": ...}]│
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 2: implement multi_query_search()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 (★★): Build robust_search()  — ~20 lines
# ═══════════════════════════════════════════════════════════════════════════
# The production wrapper: pick a strategy, optionally rerank, log timing.
#
# You REUSE from Part 3:
#   • _hybrid_search() as the default/fallback strategy
# You USE NEW today:
#   • _rerank(query, documents, top_k) → [(text, score), ...]
# ───────────────────────────────────────────────────────────────────────────

def robust_search(conn, query: str, strategy: str = "hyde",
                  use_rerank: bool = True, top_k: int = 5) -> list[dict]:
    """Production-quality search: strategy selection + optional reranking."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 3: Implement the strategy wrapper.                     │
    # │                                                              │
    # │  Step A: Record start time with time.time()                  │
    # │                                                              │
    # │  Step B: Strategy selection (if/elif/else)                   │
    # │    - "hyde"   → hyde_search(conn, query, top_k=top_k*2)     │
    # │    - "multi"  → multi_query_search(conn, query, top_k*2)    │
    # │    - else     → _hybrid_search(conn, query, top_k=top_k*2)  │
    # │    (Fetch top_k*2 so reranker has more to work with)         │
    # │                                                              │
    # │  Step C: Optional reranking                                  │
    # │    - If use_rerank: extract texts, call _rerank()            │
    # │    - Build results: [{"text": t, "score": s} for t, s in ..]│
    # │    - If not reranking: just take first top_k candidates      │
    # │                                                              │
    # │  Step D: Log timing                                          │
    # │    - Print strategy name, rerank status, elapsed time        │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 3: implement robust_search()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 (★): Wire up CLI  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# Add --strategy and --rerank flags. Same argparse pattern as Part 3.
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🟢 Path D: Robust RAG — HyDE + Multi-Query + Reranking"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 4: Add --strategy and --rerank flags.                  │
    # │                                                              │
    # │  --strategy: choices=["hyde", "multi", "hybrid"]             │
    # │              default="hyde"                                   │
    # │  --rerank:   action="store_true" (flag, no value needed)     │
    # │                                                              │
    # │  Then call robust_search() with the parsed args and          │
    # │  pass results to _generate_answer().                         │
    # └──────────────────────────────────────────────────────────────┘
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        # TODO 4: Call robust_search() and _generate_answer() here
        raise NotImplementedError("TODO 4: wire up CLI")

        conn.close()
        return 0
    except NotImplementedError as exc:
        print(f"\n⚠️  {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
