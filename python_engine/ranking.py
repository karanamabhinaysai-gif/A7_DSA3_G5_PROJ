"""
ranking.py — Hybrid Ranking, Reciprocal Rank Fusion (RRF), and MMR Diversity Reranking.

Implements multi-signal scoring, rank fusion, and diversity-preserving
Maximal Marginal Relevance (MMR) for recommendation.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np


def compute_final_ranking(
    content_scores: Dict[int, float],
    citation_scores: Dict[int, float],
    user_scores: Dict[int, float],
    weights: Optional[Dict[str, float]] = None,
    top_k: int = 10,
    recency_scores: Optional[Dict[int, float]] = None,
) -> List[Tuple[int, float, Dict[str, float]]]:
    """
    Compute multi-signal weighted score fusion for papers.

    Default weights:
        content: 0.5, citation: 0.3, user_interest: 0.2
    """
    if weights is None:
        weights = {"content": 0.5, "citation": 0.3, "user_interest": 0.2}

    w_content = weights.get("content", 0.5)
    w_citation = weights.get("citation", 0.3)
    w_user = weights.get("user_interest", 0.2)
    w_recency = weights.get("recency", 0.0)

    all_paper_ids = (
        set(content_scores.keys())
        | set(citation_scores.keys())
        | set(user_scores.keys())
    )

    results = []
    for pid in all_paper_ids:
        c_score = content_scores.get(pid, 0.0)
        cit_score = citation_scores.get(pid, 0.0)
        u_score = user_scores.get(pid, 0.0)
        r_score = recency_scores.get(pid, 0.0) if recency_scores else 0.0

        final_score = (
            w_content * c_score
            + w_citation * cit_score
            + w_user * u_score
            + w_recency * r_score
        )

        breakdown = {
            "content_score": c_score,
            "citation_score": cit_score,
            "user_score": u_score,
            "recency_score": r_score,
        }

        results.append((pid, final_score, breakdown))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def compute_reciprocal_rank_fusion(
    ranked_lists: List[List[int]],
    k: int = 60,
    top_k: int = 10,
) -> List[Tuple[int, float]]:
    """
    Reciprocal Rank Fusion (RRF).

    Combines multiple rankings (e.g. Content rank, Citation rank, User rank)
    without requiring scale normalization.
    RRF Score(d) = sum_{m in rankings} 1 / (k + rank_m(d))
    """
    rrf_scores: Dict[int, float] = {}

    for rank_list in ranked_lists:
        for rank, paper_id in enumerate(rank_list):
            rrf_scores[paper_id] = rrf_scores.get(paper_id, 0.0) + (1.0 / (k + rank + 1))

    sorted_papers = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_papers[:top_k]


def compute_mmr_ranking(
    candidate_scores: Dict[int, float],
    tfidf_matrix,
    paper_ids: List[int],
    lambda_param: float = 0.7,
    top_k: int = 10,
) -> List[Tuple[int, float]]:
    """
    Maximal Marginal Relevance (MMR) Diversity Reranking.

    Balances query relevance and topic diversity to avoid recommending near-identical papers.
    MMR = argmax_{p in R / S} [ lambda * Sim(p, Q) - (1 - lambda) * max_{s in S} Sim(p, s) ]
    """
    from sklearn.metrics.pairwise import cosine_similarity

    id_to_idx = {pid: idx for idx, pid in enumerate(paper_ids)}
    candidates = [pid for pid in candidate_scores.keys() if pid in id_to_idx]

    if not candidates:
        return []

    # Sort initial candidates by relevance
    candidates.sort(key=lambda pid: candidate_scores[pid], reverse=True)

    selected: List[int] = []
    selected_scores: List[float] = []

    # Greedily pick the highest scoring first paper
    best_first = candidates[0]
    selected.append(best_first)
    selected_scores.append(candidate_scores[best_first])
    candidates.remove(best_first)

    # Pre-extract vector representations
    while len(selected) < min(top_k, len(paper_ids)) and candidates:
        selected_vectors = tfidf_matrix[[id_to_idx[s] for s in selected]]

        best_candidate = None
        best_mmr_score = -float("inf")

        for cand in candidates:
            cand_vec = tfidf_matrix[id_to_idx[cand]]
            relevance = candidate_scores.get(cand, 0.0)

            # Max similarity to already selected papers
            sims = cosine_similarity(cand_vec, selected_vectors).flatten()
            max_sim = float(np.max(sims)) if len(sims) > 0 else 0.0

            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_sim

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate = cand

        if best_candidate is not None:
            selected.append(best_candidate)
            selected_scores.append(candidate_scores[best_candidate])
            candidates.remove(best_candidate)
        else:
            break

    return list(zip(selected, selected_scores))


def compute_recency_scores(
    papers: List[Dict],
    current_year: int = 2026,
    half_life_years: float = 5.0,
) -> Dict[int, float]:
    """
    Compute temporal recency score with exponential decay.
    Papers published recently receive higher scores; foundational papers receive lower recency.
    """
    scores = {}
    decay_constant = np.log(2) / half_life_years

    for p in papers:
        year = p.get("year") or 2020
        age = max(0, current_year - year)
        # Exponential decay: 2^(-age / half_life)
        score = np.exp(-decay_constant * age)
        scores[p["id"]] = float(round(score, 4))

    return scores
