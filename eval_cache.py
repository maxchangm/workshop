"""
Evaluation Cache - Save and load DeepEval results to avoid re-running expensive evaluations.

Cache keys are based on: corpus_name + judge_model + search_method
This ensures results from different judges or corpora are never mixed.

Usage:
    from workshop.eval_cache import save_eval_results, load_eval_results

    # Try loading cached results
    cached = load_eval_results("s17", "modal/qwen3-vl-8b", "Keyword Search")
    if cached:
        avg_scores, per_case = cached["avg_scores"], cached["per_case"]
    else:
        avg_scores = run_evaluation(search_keyword, "Keyword Search")
        save_eval_results("s17", "modal/qwen3-vl-8b", "Keyword Search", avg_scores, per_case)

    # Clear all cache
    clear_eval_cache()

    # Clear cache for specific corpus/judge combo
    clear_eval_cache(corpus_name="s17", judge_model="modal/qwen3-vl-8b")
"""

import json
import os
import re
import time

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".eval_cache")


def _sanitize(name: str) -> str:
    """Sanitize a name for use as a filename component."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.strip().lower())


def _cache_path(corpus_name: str, judge_model: str, method: str) -> str:
    """Build the cache file path for a specific evaluation run."""
    key = f"{_sanitize(corpus_name)}__{_sanitize(judge_model)}__{_sanitize(method)}"
    return os.path.join(CACHE_DIR, f"{key}.json")


def save_eval_results(
    corpus_name: str,
    judge_model: str,
    method: str,
    avg_scores: dict,
    per_case: list[dict] | None = None,
) -> str:
    """
    Save evaluation results to cache.

    Args:
        corpus_name: e.g. "synthetic", "s17", "s17_final"
        judge_model: e.g. "granite4:3b", "modal/qwen3-vl-8b"
        method: e.g. "Keyword Search", "BM25 Search", "Vector Search"
        avg_scores: dict of metric_name -> average score
        per_case: optional list of per-test-case dicts with detailed results

    Returns:
        Path to the saved cache file.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(corpus_name, judge_model, method)
    data = {
        "corpus_name": corpus_name,
        "judge_model": judge_model,
        "method": method,
        "avg_scores": avg_scores,
        "per_case": per_case or [],
        "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  💾 Cached {method} results → {os.path.basename(path)}")
    return path


def load_eval_results(
    corpus_name: str, judge_model: str, method: str
) -> dict | None:
    """
    Load cached evaluation results if available.

    Returns:
        dict with keys: avg_scores, per_case, cached_at — or None if no cache.
    """
    path = _cache_path(corpus_name, judge_model, method)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    print(f"  ⚡ Loaded cached {method} results (from {data.get('cached_at', 'unknown')})")
    return data


def clear_eval_cache(
    corpus_name: str | None = None, judge_model: str | None = None
) -> int:
    """
    Clear cached evaluation results.

    Args:
        corpus_name: If provided, only clear cache for this corpus.
        judge_model: If provided, only clear cache for this judge.

    Returns:
        Number of cache files deleted.
    """
    if not os.path.exists(CACHE_DIR):
        return 0

    deleted = 0
    prefix_parts = []
    if corpus_name:
        prefix_parts.append(_sanitize(corpus_name))
    if judge_model:
        if not prefix_parts:
            prefix_parts.append("")  # wildcard first segment
        prefix_parts.append(_sanitize(judge_model))

    for fname in os.listdir(CACHE_DIR):
        if not fname.endswith(".json"):
            continue
        if prefix_parts:
            # Check if filename matches the filter
            parts = fname.replace(".json", "").split("__")
            match = True
            if corpus_name and (len(parts) < 1 or parts[0] != _sanitize(corpus_name)):
                match = False
            if judge_model and (len(parts) < 2 or parts[1] != _sanitize(judge_model)):
                match = False
            if not match:
                continue
        os.remove(os.path.join(CACHE_DIR, fname))
        deleted += 1

    if deleted:
        print(f"  🗑️  Cleared {deleted} cached evaluation file(s)")
    return deleted

