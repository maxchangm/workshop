#!/usr/bin/env python3
"""Workshop Part 2: DuckDB Persistence & Querying.

After completing Part 1 (docling-exercise.py), you have a chunks.json file
containing document chunks with text, page numbers, section titles, and
document names.  In Part 2 you will persist those chunks into a DuckDB
database and query them using SQL.

There are 4 TODOs (numbered 8–11, continuing from Part 1).

Useful references:
  • DuckDB Python docs: https://duckdb.org/docs/stable/clients/python/overview
  • DuckDB data types:  https://duckdb.org/docs/sql/data_types/overview
  • DuckDB JSON import: https://duckdb.org/docs/data/json/overview

Run with:
    uv run --no-project --with duckdb workshop/docling-part2-exercise.py \\
        -i workshop/output/<TIMESTAMP>/chunks/chunks.json

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

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "output" / "rag_chunks.duckdb"


# ═══════════════════════════════════════════════════════════════════════════
# Helper (provided – no changes needed)
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
# TODO 8 (★): Connect to a Persistent DuckDB Database
# ═══════════════════════════════════════════════════════════════════════════
# In Day 1 you used duckdb.connect() which creates an *in-memory* database.
# Your task: return a connection to a *persistent* database at db_path so
# the data survives after the script exits.
#
# Hint: duckdb.connect() accepts a file path string.
# ───────────────────────────────────────────────────────────────────────────


def _connect_db(db_path: Path) -> duckdb.DuckDBPyConnection:
    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 8: Return a persistent DuckDB connection.              │
    # │                                                              │
    # │  In Day 1 we used:  conn = duckdb.connect()   (in-memory)   │
    # │  How do you make it persist to a file instead?               │
    # │  Hint: pass the db_path (as a string) to duckdb.connect().  │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 8: return a duckdb connection")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 9 (★★): Create the Chunks Table
# ═══════════════════════════════════════════════════════════════════════════
# Define a SQL table to store the chunk data.  Pay special attention to
# page_numbers – it's a list of integers.  DuckDB supports native array
# types (e.g. INTEGER[]) which map directly to Python lists!
#
# Use CREATE TABLE IF NOT EXISTS so the script is idempotent.
# ───────────────────────────────────────────────────────────────────────────


def _create_table(conn: duckdb.DuckDBPyConnection) -> None:
    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 9: Write a CREATE TABLE IF NOT EXISTS statement.       │
    # │                                                              │
    # │  Table name: rag_chunks                                      │
    # │  Columns:                                                    │
    # │    chunk_id       INTEGER                                    │
    # │    document_name  VARCHAR                                    │
    # │    section_title  VARCHAR                                    │
    # │    page_numbers   INTEGER[]   ← native array type!           │
    # │    text           VARCHAR                                    │
    # │    created_at     TIMESTAMP   (DEFAULT current_timestamp)    │
    # │                                                              │
    # │  In Day 1 we used:                                           │
    # │    conn.execute("CREATE TABLE documents (...)")              │
    # │  Do the same here with your own schema.                      │
    # └──────────────────────────────────────────────────────────────┘
    pass  # ← replace with your CREATE TABLE statement


# ═══════════════════════════════════════════════════════════════════════════
# TODO 10 (★★): Insert Chunks into the Table
# ═══════════════════════════════════════════════════════════════════════════
# Now that the table exists, insert the chunk data.  Use the same
# conn.execute("INSERT INTO ... VALUES (?, ?, ...)", [params]) pattern
# from Day 1 – DuckDB handles type conversion automatically
# (Python list[int] → INTEGER[]).
# ───────────────────────────────────────────────────────────────────────────


def _insert_chunks(conn: duckdb.DuckDBPyConnection, chunks: list[dict]) -> int:
    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 10: Loop over chunks and insert each one.              │
    # │                                                              │
    # │  Same pattern as Day 1:                                      │
    # │    for i, chunk in enumerate(chunks):                        │
    # │        conn.execute(                                         │
    # │            "INSERT INTO ... VALUES (?, ?, ...)",             │
    # │            [i, chunk["..."], ...]                            │
    # │        )                                                     │
    # │                                                              │
    # │  Map JSON keys → columns:                                    │
    # │    enumerate index  → chunk_id                               │
    # │    "document_name"  → document_name                          │
    # │    "section_title"  → section_title                          │
    # │    "page_numbers"   → page_numbers                           │
    # │    "text"           → text                                   │
    # │  (skip created_at – it uses the DEFAULT)                     │
    # └──────────────────────────────────────────────────────────────┘
    return 0  # ← replace: return the number of inserted rows


# ═══════════════════════════════════════════════════════════════════════════
# TODO 11 (★★): Search Chunks by Keyword
# ═══════════════════════════════════════════════════════════════════════════
# DuckDB supports ILIKE for case-insensitive pattern matching.
# Your task: query the rag_chunks table for rows whose text contains the
# given search term, and display the results.
# ───────────────────────────────────────────────────────────────────────────


def _search_chunks(conn: duckdb.DuckDBPyConnection, search_term: str) -> None:
    print(f"\n🔍 Top 5 search results for '{search_term}':")

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 11: Write a SELECT query that searches chunk text.     │
    # │                                                              │
    # │  1. SELECT section_title, page_numbers, and a snippet        │
    # │     of the text (use substr(text, 1, 200)).                  │
    # │  2. Filter with: WHERE text ILIKE '%' || $1 || '%'           │
    # │     (this is parameterized case-insensitive search).         │
    # │  3. LIMIT to 5 results.                                     │
    # │  4. Call .show() on the result to print a formatted table.   │
    # │     (In Day 1 you used .fetchall() — .show() is a shortcut  │
    # │      that prints a nicely formatted ASCII table.)            │
    # │                                                              │
    # │  Note: use conn.sql() instead of conn.execute() here —      │
    # │  conn.sql() returns a Relation that supports .show().        │
    # │  For params use $1 placeholder:                              │
    # │    conn.sql("SQL with $1", params=[search_term]).show()      │
    # └──────────────────────────────────────────────────────────────┘
    pass  # ← replace with your SELECT query


# ═══════════════════════════════════════════════════════════════════════════
# Summary & CLI (provided – no changes needed)
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
