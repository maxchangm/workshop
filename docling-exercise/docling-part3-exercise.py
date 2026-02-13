#!/usr/bin/env python3
"""Workshop Part 3: Hybrid Search & RAG with DuckDB + Ollama.

Part 2 persisted document chunks into DuckDB.  Part 3 enriches them with
vector embeddings and implements **hybrid search** (BM25 + cosine vector)
combined via Reciprocal Rank Fusion (RRF), then generates a RAG answer.

There are 6 TODOs (numbered 12–17, continuing from Part 2).

Prerequisites
─────────────
  • ``rag_chunks.duckdb`` from Part 2 must exist.
  • Ollama must be running (``ollama serve``).
  • Models pulled::

        ollama pull qwen3-embedding:0.6b
        ollama pull granite4:350m

Run with (from the workshop/ folder)::

    uv run --no-project --with duckdb --with ollama \\
        docling-part3-exercise.py \\
        --query "How does the transformer handle long-range dependencies?"

Optional flags::

    --db PATH   Path to DuckDB file (default: workshop/output/rag_chunks.duckdb)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import ollama

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "output" / "rag_chunks.duckdb"

# Must match the Ollama model names you pulled.
EMBED_MODEL = "qwen3-embedding:0.6b"   # 1024-dim embeddings
CHAT_MODEL = "granite4:350m"

# Reciprocal Rank Fusion constant (standard default).
RRF_K = 60


# ---------------------------------------------------------------------------
# Scaffolded: Database connection (provided – no TODO)
# ---------------------------------------------------------------------------

def _connect_db(db_path: Path) -> duckdb.DuckDBPyConnection:
    """Open the Part 2 database and load the VSS + FTS extensions."""
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Run Part 2 first to create rag_chunks.duckdb."
        )
    conn = duckdb.connect(str(db_path))
    conn.execute("INSTALL vss; LOAD vss;")
    conn.execute("SET hnsw_enable_experimental_persistence = true;")
    conn.execute("INSTALL fts; LOAD fts;")
    return conn


# ═══════════════════════════════════════════════════════════════════════════
# TODO 12 (★★★): Generate & Store Embeddings
# ═══════════════════════════════════════════════════════════════════════════
# The Part 2 table has no embedding column yet.  We need to:
#   a) ALTER TABLE to add a FLOAT[1024] column (if it doesn't exist).
#   b) Loop through chunks that have no embedding, call ollama.embed(),
#      and UPDATE each row.
#
# The schema check and NULL-embedding query are provided.  Your task:
# fill in the embedding loop.
# ───────────────────────────────────────────────────────────────────────────

def _add_embeddings(conn: duckdb.DuckDBPyConnection) -> None:
    # --- schema guard (idempotent) ---
    try:
        conn.execute("SELECT embedding FROM rag_chunks LIMIT 1")
    except duckdb.BinderException:
        conn.execute(
            "ALTER TABLE rag_chunks ADD COLUMN embedding FLOAT[1024]"
        )

    rows = conn.execute(
        "SELECT chunk_id, text FROM rag_chunks WHERE embedding IS NULL"
    ).fetchall()

    if not rows:
        print("✅ All chunks already have embeddings.")
        return

    print(f"🧠 Generating embeddings for {len(rows)} chunks …")

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 12: Loop through `rows` and store embeddings.          │
    # │                                                              │
    # │  Each row is (chunk_id, text).  For every row:               │
    # │                                                              │
    # │  1. Call ollama.embed(model=EMBED_MODEL, input=text)         │
    # │     → the result dict has an "embeddings" list.              │
    # │  2. Grab the first (and only) vector:                        │
    # │         vec = resp["embeddings"][0]                          │
    # │  3. UPDATE the row:                                          │
    # │     conn.execute(                                            │
    # │         "UPDATE rag_chunks SET embedding = ? "               │
    # │         "WHERE chunk_id = ?",                                │
    # │         [vec, chunk_id],                                     │
    # │     )                                                        │
    # │                                                              │
    # │  Hint: print(".", end="", flush=True) for a progress dot.    │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 12: embedding loop")

    print(f"\n✅ Embedded {len(rows)} chunks.")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 13 (★★): Create Search Indexes
# ═══════════════════════════════════════════════════════════════════════════
# Two indexes are needed – one for vector search, one for BM25.
# ───────────────────────────────────────────────────────────────────────────

def _create_indexes(conn: duckdb.DuckDBPyConnection) -> None:
    print("⚡ Creating indexes …")

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 13: Create both indexes.                               │
    # │                                                              │
    # │  A) HNSW vector index (recall Day 1):                        │
    # │     CREATE INDEX IF NOT EXISTS idx_vec                       │
    # │         ON rag_chunks USING HNSW (embedding)                 │
    # │         WITH (metric = 'cosine');                             │
    # │                                                              │
    # │  B) Full-Text Search index (new!):                           │
    # │     PRAGMA create_fts_index(                                 │
    # │         'rag_chunks', 'chunk_id', 'text', overwrite=1        │
    # │     );                                                       │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 13: create indexes")

    print("✅ Indexes ready.")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 14 (★★): Vector Search
# ═══════════════════════════════════════════════════════════════════════════
# Embed the query, then find the closest chunks by cosine similarity.
# ───────────────────────────────────────────────────────────────────────────

def _search_vector(
    conn: duckdb.DuckDBPyConnection,
    query_vec: list[float],
    limit: int = 10,
) -> list[tuple[int, float]]:
    """Return [(chunk_id, cosine_score), …] sorted by score descending."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 14: Execute a vector-similarity query.                 │
    # │                                                              │
    # │  Recall Day 1's search_vector():                             │
    # │                                                              │
    # │  SELECT chunk_id,                                            │
    # │         array_cosine_similarity(                              │
    # │             embedding, ?::FLOAT[1024]                        │
    # │         ) AS score                                           │
    # │  FROM rag_chunks                                             │
    # │  ORDER BY score DESC                                         │
    # │  LIMIT ?                                                     │
    # │                                                              │
    # │  Pass [query_vec, limit] as parameters.                      │
    # │  Return conn.execute(…).fetchall()                           │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 14: vector search query")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 15 (★★): BM25 Search
