"""
evaluator.py — Academic Evaluation and Benchmarking Suite for RecSys and IR.

Implements standard evaluation metrics from first principles:
- NDCG@K (Normalized Discounted Cumulative Gain)
- MAP@K (Mean Average Precision)
- Precision@K & Recall@K
- MRR (Mean Reciprocal Rank)
- Intra-List Diversity (ILD)
- Novelty Score
"""

import math
import time
from typing import Dict, List, Set, Tuple
import numpy as np


def compute_precision_at_k(recommended: List[int], relevant: Set[int], k: int = 10) -> float:
    """Precision@K = (Number of relevant papers in top-K) / K."""
    if k <= 0:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for pid in top_k if pid in relevant)
    return hits / k


def compute_recall_at_k(recommended: List[int], relevant: Set[int], k: int = 10) -> float:
    """Recall@K = (Number of relevant papers in top-K) / (Total relevant papers)."""
    if not relevant or k <= 0:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for pid in top_k if pid in relevant)
    return hits / len(relevant)


def compute_average_precision_at_k(recommended: List[int], relevant: Set[int], k: int = 10) -> float:
    """
    Average Precision (AP@K).
    AP@K = sum_{i=1}^K (Precision@i * rel(i)) / min(K, |Relevant|)
    """
    if not relevant or k <= 0:
        return 0.0

    score = 0.0
    hits = 0

    for i, pid in enumerate(recommended[:k]):
        if pid in relevant:
            hits += 1
            score += hits / (i + 1)

    denominator = min(k, len(relevant))
    return score / denominator if denominator > 0 else 0.0


def compute_dcg_at_k(recommended: List[int], relevant_scores: Dict[int, float], k: int = 10) -> float:
    """Discounted Cumulative Gain (DCG@K)."""
    dcg = 0.0
    for i, pid in enumerate(recommended[:k]):
        rel = relevant_scores.get(pid, 0.0)
        # Using standard formula: rel / log2(i + 2)
        dcg += rel / math.log2(i + 2)
    return dcg


def compute_ndcg_at_k(recommended: List[int], relevant_scores: Dict[int, float], k: int = 10) -> float:
    """
    Normalized Discounted Cumulative Gain (NDCG@K).
    NDCG@K = DCG@K / IDCG@K
    """
    if not relevant_scores or k <= 0:
        return 0.0

    dcg = compute_dcg_at_k(recommended, relevant_scores, k=k)

    # Ideal ranking (sorted by relevance descending)
    ideal_order = sorted(relevant_scores.keys(), key=lambda p: relevant_scores[p], reverse=True)
    idcg = compute_dcg_at_k(ideal_order, relevant_scores, k=k)

    return (dcg / idcg) if idcg > 0 else 0.0


def compute_mrr(recommended: List[int], relevant: Set[int]) -> float:
    """Mean Reciprocal Rank (MRR): 1 / rank of first relevant item."""
    for i, pid in enumerate(recommended):
        if pid in relevant:
            return 1.0 / (i + 1)
    return 0.0


def compute_intra_list_diversity(
    recommended: List[int], tfidf_matrix, paper_ids: List[int], k: int = 10
) -> float:
    """
    Intra-List Diversity (ILD).
    Measures the average pairwise dissimilarity between items in the recommendation list:
    ILD = (2 / (K * (K - 1))) * sum_{i < j} (1 - CosineSim(p_i, p_j))
    """
    from sklearn.metrics.pairwise import cosine_similarity

    id_to_idx = {pid: idx for idx, pid in enumerate(paper_ids)}
    top_k_ids = [pid for pid in recommended[:k] if pid in id_to_idx]

    if len(top_k_ids) < 2:
        return 1.0

    sub_vectors = tfidf_matrix[[id_to_idx[pid] for pid in top_k_ids]]
    sim_matrix = cosine_similarity(sub_vectors)

    n = len(top_k_ids)
    dissimilarity_sum = 0.0
    pairs = 0

    for i in range(n):
        for j in range(i + 1, n):
            dissimilarity_sum += (1.0 - sim_matrix[i, j])
            pairs += 1

    return float(dissimilarity_sum / pairs) if pairs > 0 else 0.0


