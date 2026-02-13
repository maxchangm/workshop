#!/usr/bin/env python3
"""Workshop Part 2 – ANSWER KEY: DuckDB Persistence & Querying.

This is the completed version of docling-part2-exercise.py with all TODOs
(8–11) filled in.  It loads chunks.json from Part 1, stores them in a
persistent DuckDB database, and lets you query them with SQL.

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb workshop--example-answers/docling_part2_answer.py \
        -i output/20260212_125354/chunks/chunks.json
        
    uv run --no-project --with duckdb workshop--example-answers/docling_part2_answer.py \
        -i output/<TIME_STAMP>/chunks/chunks.json

Optional flags:
    --db   PATH   DuckDB file path (default: workshop/output/rag_chunks.duckdb)
    --search TEXT  Search chunks by keyword after insertion
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "workshop" / "output" / "rag_chunks.duckdb"


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════


def _load_chunks(json_path: Path) -> list[dict]:
    """Read the chunks.json produced by Part 1 and return a list of dicts."""
    resolved = json_path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Chunks file not found: {resolved}")
    with resolved.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of chunk objects.")
    return data


# ═══════════════════════════════════════════════════════════════════════════
# TODO 8 (★): Connect to a Persistent DuckDB Database  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════


def _connect_db(db_path: Path) -> duckdb.DuckDBPyConnection:
    # In Day 1 we used duckdb.connect() for an in-memory database.
    # Passing a file path string makes it persistent on disk.
    return duckdb.connect(str(db_path))


# ═══════════════════════════════════════════════════════════════════════════
# TODO 9 (★★): Create the Chunks Table  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════


def _create_table(conn: duckdb.DuckDBPyConnection) -> None:
    # Same conn.execute("CREATE TABLE ...") pattern as Day 1, but with our
    # own schema.  INTEGER[] is a native DuckDB array type that maps directly
    # to Python list[int] – no JSON serialisation needed.
    # DROP first so re-runs replace data instead of appending duplicates.
    conn.execute("DROP TABLE IF EXISTS rag_chunks")
    conn.execute("""
        CREATE TABLE rag_chunks (
            chunk_id       INTEGER,
            document_name  VARCHAR,
            section_title  VARCHAR,
            page_numbers   INTEGER[],
            text           VARCHAR,
            created_at     TIMESTAMP DEFAULT current_timestamp
        )
    """)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 10 (★★): Insert Chunks into the Table  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════


def _insert_chunks(conn: duckdb.DuckDBPyConnection, chunks: list[dict]) -> int:
    # Same for-loop + conn.execute("INSERT INTO … VALUES (?, ?, …)") pattern
    # as Day 1.  DuckDB automatically converts Python list[int] → INTEGER[].
    for i, chunk in enumerate(chunks):
        conn.execute(
            """INSERT INTO rag_chunks
                   (chunk_id, document_name, section_title, page_numbers, text)
               VALUES (?, ?, ?, ?, ?)""",
            [
                i,
                chunk["document_name"],
                chunk["section_title"],
                chunk["page_numbers"],
                chunk["text"],
            ],
        )
    return len(chunks)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 11 (★★): Search Chunks by Keyword  ✅ ANSWER
# ═══════════════════════════════════════════════════════════════════════════


def _search_chunks(conn: duckdb.DuckDBPyConnection, search_term: str) -> None:
    print(f"\n🔍 Top 5 search results for '{search_term}':")

    # ILIKE is case-insensitive LIKE.  The '%' || ? || '%' pattern does a
    # parameterised contains-search.  conn.sql() returns a Relation object
    # whose .show() prints a formatted ASCII table (in Day 1 we used
    # conn.execute().fetchall() – .show() is a handy shortcut for display).
    conn.sql("""
        SELECT
            section_title,
            page_numbers,
            substr(text, 1, 200) AS snippet
        FROM rag_chunks
        WHERE text ILIKE '%' || $1 || '%'
        LIMIT 5
    """, params=[search_term]).show()


# ═══════════════════════════════════════════════════════════════════════════
# Summary & CLI
# ═══════════════════════════════════════════════════════════════════════════


def _show_summary(conn: duckdb.DuckDBPyConnection) -> None:
    """Display summary statistics about the stored chunks."""
    total = conn.execute("SELECT count(*) FROM rag_chunks").fetchone()[0]
    print(f"\n📊 Database summary: {total} chunks stored\n")

    print("Chunks per section:")
    conn.sql("""
        SELECT
            coalesce(section_title, '(no section)') AS section,
            count(*) AS chunks
        FROM rag_chunks
        GROUP BY section_title
        ORDER BY chunks DESC
    """).show(max_rows=50)

    print("Chunks per document:")
    conn.sql("""
        SELECT document_name, count(*) AS chunks
        FROM rag_chunks
        GROUP BY document_name
        ORDER BY chunks DESC
    """).show()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Part 2: Load chunks.json into DuckDB and query them."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to chunks.json from Part 1.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"DuckDB file path (default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Optional: search chunks containing this keyword.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        # Step 1: Load chunks from Part 1 output
        chunks = _load_chunks(args.input)
        print(f"Loaded {len(chunks)} chunks from {args.input}")

        # Step 2: Connect to DuckDB
        args.db.parent.mkdir(parents=True, exist_ok=True)
        conn = _connect_db(args.db)

        # Step 3: Create table and insert data
        _create_table(conn)
        inserted = _insert_chunks(conn, chunks)
        print(f"Inserted {inserted} chunks into {args.db}")

        # Step 4: Show summary statistics
        _show_summary(conn)

        # Step 5: Optional keyword search
        if args.search:
            _search_chunks(conn, args.search)

        conn.close()

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"\n💡 Tip: explore further with the DuckDB CLI:")
    print(f"   duckdb {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
