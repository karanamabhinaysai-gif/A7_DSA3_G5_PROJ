"""
user_matching.py — User interest matching and history-based boosting.

Computes how well each paper aligns with a user's stated interests
and their reading history using lexical and vector space similarity.
"""

from typing import Dict, List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_user_interest_score(user: Optional[Dict], papers: List[Dict]) -> Dict[int, float]:
    """
    Compute interest-match scores between user interests and papers.

    Uses a blend of multi-word phrase matching and token overlap against
    paper title, keywords, and abstract.

    Args:
        user: dict with 'interests' (comma-separated string)
        papers: list of paper dicts with 'id', 'title', 'keywords', 'abstract'

    Returns:
        dict {paper_id: score} with scores normalized to [0, 1]
    """
    if not user or not user.get('interests'):
        return {p['id']: 0.0 for p in papers}

    raw_interests = [i.strip().lower() for i in user['interests'].split(',') if i.strip()]
    if not raw_interests:
        return {p['id']: 0.0 for p in papers}

    scores = {}
    for paper in papers:
        title = (paper.get('title') or '').lower()
        keywords = (paper.get('keywords') or '').lower()
        abstract = (paper.get('abstract') or '').lower()
        text = f"{title} {keywords} {abstract}"

        match_count = 0.0
        for interest in raw_interests:
            # High reward for keyword and title matches
            if interest in title:
                match_count += 1.0
            elif interest in keywords:
                match_count += 0.8
            elif interest in text:
                match_count += 0.6
            else:
                # Sub-token overlap
                tokens = interest.split()
                if tokens and all(t in text for t in tokens):
                    match_count += 0.4

        score = match_count / len(raw_interests)
        scores[paper['id']] = min(1.0, round(score, 4))

    return scores


def compute_history_boost(
    user_history_paper_ids: List[int],
    papers: List[Dict],
    tfidf_matrix,
    vectorizer,
    paper_ids: List[int],
) -> Dict[int, float]:
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

    return {pid: round(float(score) / max_score, 4) for pid, score in zip(paper_ids, sim_scores)}