# ── Benchmark Evaluation Dataset ───────────────────────────────────────────
BENCHMARK_QUERIES = [
    {
        "query": "deep learning neural networks image recognition",
        "category": "Computer Vision",
        "relevant_ids": {6, 8, 10, 16, 17, 18, 19, 20},
        "relevance_grades": {6: 3.0, 20: 3.0, 16: 2.0, 17: 2.0, 18: 2.0, 8: 1.5, 10: 1.0},
    },
    {
        "query": "transformer attention language models BERT",
        "category": "Natural Language Processing",
        "relevant_ids": {7, 11, 12, 13, 14, 15},
        "relevance_grades": {7: 3.0, 11: 3.0, 12: 2.0, 14: 2.0, 15: 1.5, 13: 1.0},
    },
    {
        "query": "gradient boosting machine learning classification",
        "category": "Machine Learning",
        "relevant_ids": {1, 2, 3, 4, 5},
        "relevance_grades": {1: 3.0, 2: 3.0, 3: 2.0, 5: 2.0, 4: 1.5},
    },
    {
        "query": "distributed consensus systems microservices MapReduce",
        "category": "Distributed Systems",
        "relevant_ids": {21, 22, 23, 24, 25},
        "relevance_grades": {21: 3.0, 22: 3.0, 23: 2.0, 24: 2.0, 25: 1.5},
    },
]


