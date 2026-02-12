import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # 🔍 Day 1: Building a RAG Pipeline

    Welcome to the hands-on workshop! We'll build progressively better retrieval systems.

    **📋 Workshop Sections:**
    1. **☕ Mini Hands-on Part 1** — Keyword Search: Build & run your first RAG pipeline
    2. **☕ Mini Hands-on Part 2** — DeepEval: Add evaluation to your pipeline
    3. **☕ Morning Hands-on Part 3** — BM25: Upgrade your RAG pipeline
    4. **☀️ Afternoon Hands-on** — Vector Search: Semantic understanding
    5. **🏆 Scoreboard** — Compare all methods

    ---

    *Scroll down to work through each section. The instructor will guide you.*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---

    # ☕ Mini Hands-on Part 1: Keyword Search

    *Build & Run Your First RAG Pipeline*

    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    section_1_header = mo.accordion({
        "📖 Section 1: Keyword Search (The Baseline)": mo.md("""
    We start with the simplest possible retrieval: **counting word matches**.

    No neural networks. No embeddings. Just Python string operations.

    **What we'll build:**
    - A document corpus (15 facts)
    - A keyword search function
    - A query interface
    - Context builder for RAG
    - LLM generation with Ollama

    **Time:** ~20 minutes
        """)
    }, multiple=True)
    section_1_header
    return


