#!/usr/bin/env python3
"""
main.py — CLI entry point for the Smart Research Paper Recommendation System.

Usage:
    python -m python_engine.main --db <db_path> --query <query> --user_id <id> --top_k <N>

Or via JSON on stdin:
    echo '{"db_path": "database/papers.db", "query": "machine learning", "user_id": 1, "top_k": 10}' | python -m python_engine.main
"""

import argparse
import json
import os
import sys
from typing import Dict, Optional

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from python_engine.db import (
    get_connection,
    get_all_papers,
    get_citations,
    get_user_by_id,
    get_user_history,
    get_paper_by_id,
)
from python_engine.content_similarity import (
    build_tfidf_matrix,
    compute_query_similarity,
    compute_bm25_similarity,
    compute_hybrid_content_similarity,
)
from python_engine.citation_graph import (
    build_citation_graph,
    compute_pagerank,
    get_citation_neighbors,
    compute_citation_score,
    compute_personalized_pagerank,
)
from python_engine.user_matching import (
    compute_user_interest_score,
    compute_history_boost,
)
from python_engine.ranking import (
    compute_final_ranking,
    compute_reciprocal_rank_fusion,
    compute_mmr_ranking,
    compute_recency_scores,
)


def run_recommendation(
    db_path: str,
    query: str,
    user_id: Optional[int] = None,
    top_k: int = 10,
    algorithm: str = "hybrid",
    weights: Optional[Dict[str, float]] = None,
) -> dict:
    """
    Execute the recommendation pipeline and return results as a dict.

    Supported algorithms:
        - "hybrid": Weighted linear fusion of content, citation, and user interest
        - "bm25": Okapi BM25 relevance fused with citation PageRank
        - "rrf": Reciprocal Rank Fusion of distinct signals
        - "mmr": Maximal Marginal Relevance diversity reranking
    """
    if not os.path.isabs(db_path):
        db_path = os.path.join(PROJECT_ROOT, db_path)

    if not os.path.exists(db_path):
        return {"error": f"Database not found: {db_path}"}

    conn = get_connection(db_path)

    try:
        # 1. Load data
        papers = get_all_papers(conn)
        if not papers:
            return {"error": "No papers found in database."}

        citations = get_citations(conn)
        user = get_user_by_id(conn, user_id) if user_id else None

        # 2. Build TF-IDF matrix
        tfidf_matrix, vectorizer, paper_ids = build_tfidf_matrix(papers)

        # 3. Content similarity
        if algorithm == "bm25":
            content_scores = compute_bm25_similarity(query, papers)
        else:
            content_scores = compute_hybrid_content_similarity(
                query, papers, tfidf_matrix, vectorizer, paper_ids, bm25_weight=0.4
            )

        # 4. Citation graph scores
        citation_graph = build_citation_graph(citations)
        sorted_content = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
        n_seeds = max(1, len(sorted_content) // 5)
        query_relevant_ids = [pid for pid, _ in sorted_content[:n_seeds] if content_scores[pid] > 0]

        citation_scores = compute_citation_score(
            citation_graph, query_relevant_ids, paper_ids, use_personalized=True
        )

        # 5. User interest scores
        if user:
            user_interest_scores = compute_user_interest_score(user, papers)
            history_ids = get_user_history(conn, user_id)
            if history_ids:
                history_scores = compute_history_boost(
                    history_ids, papers, tfidf_matrix, vectorizer, paper_ids
                )
                for pid in paper_ids:
                    interest = user_interest_scores.get(pid, 0.0)
                    history = history_scores.get(pid, 0.0)
                    user_interest_scores[pid] = round((interest + history) / 2.0, 4)
        else:
            user_interest_scores = {pid: 0.0 for pid in paper_ids}

        # 6. Recency scores
        recency_scores = compute_recency_scores(papers)

        # 7. Ranking according to selected algorithm
        papers_dict = {p["id"]: p for p in papers}
        results = []

        if algorithm == "rrf":
            # Sort each signal into rank lists
            content_ranked = [p for p, _ in sorted(content_scores.items(), key=lambda x: x[1], reverse=True)]
            citation_ranked = [p for p, _ in sorted(citation_scores.items(), key=lambda x: x[1], reverse=True)]
            user_ranked = [p for p, _ in sorted(user_interest_scores.items(), key=lambda x: x[1], reverse=True)]

            rrf_results = compute_reciprocal_rank_fusion(
                [content_ranked, citation_ranked, user_ranked], k=60, top_k=top_k
            )

            for paper_id, score in rrf_results:
                paper = papers_dict.get(paper_id)
                if paper:
                    results.append({
                        "paper_id": paper["id"],
                        "title": paper["title"],
                        "authors": paper["authors"],
                        "year": paper["year"],
                        "abstract": paper["abstract"],
                        "venue": paper["venue"],
                        "keywords": paper["keywords"],
                        "doi": paper.get("doi", ""),
                        "url": paper.get("url", ""),
                        "pdf_url": paper.get("pdf_url", ""),
                        "scholar_url": paper.get("scholar_url", ""),
                        "final_score": round(score, 4),
                        "content_score": round(content_scores.get(paper_id, 0.0), 4),
                        "citation_score": round(citation_scores.get(paper_id, 0.0), 4),
                        "user_score": round(user_interest_scores.get(paper_id, 0.0), 4),
                    })

        elif algorithm == "mmr":
            # Initial scores via hybrid fusion
            ranked_pre = compute_final_ranking(
                content_scores, citation_scores, user_interest_scores, weights=weights, top_k=len(paper_ids)
            )
            candidate_dict = {pid: score for pid, score, _ in ranked_pre}

            mmr_results = compute_mmr_ranking(
                candidate_dict, tfidf_matrix, paper_ids, lambda_param=0.7, top_k=top_k
            )

            for paper_id, score in mmr_results:
                paper = papers_dict.get(paper_id)
                if paper:
                    results.append({
                        "paper_id": paper["id"],
                        "title": paper["title"],
                        "authors": paper["authors"],
                        "year": paper["year"],
                        "abstract": paper["abstract"],
                        "venue": paper["venue"],
                        "keywords": paper["keywords"],
                        "doi": paper.get("doi", ""),
                        "url": paper.get("url", ""),
                        "pdf_url": paper.get("pdf_url", ""),
                        "scholar_url": paper.get("scholar_url", ""),
                        "final_score": round(score, 4),
                        "content_score": round(content_scores.get(paper_id, 0.0), 4),
                        "citation_score": round(citation_scores.get(paper_id, 0.0), 4),
                        "user_score": round(user_interest_scores.get(paper_id, 0.0), 4),
                    })

        else:
            # Default: Hybrid weighted linear fusion
            ranked = compute_final_ranking(
                content_scores,
                citation_scores,
                user_interest_scores,
                weights=weights,
                top_k=top_k,
                recency_scores=recency_scores,
            )

            for paper_id, final_score, breakdown in ranked:
                paper = papers_dict.get(paper_id)
                if paper:
                    results.append({
                        "paper_id": paper["id"],
                        "title": paper["title"],
                        "authors": paper["authors"],
                        "year": paper["year"],
                        "abstract": paper["abstract"],
                        "venue": paper["venue"],
                        "keywords": paper["keywords"],
                        "doi": paper.get("doi", ""),
                        "url": paper.get("url", ""),
                        "pdf_url": paper.get("pdf_url", ""),
                        "scholar_url": paper.get("scholar_url", ""),
                        "final_score": round(final_score, 4),
                        "content_score": round(breakdown["content_score"], 4),
                        "citation_score": round(breakdown["citation_score"], 4),
                        "user_score": round(breakdown["user_score"], 4),
                        "recency_score": round(breakdown.get("recency_score", 0.0), 4),
                    })

        return {
            "query": query,
            "user_id": user_id,
            "algorithm": algorithm,
            "total_papers": len(papers),
            "results_count": len(results),
            "results": results,
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def main():
    """Parse arguments and run the recommendation pipeline."""
    parser = argparse.ArgumentParser(
        description="Smart Research Paper Recommendation System"
    )
    parser.add_argument("--db", type=str, default="database/papers.db",
                        help="Path to SQLite database")
    parser.add_argument("--query", type=str, default=None,
                        help="Search query text")
    parser.add_argument("--user_id", type=int, default=None,
                        help="User ID for personalized results")
    parser.add_argument("--top_k", type=int, default=10,
                        help="Number of results to return")
    parser.add_argument("--algorithm", type=str, default="hybrid",
                        choices=["hybrid", "bm25", "rrf", "mmr"],
                        help="Recommendation algorithm to use")
    parser.add_argument("--json", action="store_true",
                        help="Read JSON input from stdin")

    args = parser.parse_args()

    # Check for JSON stdin input
    if args.json or (not args.query and not sys.stdin.isatty()):
        try:
            stdin_data = json.load(sys.stdin)
            db_path = stdin_data.get("db_path", args.db)
            query = stdin_data.get("query", "")
            user_id = stdin_data.get("user_id", args.user_id)
            top_k = stdin_data.get("top_k", args.top_k)
            algo = stdin_data.get("algorithm", args.algorithm)
            weights = stdin_data.get("weights", None)
            res = run_recommendation(db_path, query, user_id, top_k, algorithm=algo, weights=weights)
            print(json.dumps(res, indent=2))
            return
        except Exception as e:
            print(json.dumps({"error": f"Failed to parse stdin JSON: {str(e)}"}))
            sys.exit(1)

    if not args.query:
        print(json.dumps({"error": "No query provided. Use --query or pass JSON via stdin."}))
        sys.exit(1)

    res = run_recommendation(
        args.db, args.query, args.user_id, args.top_k, algorithm=args.algorithm
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
