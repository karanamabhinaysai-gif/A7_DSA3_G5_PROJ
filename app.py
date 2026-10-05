"""
app.py — Modern Flask Web Application & REST API for the Smart Research Paper Recommendation System.

Provides full REST endpoints for recommendations, citation network graph visualization,
graph analytics, user bookmarks, live arXiv ingestion, and BibTeX citations.
"""

import hashlib
import json
import os
import sys
from typing import Dict, List

from flask import Flask, jsonify, render_template, request, Response

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from python_engine.db import (
    get_connection,
    get_all_papers,
    get_paper_by_id,
    get_citations,
    get_user_by_id,
    get_user_by_username,
    get_user_history,
    add_user_history,
    get_bookmarks,
    add_bookmark,
    remove_bookmark,
    insert_paper,
    insert_citation,
    update_user_interests,
    create_user,
)
from python_engine.content_similarity import (
    build_tfidf_matrix,
    compute_query_similarity,
    compute_bm25_similarity,
    compute_hybrid_content_similarity,
    compute_paper_similarity,
)
from python_engine.citation_graph import (
    build_citation_graph,
    compute_pagerank,
    compute_personalized_pagerank,
    compute_hits,
    detect_communities,
    find_shortest_citation_path,
    compute_citation_score,
    compute_graph_analytics,
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
from python_engine.arxiv_service import search_arxiv
from python_engine.export import to_bibtex, to_apa, export_papers_bibtex

app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, "templates"))

DB_PATH = os.path.join(PROJECT_ROOT, "database", "papers.db")


def _ensure_db():
    """Seed the database if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        from data.seed_data import seed_database
        seed_database()


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ── Frontend Route ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the modern interactive recommendation & citation explorer dashboard."""
    _ensure_db()
    return render_template("index.html")


@app.route("/login")
def login_page():
    """Serve dedicated Login and Registration page."""
    _ensure_db()
    return render_template("login.html")



# ── Recommendation API ──────────────────────────────────────────────────────