# ═══════════════════════════════════════════════════════════════════════════
# Use DuckDB's FTS extension to score chunks by keyword relevance.
# ───────────────────────────────────────────────────────────────────────────

def _search_bm25(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    limit: int = 10,
) -> list[tuple[int, float]]:
    """Return [(chunk_id, bm25_score), …] sorted by score descending."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 15: Execute a BM25 full-text search query.             │
    # │                                                              │
    # │  DuckDB FTS creates a macro under the schema                 │
    # │  fts_main_rag_chunks.  Use it like this:                     │
    # │                                                              │
    # │  SELECT chunk_id, score                                      │
    # │  FROM (                                                      │
    # │      SELECT *, fts_main_rag_chunks.match_bm25(               │
    # │          chunk_id, ?                                         │
    # │      ) AS score                                              │
    # │      FROM rag_chunks                                         │
    # │  )                                                           │
    # │  WHERE score IS NOT NULL                                     │
    # │  ORDER BY score DESC                                         │
    # │  LIMIT ?                                                     │
    # │                                                              │
    # │  Pass [query, limit] as parameters.                          │
    # │  Return conn.execute(…).fetchall()                           │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 15: BM25 search query")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 16 (★★★): Reciprocal Rank Fusion (RRF)
# ═══════════════════════════════════════════════════════════════════════════
# Combine the two ranked lists into one using the RRF formula:
#     score(d) = Σ  1 / (RRF_K + rank_i)
# where rank_i is the 1-based position in each list.
# ───────────────────────────────────────────────────────────────────────────

def _hybrid_search(
    conn: duckdb.DuckDBPyConnection, query: str, top_k: int = 5,
) -> list[dict]:
    """Run vector + BM25 search, fuse with RRF, return top_k results."""
    print(f"\n🔍 Searching: '{query}'")

    # Embed the query once (reused by vector search)
    query_vec = ollama.embed(model=EMBED_MODEL, input=query)["embeddings"][0]

    # Retrieve more candidates than top_k so RRF has room to re-rank.
    vec_results = _search_vector(conn, query_vec, limit=top_k * 2)
    bm25_results = _search_bm25(conn, query, limit=top_k * 2)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 16: Implement RRF.                                     │
    # │                                                              │
    # │  fused_scores: dict[int, float] = {}                         │
    # │                                                              │
    # │  For each ranked list (vec_results, bm25_results):           │
    # │    for i, (chunk_id, _score) in enumerate(results):          │
    # │        rank = i + 1                                          │
    # │        fused_scores[chunk_id] = (                            │
    # │            fused_scores.get(chunk_id, 0.0)                   │
    # │            + 1.0 / (RRF_K + rank)                            │
    # │        )                                                     │
    # │                                                              │
    # │  Then sort by fused score descending and take top_k IDs.     │
    # │  Fetch their text from the DB:                               │
    # │    conn.execute(                                             │
    # │        "SELECT chunk_id, text FROM rag_chunks "              │
    # │        "WHERE chunk_id = ?", [cid]                           │
    # │    ).fetchone()                                              │
    # │                                                              │
    # │  Return a list of dicts:                                     │
    # │    [{"chunk_id": …, "text": …, "rrf_score": …}, …]          │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 16: RRF fusion")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 17 (★): Generate a RAG Answer
# ═══════════════════════════════════════════════════════════════════════════
# The final step: feed the top chunks to the LLM and print the answer.
# ───────────────────────────────────────────────────────────────────────────

def _generate_answer(query: str, chunks: list[dict]) -> None:
    print("\n🤖 Generating answer …")

    # Build context from retrieved chunks
    context = "\n\n---\n\n".join(c["text"] for c in chunks)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 17: Call the LLM (recall Day 1's generate_response).   │
    # │                                                              │
    # │  1. Build a prompt string that includes `context` and        │
    # │     `query`.  For example:                                   │
    # │     "Based on the following context, answer the question.\n" │
    # │     f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"   │
    # │                                                              │
    # │  2. Call ollama.chat:                                        │
    # │     resp = ollama.chat(                                      │
    # │         model=CHAT_MODEL,                                    │
    # │         messages=[{"role": "user", "content": prompt}],      │
    # │     )                                                        │
    # │                                                              │
    # │  3. Print resp["message"]["content"]                         │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 17: generate RAG answer")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Part 3: Hybrid Search & RAG with DuckDB + Ollama."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the DuckDB file from Part 2.",
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Question to search for and answer.",
    )
    args = parser.parse_args()

    try:
        # 1. Connect & load extensions
        conn = _connect_db(args.db)

        # 2. Enrich: add embeddings to existing chunks
        _add_embeddings(conn)

        # 3. Index: create HNSW + FTS indexes
        _create_indexes(conn)

        # 4. Search: hybrid BM25 + vector → RRF fusion
        results = _hybrid_search(conn, args.query)

        print("\n--- Top Retrieved Chunks ---")
        for r in results:
            score = r["rrf_score"]
            snippet = r["text"][:120].replace("\n", " ")
            print(f"  [{score:.4f}] {snippet} …")

        # 5. Answer: feed context to LLM
        _generate_answer(args.query, results)

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