@app.cell
def _():
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # ── Corpus configuration ─────────────────────────────────────────
    # Switch between "synthetic" and "s17" to change the entire notebook
    CORPUS_NAME = "synthetic"  # "synthetic" or "s17"

    if CORPUS_NAME == "s17":
        from corpus_s17 import documents, test_questions
        DEFAULT_QUERY = "What is the role of the DITSO?"
        EXAMPLE_QUERIES = """
    | Query | Keyword | BM25 | Vector | Why? |
    |-------|---------|------|--------|------|
    | `What is the role of the DITSO?` | ⚠️ Partial | ⚠️ Better | ✅ Correct | Vector understands role = responsibilities |
    | `What are the restrictions for cloud services?` | ⚠️ Partial | ⚠️ Better | ✅ Correct | Vector understands restrictions = policy |
    | `How should cryptographic keys be managed?` | ❌ Misses | ⚠️ Better | ✅ Correct | Vector understands managed = life cycle |
    """
    else:
        from corpus import documents, test_questions
        DEFAULT_QUERY = "What is ML?"
        EXAMPLE_QUERIES = """
    | Query | Keyword | BM25 | Vector | Why? |
    |-------|---------|------|--------|------|
    | `What is ML?` | ❌ Trap doc | ⚠️ Better | ✅ Correct | Vector understands ML = Machine Learning |
    | `How do automobiles work?` | ❌ Registration doc | ⚠️ Better | ✅ Correct | Vector understands automobiles = cars |
    | `How to fix code errors?` | ❌ Misses | ❌ Misses | ✅ Correct | Vector understands fix errors = debugging |
    """
    return (
        CORPUS_NAME,
        DEFAULT_QUERY,
        EXAMPLE_QUERIES,
        documents,
        test_questions,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Step 1: The Retrieval Function

    Our keyword search counts how many query words appear in each document.

    ```python
    score = sum(1 for word in query_words if word in doc.lower())
    ```

    This is intentionally simple - we will see its limitations soon!
    """)
    return


@app.cell
def _(documents):
    import re
    _strip = re.compile(r'[^a-z0-9]')

    def search_keyword(query: str, top_k: int = 3) -> list[tuple[int, str, int]]:
        """
        Simple keyword search: count matching words.

        Returns: List of (doc_id, doc_text, score) tuples
        """
        query_words = [_strip.sub('', w) for w in query.lower().split() if _strip.sub('', w)]

        scored_docs = []
        for doc_id, doc in enumerate(documents):
            doc_words = {_strip.sub('', w) for w in doc.lower().split()}
            # Count how many query words appear in the document
            score = sum(1 for word in query_words if word in doc_words)
            if score > 0:
                scored_docs.append((doc_id, doc, score))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[2], reverse=True)
        return scored_docs[:top_k]
    return (search_keyword,)


@app.cell
def _():
    return


@app.cell
def _(mo):
    mo.md("""
    ## Step 2: Query Interface
    """)
    return


@app.cell
def _(DEFAULT_QUERY, EXAMPLE_QUERIES, mo):
    # Wrap in a form so it only triggers on submit (not every keystroke)
    query_form = mo.ui.dictionary({
        "query": mo.ui.text(
            placeholder="Enter a question...",
            label="Enter your query:",
            value=DEFAULT_QUERY,
            full_width=True
        ),
        "top_k": mo.ui.slider(
            start=1, stop=5, value=3,
            label="Number of results (top_k):",
            show_value=True
        )
    }).form(submit_button_label="🔍 Search")

    _examples = mo.md(f"""
    **💡 Try these queries to see the difference between search methods:**

    {EXAMPLE_QUERIES}
    """)

    mo.vstack([query_form, _examples])
    return (query_form,)


@app.cell
def _(DEFAULT_QUERY, mo, query_form, search_keyword):
    import re as _re

    # Get values from the submitted form
    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY
    _top_k = query_form.value["top_k"] if query_form.value else 3

    # Run the search
    if _query:
        keyword_results = search_keyword(_query, _top_k)
    else:
        keyword_results = []

    def _highlight(text, query):
        """Highlight query words in text using <mark> tags."""
        words = set(query.lower().split())
        # Match whole words, case-insensitive
        def _replacer(m):
            return f"<mark>{m.group(0)}</mark>"
        for w in words:
            text = _re.sub(r'(?i)\b' + _re.escape(w) + r'\b', _replacer, text)
        return text

    # Build document display with highlighted query words
    docs_display = ""
    for doc_id, doc_text, score in keyword_results:
        _highlighted = _highlight(doc_text, _query)
        docs_display += f"\n\n**Document {doc_id}** (Score: {score})\n> {_highlighted}"

    mo.md(f"""
    ## Retrieved Documents (Keyword Search)

    Query: **"{_query}"**

    Found **{len(keyword_results)}** matching documents:
    {docs_display if keyword_results else "*No documents found. Try a different query.*"}
    """)
    return (keyword_results,)


@app.cell
def _(mo):
    mo.md("""
    ## Step 3: Build the Context (Augmentation)

    We combine the retrieved documents into a single context string.
    """)
    return


@app.cell
def _(DEFAULT_QUERY, keyword_results, mo, query_form):
    def build_context(results: list[tuple[int, str, int]]) -> str:
        """Combine retrieved documents into context for the LLM."""
        if not results:
            return "No relevant documents found."

        context_parts = []
        for doc_id, doc_text, score in results:
            context_parts.append(f"[Document {doc_id}]: {doc_text}")

        return "\n\n".join(context_parts)

    context = build_context(keyword_results)

    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY

    _prompt_preview = f"""Based on the following context, answer the question.

    Context:
    {context}

    Question: {_query}

    Answer:"""

    mo.md(f"""
    **Prompt being sent to the LLM:**

    ```
    {_prompt_preview}
    ```
    """)
    return (context,)


@app.cell
def _():
    import ollama
    return (ollama,)


@app.cell
def _(DEFAULT_QUERY, context, mo, ollama, query_form):
    def generate_response(query: str, ctx: str) -> str:
        """Generate a response using Ollama's granite4:350m model."""
        prompt = f"""Based on the following context, answer the question.

    Context:
    {ctx}

    Question: {query}

    Answer:"""

        response = ollama.chat(
            model="granite4:350m",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

    # Get query from the submitted form
    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY

    # Generate response for current query
    if _query and context != "No relevant documents found.":
        llm_response = generate_response(_query, context)
    else:
        llm_response = "No context available to generate response."

    mo.md(f"""
    ## Step 4: Generate Response (The "G" in RAG)

    Using **granite4:350m** via Ollama to generate an answer:

    ---

    **Response:**

    {llm_response}
    """)
    return (generate_response,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---

    # ☕ Mini Hands-on Part 2: DeepEval Evaluation

    *Add Evaluation to Your Pipeline*

    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    section_2_header = mo.accordion({
        "📖 Section 2: DeepEval Integration (Measuring Our Baseline)": mo.md("""
    Now that we've built a complete RAG pipeline, let's **measure how good it is**.

    We'll use **DeepEval** - an LLM-as-Judge framework that evaluates RAG quality.

    **What we'll build:**
    - Test cases for evaluation
    - DeepEval metrics: Answer Relevancy, Context Precision

    **Time:** ~30 minutes
        """)
    }, multiple=True)
    section_2_header
    return


@app.cell
def _(mo):
    mo.md("""
    ## Step 1: Evaluate with DeepEval

    We'll create test cases and measure two key metrics for **retrieval quality**:

    | Metric | What it measures |
    |--------|-----------------|
    | **Context Precision** | Are the retrieved docs relevant? (Primary focus!) |
    | **Answer Relevancy** | Does the answer address the question? |

    > 💡 **Why these metrics?** Day 1 focuses on improving **retrieval**. We'll add Faithfulness metrics in Day 3 when we cover prompt engineering!
    """)
    return


@app.cell
def _(CORPUS_NAME, generate_response, test_questions):
    from eval_cache import load_eval_results, save_eval_results

    JUDGE_MODEL = "modal/qwen3-vl-8b"

    def load_or_run_eval(search_fn, label):
        """Load cached eval results, or run DeepEval if no cache."""
        cached = load_eval_results(CORPUS_NAME, JUDGE_MODEL, label)
        if cached:
            return cached["avg_scores"]

        # No cache — run DeepEval live
        from deepeval.metrics import AnswerRelevancyMetric, ContextualPrecisionMetric
        from deepeval.test_case import LLMTestCase
        from deepeval import evaluate

        test_cases = []
        for test in test_questions:
            results = search_fn(test["question"], top_k=3)
            retrieved_contexts = [doc for _, doc, _ in results]
            context_str = "\n\n".join(retrieved_contexts) if retrieved_contexts else "No documents found."
            actual_output = generate_response(test["question"], context_str)
            test_cases.append(LLMTestCase(
                input=test["question"],
                actual_output=actual_output,
                expected_output=test["expected"],
                retrieval_context=retrieved_contexts,
            ))

        metrics = [
            ContextualPrecisionMetric(model="ollama/granite4:350m", threshold=0.5, async_mode=False),
            AnswerRelevancyMetric(model="ollama/granite4:350m", threshold=0.5, async_mode=False),
        ]
        eval_results = evaluate(test_cases, metrics)

        # Extract avg scores and save to cache
        scores = {}
        for tr in eval_results.test_results:
            for md in tr.metrics_data:
                scores.setdefault(md.name, []).append(md.score or 0)
        avg_scores = {n: sum(v)/len(v) for n, v in scores.items()}

        per_case = [
            {"input": tc.input, "actual_output": tc.actual_output,
             "expected_output": tc.expected_output, "retrieval_context": tc.retrieval_context}
            for tc in test_cases
        ]
        save_eval_results(CORPUS_NAME, JUDGE_MODEL, label, avg_scores, per_case)
        return avg_scores
    return (load_or_run_eval,)


@app.cell
def _(load_or_run_eval, search_keyword):
    eval_scores_keyword = load_or_run_eval(search_keyword, "Keyword Search")
    return (eval_scores_keyword,)


@app.cell
def _(eval_scores_keyword, mo):
    _results_md = """
    ### 📊 Keyword Search Baseline Results

    | Metric | Score |
    |--------|-------|
    """
    for _metric, _score in eval_scores_keyword.items():
        _emoji = "✅" if _score >= 0.7 else "⚠️" if _score >= 0.5 else "❌"
        _results_md += f"| {_metric} | {_emoji} {_score:.2f} |\n"

    _results_md += """

    **Observation:** Keyword search typically scores ~0.5-0.6.
    We'll improve this with BM25 and Vector Search!
    """
    mo.md(_results_md)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---

    # ☕ Morning Hands-on Part 3: BM25 Upgrade

    *Upgrade Your RAG Pipeline to BM25*

    ---
    """)
    return


@app.cell
def _(mo):
    section_3_header = mo.accordion({
        "📖 Section 3: BM25 - A Smarter Keyword Search": mo.md("""
    BM25 (Best Matching 25) improves on simple keyword counting:

    - **TF Saturation**: Diminishing returns for repeated words
    - **IDF**: Rare words matter more than common words
    - **Length Normalization**: Fair comparison across document lengths

    **What we'll build:**
    - BM25 index using rank_bm25 library
    - Side-by-side comparison with Keyword search
    - DeepEval evaluation to prove improvement

    **Time:** ~25 minutes
        """)
    }, multiple=True)
    section_3_header
    return


@app.cell
def _(documents):
    from rank_bm25 import BM25Okapi

    # Tokenize documents for BM25
    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25_index = BM25Okapi(tokenized_docs)

    def search_bm25(query: str, top_k: int = 3) -> list[tuple[int, str, float]]:
        """
        BM25 search using rank_bm25 library.

        Returns: List of (doc_id, doc_text, score) tuples
        """
        tokenized_query = query.lower().split()
        scores = bm25_index.get_scores(tokenized_query)

        # Get top_k documents
        scored_docs = [(i, documents[i], scores[i]) for i in range(len(documents))]
        scored_docs.sort(key=lambda x: x[2], reverse=True)

        # Filter out zero scores
        scored_docs = [(i, doc, score) for i, doc, score in scored_docs if score > 0]
        return scored_docs[:top_k]
    return (search_bm25,)


@app.cell
def _(DEFAULT_QUERY, mo, query_form, search_bm25):
    import re as _re

    # Get values from the submitted form
    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY
    _top_k = query_form.value["top_k"] if query_form.value else 3

    # Run the search
    if _query:
        _bm25_results = search_bm25(_query, _top_k)
    else:
        _bm25_results = []

    def _highlight(text, query):
        """Highlight query words in text using <mark> tags."""
        words = set(query.lower().split())
        def _replacer(m):
            return f"<mark>{m.group(0)}</mark>"
        for w in words:
            text = _re.sub(r'(?i)\b' + _re.escape(w) + r'\b', _replacer, text)
        return text

    # Build document display with highlighted query words
    _docs_display = ""
    for _doc_id, _doc_text, _score in _bm25_results:
        _highlighted = _highlight(_doc_text, _query)
        _docs_display += f"\n\n**Document {_doc_id}** (Score: {_score:.2f})\n> {_highlighted}"

    mo.md(f"""
    ## Retrieved Documents (BM25)

    Query: **"{_query}"**

    Found **{len(_bm25_results)}** matching documents:
    {_docs_display if _bm25_results else "*No documents found. Try a different query.*"}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Compare: Keyword vs BM25

    Let's see how the rankings differ for the same query.
    """)
    return


@app.cell
def _(DEFAULT_QUERY, mo, query_form, search_bm25, search_keyword):
    # Get values from the submitted form
    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY
    _top_k = query_form.value["top_k"] if query_form.value else 3

    # Run both searches
    _kw_results = search_keyword(_query, _top_k)
    _bm25_results = search_bm25(_query, _top_k)

    _comparison_md = f"""
    ### Query: "{_query}"

    | Rank | Keyword Search | BM25 Search |
    |------|----------------|-------------|
    """

    _max_results = max(len(_kw_results), len(_bm25_results))
    for _i in range(_max_results):
        _kw_doc = f"Doc {_kw_results[_i][0]} (score: {_kw_results[_i][2]})" if _i < len(_kw_results) else "-"
        _bm25_doc = f"Doc {_bm25_results[_i][0]} (score: {_bm25_results[_i][2]:.2f})" if _i < len(_bm25_results) else "-"
        _comparison_md += f"| {_i+1} | {_kw_doc} | {_bm25_doc} |\n"

    mo.md(_comparison_md)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Evaluate BM25 with DeepEval

    Let's measure if BM25 actually improves our RAG quality.
    """)
    return


@app.cell
def _(load_or_run_eval, search_bm25):
    eval_scores_bm25 = load_or_run_eval(search_bm25, "BM25 Search")
    return (eval_scores_bm25,)


@app.cell
def _(eval_scores_bm25, eval_scores_keyword, mo):
    _kw_scores = eval_scores_keyword
    _bm25_scores = eval_scores_bm25

    _comparison_md = """
    ### 📊 Keyword vs BM25 Comparison

    | Metric | Keyword | BM25 | Improvement |
    |--------|---------|------|-------------|
    """
    for _metric in _kw_scores:
        _kw = _kw_scores.get(_metric, 0)
        _bm25 = _bm25_scores.get(_metric, 0)
        _diff = _bm25 - _kw
        _emoji = "📈" if _diff > 0.05 else "➡️" if _diff > -0.05 else "📉"
        _comparison_md += f"| {_metric} | {_kw:.2f} | {_bm25:.2f} | {_emoji} {_diff:+.2f} |\n"

    # Dynamic observation based on actual scores
    _kw_avg = sum(_kw_scores.values()) / len(_kw_scores) if _kw_scores else 0
    _bm25_avg = sum(_bm25_scores.values()) / len(_bm25_scores) if _bm25_scores else 0

    if _bm25_avg > _kw_avg + 0.05:
        _observation = """
    **✅ BM25 improved over Keyword Search!**

    BM25's **IDF weighting** (rare words matter more) helps it rank the correct documents higher,
    while keyword search treats every word equally — common words like "requirements" drown out
    the important ones.
    """
    elif _bm25_avg < _kw_avg - 0.05:
        _observation = """
    **🤔 Surprise — BM25 scored lower, but scroll up and compare the retrieved documents!**

    BM25 actually retrieves **better, more specific documents** (check the results above).
    So why are the scores lower? Two reasons:

    1. **Small sample size** — with only a few test questions, one question scoring differently
       swings the average significantly. These differences may not be statistically meaningful.

    2. **Answer Relevancy ≠ Answer Correctness** — this metric measures whether the answer
       *addresses the question*, not whether it's *factually correct*. When keyword search
       retrieves wrong documents, the LLM confidently **hallucates** an answer that *sounds*
       relevant — and the judge gives it a high score! Meanwhile, BM25's more specific context
       may produce a more cautious answer that the judge scores lower.

    **Key takeaway:** Evaluation metrics can be misleading — always look at the actual
    retrieved documents, not just the numbers!
    """
    else:
        _observation = """
    **➡️ BM25 and Keyword Search scored similarly.**

    Scroll up and compare the actual retrieved documents — BM25 may still be finding
    better documents even if the scores look the same. With a small number of test questions,
    metric differences this small aren't meaningful.
    """

    _comparison_md += _observation
    mo.md(_comparison_md)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ---

    # ☀️ Afternoon Hands-on: Vector Search

    *Vector Embeddings & Semantic Search*

    ---
    """)
    return


@app.cell
def _(mo):
    section_4_header = mo.accordion({
        "📖 Section 4: Vector Search - Understanding Meaning": mo.md("""
    Vector search finds documents by **meaning**, not just words.

    - "car" matches "automobile" (same meaning, different words)
    - "Python programming" matches "coding in Python"
    - Captures semantic relationships that keywords miss

    **What we'll build:**
    - Embedding model with Ollama (qwen3-embedding:0.6b)
    - DuckDB VSS with HNSW index
    - Three-way comparison: Keyword vs BM25 vs Vector
    - DeepEval evaluation to prove improvement

    **Time:** ~45 minutes
        """)
    }, multiple=True)
    section_4_header
    return


@app.cell
def _(mo):
    mo.md("""
    ## Step 1: Load the Embedding Model

    We use **qwen3-embedding:0.6b** via Ollama - a 1024-dimensional model.
    """)
    return


@app.cell
def _(documents, ollama):
    import duckdb

    # Embed all documents using Ollama
    _embed_response = ollama.embed(model="qwen3-embedding:0.6b", input=documents)
    doc_embeddings = _embed_response["embeddings"]
    return doc_embeddings, duckdb


@app.cell
def _(mo):
    mo.md("""
    ## Step 2: Store in DuckDB with VSS

    DuckDB's Vector Similarity Search extension enables fast nearest-neighbor queries.
    """)
    return


@app.cell
def _(doc_embeddings, documents, duckdb):
    # Create DuckDB connection and load VSS extension
    conn = duckdb.connect()
    conn.execute("INSTALL vss; LOAD vss;")

    # Create table and insert documents with embeddings
    conn.execute("""
        CREATE TABLE documents (
            id INTEGER,
            text VARCHAR,
            embedding FLOAT[1024]
        )
    """)

    # Insert documents
    for _i, (_doc, _emb) in enumerate(zip(documents, doc_embeddings)):
        conn.execute(
            "INSERT INTO documents VALUES (?, ?, ?)",
            [_i, _doc, _emb if isinstance(_emb, list) else _emb.tolist()]
        )

    # Create HNSW index for fast search
    conn.execute("""
        CREATE INDEX doc_hnsw_idx ON documents
        USING HNSW (embedding)
        WITH (metric = 'cosine')
    """)
    return (conn,)


@app.cell
def _(conn, ollama):
    def search_vector(query: str, top_k: int = 3) -> list[tuple[int, str, float]]:
        """
        Vector search using DuckDB VSS.

        Returns: List of (doc_id, doc_text, score) tuples
        """
        # Embed the query using Ollama
        _embed_response = ollama.embed(model="qwen3-embedding:0.6b", input=query)
        query_embedding = _embed_response["embeddings"][0]

        # Search using cosine similarity
        results = conn.execute(f"""
            SELECT id, text,
                   array_cosine_similarity(embedding, ?::FLOAT[1024]) as score
            FROM documents
            ORDER BY score DESC
            LIMIT ?
        """, [query_embedding, top_k]).fetchall()

        return [(row[0], row[1], row[2]) for row in results]
    return (search_vector,)


@app.cell
def _(DEFAULT_QUERY, mo, query_form, search_vector):
    import re as _re

    # Get values from the submitted form
    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY
    _top_k = query_form.value["top_k"] if query_form.value else 3

    # Run the search
    if _query:
        _vec_results = search_vector(_query, _top_k)
    else:
        _vec_results = []

    def _highlight(text, query):
        """Highlight query words in text using <mark> tags."""
        words = set(query.lower().split())
        def _replacer(m):
            return f"<mark>{m.group(0)}</mark>"
        for w in words:
            text = _re.sub(r'(?i)\b' + _re.escape(w) + r'\b', _replacer, text)
        return text

    # Build document display with highlighted query words
    _docs_display = ""
    for _doc_id, _doc_text, _score in _vec_results:
        _highlighted = _highlight(_doc_text, _query)
        _docs_display += f"\n\n**Document {_doc_id}** (Score: {_score:.2f})\n> {_highlighted}"

    mo.md(f"""
    ## Retrieved Documents (Vector Search)

    Query: **"{_query}"**

    Found **{len(_vec_results)}** matching documents:
    {_docs_display if _vec_results else "*No documents found. Try a different query.*"}
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Compare All Three Methods

    Let's see how Keyword, BM25, and Vector Search rank documents differently.
    """)
    return


@app.cell
def _(
    DEFAULT_QUERY,
    mo,
    query_form,
    search_bm25,
    search_keyword,
    search_vector,
):
    # Get values from the submitted form
    _query = query_form.value["query"] if query_form.value else DEFAULT_QUERY
    _top_k = query_form.value["top_k"] if query_form.value else 3

    # Run all three searches
    _kw_res = search_keyword(_query, _top_k)
    _bm25_res = search_bm25(_query, _top_k)
    _vec_res = search_vector(_query, _top_k)

    _three_way_md = f"""
    ### Query: "{_query}"

    | Rank | Keyword | BM25 | Vector |
    |------|---------|------|--------|
    """

    _max_res = max(len(_kw_res), len(_bm25_res), len(_vec_res))
    for _i in range(_max_res):
        _kw_doc = f"Doc {_kw_res[_i][0]}" if _i < len(_kw_res) else "-"
        _bm25_doc = f"Doc {_bm25_res[_i][0]}" if _i < len(_bm25_res) else "-"
        _vec_doc = f"Doc {_vec_res[_i][0]} ({_vec_res[_i][2]:.2f})" if _i < len(_vec_res) else "-"
        _three_way_md += f"| {_i+1} | {_kw_doc} | {_bm25_doc} | {_vec_doc} |\n"

    mo.md(_three_way_md)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Evaluate Vector Search with DeepEval
    """)
    return


@app.cell
def _(load_or_run_eval, search_vector):
    eval_scores_vector = load_or_run_eval(search_vector, "Vector Search")
    return (eval_scores_vector,)


@app.cell
def _(mo):
    section_5_header = mo.accordion({
        "📖 Section 5: Day 1 Scoreboard 🏆": mo.md("""
    The moment of truth! Let's compare all three retrieval methods we've implemented today.

    **What we'll see:**
    - Final comparison table: Keyword vs BM25 vs Vector
    - Per-metric breakdown: Context Precision, Answer Relevancy
    - Key insights from Day 1
    - Preview of Day 2: Hybrid Search & Reranking
        """)
    }, multiple=True)
    section_5_header
    return


@app.cell
def _(eval_scores_bm25, eval_scores_keyword, eval_scores_vector, mo):
    _kw_scores = eval_scores_keyword
    _bm25_scores = eval_scores_bm25
    _vec_scores = eval_scores_vector

    _scoreboard_md = """
    ## 📊 Final Scoreboard

    | Metric | Keyword | BM25 | Vector | Best |
    |--------|---------|------|--------|------|
    """
    _all_metrics = set(_kw_scores.keys()) | set(_bm25_scores.keys()) | set(_vec_scores.keys())

    for _metric in _all_metrics:
        _kw = _kw_scores.get(_metric, 0)
        _bm25 = _bm25_scores.get(_metric, 0)
        _vec = _vec_scores.get(_metric, 0)

        _best_score = max(_kw, _bm25, _vec)
        _best_method = "Vector" if _vec == _best_score else ("BM25" if _bm25 == _best_score else "Keyword")

        _scoreboard_md += f"| {_metric} | {_kw:.2f} | {_bm25:.2f} | {_vec:.2f} | 🏆 {_best_method} |\n"

    # Calculate overall averages
    _kw_avg = sum(_kw_scores.values()) / len(_kw_scores) if _kw_scores else 0
    _bm25_avg = sum(_bm25_scores.values()) / len(_bm25_scores) if _bm25_scores else 0
    _vec_avg = sum(_vec_scores.values()) / len(_vec_scores) if _vec_scores else 0

    _scoreboard_md += f"\n| **Average** | **{_kw_avg:.2f}** | **{_bm25_avg:.2f}** | **{_vec_avg:.2f}** | |\n"

    # Dynamic observation based on the common pattern where Vector has best CP but not best AR
    _cp_key = "Contextual Precision"
    _ar_key = "Answer Relevancy"
    _vec_cp = _vec_scores.get(_cp_key, 0)
    _kw_ar = _kw_scores.get(_ar_key, 0)
    _vec_ar = _vec_scores.get(_ar_key, 0)

    if _vec_cp >= _kw_scores.get(_cp_key, 0) and _kw_ar > _vec_ar:
        _scoreboard_md += f"""

    **🤔 Wait — Vector retrieves the best documents (CP={_vec_cp:.2f}) but Keyword has the highest Answer Relevancy ({_kw_ar:.2f})?**

    This is the same lesson from the BM25 comparison:

    - **Contextual Precision** tells us Vector finds the **right documents** every time
    - **Answer Relevancy** only measures if the answer *addresses the question* — not if it's *correct*
    - When Keyword retrieves **wrong documents**, the LLM **confidently hallucates** a detailed
      answer that *sounds* relevant — and the judge gives it a high score!
    - For example, when asked about "GIRO", Keyword retrieved unrelated docs and the LLM
      invented "Global Information Governance Organization" — completely made up, but sounds great

    **📌 Key takeaway:** Always look at the actual retrieved documents — a high Answer Relevancy
    score can hide the fact that the LLM is making things up from bad context!
    """
    else:
        _scoreboard_md += """

    **Observation:** Vector Search's semantic understanding gives it the best overall performance,
    finding the right documents even when queries use different words than the corpus.
    """

    mo.md(_scoreboard_md)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 📈 What We Learned Today

    | Step | Method | Key Insight |
    |------|--------|-------------|
    | 1 | Keyword Search | Simple but misses synonyms and context |
    | 2 | DeepEval | LLM-as-Judge gives objective metrics |
    | 3 | BM25 | TF-IDF + saturation + length norm = better |
    | 4 | Vector Search | Semantic understanding beats keywords |

    ---

    ## 🔮 Day 2 Preview: Hybrid Search & Reranking

    Tomorrow we'll combine the best of both worlds:

    - **Hybrid Search**: BM25 + Vector for maximum recall
    - **Reciprocal Rank Fusion**: Smart score combination
    - **Ollama Reranking**: Use LLM to reorder results

    See you tomorrow! 🚀
    """)
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
