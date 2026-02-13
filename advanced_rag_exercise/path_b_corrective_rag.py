#!/usr/bin/env python3
"""🔴 Path B: Corrective RAG (CRAG) — Hard · ~55 new lines

Build a self-correcting retrieval loop: Retrieve → Grade → Retry if needed.

You will:
  1. Build rewrite_query()     — LLM rewrites a poor query for better retrieval
  2. Build grade_documents()   — use reranker scores as relevance grades (0-1)
  3. Build corrective_rag()    — the full retrieve → grade → retry loop
  4. Wire up CLI               — --query and --threshold flags

═══════════════════════════════════════════════════════════════════════════════
KEY INSIGHT: RERANKER AS GRADER
═══════════════════════════════════════════════════════════════════════════════
Traditional CRAG uses an LLM to grade each document ("Is this relevant?").
That's SLOW — one LLM call per document!

Our trick: use the reranker's relevance_score (0.0 to 1.0) as a grade.
  • score > 0.5  → relevant ✅
  • score < 0.3  → irrelevant ❌ → rewrite query and retry
This is 10x faster than LLM grading!

═══════════════════════════════════════════════════════════════════════════════
REUSING YOUR PART 1-3 CODE
═══════════════════════════════════════════════════════════════════════════════
  • _hybrid_search(conn, query, top_k)  — your RRF fusion search (Part 3)
  • _generate_answer(query, chunks)     — LLM generation (Part 3)

NEW TODAY (Remote GPU):
  • chat_client.chat.completions.create()  — remote LLM for query rewriting
  • _rerank(query, documents, top_k)       — remote reranker as document grader

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_exercise/path_b_corrective_rag.py \
        --query "How does attention work in transformers?" --threshold 0.3

Prerequisites:
  • workshop/docling_part3.py must exist (cp your Part 3 exercise)
  • docling-exercise-example-answers/output/rag_chunks.duckdb from Part 2
  • Ollama running with qwen3-embedding:0.6b
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# ── Make Part 3 importable ──────────────────────────────────────────────────
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
DEFAULT_DB = Path(__file__).resolve().parent.parent / "docling-exercise-example-answers" / "output" / "rag_chunks.duckdb"
MAX_RETRIES = 2  # Maximum number of query rewrites


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 (★★): Build rewrite_query()  — ~10 lines
# ═══════════════════════════════════════════════════════════════════════════
# When retrieved documents score poorly, the query itself may be the problem.
# Ask the LLM to rewrite it for better retrieval.
# ───────────────────────────────────────────────────────────────────────────

def rewrite_query(original_query: str) -> str:
    """Ask the remote LLM to rewrite a query for better retrieval."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 1: Rewrite the query using the remote LLM.             │
    # │                                                              │
    # │  Step A: Build a rewrite prompt                              │
    # │    - "Rewrite this search query to be more specific and      │
    # │      likely to find relevant documents: {original_query}"    │
    # │    - "Return ONLY the rewritten query, nothing else."        │
    # │                                                              │
    # │  Step B: Call chat_client.chat.completions.create()          │
    # │    - model=CHAT_MODEL                                        │
    # │    - Extract: resp.choices[0].message.content.strip()        │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 1: implement rewrite_query()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 (★★★): Build grade_documents()  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# Use the reranker as a GRADER. Instead of asking an LLM "is this relevant?"
# (slow!), we use the reranker's score as a relevance signal.
#
# Score interpretation:
#   > threshold (e.g. 0.3) → relevant ✅ keep it
#   ≤ threshold             → irrelevant ❌ discard it
# ───────────────────────────────────────────────────────────────────────────

def grade_documents(query: str, chunks: list[dict],
                    threshold: float = 0.3) -> tuple[list[dict], float]:
    """Grade documents using reranker scores. Returns (good_chunks, avg_score)."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 2: Grade documents using the reranker.                 │
    # │                                                              │
    # │  Step A: Extract texts from chunks                           │
    # │    - texts = [c["text"] for c in chunks]                     │
    # │                                                              │
    # │  Step B: Rerank ALL documents (not just top_k)               │
    # │    - scored = _rerank(query, texts, top_k=len(texts))        │
    # │    - This gives us scores for every document                 │
    # │                                                              │
    # │  Step C: Filter by threshold                                 │
    # │    - good = [{"text": t, "score": s} for t, s in scored      │
    # │             if s >= threshold]                                │
    # │    - avg_score = mean of all scores                          │
    # │                                                              │
    # │  Step D: Return (good_chunks, avg_score)                     │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 2: implement grade_documents()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 (★★★★): Build corrective_rag()  — ~25 lines
# ═══════════════════════════════════════════════════════════════════════════
# The CRAG loop: retrieve → grade → if bad, rewrite query → retry.
#
# Loop logic:
#   1. Search with current query
#   2. Grade the results
#   3. If avg_score >= threshold → good enough, generate answer
#   4. If avg_score < threshold  → rewrite query, go to step 1
#   5. After MAX_RETRIES, use whatever we have
# ───────────────────────────────────────────────────────────────────────────

def corrective_rag(conn, query: str, threshold: float = 0.3,
                   top_k: int = 5) -> list[dict]:
    """CRAG loop: retrieve → grade → rewrite if needed → retry."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 3: Implement the CRAG loop.                            │
    # │                                                              │
    # │  current_query = query                                       │
    # │  for attempt in range(MAX_RETRIES + 1):                      │
    # │                                                              │
    # │    Step A: Retrieve                                          │
    # │      - chunks = _hybrid_search(conn, current_query, top_k)   │
    # │      - Print: "🔍 Attempt {attempt+1}: searching..."         │
    # │                                                              │
    # │    Step B: Grade                                             │
    # │      - good, avg = grade_documents(current_query, chunks,    │
    # │                                    threshold)                │
    # │      - Print: "📊 Avg score: {avg:.3f}, Good: {len(good)}"  │
    # │                                                              │
    # │    Step C: Decide                                            │
    # │      - If avg >= threshold OR last attempt: return good      │
    # │        (or chunks if no good ones)                           │
    # │      - Else: rewrite query and continue loop                 │
    # │        new_q = rewrite_query(current_query)                  │
    # │        Print: "🔄 Rewriting: '{current_query}' → '{new_q}'" │
    # │        current_query = new_q                                 │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 3: implement corrective_rag()")



# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 (★): Wire up CLI  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# Add --query and --threshold flags.
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🔴 Path B: Corrective RAG — Retrieve → Grade → Retry"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--threshold", type=float, default=0.3)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 4: Wire up the pipeline.                               │
    # │                                                              │
    # │  - results = corrective_rag(conn, query, threshold)          │
    # │  - _generate_answer(query, results)                          │
    # └──────────────────────────────────────────────────────────────┘
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        # TODO 4: Call corrective_rag() and _generate_answer() here
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