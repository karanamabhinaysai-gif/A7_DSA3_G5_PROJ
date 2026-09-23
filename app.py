"""
app.py — Flask web application for the Smart Research Paper Recommendation System.

Serves as the Vercel entrypoint and provides a web API + simple UI.
"""

import hashlib
import json
import os
import sys

from flask import Flask, jsonify, render_template_string, request

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from python_engine.db import (
    get_connection,
    get_all_papers,
    get_citations,
    get_user_by_id,
    get_user_by_username,
    get_user_history,
    add_user_history,
)
from python_engine.content_similarity import build_tfidf_matrix, compute_query_similarity
from python_engine.citation_graph import build_citation_graph, compute_citation_score
from python_engine.user_matching import compute_user_interest_score, compute_history_boost
from python_engine.ranking import compute_final_ranking

app = Flask(__name__)

DB_PATH = os.path.join(PROJECT_ROOT, "database", "papers.db")


def _ensure_db():
    """Seed the database if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        from data.seed_data import seed_database
        seed_database()


def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ── API Routes ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve a simple web UI."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/recommend", methods=["GET", "POST"])
def recommend():
    """
    Recommendation API endpoint.

    Query params or JSON body:
        query (str): search query
        user_id (int, optional): user ID for personalization
        top_k (int, optional): number of results (default 10)
    """
    _ensure_db()

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
    else:
        data = request.args.to_dict()

    query = data.get("query", "").strip()
    user_id = data.get("user_id")
    top_k = int(data.get("top_k", 10))

    if not query:
        return jsonify({"error": "No search query provided."}), 400

    if user_id is not None:
        user_id = int(user_id)

    try:
        conn = get_connection(DB_PATH)
        papers = get_all_papers(conn)
        citations = get_citations(conn)
        user = get_user_by_id(conn, user_id) if user_id else None

        # Content similarity
        tfidf_matrix, vectorizer, paper_ids = build_tfidf_matrix(papers)
        content_scores = compute_query_similarity(query, tfidf_matrix, vectorizer, paper_ids)

        # Citation scores
        citation_graph = build_citation_graph(citations)
        sorted_content = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
        n_seeds = max(1, len(sorted_content) // 5)
        query_relevant_ids = [pid for pid, _ in sorted_content[:n_seeds] if content_scores[pid] > 0]
        citation_scores = compute_citation_score(citation_graph, query_relevant_ids, paper_ids)

        # User interest scores
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
                    user_interest_scores[pid] = (interest + history) / 2.0
        else:
            user_interest_scores = {pid: 0.0 for pid in paper_ids}

        # Rank
        ranked = compute_final_ranking(content_scores, citation_scores, user_interest_scores, top_k=top_k)

        results = []
        papers_dict = {p["id"]: p for p in papers}
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
                "final_score": round(final_score, 4),
                "content_score": round(breakdown["content_score"], 4),
                "citation_score": round(breakdown["citation_score"], 4),
                "user_score": round(breakdown["user_score"], 4),
            })

        conn.close()
        return jsonify({"query": query, "user_id": user_id, "results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate a user."""
    _ensure_db()
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    conn = get_connection(DB_PATH)
    user = get_user_by_username(conn, username)
    conn.close()

    if user and user["password_hash"] == _hash(password):
        return jsonify({"user_id": user["id"], "username": user["username"], "interests": user["interests"]})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/papers", methods=["GET"])
def list_papers():
    """List all papers."""
    _ensure_db()
    conn = get_connection(DB_PATH)
    papers = get_all_papers(conn)
    conn.close()
    return jsonify({"papers": papers, "count": len(papers)})


