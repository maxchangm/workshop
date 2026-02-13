#!/usr/bin/env python3
"""Workshop Part 3 – ANSWER KEY: Hybrid Search & RAG with DuckDB + Ollama.

This is the completed version of docling-part3-exercise.py with all TODOs
(12–17) filled in.  It enriches Part 2's DuckDB with vector embeddings,
builds HNSW + FTS indexes, performs hybrid search (BM25 + cosine vector)
via Reciprocal Rank Fusion, and generates a RAG answer with Ollama.

Run with (from the workshop/ folder)::

    uv run --no-project --with duckdb --with ollama \
        workshop--example-answers/docling_part3_answer.py \
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
# Answer scripts live in workshop--example-answers/, but the DB is in workshop/output/.
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "workshop" / "output" / "rag_chunks.duckdb"

# Must match the Ollama model names you pulled.
EMBED_MODEL = "qwen3-embedding:0.6b"   # 1024-dim embeddings
CHAT_MODEL = "granite4:350m"

# Reciprocal Rank Fusion constant (standard default).
RRF_K = 60


# ---------------------------------------------------------------------------
# Database connection (same as exercise – no TODO)
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
# TODO 12 (★★★): Generate & Store Embeddings  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════

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

    # Loop through each chunk, call ollama.embed(), and UPDATE the row.
    # Same pattern as Day 1's embedding loop, but using UPDATE instead of
    # INSERT because the rows already exist from Part 2.
    for chunk_id, text in rows:
        resp = ollama.embed(model=EMBED_MODEL, input=text)
        vec = resp["embeddings"][0]
        conn.execute(
            "UPDATE rag_chunks SET embedding = ? WHERE chunk_id = ?",
            [vec, chunk_id],
        )
        print(".", end="", flush=True)

    print(f"\n✅ Embedded {len(rows)} chunks.")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 13 (★★): Create Search Indexes  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════

def _create_indexes(conn: duckdb.DuckDBPyConnection) -> None:
    print("⚡ Creating indexes …")

    # A) HNSW vector index – same as Day 1.
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_vec
            ON rag_chunks USING HNSW (embedding)
            WITH (metric = 'cosine')
    """)

    # B) Full-Text Search index – new!  DuckDB's FTS extension creates a
    #    schema called fts_main_rag_chunks with a match_bm25() macro.
    conn.execute(
        "PRAGMA create_fts_index('rag_chunks', 'chunk_id', 'text', overwrite=1)"
    )

    print("✅ Indexes ready.")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 14 (★★): Vector Search  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════

def _search_vector(
    conn: duckdb.DuckDBPyConnection,
    query_vec: list[float],
    limit: int = 10,
) -> list[tuple[int, float]]:
    """Return [(chunk_id, cosine_score), …] sorted by score descending."""
    # Same array_cosine_similarity() pattern as Day 1's search_vector().
    return conn.execute("""
        SELECT chunk_id,
               array_cosine_similarity(embedding, ?::FLOAT[1024]) AS score
        FROM rag_chunks
        ORDER BY score DESC
        LIMIT ?
    """, [query_vec, limit]).fetchall()


# ═══════════════════════════════════════════════════════════════════════════
# TODO 15 (★★): BM25 Search  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════

def _search_bm25(
    conn: duckdb.DuckDBPyConnection,
    query: str,
    limit: int = 10,
) -> list[tuple[int, float]]:
    """Return [(chunk_id, bm25_score), …] sorted by score descending."""
    # DuckDB FTS creates a macro fts_main_rag_chunks.match_bm25() that
    # scores each row.  Rows with no keyword match get NULL → filter them.
    return conn.execute("""
        SELECT chunk_id, score
        FROM (
            SELECT *, fts_main_rag_chunks.match_bm25(chunk_id, ?) AS score
            FROM rag_chunks
        )
        WHERE score IS NOT NULL
        ORDER BY score DESC
        LIMIT ?
    """, [query, limit]).fetchall()


# ═══════════════════════════════════════════════════════════════════════════
# TODO 16 (★★★): Reciprocal Rank Fusion (RRF)  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════

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

    # RRF: for each ranked list, accumulate 1/(k + rank) per chunk_id.
    # Chunks that appear in BOTH lists get a higher fused score.
    fused_scores: dict[int, float] = {}

    for i, (chunk_id, _score) in enumerate(vec_results):
        rank = i + 1
        fused_scores[chunk_id] = (
            fused_scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        )

    for i, (chunk_id, _score) in enumerate(bm25_results):
        rank = i + 1
        fused_scores[chunk_id] = (
            fused_scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        )

    # Sort by fused score descending, take top_k
    sorted_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[
        :top_k
    ]

    # Fetch the actual text for the top chunks
    results = []
    for chunk_id, score in sorted_ids:
        row = conn.execute(
            "SELECT chunk_id, text FROM rag_chunks WHERE chunk_id = ?",
            [chunk_id],
        ).fetchone()
        results.append({"chunk_id": row[0], "text": row[1], "rrf_score": score})

    return results


# ═══════════════════════════════════════════════════════════════════════════
# TODO 17 (★): Generate a RAG Answer  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════

def _generate_answer(query: str, chunks: list[dict]) -> None:
    print("\n🤖 Generating answer …")

    # Build context from retrieved chunks
    context = "\n\n---\n\n".join(c["text"] for c in chunks)

    # Same prompt pattern as Day 1's generate_response().
    prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""

    resp = ollama.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    print(resp["message"]["content"])


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Part 3 ANSWER KEY: Hybrid Search & RAG with DuckDB + Ollama."
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

    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
