#!/usr/bin/env python3
"""🔴 Path C: Self-RAG — Hardest · ~50 new lines

Build a self-reflective generation loop: Generate → Reflect → Improve.

You will:
  1. Build generate_draft()      — generate an initial answer from retrieved context
  2. Build reflect_on_answer()   — LLM critiques its own answer for gaps/errors
  3. Build self_rag()            — the full generate → reflect → improve loop
  4. Wire up CLI                 — --query and --max-rounds flags

═══════════════════════════════════════════════════════════════════════════════
KEY INSIGHT: SELF-REFLECTION
═══════════════════════════════════════════════════════════════════════════════
Standard RAG: retrieve → generate → done (hope for the best!)
Self-RAG:     retrieve → generate → REFLECT → improve → repeat

The LLM checks its OWN answer:
  "Is this answer complete? Does it address the question? Any gaps?"
If the reflection finds issues, we retrieve MORE context and try again.

═══════════════════════════════════════════════════════════════════════════════
REUSING YOUR PART 1-3 CODE
═══════════════════════════════════════════════════════════════════════════════
  • _hybrid_search(conn, query, top_k)  — your RRF fusion search (Part 3)

NEW TODAY (Remote GPU):
  • chat_client.chat.completions.create()  — remote 8B LLM for generation + reflection

Run with (from the workshop/ folder):
    uv run --no-project --with duckdb --with ollama --with openai --with requests \
        advanced_rag_exercise/path_c_self_rag.py \
        --query "How does attention work in transformers?" --max-rounds 3

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
    _connect_db, _hybrid_search,
    _add_embeddings, _create_indexes,
)
from openai import OpenAI

# ── Remote GPU Models (provided — no changes needed) ────────────────────────
chat_client = OpenAI(
    base_url="https://dev-8--vllm-qwen3-vl-8b-serve.modal.run/v1",
    api_key="not-needed",
)
CHAT_MODEL = "qwen3-vl-8b"

# ── Constants ───────────────────────────────────────────────────────────────
DEFAULT_DB = Path(__file__).resolve().parent.parent / "docling-exercise-example-answers" / "output" / "rag_chunks.duckdb"
MAX_ROUNDS = 3  # Maximum reflection rounds


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 (★★): Build generate_draft()  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# Generate an initial answer from retrieved context using the remote LLM.
# This is similar to _generate_answer() from Part 3, but returns the text
# instead of printing it, so we can feed it to the reflection step.
# ───────────────────────────────────────────────────────────────────────────

def generate_draft(query: str, chunks: list[dict],
                   previous_answer: str = "") -> str:
    """Generate an answer draft from context. Optionally improve a previous answer."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 1: Generate a draft answer using the remote LLM.       │
    # │                                                              │
    # │  Step A: Build context from chunks                           │
    # │    - context = "\n\n---\n\n".join(c["text"] for c in chunks) │
    # │                                                              │
    # │  Step B: Build the prompt                                    │
    # │    - If previous_answer is empty (first draft):              │
    # │      "Based on the context, answer: {query}\n\n              │
    # │       Context:\n{context}"                                   │
    # │    - If previous_answer exists (improvement round):          │
    # │      "Improve this answer: {previous_answer}\n\n             │
    # │       Additional context:\n{context}\n\n                     │
    # │       Question: {query}"                                     │
    # │                                                              │
    # │  Step C: Call chat_client.chat.completions.create()          │
    # │    - Return resp.choices[0].message.content                  │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 1: implement generate_draft()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 (★★★): Build reflect_on_answer()  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# The LLM critiques its OWN answer. This is the key Self-RAG innovation.
# Returns a tuple: (is_sufficient: bool, critique: str)
# ───────────────────────────────────────────────────────────────────────────

def reflect_on_answer(query: str, answer: str) -> tuple[bool, str]:
    """LLM reflects on its own answer. Returns (is_sufficient, critique)."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 2: Implement self-reflection.                          │
    # │                                                              │
    # │  Step A: Build a reflection prompt                           │
    # │    - "Question: {query}\nAnswer: {answer}\n\n                │
    # │       Evaluate this answer:                                  │
    # │       1. Does it fully address the question?                 │
    # │       2. Are there any gaps or inaccuracies?                 │
    # │       3. What additional information would improve it?       │
    # │                                                              │
    # │       Start with SUFFICIENT or INSUFFICIENT,                 │
    # │       then explain why."                                     │
    # │                                                              │
    # │  Step B: Call chat_client.chat.completions.create()          │
    # │    - Extract reflection text                                 │
    # │                                                              │
    # │  Step C: Parse the response                                  │
    # │    - is_sufficient = reflection starts with "SUFFICIENT"     │
    # │    - Return (is_sufficient, reflection)                      │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 2: implement reflect_on_answer()")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 (★★★★): Build self_rag()  — ~20 lines
# ═══════════════════════════════════════════════════════════════════════════
# The Self-RAG loop: generate → reflect → if insufficient, retrieve more → improve.
#
# Loop logic:
#   1. Retrieve initial context
#   2. Generate draft answer
#   3. Reflect on the answer
#   4. If SUFFICIENT → done!
#   5. If INSUFFICIENT → retrieve more context, generate improved answer
#   6. Repeat up to MAX_ROUNDS
# ───────────────────────────────────────────────────────────────────────────

def self_rag(conn, query: str, max_rounds: int = 3,
             top_k: int = 5) -> str:
    """Self-RAG loop: generate → reflect → improve until sufficient."""

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 3: Implement the Self-RAG loop.                        │
    # │                                                              │
    # │  Step A: Initial retrieval                                   │
    # │    - chunks = _hybrid_search(conn, query, top_k=top_k)       │
    # │    - all_chunks = list(chunks)  # accumulate across rounds   │
    # │                                                              │
    # │  Step B: Loop for max_rounds                                 │
    # │    for round_num in range(1, max_rounds + 1):                │
    # │                                                              │
    # │    - Generate: answer = generate_draft(query, all_chunks,    │
    # │                                        previous_answer)      │
    # │      Print: "📝 Round {round_num} draft: {answer[:100]}..."  │
    # │                                                              │
    # │    - Reflect: sufficient, critique = reflect_on_answer(      │
    # │                                        query, answer)        │
    # │      Print: "🪞 Reflection: {critique[:100]}..."             │
    # │                                                              │
    # │    - If sufficient: print "✅ Sufficient!" and return answer │
    # │                                                              │
    # │    - If not sufficient and not last round:                   │
    # │      Retrieve more: new = _hybrid_search(conn, query, top_k)│
    # │      all_chunks.extend(new)                                  │
    # │      previous_answer = answer                                │
    # │                                                              │
    # │  Step C: Return final answer after all rounds                │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 3: implement self_rag()")



# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 (★): Wire up CLI  — ~15 lines
# ═══════════════════════════════════════════════════════════════════════════
# Add --query and --max-rounds flags.
# ───────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="🔴 Path C: Self-RAG — Generate → Reflect → Improve"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--query", type=str, required=True)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 4: Add --max-rounds flag and wire up the pipeline.     │
    # │                                                              │
    # │  --max-rounds: type=int, default=3                           │
    # │    (maximum number of generate→reflect cycles)               │
    # │                                                              │
    # │  Then:                                                       │
    # │  - answer = self_rag(conn, query, max_rounds)                │
    # │  - Print the final answer                                    │
    # └──────────────────────────────────────────────────────────────┘
    args = parser.parse_args()

    try:
        conn = _connect_db(args.db)
        _add_embeddings(conn)
        _create_indexes(conn)

        # TODO 4: Call self_rag() and print the answer here
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