# ── HTML Template (Single-Page UI) ────────────────────────────────────────

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Research Paper Recommendation System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; color: #1f2937; }
        .header { background: #1e40af; color: white; padding: 24px; text-align: center; }
        .header h1 { font-size: 1.8rem; margin-bottom: 4px; }
        .header p { opacity: 0.85; font-size: 0.95rem; }
        .container { max-width: 900px; margin: 0 auto; padding: 24px; }
        .search-box { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }
        .search-row { display: flex; gap: 12px; flex-wrap: wrap; }
        .search-row input[type="text"] { flex: 1; min-width: 200px; padding: 12px 16px; border: 2px solid #dbeafe; border-radius: 8px; font-size: 1rem; outline: none; }
        .search-row input[type="text"]:focus { border-color: #2563eb; }
        .search-row input[type="number"] { width: 80px; padding: 12px; border: 2px solid #dbeafe; border-radius: 8px; font-size: 1rem; text-align: center; }
        .search-row select { padding: 12px; border: 2px solid #dbeafe; border-radius: 8px; font-size: 1rem; }
        .btn { background: #2563eb; color: white; border: none; padding: 12px 28px; border-radius: 8px; font-size: 1rem; cursor: pointer; font-weight: 600; }
        .btn:hover { background: #1d4ed8; }
        .btn:disabled { background: #93c5fd; cursor: not-allowed; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #2563eb; }
        .card h3 { color: #1e40af; margin-bottom: 6px; font-size: 1.1rem; }
        .card .meta { color: #6b7280; font-size: 0.9rem; margin-bottom: 8px; }
        .card .abstract { color: #374151; font-size: 0.95rem; line-height: 1.5; margin-bottom: 10px; }
        .scores { display: flex; gap: 12px; flex-wrap: wrap; }
        .score-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
        .score-overall { background: #dbeafe; color: #1e40af; }
        .score-content { background: #dcfce7; color: #166534; }
        .score-citation { background: #fef9c3; color: #854d0e; }
        .score-user { background: #fce7f3; color: #9d174d; }
        .empty { text-align: center; padding: 48px; color: #9ca3af; }
        .loading { text-align: center; padding: 32px; color: #6b7280; }
        .team { text-align: center; padding: 24px; color: #9ca3af; font-size: 0.85rem; margin-top: 24px; }
        .error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Smart Research Paper Recommendation System</h1>
        <p>KL University — Dept. of Computer Science & Engineering — Section A7</p>
    </div>
    <div class="container">
        <div class="search-box">
            <div class="search-row">
                <input type="text" id="query" placeholder="Search research papers... (e.g. machine learning, NLP, computer vision)" />
                <select id="user">
                    <option value="">No user (anonymous)</option>
                    <option value="1">Alice (ML/DL)</option>
                    <option value="2">Bob (NLP/IR)</option>
                    <option value="3">Charlie (CV/DL)</option>
                </select>
                <input type="number" id="topk" value="10" min="1" max="50" title="Top-K results" />
                <button class="btn" id="searchBtn" onclick="search()">Search</button>
            </div>
        </div>
        <div id="error"></div>
        <div id="results">
            <div class="empty">Enter a search query to get personalized paper recommendations</div>
        </div>
    </div>
    <div class="team">
        Team: Abhinay Sai (2510030103) · K V Srinath (2510030106) · Poli Naidu (2510030160) · Chandu (2510030083)
    </div>
    <script>
        const $ = id => document.getElementById(id);
        $('query').addEventListener('keydown', e => { if (e.key === 'Enter') search(); });

        async function search() {
            const query = $('query').value.trim();
            if (!query) return;
            const userId = $('user').value || null;
            const topK = $('topk').value || 10;

            $('searchBtn').disabled = true;
            $('searchBtn').textContent = 'Searching...';
            $('error').innerHTML = '';
            $('results').innerHTML = '<div class="loading">⏳ Analyzing papers and computing recommendations...</div>';

            try {
                const params = new URLSearchParams({ query, top_k: topK });
                if (userId) params.append('user_id', userId);
                const res = await fetch('/api/recommend?' + params);
                const data = await res.json();

                if (data.error) {
                    $('error').innerHTML = '<div class="error">⚠️ ' + data.error + '</div>';
                    $('results').innerHTML = '';
                    return;
                }

                if (!data.results || data.results.length === 0) {
                    $('results').innerHTML = '<div class="empty">No results found for "' + query + '"</div>';
                    return;
                }

                $('results').innerHTML = data.results.map((r, i) => `
                    <div class="card">
                        <h3>${i + 1}. ${r.title}</h3>
                        <div class="meta">${r.authors} · ${r.year} · ${r.venue}</div>
                        <div class="abstract">${r.abstract}</div>
                        <div class="scores">
                            <span class="score-badge score-overall">Overall: ${r.final_score.toFixed(3)}</span>
                            <span class="score-badge score-content">Content: ${r.content_score.toFixed(3)}</span>
                            <span class="score-badge score-citation">Citation: ${r.citation_score.toFixed(3)}</span>
                            <span class="score-badge score-user">Interest: ${r.user_score.toFixed(3)}</span>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                $('error').innerHTML = '<div class="error">⚠️ ' + err.message + '</div>';
                $('results').innerHTML = '';
            } finally {
                $('searchBtn').disabled = false;
                $('searchBtn').textContent = 'Search';
            }
        }
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    _ensure_db()
    app.run(debug=True, port=5000)