@app.route("/api/recommend", methods=["GET", "POST"])
def recommend():
    """
    Advanced Multi-Signal Recommendation API.

    Supports:
        - query (str): search term
        - user_id (int, optional): user ID for personalized scoring
        - top_k (int, optional): number of results (default 10)
        - algorithm (str, optional): 'hybrid' | 'bm25' | 'rrf' | 'mmr'
        - weights (dict, optional): custom weights for signals
    """
    _ensure_db()

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
    else:
        data = request.args.to_dict()

    query = data.get("query", "").strip()
    user_id = data.get("user_id")
    top_k = int(data.get("top_k", 10))
    algorithm = data.get("algorithm", "hybrid")
    weights = data.get("weights")

    if not query:
        return jsonify({"error": "No search query provided."}), 400

    if user_id is not None:
        try:
            user_id = int(user_id)
        except ValueError:
            user_id = None

    try:
        conn = get_connection(DB_PATH)
        papers = get_all_papers(conn)
        if not papers:
            conn.close()
            return jsonify({"error": "No papers in database"}), 404

        citations = get_citations(conn)
        user = get_user_by_id(conn, user_id) if user_id else None

        # 1. Content Similarity (TF-IDF + Okapi BM25)
        tfidf_matrix, vectorizer, paper_ids = build_tfidf_matrix(papers)

        if algorithm == "bm25":
            content_scores = compute_bm25_similarity(query, papers)
        else:
            content_scores = compute_hybrid_content_similarity(
                query, papers, tfidf_matrix, vectorizer, paper_ids, bm25_weight=0.4
            )

        # 2. Citation Graph & Network Analysis
        citation_graph = build_citation_graph(citations)
        sorted_content = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
        n_seeds = max(1, len(sorted_content) // 5)
        query_relevant_ids = [pid for pid, _ in sorted_content[:n_seeds] if content_scores[pid] > 0]

        citation_scores = compute_citation_score(
            citation_graph, query_relevant_ids, paper_ids, use_personalized=True
        )

        # 3. User Interest & Reading History Profiling
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

            # Record search action in user history
            if query_relevant_ids:
                add_user_history(conn, user_id, query_relevant_ids[0], action="searched")
        else:
            user_interest_scores = {pid: 0.0 for pid in paper_ids}

        # 4. Temporal Recency Scores
        recency_scores = compute_recency_scores(papers)

        # 5. Ranking Selection
        papers_dict = {p["id"]: p for p in papers}
        results = []

        if algorithm == "rrf":
            content_ranked = [p for p, _ in sorted(content_scores.items(), key=lambda x: x[1], reverse=True)]
            citation_ranked = [p for p, _ in sorted(citation_scores.items(), key=lambda x: x[1], reverse=True)]
            user_ranked = [p for p, _ in sorted(user_interest_scores.items(), key=lambda x: x[1], reverse=True)]

            rrf_res = compute_reciprocal_rank_fusion(
                [content_ranked, citation_ranked, user_ranked], k=60, top_k=top_k
            )

            for paper_id, rrf_score in rrf_res:
                p = papers_dict.get(paper_id, {})
                results.append({
                    "paper_id": paper_id,
                    "title": p.get("title", ""),
                    "authors": p.get("authors", ""),
                    "year": p.get("year", 0),
                    "abstract": p.get("abstract", ""),
                    "venue": p.get("venue", ""),
                    "keywords": p.get("keywords", ""),
                    "doi": p.get("doi", ""),
                    "url": p.get("url", ""),
                    "pdf_url": p.get("pdf_url", ""),
                    "scholar_url": p.get("scholar_url", ""),
                    "semantic_scholar_url": p.get("semantic_scholar_url", ""),
                    "final_score": round(rrf_score, 4),
                    "content_score": round(content_scores.get(paper_id, 0.0), 4),
                    "citation_score": round(citation_scores.get(paper_id, 0.0), 4),
                    "user_score": round(user_interest_scores.get(paper_id, 0.0), 4),
                    "recency_score": round(recency_scores.get(paper_id, 0.0), 4),
                })

        elif algorithm == "mmr":
            ranked_pre = compute_final_ranking(
                content_scores, citation_scores, user_interest_scores, weights=weights, top_k=len(paper_ids)
            )
            candidate_dict = {pid: score for pid, score, _ in ranked_pre}

            mmr_res = compute_mmr_ranking(
                candidate_dict, tfidf_matrix, paper_ids, lambda_param=0.7, top_k=top_k
            )

            for paper_id, mmr_score in mmr_res:
                p = papers_dict.get(paper_id, {})
                results.append({
                    "paper_id": paper_id,
                    "title": p.get("title", ""),
                    "authors": p.get("authors", ""),
                    "year": p.get("year", 0),
                    "abstract": p.get("abstract", ""),
                    "venue": p.get("venue", ""),
                    "keywords": p.get("keywords", ""),
                    "doi": p.get("doi", ""),
                    "url": p.get("url", ""),
                    "pdf_url": p.get("pdf_url", ""),
                    "scholar_url": p.get("scholar_url", ""),
                    "semantic_scholar_url": p.get("semantic_scholar_url", ""),
                    "final_score": round(mmr_score, 4),
                    "content_score": round(content_scores.get(paper_id, 0.0), 4),
                    "citation_score": round(citation_scores.get(paper_id, 0.0), 4),
                    "user_score": round(user_interest_scores.get(paper_id, 0.0), 4),
                    "recency_score": round(recency_scores.get(paper_id, 0.0), 4),
                })

        else:
            # Default: Hybrid Weighted Linear Fusion
            ranked = compute_final_ranking(
                content_scores,
                citation_scores,
                user_interest_scores,
                weights=weights,
                top_k=top_k,
                recency_scores=recency_scores,
            )

            for paper_id, final_score, breakdown in ranked:
                p = papers_dict.get(paper_id, {})
                results.append({
                    "paper_id": paper_id,
                    "title": p.get("title", ""),
                    "authors": p.get("authors", ""),
                    "year": p.get("year", 0),
                    "abstract": p.get("abstract", ""),
                    "venue": p.get("venue", ""),
                    "keywords": p.get("keywords", ""),
                    "doi": p.get("doi", ""),
                    "url": p.get("url", ""),
                    "pdf_url": p.get("pdf_url", ""),
                    "scholar_url": p.get("scholar_url", ""),
                    "semantic_scholar_url": p.get("semantic_scholar_url", ""),
                    "final_score": round(final_score, 4),
                    "content_score": round(breakdown["content_score"], 4),
                    "citation_score": round(breakdown["citation_score"], 4),
                    "user_score": round(breakdown["user_score"], 4),
                    "recency_score": round(breakdown.get("recency_score", 0.0), 4),
                })

        conn.close()
        return jsonify({
            "query": query,
            "user_id": user_id,
            "algorithm": algorithm,
            "total_papers": len(papers),
            "results": results,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Citation Graph & Analytics Endpoints ────────────────────────────────────

@app.route("/api/graph/data", methods=["GET"])
def get_graph_data():
    """Return nodes and edges formatted for Cytoscape.js visualization."""
    _ensure_db()
    conn = get_connection(DB_PATH)
    papers = get_all_papers(conn)
    citations = get_citations(conn)
    conn.close()

    graph = build_citation_graph(citations)
    pr_scores = compute_pagerank(graph)
    hubs, authorities = compute_hits(graph)
    communities = detect_communities(graph)

    nodes = []
    for p in papers:
        pid = p["id"]
        nodes.append({
            "id": pid,
            "title": p["title"],
            "authors": p["authors"],
            "year": p["year"],
            "venue": p["venue"],
            "abstract": p["abstract"],
            "url": p.get("url", ""),
            "pdf_url": p.get("pdf_url", ""),
            "scholar_url": p.get("scholar_url", ""),
            "pagerank": round(pr_scores.get(pid, 0.0), 5),
            "authority_score": round(authorities.get(pid, 0.0), 5),
            "hub_score": round(hubs.get(pid, 0.0), 5),
            "community": communities.get(pid, 0),
        })

    edges = [{"source": c[0], "target": c[1]} for c in citations]
    return jsonify({"nodes": nodes, "edges": edges})


@app.route("/api/graph/analytics", methods=["GET"])
def get_graph_analytics_endpoint():
    """Return network science metrics and algorithm rankings."""
    _ensure_db()
    conn = get_connection(DB_PATH)
    citations = get_citations(conn)
    conn.close()

    graph = build_citation_graph(citations)
    analytics = compute_graph_analytics(graph)
    return jsonify(analytics)


@app.route("/api/graph/path", methods=["GET"])
def get_citation_path():
    """Calculate the shortest citation lineage path between two papers."""
    source_id = request.args.get("source_id", type=int)
    target_id = request.args.get("target_id", type=int)

    if not source_id or not target_id:
        return jsonify({"error": "source_id and target_id required"}), 400

    _ensure_db()
    conn = get_connection(DB_PATH)
    citations = get_citations(conn)
    conn.close()

    graph = build_citation_graph(citations)
    path = find_shortest_citation_path(graph, source_id, target_id)

    if path:
        return jsonify({"source_id": source_id, "target_id": target_id, "path": path, "length": len(path) - 1})
    return jsonify({"source_id": source_id, "target_id": target_id, "path": [], "length": -1})


# ── Papers CRUD ─────────────────────────────────────────────────────────────

@app.route("/api/papers", methods=["GET", "POST"])
def papers_endpoint():
    """List or add papers."""
    _ensure_db()
    conn = get_connection(DB_PATH)

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        title = data.get("title", "").strip()
        if not title:
            conn.close()
            return jsonify({"error": "Paper title is required"}), 400

        paper_id = insert_paper(
            conn,
            title=title,
            abstract=data.get("abstract", ""),
            authors=data.get("authors", "Unknown"),
            year=int(data.get("year", 2024)),
            keywords=data.get("keywords", ""),
            venue=data.get("venue", ""),
            doi=data.get("doi", ""),
        )
        conn.close()
        return jsonify({"success": True, "paper_id": paper_id})

    # GET papers
    papers = get_all_papers(conn)
    conn.close()
    return jsonify({"papers": papers, "count": len(papers)})


@app.route("/api/papers/<int:paper_id>", methods=["GET"])
def get_paper_details(paper_id: int):
    """Get single paper metadata and its citation links."""
    _ensure_db()
    conn = get_connection(DB_PATH)
    paper = get_paper_by_id(conn, paper_id)
    if not paper:
        conn.close()
        return jsonify({"error": "Paper not found"}), 404

    citations = get_citations(conn)
    conn.close()

    citing = [c[0] for c in citations if c[1] == paper_id]
    cited = [c[1] for c in citations if c[0] == paper_id]

    return jsonify({
        "paper": paper,
        "cited_by_paper_ids": citing,
        "references_paper_ids": cited,
    })


# ── User Bookmarks & Library ────────────────────────────────────────────────

@app.route("/api/bookmarks", methods=["GET", "POST"])
def bookmarks_endpoint():
    """Retrieve or save paper bookmarks."""
    _ensure_db()
    conn = get_connection(DB_PATH)

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        user_id = data.get("user_id", 1)
        paper_id = data.get("paper_id")
        status = data.get("status", "to_read")
        notes = data.get("notes", "")

        if not paper_id:
            conn.close()
            return jsonify({"error": "paper_id is required"}), 400

        success = add_bookmark(conn, user_id=int(user_id), paper_id=int(paper_id), status=status, notes=notes)
        conn.close()
        return jsonify({"success": success})

    user_id = request.args.get("user_id", default=1, type=int)
    bookmarks = get_bookmarks(conn, user_id)
    conn.close()
    return jsonify({"bookmarks": bookmarks, "count": len(bookmarks)})


@app.route("/api/bookmarks/<int:paper_id>", methods=["DELETE"])
def delete_bookmark_endpoint(paper_id: int):
    """Remove a paper bookmark."""
    _ensure_db()
    user_id = request.args.get("user_id", default=1, type=int)
    conn = get_connection(DB_PATH)
    removed = remove_bookmark(conn, user_id, paper_id)
    conn.close()
    return jsonify({"success": removed})


# ── Live arXiv Integration ──────────────────────────────────────────────────

@app.route("/api/arxiv/search", methods=["GET"])
def arxiv_search_endpoint():
    """Search arXiv preprints live."""
    query = request.args.get("query", "").strip()
    max_results = request.args.get("max_results", default=5, type=int)
    if not query:
        return jsonify({"results": []})
    results = search_arxiv(query, max_results=max_results)
    return jsonify({"results": results})


@app.route("/api/arxiv/import", methods=["POST"])
def arxiv_import_endpoint():
    """
    Import an arXiv paper into the database and link citations
    to existing related papers automatically.
    """
    _ensure_db()
    data = request.get_json(force=True, silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "Missing paper title"}), 400

    conn = get_connection(DB_PATH)

    # Insert paper
    new_id = insert_paper(
        conn,
        title=title,
        abstract=data.get("abstract", ""),
        authors=data.get("authors", "Unknown"),
        year=int(data.get("year", 2024)),
        keywords=data.get("keywords", ""),
        venue=data.get("venue", "arXiv"),
        doi=data.get("doi", ""),
    )

    # Link citations to top 2-3 most similar existing papers
    all_papers = get_all_papers(conn)
    if len(all_papers) > 1:
        tfidf_matrix, vectorizer, paper_ids = build_tfidf_matrix(all_papers)
        sim_scores = compute_paper_similarity(new_id, tfidf_matrix, paper_ids)
        # Exclude self
        sim_scores.pop(new_id, None)
        sorted_sim = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)

        for cited_pid, score in sorted_sim[:3]:
            if score > 0.05:
                insert_citation(conn, new_id, cited_pid)

    conn.close()
    return jsonify({"success": True, "paper_id": new_id})


# ── Export Citations ────────────────────────────────────────────────────────

@app.route("/api/export/bibtex", methods=["GET"])
def export_bibtex():
    """Export single paper or user's entire library as BibTeX."""
    _ensure_db()
    paper_id = request.args.get("paper_id", type=int)
    user_id = request.args.get("user_id", type=int)

    conn = get_connection(DB_PATH)

    if paper_id:
        paper = get_paper_by_id(conn, paper_id)
        conn.close()
        if not paper:
            return "Paper not found", 404
        return Response(to_bibtex(paper), mimetype="text/plain")

    if user_id:
        bookmarks = get_bookmarks(conn, user_id)
        conn.close()
        papers = []
        for b in bookmarks:
            papers.append({
                "title": b["title"],
                "authors": b["authors"],
                "year": b["year"],
                "venue": b["venue"],
                "doi": b["doi"],
            })
        bib_output = export_papers_bibtex(papers)
        return Response(
            bib_output,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment;filename=library_user_{user_id}.bib"},
        )

    conn.close()
    return "Specify paper_id or user_id", 400


# ── User Profile & Auth ─────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate a user."""
    _ensure_db()
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_connection(DB_PATH)
    user = get_user_by_username(conn, username)
    conn.close()

    if user and user["password_hash"] == _hash(password):
        return jsonify({
            "success": True,
            "user_id": user["id"],
            "username": user["username"],
            "interests": user.get("interests", ""),
        })
    return jsonify({"error": "Invalid username or password."}), 401


@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user account."""
    _ensure_db()
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    interests = data.get("interests", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters."}), 400

    conn = get_connection(DB_PATH)
    existing = get_user_by_username(conn, username)
    if existing:
        conn.close()
        return jsonify({"error": "Username is already taken."}), 409

    try:
        new_id = create_user(conn, username, _hash(password), interests)
        conn.close()
        return jsonify({
            "success": True,
            "user_id": new_id,
            "username": username,
            "interests": interests,
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/<int:user_id>", methods=["GET"])
def get_user_profile(user_id: int):
    """Get public user profile info."""
    _ensure_db()
    conn = get_connection(DB_PATH)
    user = get_user_by_id(conn, user_id)
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "user_id": user["id"],
        "username": user["username"],
        "interests": user.get("interests", ""),
    })


@app.route("/api/user/interests", methods=["POST"])
def update_interests():
    """Update user interests."""
    _ensure_db()
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")
    interests = data.get("interests", "")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection(DB_PATH)
    update_user_interests(conn, int(user_id), interests)
    conn.close()
    return jsonify({"success": True})



if __name__ == "__main__":
    _ensure_db()
    app.run(debug=True, port=5000)
