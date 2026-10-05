import pytest
from python_engine.evaluator import (
    compute_precision_at_k,
    compute_recall_at_k,
    compute_average_precision_at_k,
    compute_ndcg_at_k,
    compute_mrr,
    compute_intra_list_diversity,
    run_algorithm_benchmark,
)
from python_engine.db import get_connection
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "papers.db")


def test_precision_recall_ap():
    recommended = [1, 2, 3, 4, 5]
    relevant = {2, 4, 6}

    p = compute_precision_at_k(recommended, relevant, k=5)
    assert p == 2 / 5

    r = compute_recall_at_k(recommended, relevant, k=5)
    assert r == 2 / 3

    ap = compute_average_precision_at_k(recommended, relevant, k=5)
    assert 0.0 < ap <= 1.0


def test_ndcg_at_k():
    recommended = [1, 2, 3, 4]
    rel_scores = {1: 3.0, 2: 2.0, 3: 1.0, 4: 0.0}

    # Perfect ranking
    ndcg = compute_ndcg_at_k(recommended, rel_scores, k=4)
    assert pytest.approx(ndcg, 0.01) == 1.0

    # Suboptimal ranking
    suboptimal = [4, 3, 2, 1]
    ndcg_sub = compute_ndcg_at_k(suboptimal, rel_scores, k=4)
    assert ndcg_sub < ndcg


def test_mrr():
    assert compute_mrr([1, 2, 3], {2}) == 0.5
    assert compute_mrr([1, 2, 3], {1}) == 1.0
    assert compute_mrr([1, 2, 3], {4}) == 0.0


def test_run_algorithm_benchmark():
    if os.path.exists(DB_PATH):
        conn = get_connection(DB_PATH)
        res = run_algorithm_benchmark(conn, k=5)
        conn.close()
        assert "models" in res
        assert "hybrid" in res["models"]
        assert "bm25" in res["models"]
        assert "ndcg_at_k" in res["models"]["hybrid"]
        assert res["models"]["hybrid"]["ndcg_at_k"] > 0