def run_algorithm_benchmark(conn, k: int = 10) -> Dict:
    """
    Run empirical ablation study comparing all models across benchmark test sets.

    Compares:
        1. BM25 Only
        2. TF-IDF Cosine Only
        3. Graph PageRank Only
        4. Hybrid Multi-Signal (Default)
        5. MMR Diversity Reranked
        6. Reciprocal Rank Fusion (RRF)
    """
    from python_engine.db import get_all_papers, get_citations
    from python_engine.content_similarity import (
        build_tfidf_matrix,
        compute_query_similarity,
        compute_bm25_similarity,
        compute_hybrid_content_similarity,
    )
    from python_engine.citation_graph import (
        build_citation_graph,
        compute_citation_score,
        compute_pagerank,
    )
    from python_engine.ranking import (
        compute_final_ranking,
        compute_mmr_ranking,
        compute_reciprocal_rank_fusion,
    )

    papers = get_all_papers(conn)
    citations = get_citations(conn)
    tfidf_matrix, vectorizer, paper_ids = build_tfidf_matrix(papers)
    graph = build_citation_graph(citations)
    pagerank_scores = compute_pagerank(graph)

    models = ["bm25", "tfidf", "graph_only", "hybrid", "mmr", "rrf"]
    results = {
        m: {
            "ndcg": [],
            "map": [],
            "precision": [],
            "recall": [],
            "mrr": [],
            "diversity": [],
            "latencies": [],
        }
        for m in models
    }

    for bq in BENCHMARK_QUERIES:
        query = bq["query"]
        rel_set = bq["relevant_ids"]
        rel_grades = bq["relevance_grades"]

        # 1. BM25
        t0 = time.perf_counter()
        bm25_scores = compute_bm25_similarity(query, papers)
        bm25_ranked = sorted(bm25_scores.keys(), key=lambda p: bm25_scores[p], reverse=True)
        results["bm25"]["latencies"].append((time.perf_counter() - t0) * 1000)
        _record_metrics(results["bm25"], bm25_ranked, rel_set, rel_grades, tfidf_matrix, paper_ids, k)

        # 2. TF-IDF
        t0 = time.perf_counter()
        tfidf_scores = compute_query_similarity(query, tfidf_matrix, vectorizer, paper_ids)
        tfidf_ranked = sorted(tfidf_scores.keys(), key=lambda p: tfidf_scores[p], reverse=True)
        results["tfidf"]["latencies"].append((time.perf_counter() - t0) * 1000)
        _record_metrics(results["tfidf"], tfidf_ranked, rel_set, rel_grades, tfidf_matrix, paper_ids, k)

        # 3. Graph Only
        t0 = time.perf_counter()
        graph_ranked = sorted(pagerank_scores.keys(), key=lambda p: pagerank_scores.get(p, 0), reverse=True)
        results["graph_only"]["latencies"].append((time.perf_counter() - t0) * 1000)
        _record_metrics(results["graph_only"], graph_ranked, rel_set, rel_grades, tfidf_matrix, paper_ids, k)

        # 4. Hybrid Multi-Signal
        t0 = time.perf_counter()
        hybrid_content = compute_hybrid_content_similarity(query, papers, tfidf_matrix, vectorizer, paper_ids)
        sorted_c = sorted(hybrid_content.items(), key=lambda x: x[1], reverse=True)
        seed_ids = [pid for pid, _ in sorted_c[:5] if hybrid_content[pid] > 0]
        cit_scores = compute_citation_score(graph, seed_ids, paper_ids)
        user_scores = {p: 0.0 for p in paper_ids}
        hybrid_ranked_tuples = compute_final_ranking(hybrid_content, cit_scores, user_scores, top_k=k)
        hybrid_ranked = [p for p, _, _ in hybrid_ranked_tuples]
        results["hybrid"]["latencies"].append((time.perf_counter() - t0) * 1000)
        _record_metrics(results["hybrid"], hybrid_ranked, rel_set, rel_grades, tfidf_matrix, paper_ids, k)

        # 5. MMR Diversity Reranked
        t0 = time.perf_counter()
        candidate_dict = {p: s for p, s, _ in compute_final_ranking(hybrid_content, cit_scores, user_scores, top_k=len(paper_ids))}
        mmr_ranked_tuples = compute_mmr_ranking(candidate_dict, tfidf_matrix, paper_ids, lambda_param=0.6, top_k=k)
        mmr_ranked = [p for p, _ in mmr_ranked_tuples]
        results["mmr"]["latencies"].append((time.perf_counter() - t0) * 1000)
        _record_metrics(results["mmr"], mmr_ranked, rel_set, rel_grades, tfidf_matrix, paper_ids, k)

        # 6. Reciprocal Rank Fusion (RRF)
        t0 = time.perf_counter()
        rrf_tuples = compute_reciprocal_rank_fusion([bm25_ranked, graph_ranked, tfidf_ranked], k=60, top_k=k)
        rrf_ranked = [p for p, _ in rrf_tuples]
        results["rrf"]["latencies"].append((time.perf_counter() - t0) * 1000)
        _record_metrics(results["rrf"], rrf_ranked, rel_set, rel_grades, tfidf_matrix, paper_ids, k)

    # Compute summary averages
    summary = {}
    model_names = {
        "hybrid": "SRPS Hybrid Fusion (Our Model)",
        "mmr": "MMR Diversity Reranking",
        "rrf": "Reciprocal Rank Fusion",
        "bm25": "Okapi BM25 Baseline",
        "tfidf": "TF-IDF Vector Space",
        "graph_only": "PageRank Graph Only",
    }

    for m in models:
        summary[m] = {
            "name": model_names[m],
            "ndcg_at_k": round(float(np.mean(results[m]["ndcg"])), 4),
            "map_at_k": round(float(np.mean(results[m]["map"])), 4),
            "precision_at_k": round(float(np.mean(results[m]["precision"])), 4),
            "recall_at_k": round(float(np.mean(results[m]["recall"])), 4),
            "mrr": round(float(np.mean(results[m]["mrr"])), 4),
            "diversity_ild": round(float(np.mean(results[m]["diversity"])), 4),
            "avg_latency_ms": round(float(np.mean(results[m]["latencies"])), 2),
        }

    return {
        "k": k,
        "test_queries_count": len(BENCHMARK_QUERIES),
        "models": summary,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _record_metrics(metric_dict, ranked_list, rel_set, rel_grades, matrix, paper_ids, k):
    metric_dict["ndcg"].append(compute_ndcg_at_k(ranked_list, rel_grades, k=k))
    metric_dict["map"].append(compute_average_precision_at_k(ranked_list, rel_set, k=k))
    metric_dict["precision"].append(compute_precision_at_k(ranked_list, rel_set, k=k))
    metric_dict["recall"].append(compute_recall_at_k(ranked_list, rel_set, k=k))
    metric_dict["mrr"].append(compute_mrr(ranked_list, rel_set))
    metric_dict["diversity"].append(compute_intra_list_diversity(ranked_list, matrix, paper_ids, k=k))
