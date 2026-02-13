#!/usr/bin/env python3
"""🔴 Path B: Corrective RAG (CRAG) — ANSWER KEY

Complete implementation of Retrieve → Grade → Retry loop.

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_example_answer/path_b_corrective_rag_answer.py \
        --query "How does attention work in transformers?" --threshold 0.3
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# NOTE: This imports from the example answer key. To use YOUR OWN Part 3 code
# instead, change the two lines below:
#   sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docling-exercise"))
#   from docling_part3_exercise import (  ← rename your file to use underscores!)
# (Python can't import filenames with hyphens, so rename
#  docling-part3-exercise.py → docling_part3_exercise.py first)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docling-exercise-example-answers"))

from docling_part3_answer import (  # ← change to docling_part3_exercise to use YOUR code (see NOTE above)
    _connect_db, _hybrid_search, _generate_answer,
    _add_embeddings, _create_indexes,
)
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
MAX_RETRIES = 2


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 ✅: rewrite_query()
# ═══════════════════════════════════════════════════════════════════════════

def rewrite_query(original_query: str) -> str:
    """Ask the remote LLM to rewrite a query for better retrieval."""
    resp = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user",
                   "content": (
                       f"Rewrite this search query to be more specific and "
                       f"likely to find relevant documents: {original_query}\n\n"
                       f"Return ONLY the rewritten query, nothing else."
                   )}],
    )
    rewritten = resp.choices[0].message.content.strip()
    return rewritten



# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 ✅: grade_documents()
# ═══════════════════════════════════════════════════════════════════════════

def grade_documents(query: str, chunks: list[dict],
                    threshold: float = 0.3) -> tuple[list[dict], float]:
    """Grade documents using reranker scores. Returns (good_chunks, avg_score)."""
    texts = [c["text"] for c in chunks]

    # Rerank ALL documents to get scores
    scored = _rerank(query, texts, top_k=len(texts))

    # Filter by threshold
    good = [{"text": t, "score": s} for t, s in scored if s >= threshold]
    all_scores = [s for _, s in scored]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

    print(f"   📊 Grading results:")
    for i, (t, s) in enumerate(scored):
        status = "✅" if s >= threshold else "❌"
        print(f"\n   ── Rank {i+1} | rerank_score={s:.4f} {status} ──")
        print(f"   {t}")
    print(f"\n   📊 Avg score: {avg_score:.3f} | Threshold: {threshold}")
    print(f"   📊 Kept {len(good)}/{len(chunks)} documents above threshold")

    return good, avg_score


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 ✅: corrective_rag()
# ═══════════════════════════════════════════════════════════════════════════

def corrective_rag(conn, query: str, threshold: float = 0.3,
                   top_k: int = 5) -> list[dict]:
    """CRAG loop: retrieve → grade → rewrite if needed → retry."""
    current_query = query
    t0 = time.time()

    for attempt in range(MAX_RETRIES + 1):
        print(f"\n{'='*60}")
        print(f"🔍 Attempt {attempt + 1}/{MAX_RETRIES + 1}: '{current_query}'")
        print(f"{'='*60}")

        # Step A: Retrieve
        chunks = _hybrid_search(conn, current_query, top_k=top_k)
        print(f"   📦 Retrieved {len(chunks)} chunks")

        # Step B: Grade
        good, avg = grade_documents(current_query, chunks, threshold)

        # Step C: Decide
        if avg >= threshold:
            elapsed = time.time() - t0
            print(f"\n   ✅ Quality sufficient! (avg={avg:.3f} >= {threshold})")
            print(f"   ⏱️  Total time: {elapsed:.1f}s across {attempt + 1} attempt(s)")
            return good if good else chunks

        if attempt < MAX_RETRIES:
            # Rewrite and retry
            new_q = rewrite_query(current_query)
            print(f"\n   🔄 Rewriting query:")
            print(f"      Before: '{current_query}'")
            print(f"      After:  '{new_q}'")
            current_query = new_q
        else:
            elapsed = time.time() - t0
            print(f"\n   ⚠️  Max retries reached. Using best available results.")
            print(f"   ⏱️  Total time: {elapsed:.1f}s across {attempt + 1} attempt(s)")
            return good if good else chunks

    return chunks  # fallback


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 ✅: CLI main()
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🔴 Path B: Corrective RAG — Retrieve → Grade → Retry"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--threshold", type=float, default=0.3)
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        good_chunks = corrective_rag(conn, args.query, args.threshold)

        print(f"\n{'='*60}")
        print(f"💬 Generating final answer...")
        print(f"{'='*60}")
        _generate_answer(args.query, good_chunks)

        conn.close()
        return 0
    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())