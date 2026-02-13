#!/usr/bin/env python3
"""🔴 Path C: Self-RAG — ANSWER KEY

Complete implementation of Generate → Reflect → Improve loop.

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_example_answer/path_c_self_rag_answer.py \
        --query "How does attention work in transformers?" --max-rounds 3
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
    _connect_db, _hybrid_search,
    _add_embeddings, _create_indexes,
)
from openai import OpenAI

# ── Remote GPU Models ────────────────────────────────────────────────────────
chat_client = OpenAI(
    base_url="https://dev-8--vllm-qwen3-vl-8b-serve.modal.run/v1",
    api_key="not-needed",
)
CHAT_MODEL = "qwen3-vl-8b"

DEFAULT_DB = Path(__file__).resolve().parent.parent / "docling-exercise-example-answers" / "output" / "rag_chunks.duckdb"
MAX_ROUNDS = 3


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 ✅: generate_draft()
# ═══════════════════════════════════════════════════════════════════════════

def generate_draft(query: str, chunks: list[dict],
                   previous_answer: str = "") -> str:
    """Generate an answer draft from context. Optionally improve a previous answer."""
    context = "\n\n---\n\n".join(c["text"] for c in chunks)

    if not previous_answer:
        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\nAnswer:"
        )
    else:
        prompt = (
            f"Improve this answer:\n{previous_answer}\n\n"
            f"Using this additional context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Provide an improved, more complete answer:"
        )

    resp = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 ✅: reflect_on_answer()
# ═══════════════════════════════════════════════════════════════════════════

def reflect_on_answer(query: str, answer: str) -> tuple[bool, str]:
    """LLM reflects on its own answer. Returns (is_sufficient, critique)."""
    prompt = (
        f"Question: {query}\n"
        f"Answer: {answer}\n\n"
        f"Evaluate this answer:\n"
        f"1. Does it fully address the question?\n"
        f"2. Are there any gaps or inaccuracies?\n"
        f"3. What additional information would improve it?\n\n"
        f"Start your response with SUFFICIENT or INSUFFICIENT, then explain why."
    )

    resp = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    reflection = resp.choices[0].message.content
    is_sufficient = reflection.strip().upper().startswith("SUFFICIENT")
    return is_sufficient, reflection



# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 ✅: self_rag()
# ═══════════════════════════════════════════════════════════════════════════

def self_rag(conn, query: str, max_rounds: int = 3,
             top_k: int = 5) -> str:
    """Self-RAG loop: generate → reflect → improve until sufficient."""
    t0 = time.time()
    print(f"\n🧠 [Self-RAG] Starting with query: '{query}'")

    # Step A: Initial retrieval
    chunks = _hybrid_search(conn, query, top_k=top_k)
    all_chunks = list(chunks)
    print(f"   📦 Initial retrieval: {len(chunks)} chunks:")
    for i, c in enumerate(chunks):
        print(f"\n   ── Chunk {i+1} | chunk_id={c['chunk_id']} ──")
        print(f"   {c['text']}")

    previous_answer = ""

    # Step B: Loop
    for round_num in range(1, max_rounds + 1):
        print(f"\n{'='*60}")
        print(f"📝 Round {round_num}/{max_rounds}")
        print(f"{'='*60}")

        # Generate
        answer = generate_draft(query, all_chunks, previous_answer)
        print(f"   📝 Draft ({len(answer)} chars):")
        print(f"   ┌{'─'*70}")
        for line in answer.splitlines():
            print(f"   │ {line}")
        print(f"   └{'─'*70}")

        # Reflect
        sufficient, critique = reflect_on_answer(query, answer)
        status = "✅ SUFFICIENT" if sufficient else "❌ INSUFFICIENT"
        print(f"   🪞 Reflection: {status}")
        print(f"   ┌{'─'*70}")
        for line in critique.splitlines():
            print(f"   │ {line}")
        print(f"   └{'─'*70}")

        if sufficient:
            elapsed = time.time() - t0
            print(f"\n   🎉 Answer deemed sufficient after {round_num} round(s)!")
            print(f"   ⏱️  Total time: {elapsed:.1f}s")
            return answer

        if round_num < max_rounds:
            # Retrieve more context for next round
            print(f"   🔄 Retrieving additional context for improvement...")
            new_chunks = _hybrid_search(conn, query, top_k=top_k)
            all_chunks.extend(new_chunks)
            previous_answer = answer
            print(f"   📦 Total chunks now: {len(all_chunks)}")

    # After all rounds, return the last answer
    elapsed = time.time() - t0
    print(f"\n   ⚠️  Max rounds reached. Returning best answer.")
    print(f"   ⏱️  Total time: {elapsed:.1f}s")
    return answer


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 ✅: CLI main()
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🔴 Path C: Self-RAG — Generate → Reflect → Improve"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--max-rounds", type=int, default=MAX_ROUNDS)
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        answer = self_rag(conn, args.query, args.max_rounds)

        print(f"\n{'='*60}")
        print(f"📝 Final Answer:")
        print(f"{'='*60}")
        print(answer)

        conn.close()
        return 0
    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())