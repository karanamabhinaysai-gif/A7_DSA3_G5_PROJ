"""
user_matching.py — User interest matching and history-based boosting.

Computes how well each paper aligns with a user's stated interests
and their reading history.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_user_interest_score(user, papers):
    """
    Compute interest-match scores between user interests and papers.

    Matches user interest phrases (e.g. "machine learning") against paper
    title, keywords, and abstract using substring matching. This handles
    both single-word and multi-word interest terms.

    Args:
        user: dict with 'interests' (comma-separated string)
        papers: list of paper dicts with 'id', 'title', 'keywords', 'abstract'

    Returns:
        dict {paper_id: score} with scores normalized to [0, 1]
    """
    if not user or not user.get('interests'):
        return {p['id']: 0.0 for p in papers}

    # Parse user interests into individual phrases
    user_interests = [i.strip().lower() for i in user['interests'].split(',') if i.strip()]
    if not user_interests:
        return {p['id']: 0.0 for p in papers}

    scores = {}
    for paper in papers:
        # Combine all text fields for matching
        text = ' '.join([
            paper.get('title', ''),
            paper.get('keywords', ''),
            paper.get('abstract', ''),
        ]).lower()

        # Count how many user interests appear in the paper text
        matches = sum(1 for interest in user_interests if interest in text)
        score = matches / len(user_interests)
        scores[paper['id']] = min(1.0, score)

    return scores


def compute_history_boost(user_history_paper_ids, papers, tfidf_matrix, vectorizer, paper_ids):
    """
    Boost scores for papers similar to the user's previously viewed papers.

    Computes the average TF-IDF vector of the user's history and measures
    cosine similarity against all papers.

    Args:
        user_history_paper_ids: list of paper IDs the user has interacted with
        papers: list of paper dicts
        tfidf_matrix: pre-built TF-IDF matrix
        vectorizer: fitted TfidfVectorizer
        paper_ids: list of paper IDs corresponding to matrix rows

    Returns:
        dict {paper_id: score} normalized to [0, 1]
    """
    if not user_history_paper_ids:
        return {pid: 0.0 for pid in paper_ids}

    history_indices = [paper_ids.index(pid) for pid in user_history_paper_ids if pid in paper_ids]
    if not history_indices:
        return {pid: 0.0 for pid in paper_ids}

    history_vecs = tfidf_matrix[history_indices]
    avg_history_vec = np.mean(history_vecs, axis=0)

    sim_scores = cosine_similarity(np.asarray(avg_history_vec), tfidf_matrix).flatten()

    max_score = np.max(sim_scores) if len(sim_scores) > 0 and np.max(sim_scores) > 0 else 1.0

    return {pid: float(score) / max_score for pid, score in zip(paper_ids, sim_scores)}
