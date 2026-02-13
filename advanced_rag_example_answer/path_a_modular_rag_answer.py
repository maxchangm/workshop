#!/usr/bin/env python3
"""🟡 Path A: Modular RAG — ANSWER KEY

Complete implementation of smart query router with HyDE + Multi-Query + BM25.

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_example_answer/path_a_modular_rag_answer.py \
        --query "How does attention work in transformers?"
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

# NOTE: This imports from the example answer key. To use YOUR OWN Part 3 code
# instead, change the two lines below:
#   sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docling-exercise"))
#   from docling_part3_exercise import (  ← rename your file to use underscores!)
# (Python can't import filenames with hyphens, so rename
#  docling-part3-exercise.py → docling_part3_exercise.py first)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docling-exercise-example-answers"))

from docling_part3_answer import (  # ← change to docling_part3_exercise to use YOUR code (see NOTE above)
    _connect_db, _search_vector, _search_bm25,
    _hybrid_search, _generate_answer,
    _add_embeddings, _create_indexes,
    EMBED_MODEL, RRF_K,
)
import ollama
from openai import OpenAI
import requests

# ── Remote GPU Models ────────────────────────────────────────────────────────
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

DEFAULT_DB = Path(__file__).resolve().parent.parent / "docling-exercise-example-answers" / "output" / "rag_chunks.duckdb"


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 ✅: hyde_search()
# ═══════════════════════════════════════════════════════════════════════════

def hyde_search(conn, query: str, top_k: int = 5) -> list[dict]:
    """Search using HyDE: generate fake answer → embed it → vector search."""
    print(f"\n🔮 [HyDE] Generating hypothetical answer for: '{query}'")

    resp = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user",
                   "content": f"Write a short passage (~200 words) that answers: {query}"}],
    )
    fake_answer = resp.choices[0].message.content
    print(f"   📝 Fake answer:")
    print(f"   ┌{'─'*70}")
    for line in fake_answer.splitlines():
        print(f"   │ {line}")
    print(f"   └{'─'*70}")

    hyde_vec = ollama.embed(model=EMBED_MODEL, input=fake_answer)["embeddings"][0]
    print(f"   📐 Embedded fake answer → {len(hyde_vec)}-dim vector")

    vec_results = _search_vector(conn, hyde_vec, limit=top_k)

    results = []
    for chunk_id, score in vec_results:
        row = conn.execute(
            "SELECT chunk_id, text FROM rag_chunks WHERE chunk_id = ?",
            [chunk_id],
        ).fetchone()
        results.append({"chunk_id": row[0], "text": row[1], "score": score})

    print(f"\n   ✅ Found {len(results)} chunks via HyDE:")
    for i, c in enumerate(results):
        print(f"\n   ── Rank {i+1} | chunk_id={c['chunk_id']} | score={c['score']:.4f} ──")
        print(f"   {c['text']}")
    return results



# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 ✅: multi_query_search()
# ═══════════════════════════════════════════════════════════════════════════

def multi_query_search(conn, query: str, top_k: int = 5) -> list[dict]:
    """Search using Multi-Query: generate variants → search all → RRF merge."""
    print(f"\n🔀 [Multi-Query] Generating variants for: '{query}'")

    resp = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user",
                   "content": (
                       f"Generate 3 different search queries for: {query}\n"
                       f"Return one query per line. No numbering. No explanation."
                   )}],
    )
    raw = resp.choices[0].message.content
    variants = [line.strip() for line in raw.strip().split("\n") if line.strip()][:3]
    all_queries = [query] + variants

    print(f"   📋 All queries ({len(all_queries)}):")
    for i, q in enumerate(all_queries):
        tag = "original" if i == 0 else f"variant {i}"
        print(f"      [{tag}] {q}")

    fused_scores: dict[int, float] = defaultdict(float)
    chunk_texts: dict[int, str] = {}

    for q in all_queries:
        results = _hybrid_search(conn, q, top_k=top_k)
        for rank, chunk in enumerate(results):
            cid = chunk["chunk_id"]
            fused_scores[cid] += 1.0 / (RRF_K + rank + 1)
            chunk_texts[cid] = chunk["text"]

    sorted_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for cid, score in sorted_ids:
        results.append({"chunk_id": cid, "text": chunk_texts[cid], "rrf_score": score})

    print(f"\n   ✅ Fused {len(fused_scores)} unique chunks → returning top {len(results)}:")
    for i, c in enumerate(results):
        print(f"\n   ── Rank {i+1} | chunk_id={c['chunk_id']} | rrf_score={c['rrf_score']:.4f} ──")
        print(f"   {c['text']}")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 ✅: classify_query()
# ═══════════════════════════════════════════════════════════════════════════

def classify_query(query: str) -> str:
    """Classify query as 'factual', 'conceptual', or 'ambiguous'."""
    print(f"\n🏷️  [Classify] Analyzing query type: '{query}'")

    resp = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user",
                   "content": (
                       f"Classify this query into exactly one category:\n"
                       f"- factual: asks for specific facts, numbers, names\n"
                       f"- conceptual: asks about ideas, explanations, how things work\n"
                       f"- ambiguous: short, vague, or could mean multiple things\n\n"
                       f"Query: {query}\n\n"
                       f"Return ONLY the category name (factual, conceptual, or ambiguous)."
                   )}],
    )
    category = resp.choices[0].message.content.strip().lower()

    # Normalize to valid categories
    if "factual" in category:
        category = "factual"
    elif "conceptual" in category:
        category = "conceptual"
    else:
        category = "ambiguous"

    print(f"   🏷️  Category: {category}")
    return category


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 ✅: modular_rag()
# ═══════════════════════════════════════════════════════════════════════════

def modular_rag(conn, query: str, top_k: int = 5) -> list[dict]:
    """Route query to the best search strategy based on classification."""
    t0 = time.time()
    category = classify_query(query)

    print(f"\n🔀 [Router] Routing '{category}' query to best strategy...")

    if category == "factual":
        print(f"   → Using BM25 (keyword search for factual queries)")
        results = _search_bm25(conn, query, limit=top_k)
        chunks = []
        for chunk_id, score in results:
            row = conn.execute(
                "SELECT chunk_id, text FROM rag_chunks WHERE chunk_id = ?",
                [chunk_id],
            ).fetchone()
            chunks.append({"chunk_id": row[0], "text": row[1], "score": score})
        print(f"\n   ✅ Found {len(chunks)} chunks via BM25:")
        for i, c in enumerate(chunks):
            print(f"\n   ── Rank {i+1} | chunk_id={c['chunk_id']} | score={c['score']:.4f} ──")
            print(f"   {c['text']}")
    elif category == "conceptual":
        print(f"   → Using HyDE (semantic search for conceptual queries)")
        chunks = hyde_search(conn, query, top_k=top_k)
    else:  # ambiguous
        print(f"   → Using Multi-Query (cast wider net for ambiguous queries)")
        chunks = multi_query_search(conn, query, top_k=top_k)

    elapsed = time.time() - t0
    print(f"\n   ⏱️  Total routing + search time: {elapsed:.1f}s")
    return chunks


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5 ✅: CLI main()
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🟡 Path A: Modular RAG — Smart Query Router"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        chunks = modular_rag(conn, args.query)

        print(f"\n{'='*60}")
        print(f"💬 Generating final answer...")
        print(f"{'='*60}")
        _generate_answer(args.query, chunks)

        conn.close()
        return 0
    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())