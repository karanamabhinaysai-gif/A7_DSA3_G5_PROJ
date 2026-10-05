"""
paper_analyzer.py — Manuscript Abstract Analyzer & Smart Citation Recommender.

Allows researchers or evaluators to paste an abstract or draft paper to:
1. Extract high-salience keyphrases.
2. Automatically classify the target research domain.
3. Recommend seminal papers to cite (Foundational References).
4. Discover contemporary related works.
"""

from typing import Dict, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from python_engine.content_similarity import build_tfidf_matrix
from python_engine.keyword_extractor import extract_keywords


DOMAINS = {
    "Computer Vision": ["image", "object detection", "segmentation", "resnet", "yolo", "cnn", "vision", "point cloud"],
    "Natural Language Processing": ["nlp", "bert", "transformer", "attention", "summarization", "language model", "sentiment"],
    "Machine Learning & Optimization": ["classification", "svm", "boosting", "xgboost", "automl", "federated", "transfer learning"],
    "Distributed Systems": ["distributed", "consensus", "raft", "paxos", "mapreduce", "kubernetes", "microservices", "stream"],
    "Database Systems": ["database", "nosql", "newsql", "query optimization", "spanner", "transactions", "graph database"],
}


def analyze_paper_text(text: str, papers: List[Dict], top_citations: int = 5) -> Dict:
    """
    Analyze manuscript text and provide automated citation suggestions and domain classification.
    """
    if not text or len(text.strip()) < 10:
        return {"error": "Input text too short. Please provide at least a couple of sentences."}

    # 1. Keyphrase extraction
    raw_keywords = extract_keywords(text, top_n=8)
    extracted_terms = [k for k, _ in raw_keywords]

    # 2. Domain classification based on keyword overlap
    text_lower = text.lower()
    domain_scores = {}
    for domain, terms in DOMAINS.items():
        score = sum(1 for t in terms if t in text_lower)
        domain_scores[domain] = score

    primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if max(domain_scores.values()) > 0 else "Computer Science (General)"

    # 3. Vector Space Matching against Corpus
    tfidf_matrix, vectorizer, paper_ids = build_tfidf_matrix(papers)
    query_vec = vectorizer.transform([text])
    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    papers_dict = {p["id"]: p for p in papers}
    ranked_indices = np.argsort(sim_scores)[::-1]

    foundational = []
    recent_works = []

    for idx in ranked_indices:
        pid = paper_ids[idx]
        score = float(sim_scores[idx])
        p = papers_dict.get(pid, {})
        year = p.get("year", 2020)

        paper_item = {
            "id": pid,
            "title": p.get("title", ""),
            "authors": p.get("authors", ""),
            "year": year,
            "venue": p.get("venue", ""),
            "abstract": p.get("abstract", "")[:200] + "...",
            "similarity_score": round(score, 4),
            "url": p.get("url", ""),
            "pdf_url": p.get("pdf_url", ""),
            "scholar_url": p.get("scholar_url", ""),
        }

        if year <= 2019 and len(foundational) < top_citations and score > 0.05:
            foundational.append(paper_item)
        elif year >= 2020 and len(recent_works) < top_citations and score > 0.05:
            recent_works.append(paper_item)

        if len(foundational) >= top_citations and len(recent_works) >= top_citations:
            break

    return {
        "primary_domain": primary_domain,
        "extracted_keywords": extracted_terms,
        "word_count": len(text.split()),
        "recommended_foundational_citations": foundational,
        "related_contemporary_papers": recent_works,
    }
