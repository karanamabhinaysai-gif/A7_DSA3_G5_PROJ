from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Tuple
from python_engine.bm25 import BM25Okapi


def build_tfidf_matrix(papers: List[Dict]):
    """
    Build TF-IDF matrix from paper titles, abstracts, and keywords.
    """
    paper_ids = [p['id'] for p in papers]
    corpus = [
        f"{p.get('title', '')} {p.get('keywords', '')} {p.get('abstract', '')}"
        for p in papers
    ]

    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # unigrams and bigrams
        sublinear_tf=True
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    return tfidf_matrix, vectorizer, paper_ids


def compute_query_similarity(query: str, tfidf_matrix, vectorizer, paper_ids: List[int]) -> Dict[int, float]:
    """
    Compute cosine similarity between query and all papers in the TF-IDF space.
    """
    if not query:
        return {pid: 0.0 for pid in paper_ids}

    query_vec = vectorizer.transform([query])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    return {pid: float(score) for pid, score in zip(paper_ids, sim_scores)}


def compute_paper_similarity(paper_id: int, tfidf_matrix, paper_ids: List[int]) -> Dict[int, float]:
    """
    Compute pairwise similarity of paper_id against all other papers.
    """
    try:
        idx = paper_ids.index(paper_id)
    except ValueError:
        return {pid: 0.0 for pid in paper_ids}

    paper_vec = tfidf_matrix[idx]
    sim_scores = cosine_similarity(paper_vec, tfidf_matrix).flatten()

    return {pid: float(score) for pid, score in zip(paper_ids, sim_scores)}


def compute_bm25_similarity(query: str, papers: List[Dict]) -> Dict[int, float]:
    """
    Compute relevance scores using Okapi BM25.
    """
    bm25 = BM25Okapi()
    bm25.fit(papers)
    return bm25.compute_query_scores(query)


def compute_hybrid_content_similarity(
    query: str,
    papers: List[Dict],
    tfidf_matrix,
    vectorizer,
    paper_ids: List[int],
    bm25_weight: float = 0.5,
) -> Dict[int, float]:
    """
    Blend TF-IDF Cosine Similarity and Okapi BM25 for superior information retrieval.
    """
    tfidf_scores = compute_query_similarity(query, tfidf_matrix, vectorizer, paper_ids)
    bm25_scores = compute_bm25_similarity(query, papers)

    hybrid = {}
    for pid in paper_ids:
        t_score = tfidf_scores.get(pid, 0.0)
        b_score = bm25_scores.get(pid, 0.0)
        hybrid[pid] = (1.0 - bm25_weight) * t_score + bm25_weight * b_score

    return hybrid
