#!/usr/bin/env python3
"""🟡 Path A: Modular RAG — Medium · ~80 new lines

Build a smart router that classifies queries and picks the best search strategy.

You will:
  1. Build hyde_search()        — generate a fake answer, embed it, search (same as Path D)
  2. Build multi_query_search() — generate variants, search all, RRF merge (same as Path D)
  3. Build classify_query()     — LLM classifies query as factual/conceptual/ambiguous
  4. Build modular_rag()        — router that picks the best strategy per query type
  5. Wire up CLI                — --query flag, automatic routing

═══════════════════════════════════════════════════════════════════════════════
REUSING YOUR PART 1-3 CODE
═══════════════════════════════════════════════════════════════════════════════
This file imports functions YOU built in Parts 1-3:
  • _search_bm25(conn, query, limit)           — keyword search (Part 3, TODO 13)
  • _search_vector(conn, query_vec, limit)      — cosine similarity (Part 3, TODO 14)
  • _hybrid_search(conn, query, top_k)          — RRF fusion (Part 3, TODO 16)
  • _generate_answer(query, chunks)             — LLM generation (Part 3, TODO 17)
  • ollama.embed(model, input)                  — local embeddings (Part 3, TODO 12)
  • RRF_K                                       — RRF constant k=60

NEW TODAY (Remote GPU):
  • chat_client.chat.completions.create()       — remote 8B LLM for classification
  • _rerank(query, documents, top_k)            — remote reranker for scoring

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_exercise/path_a_modular_rag.py \
        --query "How does attention work in transformers?"

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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "workshop--example-answers"))

from docling_part3_answer import (
    _connect_db, _search_vector, _search_bm25,
    _hybrid_search, _generate_answer,
    _add_embeddings, _create_indexes,
    EMBED_MODEL, RRF_K,
)
import ollama
from openai import OpenAI
import requests

# ── Remote GPU Models (provided — no changes needed) ────────────────────────
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
# A short query produces a vague embedding. A fake 200-word answer produces
# a SPECIFIC embedding closer to real documents in vector space.
#
# You REUSE: ollama.embed(), _search_vector()
# You USE NEW: chat_client.chat.completions.create()
# ───────────────────────────────────────────────────────────────────────────

def hyde_search(conn, query: str, top_k: int = 5) -> list[dict]:
    """Search using HyDE: generate fake answer → embed it → vector search."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 1: Implement HyDE search.                              │
    # │                                                              │
    # │  Step A: Generate a hypothetical answer using remote LLM     │
    # │    - chat_client.chat.completions.create(model=CHAT_MODEL,   │
    # │      messages=[{"role":"user","content":"Write a short       │
    # │      passage that answers: {query}"}])                       │
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
    # │      WHERE chunk_id = ?", [cid]).fetchone()                  │
    # │    - Return [{"chunk_id": ..., "text": ..., "score": ...}]   │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 1: implement hyde_search()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 (★★★): Build multi_query_search()  — ~25 lines
# ═══════════════════════════════════════════════════════════════════════════
# Generate 3 query variants, search with ALL of them, fuse with RRF.
# Same RRF algorithm you built in Part 3!
#
# You REUSE: _hybrid_search(), RRF_K
# ───────────────────────────────────────────────────────────────────────────

def multi_query_search(conn, query: str, top_k: int = 5) -> list[dict]:
    """Search using Multi-Query: generate variants → search all → RRF merge."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 2: Implement Multi-Query search.                       │
    # │                                                              │
    # │  Step A: Generate 3 query variants using remote LLM          │
    # │    - Prompt: "Generate 3 different search queries for:       │
    # │      {query}\nReturn one query per line. No numbering."      │
    # │    - Split by newlines, take first 3 non-empty lines         │
    # │    - all_queries = [query] + variants                        │
    # │                                                              │
    # │  Step B: Search with each variant using _hybrid_search()     │
    # │    - For each q: results = _hybrid_search(conn, q, top_k)   │
    # │    - Accumulate RRF: fused[cid] += 1/(RRF_K + rank + 1)    │
    # │                                                              │
    # │  Step C: Sort by fused score, fetch text, return top_k       │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 2: implement multi_query_search()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 (★★★): Build classify_query()  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# The BRAIN of Modular RAG. Classify the query so we can route it.
#
# Query types:
#   "factual"    → specific fact lookup  → BM25 is best (exact keyword match)
#   "conceptual" → explanation needed    → HyDE is best (semantic understanding)
#   "ambiguous"  → vague/short query     → Multi-Query (cast a wider net)
# ───────────────────────────────────────────────────────────────────────────

def classify_query(query: str) -> str:
    """Classify query as 'factual', 'conceptual', or 'ambiguous'."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 3: Classify the query type using the remote LLM.       │
    # │                                                              │
    # │  Step A: Build a classification prompt                       │
    # │    - System: "Classify the query as one of: factual,         │
    # │      conceptual, ambiguous. Reply with ONLY the word."       │
    # │    - User: the query                                         │
    # │                                                              │
    # │  Step B: Call chat_client.chat.completions.create()          │
    # │    - model=CHAT_MODEL, messages=[system_msg, user_msg]       │
    # │    - Extract: resp.choices[0].message.content.strip().lower()│
    # │                                                              │
    # │  Step C: Validate — if result not in expected set,           │
    # │    default to "ambiguous"                                    │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 3: implement classify_query()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 (★★): Build modular_rag()  — ~20 lines
# ═══════════════════════════════════════════════════════════════════════════
# The ROUTER: classify → pick strategy → search → rerank → generate.
#
# Routing table:
#   "factual"    → _search_bm25() + rerank
#   "conceptual" → hyde_search()  + rerank
#   "ambiguous"  → multi_query_search() + rerank
# ───────────────────────────────────────────────────────────────────────────

def modular_rag(conn, query: str, top_k: int = 5) -> list[dict]:
    """Smart router: classify query → pick best strategy → search → rerank."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 4: Implement the modular RAG router.                   │
    # │                                                              │
    # │  Step A: Classify the query                                  │
    # │    - qtype = classify_query(query)                           │
    # │    - Print: "📋 Query type: {qtype}"                         │
    # │                                                              │
    # │  Step B: Route to the best strategy                          │
    # │    - "factual"    → BM25 search (exact keywords)             │
    # │      rows = _search_bm25(conn, query, limit=top_k*2)        │
    # │      candidates = fetch text for each chunk_id               │
    # │    - "conceptual" → HyDE search (semantic)                   │
    # │      candidates = hyde_search(conn, query, top_k=top_k*2)   │
    # │    - "ambiguous"  → Multi-Query (wide net)                   │
    # │      candidates = multi_query_search(conn, query, top_k*2)  │
    # │                                                              │
    # │  Step C: Rerank all candidates                               │
    # │    - texts = [c["text"] for c in candidates]                 │
    # │    - reranked = _rerank(query, texts, top_k=top_k)           │
    # │    - Return [{"text": t, "score": s} for t, s in reranked]  │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 4: implement modular_rag()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5 (★): Wire up CLI  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# Simple CLI: just --query. The router decides the strategy automatically!
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🟡 Path A: Modular RAG — Smart Query Router"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 5: Wire up the CLI.                                    │
    # │                                                              │
    # │  - Parse args                                                │
    # │  - Connect DB, add embeddings, create indexes                │
    # │  - Call modular_rag(conn, args.query)                        │
    # │  - Pass results to _generate_answer(args.query, results)     │
    # └──────────────────────────────────────────────────────────────┘
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        # TODO 5: Call modular_rag() and _generate_answer() here
        raise NotImplementedError("TODO 5: wire up CLI")

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

