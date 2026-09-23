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

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from python_engine.db import get_connection, get_all_papers, get_citations, get_user_by_id, get_user_history, get_paper_by_id
from python_engine.content_similarity import build_tfidf_matrix, compute_query_similarity
from python_engine.citation_graph import build_citation_graph, compute_pagerank, get_citation_neighbors, compute_citation_score
from python_engine.user_matching import compute_user_interest_score, compute_history_boost
from python_engine.ranking import compute_final_ranking


def run_recommendation(db_path: str, query: str, user_id: int, top_k: int = 10) -> dict:
    """
    Execute the full recommendation pipeline and return results as a dict.

    Steps:
        1. Load papers and citations from DB
        2. Build TF-IDF matrix from paper abstracts
        3. Compute content similarity for the user query
        4. Build citation graph and compute citation-based scores
        5. Load user profile and compute interest scores
        6. Fuse all scores and return Top-K
    """
    # Resolve db_path relative to project root if not absolute
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
        content_scores = compute_query_similarity(query, tfidf_matrix, vectorizer, paper_ids)

        # 4. Citation graph scores
        citation_graph = build_citation_graph(citations)

        # Find papers that are content-relevant (top 20%) as seeds for citation scoring
        sorted_content = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
        n_seeds = max(1, len(sorted_content) // 5)
        query_relevant_ids = [pid for pid, _ in sorted_content[:n_seeds] if content_scores[pid] > 0]

        citation_scores = compute_citation_score(citation_graph, query_relevant_ids, paper_ids)

        # 5. User interest scores
        if user:
            user_interest_scores = compute_user_interest_score(user, papers)

            # Also boost papers similar to user's history
            history_ids = get_user_history(conn, user_id)
            if history_ids:
                history_scores = compute_history_boost(
                    history_ids, papers, tfidf_matrix, vectorizer, paper_ids
                )
                # Combine interest and history (average)
                for pid in paper_ids:
                    interest = user_interest_scores.get(pid, 0.0)
                    history = history_scores.get(pid, 0.0)
                    user_interest_scores[pid] = (interest + history) / 2.0
        else:
            user_interest_scores = {pid: 0.0 for pid in paper_ids}

        # 6. Fuse and rank
        ranked = compute_final_ranking(
            content_scores, citation_scores, user_interest_scores, top_k=top_k
        )

        # Build output
        results = []
        for paper_id, final_score, breakdown in ranked:
            paper = get_paper_by_id(conn, paper_id)
            if paper:
                results.append({
                    "paper_id": paper["id"],
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "year": paper["year"],
                    "abstract": paper["abstract"],
                    "venue": paper["venue"],
                    "keywords": paper["keywords"],
                    "final_score": round(final_score, 4),
                    "content_score": round(breakdown["content_score"], 4),
                    "citation_score": round(breakdown["citation_score"], 4),
                    "user_score": round(breakdown["user_score"], 4),
                })

        return {
            "query": query,
            "user_id": user_id,
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
    parser.add_argument("--json", action="store_true",
                        help="Read JSON input from stdin")

    args = parser.parse_args()

    # Check for JSON stdin input
    if args.json or (not args.query and not sys.stdin.isatty()):
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                params = json.loads(stdin_data)
                db_path = params.get("db_path", args.db)
                query = params.get("query", "")
                user_id = params.get("user_id", None)
                top_k = params.get("top_k", 10)
            else:
                print(json.dumps({"error": "No input provided."}))
                sys.exit(1)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON: {e}"}))
            sys.exit(1)
    else:
        db_path = args.db
        query = args.query or ""
        user_id = args.user_id
        top_k = args.top_k

    if not query:
        print(json.dumps({"error": "No search query provided. Use --query <text>"}))
        sys.exit(1)

    result = run_recommendation(db_path, query, user_id, top_k)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
